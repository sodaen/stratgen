#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from datetime import datetime
from services.changelog_rotate import rotate_if_needed

BASE = 'CHANGELOG.md'

def main():
    # Text aus argv oder stdin
    if len(sys.argv) > 1:
        text = " ".join(sys.argv[1:]).strip()
    else:
        text = sys.stdin.read().strip()

    if not text:
        print("[changelog_append] Kein Text übergeben.", file=sys.stderr)
        sys.exit(2)

    rotate_if_needed(BASE)
    ts = datetime.utcnow().isoformat()+'Z'
    with open(BASE, 'a', encoding='utf-8') as f:
        f.write(f'- [{ts}] {text}\n')
    print("[changelog_append] OK")

if __name__ == "__main__":
    main()
