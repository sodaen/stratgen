#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erzeugt einen Zustands-Snapshot der Codebasis:
- Dateiliste mit SHA256, Größe, mtime
- FastAPI-Routen (falls importierbar)
- Abhängigkeiten aus requirements*.txt
Speichert unter changelogs/snapshots/<timestamp>.json und aktualisiert changelogs/latest.json
"""
from __future__ import annotations
import os, sys, json, hashlib, time, subprocess, traceback
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "changelogs" / "snapshots"
OUT_DIR.mkdir(parents=True, exist_ok=True)
LATEST = ROOT / "changelogs" / "latest.json"

EXCLUDES_DIR = {
    ".git", ".idea", ".vscode", "__pycache__", "node_modules",
    ".venv", "venv", ".mypy_cache", ".pytest_cache",
    "data/exports", "export", "dist", "build"
}
EXCLUDES_SUFFIX = {
    ".pptx", ".ppt", ".pdf", ".png", ".jpg", ".jpeg", ".gif", ".zip",
    ".log"
}

def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def should_include(p: Path) -> bool:
    rel = p.relative_to(ROOT).as_posix()
    parts = rel.split("/")
    if parts[0] in EXCLUDES_DIR:
        return False
    if any("/".join(parts[:i]) in EXCLUDES_DIR for i in range(1, len(parts)+1)):
        return False
    if p.suffix.lower() in EXCLUDES_SUFFIX:
        return False
    return True

def list_files():
    files = []
    for p in ROOT.rglob("*"):
        if not p.is_file():
            continue
        if not should_include(p):
            continue
        try:
            files.append({
                "path": p.relative_to(ROOT).as_posix(),
                "size": p.stat().st_size,
                "mtime": int(p.stat().st_mtime),
                "sha256": sha256_file(p),
            })
        except Exception:
            continue
    return sorted(files, key=lambda x: x["path"])

def git_info():
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=str(ROOT)
        ).decode("utf-8").strip()
    except Exception:
        commit = None
    try:
        branch = subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(ROOT)
        ).decode("utf-8").strip()
    except Exception:
        branch = None
    return {"commit": commit, "branch": branch}

def fastapi_routes():
    sys.path.insert(0, str(ROOT))
    try:
        from backend.api import app  # type: ignore
        routes = []
        for r in getattr(app, "routes", []):
            try:
                methods = sorted(list(getattr(r, "methods", [])))
                path = getattr(r, "path", "")
                name = getattr(r, "name", "")
                routes.append({"methods": methods, "path": path, "name": name})
            except Exception:
                pass
        routes.sort(key=lambda x: (x["path"], ",".join(x["methods"])))
        return routes
    except Exception:
        # Import kann legit scheitern (z.B. wenn .env fehlt) – dann leer zurückgeben
        return []

def read_requirements():
    reqs = {}
    for fn in ("requirements.txt", "requirements-img.txt", "pyproject.toml"):
        p = ROOT / fn
        if p.exists():
            try:
                reqs[fn] = {
                    "sha256": sha256_file(p),
                    "size": p.stat().st_size,
                    "content": p.read_text(encoding="utf-8", errors="ignore")
                }
            except Exception:
                pass
    return reqs

def main():
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    snapshot = {
        "created_utc": ts,
        "root": str(ROOT),
        "git": git_info(),
        "files": list_files(),
        "routes": fastapi_routes(),
        "requirements": read_requirements(),
    }
    out = OUT_DIR / f"{ts}.json"
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    LATEST.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[snapshot] geschrieben: {out}")
    print(f"[snapshot] latest -> {LATEST}")

if __name__ == "__main__":
    main()

