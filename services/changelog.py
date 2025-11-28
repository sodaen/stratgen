from __future__ import annotations
from datetime import datetime
from services.changelog_rotate import rotate_if_needed

BASE = 'CHANGELOG.md'

def append_line(text: str) -> None:
    rotate_if_needed(BASE)
    ts = datetime.utcnow().isoformat()+'Z'
    with open(BASE, 'a', encoding='utf-8') as f:
        f.write(f'- [{ts}] {text}\n')
