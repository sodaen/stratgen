from __future__ import annotations
import re
from typing import List, Dict, Any, Optional

HEX_RE = re.compile(r"^#?([0-9a-fA-F]{6}|[0-9a-fA-F]{3})$")

def norm_hex(s: Optional[str]) -> Optional[str]:
    if not s: return None
    s = s.strip()
    m = HEX_RE.match(s)
    if not m: return None
    h = m.group(1)
    if len(h) == 3:
        h = "".join(c*2 for c in h)
    return f"#{h.lower()}"

def validate_colors(primary: Optional[str], secondary: Optional[str], accent: Optional[str]) -> Dict[str,str]:
    out = {}
    for key,val in (("primary",primary),("secondary",secondary),("accent",accent)):
        if val is None: 
            continue
        n = norm_hex(val)
        if not n:
            raise ValueError(f"INVALID_BRAND_COLOR::{key}::{val}")
        out[key] = n
    return out

ALLOWED_LOGO_EXT = {"png","jpg","jpeg"}

def validate_logo(filename: Optional[str], size_bytes: int) -> None:
    if not filename:
        return
    if "." not in filename:
        raise ValueError("INVALID_LOGO::NO_EXT")
    ext = filename.rsplit(".",1)[-1].lower()
    if ext not in ALLOWED_LOGO_EXT:
        raise ValueError(f"INVALID_LOGO::EXT::{ext}")
    if size_bytes > 5*1024*1024:
        raise ValueError("INVALID_LOGO::TOO_LARGE")


def _extract_topic_subs(item):
    # Unterstützt sowohl dicts als auch Pydantic/BaseModel-ähnliche Objekte
    if isinstance(item, dict):
        topic = item.get("topic") or item.get("title") or item.get("name")
        subs = item.get("subtopics") or item.get("subs") or []
    else:
        topic = getattr(item, "topic", None) or getattr(item, "title", None) or getattr(item, "name", None)
        subs = getattr(item, "subtopics", None) or getattr(item, "subs", None) or []
    return topic, (subs if subs is not None else [])


def validate_agenda(agenda):
    if not isinstance(agenda, (list, tuple)):
        raise ValueError("INVALID_AGENDA::NOT_A_LIST")
    for i, it in enumerate(agenda):
        topic, subs = _extract_topic_subs(it)
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError(f"INVALID_AGENDA::MISSING_TOPIC::{i}")
        if subs is not None and not isinstance(subs, (list, tuple)):
            raise ValueError(f"INVALID_AGENDA::SUBTOPICS_NOT_LIST::{i}")
    return True


def validate_content_map(agenda, content_map):
    if not isinstance(content_map, dict):
        raise ValueError("INVALID_CONTENT_MAP::NOT_A_DICT")
    topics = []
    for i, it in enumerate(agenda):
        t = _get_topic(it)
        if not isinstance(t, str) or not t.strip():
            raise ValueError(f"INVALID_AGENDA::MISSING_TOPIC::{i}")
        topics.append(t)
    # content_map darf Topics weglassen, aber was drin ist, muss stimmen
    for t, submap in content_map.items():
        if not isinstance(submap, dict):
            raise ValueError(f"INVALID_CONTENT_MAP::TOPIC_NOT_OBJECT::{t}")
        for sub, entry in submap.items():
            if not isinstance(entry, dict):
                raise ValueError(f"INVALID_CONTENT_MAP::ENTRY_NOT_OBJECT::{t}::{sub}")
            bullets = entry.get("bullets", [])
            citations = entry.get("citations", [])
            if bullets is not None and not isinstance(bullets, (list, tuple)):
                raise ValueError(f"INVALID_CONTENT_MAP::BULLETS_NOT_LIST::{t}::{sub}")
            if citations is not None and not isinstance(citations, (list, tuple)):
                raise ValueError(f"INVALID_CONTENT_MAP::CITATIONS_NOT_LIST::{t}::{sub}")
    return True

def estimate_slide_count(agenda: List[Dict[str,Any]]) -> int:
    # 1 Start + 1 Agenda + je Topic (1 Section + len(subs)) + 1 Sources + 1 End
    subs_total = sum(len(x.get("subtopics") or []) for x in agenda)
    return 1 + 1 + len(agenda) + subs_total + 1 + 1


def validate_slide_budget(agenda, max_slides=80):
    # sehr simple Heuristik: 1 Folie je Topic + 1 je Subtopic
    total = 0
    for it in agenda:
        t, subs = _extract_topic_subs(it)
        total += 1
        total += len(subs or [])
    if total > max_slides:
        raise ValueError(f"SLIDE_BUDGET_EXCEEDED::{total}::MAX::{max_slides}")
    return True


# ---- helpers (sicher vorhanden machen) ----
try:
    _extract_topic_subs
except NameError:
    def _extract_topic_subs(item):
        if isinstance(item, dict):
            topic = item.get("topic") or item.get("title") or item.get("name")
            subs  = item.get("subtopics") or item.get("subs") or []
        else:
            topic = getattr(item, "topic", None) or getattr(item, "title", None) or getattr(item, "name", None)
            subs  = getattr(item, "subtopics", None) or getattr(item, "subs", None) or []
        return topic, (subs if subs is not None else [])

try:
    _get_topic
except NameError:
    def _get_topic(item):
        t, _ = _extract_topic_subs(item)
        return t

# ---- robuste Re-Definitionen (letzte Definition gewinnt in Python) ----
def validate_agenda(agenda):
    if not isinstance(agenda, (list, tuple)):
        raise ValueError("INVALID_AGENDA::NOT_A_LIST")
    for i, it in enumerate(agenda):
        topic, subs = _extract_topic_subs(it)
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError(f"INVALID_AGENDA::MISSING_TOPIC::{i}")
        if subs is not None and not isinstance(subs, (list, tuple)):
            raise ValueError(f"INVALID_AGENDA::SUBTOPICS_NOT_LIST::{i}")
    return True

def validate_content_map(agenda, content_map):
    if not isinstance(content_map, dict):
        raise ValueError("INVALID_CONTENT_MAP::NOT_A_DICT")
    # Agenda-Topics validieren
    for i, it in enumerate(agenda):
        topic, _ = _extract_topic_subs(it)
        if not isinstance(topic, str) or not topic.strip():
            raise ValueError(f"INVALID_AGENDA::MISSING_TOPIC::{i}")
    # Struktur des content_map prüfen
    for t, submap in content_map.items():
        if not isinstance(submap, dict):
            raise ValueError(f"INVALID_CONTENT_MAP::TOPIC_NOT_OBJECT::{t}")
        for sub, entry in submap.items():
            if not isinstance(entry, dict):
                raise ValueError(f"INVALID_CONTENT_MAP::ENTRY_NOT_OBJECT::{t}::{sub}")
            bullets   = entry.get("bullets", [])
            citations = entry.get("citations", [])
            if bullets is not None and not isinstance(bullets, (list, tuple)):
                raise ValueError(f"INVALID_CONTENT_MAP::BULLETS_NOT_LIST::{t}::{sub}")
            if citations is not None and not isinstance(citations, (list, tuple)):
                raise ValueError(f"INVALID_CONTENT_MAP::CITATIONS_NOT_LIST::{t}::{sub}")
    return True

def validate_slide_budget(agenda, max_slides=80):
    total = 0
    for it in agenda:
        _, subs = _extract_topic_subs(it)
        total += 1
        total += len(subs or [])
    if total > max_slides:
        raise ValueError(f"SLIDE_BUDGET_EXCEEDED::{total}::MAX::{max_slides}")
    return True

