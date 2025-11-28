#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys, subprocess
from pathlib import Path
import os, sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from services.changelog_rotate import rotate_if_needed

# Wir verwenden dein vorhandenes changelog.py (aus dem Repo-Root)
# und rufen es nur auf. Pfad anpassen, falls es woanders liegt:
ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "changelog.py"

def main():
    if not TOOL.exists():
        print("[changelog] changelog.py fehlt im Repo-Root.")
        sys.exit(1)
    subprocess.run([sys.executable, str(TOOL)], cwd=str(ROOT), check=False)

if __name__ == "__main__":
    main()
