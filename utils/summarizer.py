from google import genai
import os

def summarize_transcript(transcript_text, logger, api_key=None, model_name="models/gemini-2.5-flash"):
    """
    Summarizes the transcript using Google Gemini.
    Returns a dict with summary, outline, etc.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        
    if not api_key:
        logger.critical("Gemini API Key is missing.")
        return None

    logger.info(f"Generating summary with Gemini ({model_name})...")
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Analyze the following transcript and provide:\n"
            "1. A concise summary.\n"
            "2. A structured outline.\n"
            "3. Key takeaways.\n\n"
            "Transcript:\n"
            f"{transcript_text[:30000]}" # Truncate if too long
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
