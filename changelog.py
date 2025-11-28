#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MD   = ROOT / "CHANGELOG.md"

def _git_changed_files():
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT))
        lines = out.decode("utf-8", errors="ignore").splitlines()
        # nur Dateinamen extrahieren
        files = []
        for ln in lines:
            ln = ln.strip()
            if not ln: 
                continue
            # Format: "XY path"
            parts = ln.split(None, 1)
            files.append(parts[-1])
        return files
    except Exception:
        return []

def main():
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    files = _git_changed_files()

    if not MD.exists():
        MD.write_text("# CHANGELOG\n\n", encoding="utf-8")

    with MD.open("a", encoding="utf-8") as f:
        if files:
            f.write(f"## {ts}\n")
            f.write("Geänderte Dateien (git status):\n\n")
            for p in files:
                f.write(f"- {p}\n")
            f.write("\n")
            print("[changelog] aktualisiert.")
        else:
            # Heartbeat, wenn nichts zu loggen ist
            f.write(f"_heartbeat {ts}_\n")
            print("[changelog] Nichts zu protokollieren.")

if __name__ == "__main__":
    main()
