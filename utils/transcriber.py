import mlx_whisper
import os
import time
from pydub import AudioSegment
from tqdm import tqdm

def transcribe_audio(audio_path, model_name, logger):
    """
    Transcribes audio using mlx-whisper with progress logging.
    Splits audio into 30s chunks and logs progress every ~10 seconds.
    Returns the transcript text.
    """
    logger.info(f"Transcribing {audio_path} using {model_name}...")
    
    try:
        # 1. Load audio and calculate total duration
        audio = AudioSegment.from_file(audio_path)
        total_ms = len(audio)
        chunk_size_ms = 30000  # Whisper standard chunk size is 30 seconds
        chunks = range(0, total_ms, chunk_size_ms)
        
        full_transcript = []
        last_log_time = {"time": 0}
        total_chunks = len(chunks)
        
        logger.info(f"Audio length: {total_ms/1000:.2f}s. Split into {total_chunks} chunks.")

        for i, start_ms in enumerate(chunks):
            # Cut audio chunk
            end_ms = min(start_ms + chunk_size_ms, total_ms)
            chunk_audio = audio[start_ms:end_ms]
            
            # Export temp file (mlx-whisper needs file path)
            # Use unique name to avoid conflicts if parallel (though streamlit is sequential per session)
            # Better to put in same dir as audio_path or temp dir
            temp_chunk_path = f"{audio_path}_temp_chunk_{i}.wav"
            chunk_audio.export(temp_chunk_path, format="wav")
            
            # Transcribe chunk
            # suppress internal print if possible, but mlx-whisper might not have verbose=False arg in all versions?
            # User snippet used verbose=False.
            result = mlx_whisper.transcribe(
                temp_chunk_path, 
                path_or_hf_repo=model_name,
                verbose=False
            )
            
            text = result.get("text", "").strip()
            full_transcript.append(text)
            
            # Remove temp file
            try:
                os.remove(temp_chunk_path)
            except OSError:
                pass
            
            # Log progress every 10 seconds
            current_time = time.time()
            if current_time - last_log_time["time"] >= 10:
                progress = (i + 1) / total_chunks * 100
                logger.info(f"Transcription progress: {progress:.1f}% ({i + 1}/{total_chunks} chunks)")
                last_log_time["time"] = current_time

        final_text = " ".join(full_transcript)
        logger.info(f"Transcription complete (length: {len(final_text)} chars)")
        return final_text
        
    except Exception as e:
        logger.critical(f"Error during transcription: {e}")
        # Clean up any potential temp files if needed? 
        return ""
