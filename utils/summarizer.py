from google import genai
import os

def summarize_transcript(transcript_text, video_link, logger, api_key=None, model_name="models/gemini-2.5-flash"):
    """
    Summarizes the transcript using Google Gemini.
    Returns a dict with summary, outline, etc.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        
    if not api_key:
        logger.critical("Gemini API Key is missing.")
        return None

    logger.info(f"Generating response with Gemini ({model_name})...")
    
    try:
        client = genai.Client(api_key=api_key)

        logger.info(f"(1/2) Generating abstract with Gemini ({model_name})...")
        
        prompt = (
            "使用繁體中文，分析以下 YouTube 影片連結 f{video_link} 並提供：\n"
            "1. 簡明摘要\n"
            "2. 結構化提綱\n"
            "3. 主要結論\n\n"
        )
        
        abstract_response = client.models.generate_content(
            model=model_name,
            contents=[prompt]
        )

        logger.info(f"(2/2) Generating summary with Gemini ({model_name})...")

        prompt = (
            "使用繁體中文，分析以下文字稿和摘要，並提供以下資訊:\n"
            "1. 簡明摘要\n"
            "2. 結構化提綱\n"
            "3. 主要結論\n\n"
            "逐字稿:\n"
            f"{transcript_text[:80000]}\n\n"
            "摘要:\n"
            f"{abstract_response.text}"
        )
        
        response = client.models.generate_content(
            model=model_name,
            contents=[prompt]
        )
        
        return {
            "summary_content": response.text, 
            "detailed_transcript": transcript_text
        }
    except Exception as e:
        logger.critical(f"Error generation summary: {e}")
        return None
