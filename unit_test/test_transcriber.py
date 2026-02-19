import sys
import os
import argparse

# Add parent directory to path to import utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.transcriber import transcribe_audio

class DummyLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    def critical(self, msg):
        print(f"[CRITICAL] {msg}")
    def error(self, msg):
        print(f"[ERROR] {msg}")

def main():
    parser = argparse.ArgumentParser(description="Test Transcriber")
    parser.add_argument("audio_file", nargs="?", help="Path to the audio file to transcribe", default="/Users/hao/hao/vibe_coding_project/YouTube_Summarizer_App/output/Trigger_2026-02-19_01-45-00_From_2026-02-15_00-00-00_2026-02-19_23-59-00/kLLOxiUsZx4.m4a")
    args = parser.parse_args()
    
    audio_path = args.audio_file
    model_name = "mlx-community/whisper-large-v3-turbo"
    logger = DummyLogger()

    print(f"Starting transcription for {audio_path}...")
    
    if not os.path.exists(audio_path):
        print(f"Error: Audio file not found at {audio_path}")
        return

    transcript = transcribe_audio(audio_path, model_name, logger)
    
    output_file = os.path.join(os.path.dirname(__file__), "test_transcript.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(transcript)
        
    print(f"\nTranscript saved to {output_file}")

if __name__ == "__main__":
    main()
