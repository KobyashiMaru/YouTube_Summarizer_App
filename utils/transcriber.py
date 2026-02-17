import mlx_whisper

def transcribe_audio(audio_path, model_name, logger):
    """
    Transcribes audio using mlx-whisper.
    Returns the transcript text.
    """
    logger.info(f"Transcribing {audio_path} using {model_name}...")
    
    try:
        # mlx_whisper automatically handles model downloading if not present
        result = mlx_whisper.transcribe(
            audio_path, 
            path_or_hf_repo=model_name
        )
        text = result.get("text", "")
        logger.info(f"Transcription complete (length: {len(text)} chars)")
        return text
    except Exception as e:
        logger.critical(f"Error during transcription: {e}")
        return ""
