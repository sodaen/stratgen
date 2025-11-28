import re
from typing import List, Tuple, Dict

CIT_PAT = re.compile(r"\[\[\s*(?:Quelle|Source)\s*:\s*(.+?)\s*\]\]", re.IGNORECASE)

def extract(bullets_text: str) -> Tuple[List[str], List[str]]:
    """
    Erwartet Bullets-Text (eine Zeile pro Bullet; Prefix '•' optional).
    Erkennt Zitate im Format [[Quelle: ...]].
    Gibt (bullets_ohne_marker, footnotes) zurück.
    """
    lines = [ln.strip() for ln in bullets_text.splitlines() if ln.strip()]
    clean: List[str] = []
    found: List[str] = []
    for ln in lines:
        cites = CIT_PAT.findall(ln)
        if cites:
            for c in cites:
                c_norm = " ".join(c.split())
                if c_norm not in found:
                    found.append(c_norm)
            ln = CIT_PAT.sub("", ln).strip()
        if ln:
            if not ln.startswith("•"):
                ln = "• " + ln
            clean.append(ln)
    # mind. 5 bullets auffüllen, falls nötig
    while len(clean) < 5:
        clean.append("• [[[TODO: Inhalte ergänzen]]]")
    return clean[:7], found[:6]  # 5–7 bullets, max 6 Fußnoten pro Folie
