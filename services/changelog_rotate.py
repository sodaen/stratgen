
from __future__ import annotations
import os, glob, re, shutil

DEFAULT_BASE = "CHANGELOG.md"
MAX_BYTES = 10 * 1024 * 1024  # 10 MB
MAX_ROLLS = 999               # genug Puffer

_roll_re = re.compile(r"^CHANGELOG\.(\d{3})\.md$")

def _next_index(existing: list[str]) -> int:
    idxs = []
    for name in existing:
        m = _roll_re.match(name)
        if m:
            idxs.append(int(m.group(1)))
    return (max(idxs) + 1) if idxs else 1

def rotate_if_needed(base: str = DEFAULT_BASE, limit: int = MAX_BYTES) -> tuple[bool, str]:
    """Dreht base nach CHANGELOG.###.md, sobald limit überschritten ist.
       Liefert (rotated, current_path)."""
    base = base or DEFAULT_BASE
    if not os.path.exists(base):
        # kein File -> nichts zu drehen
        return (False, base)

    size = os.path.getsize(base)
    if size < limit:
        return (False, base)

    # vorhandene Roll-Dateien ermitteln
    existing = [os.path.basename(p) for p in glob.glob("CHANGELOG.*.md")]
    nxt = _next_index(existing)
    if nxt > MAX_ROLLS:
        # Sicherheitsnetz: älteste löschen/verschieben? Für jetzt: einfach überschreiben ab 001
        nxt = 1

    rolled = f"CHANGELOG.{nxt:03d}.md"
    shutil.move(base, rolled)
    # neue leere Basisdatei anlegen (Header als freundliche Markierung)
    with open(base, "w", encoding="utf-8") as f:
        f.write("# CHANGELOG\n\n_Vorherige Datei rotiert nach **%s** (Limit erreicht)._ \n\n" % rolled)
    return (True, base)
