import re, unicodedata

def norm_query(q: str) -> str:
    if not isinstance(q, str):
        return ""
    q = q.strip()
    # Unicode -> NFKD, Akzente/Diakritika entfernen
    q = unicodedata.normalize("NFKD", q)
    q = "".join(ch for ch in q if not unicodedata.combining(ch))
    # Umlaute auch explizit mappen
    q = q.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß","ss")
    q = q.replace("Ä", "Ae").replace("Ö", "Oe").replace("Ü", "Ue")
    # Kleinbuchstaben, Whitespace komprimieren, rudimentäre Zeichen filtern
    q = q.lower()
    q = re.sub(r"[^a-z0-9\s\-\_\.]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q
