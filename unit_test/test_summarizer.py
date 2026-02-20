import sys
import os
from dotenv import load_dotenv

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

from utils.summarizer import summarize_transcript

class DummyLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    def critical(self, msg):
        print(f"[CRITICAL] {msg}")
    def error(self, msg):
        print(f"[ERROR] {msg}")
    def warning(self, msg):
        print(f"[WARNING] {msg}")

def main():
    transcript_file = os.path.join(os.path.dirname(__file__), "test_transcript.txt")
    
    if not os.path.exists(transcript_file):
        print(f"Error: Transcript file not found at {transcript_file}. Please run test_transcriber.py first.")
        return

    print(f"Reading transcript from {transcript_file}...")
    with open(transcript_file, "r", encoding="utf-8") as f:
        transcript_text = f.read()

    video_link = "https://www.youtube.com/watch?v=kLLOxiUsZx4" # Dummy link or actual if known
    logger = DummyLogger()
    api_key_input = os.getenv("GEMINI_API_KEY")
    
    if not api_key_input:
        print("Error: GEMINI_API_KEY not found in environment.")
        return

    # Parse keys similarly to app.py
    raw_keys = api_key_input.replace(",", "\n").split("\n")
    api_keys = [k.strip() for k in raw_keys if k.strip()]

    print(f"Loaded {len(api_keys)} API keys.")

    print("Generating summary...")
    # Pass api_keys list instead of single api_key
    summary_data = summarize_transcript(transcript_text, video_link, logger, api_keys=api_keys)
    
    if summary_data:
        output_file = os.path.join(os.path.dirname(__file__), "test_summary.md")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("# Summary Output\n\n")
            f.write(summary_data.get('summary_content', 'No content'))
            
        print(f"\nSummary saved to {output_file}")
    else:
        print("Failed to generate summary.")

if __name__ == "__main__":
    main()
