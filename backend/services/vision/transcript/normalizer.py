"""
Text normalization utilities for transcript and OCR string matching.
"""
import re


def normalize_text(text: str) -> str:
    """
    Text normalization reduces formatting differences between
    OCR output and speech transcription while preserving keywords.
    """
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r'[^\w\s]', ' ', text)  # Strip punctuation
    text = re.sub(r'\s+', ' ', text)      # Normalize spaces
    return text.strip()
