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
    Translate using Omniroute's Gemini-compatible endpoint.
    
    Note: Uses Omniroute (local AI gateway) instead of Google's Gemini API directly.
    Requires GEMINI_API_KEY in .env to be set to an Omniroute unified key (format: omnikey-g-...).
    """
    from app.config import settings
    import httpx
    import json
    
    if not settings.gemini_api_key:
        raise ValueError("No Omniroute API key configured. Set GEMINI_API_KEY in .env to your Omniroute key (omnikey-g-...)")
    
    # Omniroute's Gemini-compatible endpoint
    omniroute_base_url = "http://localhost:20128/v1beta"
    
    # Language names for better prompting
    lang_names = settings.language_names
    source_name = lang_names.get(source_lang, source_lang)
    target_name = lang_names.get(target_lang, target_lang)
    
    prompt = f"""Translate the following text from {source_name} to {target_name}.
Preserve the meaning, tone, and educational context. This is for primary school students.

Text to translate:
{text}

Translation:"""
    
    # Call Omniroute using Gemini API format
    url = f"{omniroute_base_url}/models/gemini-pro:generateContent"
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": settings.gemini_api_key
    }
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            # Extract text from Gemini API response format
            if "candidates" in result and len(result["candidates"]) > 0:
                candidate = result["candidates"][0]
                if "content" in candidate and "parts" in candidate["content"]:
                    parts = candidate["content"]["parts"]
                    if len(parts) > 0 and "text" in parts[0]:
                        return parts[0]["text"].strip()
            
            raise ValueError(f"Unexpected response format from Omniroute: {result}")
    
    except httpx.HTTPStatusError as e:
        raise ValueError(f"Omniroute API error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        raise ValueError(f"Failed to connect to Omniroute at {omniroute_base_url}: {e}")
