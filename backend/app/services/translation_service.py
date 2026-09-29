"""
Translation service using IndicTrans2 for Indian language pairs.
Falls back to LLM-based translation for unsupported pairs or if IndicTrans2 is unavailable.
"""

import os

# Map our ISO language codes to IndicTrans2 FLORES-200 codes
_FLORES_CODE_MAP = {
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "kn": "kan_Knda",
    "bn": "ben_Beng",
}

# Model checkpoints (distilled 200M variants - practical for CPU inference)
_EN_INDIC_MODEL = "ai4bharat/indictrans2-en-indic-dist-200M"
_INDIC_EN_MODEL = "ai4bharat/indictrans2-indic-en-dist-200M"

# Cached loaded models (one per direction; 200M models ~700MB RAM each in fp32)
_models = {}


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
    Translate using AI4Bharat IndicTrans2 model (HF-compatible checkpoint).

    Uses the distilled 200M checkpoints (practical for CPU inference):
    - en -> indic: ai4bharat/indictrans2-en-indic-dist-200M
    - indic -> en: ai4bharat/indictrans2-indic-en-dist-200M

    Note: These are gated repos on HuggingFace. A HF_TOKEN with accepted
    terms ('share your contact information') is required to download them.
    """
    if source_lang == "en":
        model_name = _EN_INDIC_MODEL
    elif target_lang == "en":
        model_name = _INDIC_EN_MODEL
    else:
        raise ValueError(
            "IndicTrans2 en-indic/indic-en models do not support indic->indic pairs. "
            "The indic-indic model is not bundled; falling back to LLM."
        )

    src_flores = _FLORES_CODE_MAP.get(source_lang)
    tgt_flores = _FLORES_CODE_MAP.get(target_lang)
    if not src_flores or not tgt_flores:
        raise ValueError(f"Unsupported language pair for IndicTrans2: {source_lang}->{target_lang}")

    import torch
    from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
    from IndicTransToolkit.processor import IndicProcessor

    # Lazy-load (and cache) model + tokenizer + processor
    if model_name not in _models:
        tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True, token=os.getenv("HF_TOKEN")
        )
        model = AutoModelForSeq2SeqLM.from_pretrained(
            model_name, trust_remote_code=True, token=os.getenv("HF_TOKEN")
        )
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = model.to(device).eval()
        _models[model_name] = (model, tokenizer, device)

    model, tokenizer, device = _models[model_name]
    ip = IndicProcessor(inference=True)

    # Split long transcripts into sentences for reliable translation
    sentences = _split_sentences(text, source_lang)

    # Preprocess, tokenize, translate in a single batch
    batch = ip.preprocess_batch(sentences, src_lang=src_flores, tgt_lang=tgt_flores)
    inputs = tokenizer(
        batch,
        truncation=True,
        padding="longest",
        return_tensors="pt",
        return_attention_mask=True,
    ).to(device)

    with torch.no_grad():
        generated_tokens = model.generate(
            **inputs,
            use_cache=True,
            min_length=0,
            max_length=256,
            num_beams=5,
            num_return_sequences=1,
        )

    with tokenizer.as_target_tokenizer():
        generated_tokens = tokenizer.batch_decode(
            generated_tokens,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=True,
        )

    translations = ip.postprocess_batch(generated_tokens, lang=tgt_flores)
    return " ".join(translations)


def _split_sentences(text: str, lang: str) -> list:
    """Split transcript text into sentence chunks for batch translation."""
    import re
    # Simple sentence splitting on common sentence boundaries
    parts = re.split(r"(?<=[.!?।]) +", text.strip())
    parts = [p.strip() for p in parts if p.strip()]
    return parts or [text.strip()]


def _translate_with_llm(text: str, source_lang: str, target_lang: str) -> str:
    """
    Translate using Omniroute's OpenAI-compatible endpoint.
    
    Note: Uses Omniroute (local AI gateway) with kr/claude-sonnet-4.5 model.
    Requires GEMINI_API_KEY in .env to be set to an Omniroute unified key.
    """
    from app.config import settings
    import httpx
    
    if not settings.gemini_api_key:
        raise ValueError("No Omniroute API key configured. Set GEMINI_API_KEY in .env to your Omniroute key")
    
    # Omniroute's OpenAI-compatible endpoint
    omniroute_base_url = "http://localhost:20128/v1"
    
    # Language names for better prompting
    lang_names = settings.language_names
    source_name = lang_names.get(source_lang, source_lang)
    target_name = lang_names.get(target_lang, target_lang)
    
    prompt = f"""Translate the following text from {source_name} to {target_name}.
Preserve the meaning, tone, and educational context. This is for primary school students.

Text to translate:
{text}

Translation:"""
    
    # Call Omniroute using OpenAI API format
    url = f"{omniroute_base_url}/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.gemini_api_key}"
    }
    payload = {
        "model": "kr/claude-sonnet-4.5",
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    
    try:
        with httpx.Client(timeout=60.0) as client:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            
            result = response.json()
            # Extract text from OpenAI API response format
            if "choices" in result and len(result["choices"]) > 0:
                message = result["choices"][0]["message"]
                if "content" in message:
                    return message["content"].strip()
            
            raise ValueError(f"Unexpected response format from Omniroute: {result}")
    
    except httpx.HTTPStatusError as e:
        raise ValueError(f"Omniroute API error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        raise ValueError(f"Failed to connect to Omniroute at {omniroute_base_url}: {e}")
