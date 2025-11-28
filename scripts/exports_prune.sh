#!/usr/bin/env bash
set -Eeuo pipefail
KEEP="${KEEP:-20}"           # wie viele neueste behalten
OLDER_DAYS="${OLDER_DAYS:-}" # optional: zusätzliche Altersgrenze (Tage)
DRY_RUN="${DRY_RUN:-1}"      # 1 = nur anzeigen; 0 = löschen
DIR="data/exports"

python3 - "$DIR" "$KEEP" "$OLDER_DAYS" "$DRY_RUN" <<'PY'
import sys, os, time, pathlib
from datetime import datetime, timedelta

DIR = pathlib.Path(sys.argv[1])
KEEP = int(sys.argv[2])
OLDER_DAYS = int(sys.argv[3]) if sys.argv[3] else None
DRY = bool(int(sys.argv[4]))

if not DIR.exists():
    print(f"[info] {DIR} existiert nicht – nichts zu tun.")
    sys.exit(0)

files = [p for p in DIR.iterdir() if p.is_file()]
files.sort(key=lambda p: p.stat().st_mtime, reverse=True)

keep_set = set(f for f in files[:KEEP])
candidates = [f for f in files[KEEP:]]

if OLDER_DAYS is not None:
    cutoff = time.time() - OLDER_DAYS*86400
    candidates = [f for f in candidates if f.stat().st_mtime < cutoff]

print(f"[plan] Behalte {len(keep_set)} neueste Dateien; Kandidaten zum Entfernen: {len(candidates)}")
for f in candidates:
    ts = datetime.fromtimestamp(f.stat().st_mtime).isoformat(timespec="seconds")
    print(("DRY" if DRY else "DEL")+f": {f}  (mtime={ts}, size={f.stat().st_size}B)")
    if not DRY:
        try:
            f.unlink()
        except Exception as e:
            print(f"[warn] konnte {f} nicht löschen: {e}")
PY
