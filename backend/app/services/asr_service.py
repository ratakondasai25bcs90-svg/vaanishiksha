from faster_whisper import WhisperModel


def transcribe_audio(audio_file_path: str, language: str = None) -> str:
    """
    Transcribe audio file to text using Whisper.
    
    Args:
        audio_file_path: Path to audio/video file
        language: ISO language code (e.g., 'en', 'hi', 'ta')
    
    Returns:
        Transcript text
    """
    # Use faster-whisper for better performance
    # Model size: tiny, base, small, medium, large
    model = WhisperModel("small", device="cpu", compute_type="int8")

    # faster-whisper expects ISO-639-1 codes (e.g. 'en', 'hi', 'ta').
    # Our supported languages (en, hi, ta, te, kn, bn) are all valid whisper
    # codes, so pass them through directly. When None, Whisper auto-detects.
    whisper_lang = language if language else None
    
    segments, info = model.transcribe(
        audio_file_path,
        language=whisper_lang,
        beam_size=5
    )
    
    # Combine all segments into full transcript
    transcript = " ".join([segment.text for segment in segments])
    
    return transcript.strip()
