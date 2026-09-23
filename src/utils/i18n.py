import json
import streamlit as st
from pathlib import Path

# Resolve locales directory relative to repository root
_ROOT = Path(__file__).resolve().parents[2]
LOCALES_DIR = _ROOT / "dashboard" / "locales"

def load_locales() -> dict:
    """Load English and Indonesian locale files."""
    locales = {}
    for lang in ['en', 'id']:
        path = LOCALES_DIR / f"{lang}.json"
        if not path.exists():
            # Fallback to local relative path
            path = Path("dashboard/locales") / f"{lang}.json"
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
