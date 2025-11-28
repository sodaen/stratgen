from __future__ import annotations
from pathlib import Path
from typing import Dict, Any
import json

STORE_DIR = Path("data/styles"); STORE_DIR.mkdir(parents=True, exist_ok=True)
STORE_FILE = STORE_DIR / "profiles.json"
DEFAULT_FILE = STORE_DIR / "default.txt"

DEFAULTS = {
  "neutral_de": {
    "label": "Neutral DE (Sie, präzise)",
    "tone": "sie",                 # "sie" | "du"
    "formality": "hoch",           # "hoch" | "mittel" | "locker"
    "verbs": "aktiv",              # "aktiv" | "neutral"
    "bullets_min": 5,
    "bullets_max": 7,
    "max_words_per_bullet": 22,
    "headline_case": "Sentence",
    "allow_emojis": False,
    "forbid_hard_numbers_in_ideation": True,
    "brand_voice": "präzise, beratend, klar"
  },
  "agency_du": {
    "label": "Agentur (Du, knackig)",
    "tone": "du",
    "formality": "mittel",
    "verbs": "aktiv",
    "bullets_min": 4,
    "bullets_max": 6,
    "max_words_per_bullet": 18,
    "headline_case": "Sentence",
    "allow_emojis": False,
    "forbid_hard_numbers_in_ideation": True,
    "brand_voice": "energisch, lösungsorientiert"
  },
  "punchy_de": {
    "label": "Punchy (Du, sehr kurz)",
    "tone": "du",
    "formality": "locker",
    "verbs": "aktiv",
    "bullets_min": 4,
    "bullets_max": 5,
    "max_words_per_bullet": 14,
    "headline_case": "Sentence",
    "allow_emojis": True,
    "forbid_hard_numbers_in_ideation": True,
    "brand_voice": "pointiert, kreativ"
  }
}

def _load_store() -> Dict[str, Any]:
    if not STORE_FILE.exists():
        STORE_FILE.write_text(json.dumps(DEFAULTS, ensure_ascii=False, indent=2), encoding="utf-8")
    return json.loads(STORE_FILE.read_text(encoding="utf-8"))

def list_profiles() -> Dict[str, Any]:
    return _load_store()

def get_default_name() -> str:
    if DEFAULT_FILE.exists():
        return DEFAULT_FILE.read_text(encoding="utf-8").strip() or "neutral_de"
    DEFAULT_FILE.write_text("neutral_de", encoding="utf-8")
    return "neutral_de"

def set_default_name(name: str):
    store = _load_store()
    if name not in store:
        raise KeyError(name)
    DEFAULT_FILE.write_text(name, encoding="utf-8")

def get_profile(name: str | None = None) -> Dict[str, Any]:
    store = _load_store()
    key = name or get_default_name()
    prof = store.get(key) or store["neutral_de"]
    # Guards
    prof["bullets_min"] = int(max(3, min(8, prof.get("bullets_min",5))))
    prof["bullets_max"] = int(max(prof["bullets_min"], min(8, prof.get("bullets_max",7))))
    prof["max_words_per_bullet"] = int(max(10, min(30, prof.get("max_words_per_bullet",22))))
    return prof

def merge_overrides(base: Dict[str, Any], override: Dict[str, Any] | None) -> Dict[str, Any]:
    if not override: 
        return base
    out = dict(base)
    for k,v in override.items():
        if v is None: 
            continue
        out[k] = v
    # Guards erneut
    return get_profile_forced(out)

def get_profile_forced(prof: Dict[str, Any]) -> Dict[str, Any]:
    # gleiche Guards wie get_profile()
    prof["bullets_min"] = int(max(3, min(8, prof.get("bullets_min",5))))
    prof["bullets_max"] = int(max(prof["bullets_min"], min(8, prof.get("bullets_max",7))))
    prof["max_words_per_bullet"] = int(max(10, min(30, prof.get("max_words_per_bullet",22))))
    return prof
