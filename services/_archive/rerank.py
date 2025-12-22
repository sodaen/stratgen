
from typing import List, Tuple
try:
    # RapidFuzz ist leichtgewichtig und schon installiert
    from rapidfuzz import fuzz
except Exception:  # Fallback auf einfache Python-Ähnlichkeit
    fuzz = None

def rerank(query: str, texts: List[str], top_k: int = 5) -> List[Tuple[str, float]]:
    """
    Gibt Liste von (text, score)-Tupeln zurück (score in [0..1]), Top-K nach Score.
    """
    if not texts:
        return []
    scores = []
    if fuzz:
        for t in texts:
            # token_set_ratio ist robust gegen Wort-Reihenfolge/Duplikate
            s = fuzz.token_set_ratio(query or "", t or "") / 100.0
            scores.append((t, float(s)))
    else:
        # sehhhhhr einfacher Fallback: Anteil gemeinsamer Tokens
        qt = set((query or "").lower().split())
        for t in texts:
            tt = set((t or "").lower().split())
            inter = len(qt & tt)
            denom = max(1, len(qt) + len(tt) - inter)
            s = inter / denom
            scores.append((t, float(s)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:top_k]
