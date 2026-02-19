import mlx_whisper
import sys
import re
import ffmpeg
import threading
import time
from io import StringIO

def get_audio_duration(file_path):
    """
    Get the duration of the audio file in seconds using ffmpeg-python.
    """
    try:
        probe = ffmpeg.probe(file_path)
        return float(probe['format']['duration'])
    except Exception as e:
        print(f"Error getting duration: {e}")
        return None

class ProgressCapturer:
    def __init__(self, logger, total_duration):
        self.logger = logger
        self.total_duration = total_duration
        self._stdout = None
        self._original_stdout = None
        self._buffer = ""
        # Regex to capture timestamp from mlx_whisper output: [00:00.000 --> 00:07.480]
        self._pattern = re.compile(r"-->\s*(\d{2}):(\d{2})\.(\d{3})")
        self._last_log_time = 0
        self._log_interval = 2.0  # Log every 2 seconds to avoid flooding

    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout = self._original_stdout

    def write(self, data):
        # Pass through to original stdout so it still shows in terminal
        self._original_stdout.write(data)
        
        # Buffer checking for pattern
        self._buffer += data
        # Process lines
        while '\n' in self._buffer:
            line, self._buffer = self._buffer.split('\n', 1)
            self._process_line(line)

    def flush(self):
        self._original_stdout.flush()

    def _process_line(self, line):
        # Expected format: [00:00.000 --> 00:07.480] ... text ...
        match = self._pattern.search(line)
        if match:
            minutes, seconds, milliseconds = match.groups()
            current_seconds = float(minutes) * 60 + float(seconds) + float(milliseconds) / 1000
            
            # Log progress if interval met
            current_time = time.time()
            if current_time - self._last_log_time >= self._log_interval:
                if self.total_duration:
                    progress_percent = min(100, (current_seconds / self.total_duration) * 100)
                    self.logger.info(f"Transcribing: {current_seconds:.1f} / {self.total_duration:.1f} seconds ({progress_percent:.1f}%)")
                else:
                    self.logger.info(f"Transcribing: {current_seconds:.1f} seconds processed")
                
                self._last_log_time = current_time

def transcribe_audio(audio_path, model_name, logger):
    """
    Transcribes audio using mlx-whisper.
    Returns the transcript text.
    """
    logger.info(f"Transcribing {audio_path} using {model_name}...")
    
    duration = get_audio_duration(audio_path)
    if duration:
        logger.info(f"Audio duration: {duration:.2f} seconds")
    
    try:
        # mlx_whisper automatically handles model downloading if not present
        # We capture stdout to parse progress
        with ProgressCapturer(logger, duration):
            result = mlx_whisper.transcribe(
                audio_path, 
                path_or_hf_repo=model_name, 
                verbose=True
            )
            
        text = result.get("text", "")
        logger.info(f"Transcription complete (length: {len(text)} chars)")
        return text
    except Exception as e:
        logger.critical(f"Error during transcription: {e}")
        return ""