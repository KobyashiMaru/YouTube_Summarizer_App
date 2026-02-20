from google import genai
import os
import time

def call_gemini_with_retry(api_keys, model, prompt, logger, max_retries=20, delay=10, current_key_index=0):
    """
    Calls Gemini API with:
    1. Retry mechanism for 503 errors (wait and retry same key).
    2. Rotation mechanism for 429 errors (switch to next key and wait).
    """
    
    if not api_keys:
        logger.critical("No API keys available.")
        return None
        
    attempt = 1
    num_keys = len(api_keys)
    
    while attempt <= max_retries:
        api_key = api_keys[current_key_index]
        client = genai.Client(api_key=api_key)

        # logger.info(f"Using API key {api_key}, index {current_key_index}")
        
        try:
            return client.models.generate_content(
                model=model,
                contents=[prompt]
            )
        except Exception as e:
            error_str = str(e)
            
            # Case 1: 429 Quota Exceeded -> Rotate Key
            if "429" in error_str or "quota" in error_str.lower():
                logger.warning(f"Quota exceeded (429) on key index {current_key_index}. Switching to next key...")
                
                # Move to next key
                current_key_index = (current_key_index + 1) % num_keys
                attempt += 1
                
                if current_key_index == 0:
                    # Cycled through all keys, wait before trying the first one again
                    logger.warning(f"Cycled through all {num_keys} keys. Waiting {delay} seconds before retrying...")
                    time.sleep(delay)
                else:
                    # Brief delay between key switches
                    time.sleep(1)
                
                continue
            
            # Case 2: 503 Service Unavailable -> Wait and Retry same key
            elif "503" in error_str or "UNAVAILABLE" in error_str:
                if attempt < max_retries:
                    logger.warning(f"Model currently unavailable (503). Retrying {attempt}/{max_retries} in {delay} seconds...\nError details: {e}")
                    print(f"System sleeping for {delay} seconds due to 503 error...") 
                    time.sleep(delay)
                    attempt += 1
                    continue
            
            # If not 503/429 or retries exhausted, re-raise
            raise e
            
    logger.error(f"Exhausted {max_retries} attempts.")
    return None

def summarize_transcript(transcript_text, video_link, logger, api_keys=None, abstract_model="models/gemini-2.5-flash-lite", summary_model="models/gemini-2.5-pro"):
    """
    Summarizes the transcript using Google Gemini.
    Returns a dict with summary, outline, etc.
    """
    # Helper to support legacy single key arg if needed, but app.py sends list now
    if not api_keys:
        # Fallback to env var if not passed
        env_key = os.getenv("GEMINI_API_KEY")
        if env_key:
            api_keys = [env_key]
        
    if not api_keys:
        logger.critical("Gemini API Key is missing.")
        return None

    logger.info(f"Generating response with Gemini...")
    logger.info(f"Abstract Model: {abstract_model}")
    logger.info(f"Summary Model: {summary_model}")
    logger.info(f"Available Keys: {len(api_keys)}")
    
    try:
        # Client initialization is now handled inside call_gemini_with_retry per call/key
        
        logger.info(f"(1/2) Generating abstract with Gemini ({abstract_model})...")
        
        prompt_abstract = (
            f"使用繁體中文，分析以下 YouTube 影片連結 {video_link} 並提供：\n"
            "1. 簡明摘要\n"
            "2. 結構化提綱\n"
            "3. 主要結論\n\n"
        )
        
        abstract_response = call_gemini_with_retry(api_keys, abstract_model, prompt_abstract, logger)
        if not abstract_response:
             return None

        logger.info(f"(2/2) Generating summary with Gemini ({summary_model})...")

        prompt_summary = (
            "使用繁體中文，分析以下文字稿和摘要，並提供以下資訊:\n"
            "1. 簡明摘要\n"
            "2. 結構化提綱\n"
            "3. 主要結論\n\n"
            "逐字稿:\n"
            f"{transcript_text[:80000]}\n\n"
            "摘要:\n"
            f"{abstract_response.text}"
        )
        
        response = call_gemini_with_retry(api_keys, summary_model, prompt_summary, logger)
        if not response:
            return None
            
        return {
            "summary_content": response.text, 
            "detailed_transcript": transcript_text
        }
    except Exception as e:
        logger.critical(f"Error generation summary: {e}")
        return None
