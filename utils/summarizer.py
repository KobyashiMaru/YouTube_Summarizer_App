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
            "Analyze the following youtube f{video_link} link and provide:\n"
            "1. A concise summary.\n"
            "2. A structured outline.\n"
            "3. Key takeaways.\n\n"
        )
        
        abstract_response = client.models.generate_content(
            model=model_name,
            contents=[prompt]
        )

        logger.info(f"(2/2) Generating summary with Gemini ({model_name})...")

        prompt = (
            "Analyze the following transcript and abstract, and provide:\n"
            "1. A concise summary.\n"
            "2. A structured outline.\n"
            "3. Key takeaways.\n\n"
            "Transcript:\n"
            f"{transcript_text[:80000]}\n\n"
            "Abstract:\n"
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
