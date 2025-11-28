# -*- coding: utf-8 -*-
# Einfache Style-Vorgaben für Deck-Export

# Hinweis: PRESETS-Einträge sind flach (kein "options"-Nesting).
# Der get_style_options()-Shim unten akzeptiert aber auch Nested-Form.

PRESETS = {
    "brand": {
        "title_font": "Montserrat",
        "body_font": "Inter",
        "accent_color": "FF3B82",   # Pink
        "text_color": "222222",
        "bg_color": "FFFFFF",
        "title_size": 40,
        "body_size": 20,
        "margin": 24,
    },
    "minimal": {
        "title_font": "Calibri",
        "body_font": "Calibri",
        "accent_color": "2F5597",   # Blau
        "text_color": "000000",
        "bg_color": "FFFFFF",
        "title_size": 36,
        "body_size": 18,
        "margin": 20,
    },
}

def get_style_options(name: str) -> dict:
    """
    Kompatibilitäts-Shim:
    - Wenn PRESETS[name] ein Dict mit "options" ist → dieses Dict zurückgeben.
    - Wenn PRESETS[name] ein flaches Dict ist → dieses Dict zurückgeben.
    - Sonst → {}.
    """
    entry = (PRESETS or {}).get(name)
    if isinstance(entry, dict):
        opts = entry.get("options")
        if isinstance(opts, dict):
            return opts
        return entry
    return {}
