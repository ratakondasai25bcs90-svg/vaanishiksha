"""
Translation service using IndicTrans2 for Indian language pairs.
Falls back to LLM-based translation for unsupported pairs.
"""


def translate_text(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate text from source language to target language.
    
    Args:
        text: Text to translate
        source_lang: Source language ISO code
        target_lang: Target language ISO code
    
    Returns:
        Translated text
    """
    # If source and target are the same, return as-is
    if source_lang == target_lang:
        return text
    
    # Try IndicTrans2 for Indian language pairs
    if _is_indic_language_pair(source_lang, target_lang):
        try:
            return _translate_with_indictrans2(text, source_lang, target_lang)
        except Exception as e:
            print(f"IndicTrans2 failed: {e}. Falling back to LLM translation.")
    
    # Fall back to LLM-based translation
    return _translate_with_llm(text, source_lang, target_lang)


def _is_indic_language_pair(source_lang: str, target_lang: str) -> bool:
    """Check if both languages are supported by IndicTrans2"""
    indic_langs = {"hi", "ta", "te", "kn", "bn", "en"}
    return source_lang in indic_langs and target_lang in indic_langs


def _translate_with_indictrans2(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate using IndicTrans2 model.
    
    Note: This is a placeholder. Actual implementation requires:
    - Installing AI4Bharat IndicTrans2 model
    - Downloading model weights
    - Setting up inference pipeline
    
    For MVP, we'll use a simpler approach or LLM fallback.
    """
    # TODO: Implement actual IndicTrans2 integration
    # For now, fall back to LLM
    raise NotImplementedError("IndicTrans2 not yet integrated")


def _translate_with_llm(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate using an LLM API (e.g., Gemini, GPT).
    
    Note: Requires API key to be configured.
    """
    from app.config import settings
    
    if not settings.gemini_api_key:
        raise ValueError("No API key configured for translation. Set GEMINI_API_KEY in .env")
    
    import google.generativeai as genai
    
    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    # Language names for better prompting
    lang_names = settings.language_names
    source_name = lang_names.get(source_lang, source_lang)
    target_name = lang_names.get(target_lang, target_lang)
    
    prompt = f"""Translate the following text from {source_name} to {target_name}.
Preserve the meaning, tone, and educational context. This is for primary school students.

Text to translate:
{text}

Translation:"""
    
    response = model.generate_content(prompt)
    return response.text.strip()
