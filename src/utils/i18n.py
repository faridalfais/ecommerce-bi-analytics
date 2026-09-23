import json
import streamlit as st
from pathlib import Path

LOCALES_DIR = Path("dashboard/locales")

def load_locales() -> dict:
    """Load English and Indonesian locale files."""
    locales = {}
    for lang in ['en', 'id']:
        path = LOCALES_DIR / f"{lang}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                locales[lang] = json.load(f)
        else:
            locales[lang] = {}
    return locales

_LOCALES = load_locales()

def get_text(key: str, lang: str = "en") -> str:
    """Retrieve translated UI string by key and active language."""
    if lang not in _LOCALES:
        lang = "en"
    return _LOCALES.get(lang, {}).get(key, _LOCALES.get("en", {}).get(key, key))
