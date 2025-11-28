from __future__ import annotations
from typing import List, Tuple
import regex as re

# grobe Zahlenerkennung: 12, 12.3, 12,3, 12%, 12.3%, 12,3%
NUM_RE = re.compile(r"(?<!#)(?<!\\w)(\\d{1,3}(?:[\\.,]\\d+)?%?)")

def bullets_need_citation(lines: List[str]) -> bool:
    if not lines:
        return False
    for ln in lines:
        if NUM_RE.search(ln or ""):
            return True
    return False

def mask_numbers(line: str) -> str:
    return NUM_RE.sub("[[[ZAHL]]]", line or "")

def enforce_facts_on_slide(
    bullets: List[str] | None,
    citations: List[str] | None
) -> Tuple[List[str], List[str], List[str]]:
    """
    Gibt (bullets_sanitized, citations, warnings) zurück.
    - Wenn Zahlen erkannt & keine citations -> Zahlen maskieren + WARN
    - Sonst: unverändert
    """
    b = list(bullets or [])
    c = list(citations or [])
    warnings: List[str] = []

    if bullets_need_citation(b) and not c:
        b = [mask_numbers(ln) for ln in b]
        if not any("DATENQUELLE" in (ln or "") for ln in b):
            b.append("• [[[DATENQUELLE benötigt – Quelle (z. B. Statista) einfügen]]]")
        warnings.append("Faktenmodus: Zahlen ohne Quelle → maskiert & TODO gesetzt")

    return b, c, warnings
