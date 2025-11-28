#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import time, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "scripts" / "changelog.py"

def run():
    while True:
        try:
            subprocess.run([sys.executable, str(TOOL)], cwd=str(ROOT), check=False)
        except Exception as e:
            print("[sentinel] Fehler:", e, flush=True)
        time.sleep(60)

if __name__ == "__main__":
    print("[sentinel] läuft. schreibe regelmäßig CHANGELOG.md …", flush=True)
    run()
