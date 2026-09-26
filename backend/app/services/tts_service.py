"""
Text-to-Speech service for generating dubbed audio.

For MVP: Using Google's TTS API or Coqui TTS with multi-language support.
For production: Should integrate AI4Bharat IndicTTS for better Indian language support.
"""
from gtts import gTTS
import os


def text_to_speech(text: str, language: str, output_path: str) -> str:
    """
    Convert text to speech audio file.
    
    Args:
        text: Text to convert
        language: Target language ISO code
        output_path: Where to save the audio file
    
    Returns:
        Path to generated audio file
    """
    # Map our language codes to gTTS language codes
    lang_map = {
        "en": "en",
        "hi": "hi",
        "ta": "ta",
        "te": "te",
        "kn": "kn",
        "bn": "bn"
    }
    
    gtts_lang = lang_map.get(language, language)
    
    try:
        # Generate speech
        tts = gTTS(text=text, lang=gtts_lang, slow=False)
        tts.save(output_path)
        return output_path
    
    except Exception as e:
        print(f"gTTS failed for language {language}: {e}")
        # Fall back to English if language not supported
        if language != "en":
            print("Falling back to English TTS")
            tts = gTTS(text=text, lang="en", slow=False)
            tts.save(output_path)
            return output_path
        raise


def text_to_speech_with_timestamps(text: str, language: str, output_path: str):
    """
    Generate TTS with word-level timestamps for subtitle synchronization.
    
    This is a more advanced feature needed for proper caption sync.
    Requires a more sophisticated TTS engine than gTTS.
    
    TODO: Implement with a TTS engine that supports timestamp output
    (e.g., Coqui TTS, Azure TTS, or custom IndicTTS)
    """
    # For now, use basic TTS
    return text_to_speech(text, language, output_path)
