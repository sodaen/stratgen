#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os, sys, time, subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.changelog_rotate import rotate_if_needed
MD = ROOT / "CHANGELOG.md"

def git_changed_files() -> list[str]:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=str(ROOT))
        lines = out.decode("utf-8", errors="ignore").splitlines()
        return [ln.split(None,1)[-1] for ln in lines if ln.strip()]
    except Exception:
        return []

def main():
    last = set()
    interval = int(os.environ.get("CLG_INTERVAL","5"))
    print(f"[watch] starte (Intervall {interval}s)…")
    while True:
        cur = set(git_changed_files())
        if cur != last:
            rotate_if_needed(str(MD))
            ts = time.strftime("%Y-%m-%d %H:%M:%S")
            with MD.open("a", encoding="utf-8") as f:
                if cur:
                    f.write(f"## {ts}\n")
                    f.write("Geänderte Dateien (watch):\n\n")
                    for p in sorted(cur):
                        f.write(f"- {p}\n")
                    f.write("\n")
                else:
                    f.write(f"_heartbeat {ts}_\n")
            print("[watch] changelog aktualisiert.")
            last = cur
        time.sleep(interval)

if __name__ == "__main__":
    main()
