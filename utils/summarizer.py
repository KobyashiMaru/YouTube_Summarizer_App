from google import genai
import os

def summarize_transcript(transcript_text, logger, api_key=None):
    """
    Summarizes the transcript using Google Gemini.
    Returns a dict with summary, outline, etc.
    """
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
        
    if not api_key:
        logger.critical("Gemini API Key is missing.")
        return None

    logger.info("Generating summary with Gemini...")
    
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = (
            "Analyze the following transcript and provide:\n"
            "1. A concise summary.\n"
            "2. A structured outline.\n"
            "3. Key takeaways.\n\n"
            "Transcript:\n"
            f"{transcript_text[:30000]}" # Truncate if too long, though 1.5 Flash has 1M context. 
            # Better to not truncate unless necessary, but safeguard for now. 
            # Actually, 1.5 Flash can handle huge context, let's remove truncation or make it large.
        )
        
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=[prompt]
        )
        
        return {
            "summary_content": response.text, 
            "detailed_transcript": transcript_text
        }
    except Exception as e:
        logger.critical(f"Error generation summary: {e}")
        return None
