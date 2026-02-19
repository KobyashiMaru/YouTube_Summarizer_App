import sys
import os

# Ensure the root of the project is in the Python path
sys.path.append(os.getcwd())

from utils.transcriber import transcribe_audio

class DummyLogger:
    def info(self, msg):
        print(f"[INFO] {msg}")
    def critical(self, msg):
        print(f"[CRITICAL] {msg}")
    def error(self, msg):
        print(f"[ERROR] {msg}")

def main():
    audio_path = "/Users/hao/hao/vibe_coding_project/YouTube_Summarizer_App/output/Trigger_2026-02-19_01-45-00_From_2026-02-15_00-00-00_2026-02-19_23-59-00/kLLOxiUsZx4.m4a"
    model_name = "mlx-community/whisper-large-v3-turbo"
    logger = DummyLogger()

    print(f"Starting transcription for {audio_path}...")
    transcript = transcribe_audio(audio_path, model_name, logger)
    print("\n--- TRANSCRIPT ---")
    print(transcript)
    print("--- END TRANSCRIPT ---")

if __name__ == "__main__":
    main()
