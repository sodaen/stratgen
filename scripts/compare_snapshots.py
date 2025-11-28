#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vergleicht zwei Snapshots (JSON) und schreibt/appendet CHANGELOG.md
Nutzung:
  python scripts/compare_snapshots.py [base.json] [head.json]
Wenn keine Argumente: nimmt die zwei neuesten in changelogs/snapshots/.
"""
from __future__ import annotations
import sys, json, difflib
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
SNAP_DIR = ROOT / "changelogs" / "snapshots"
CHANGELOG = ROOT / "CHANGELOG.md"

def load_snap(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))

def pick_two_latest():
    snaps = sorted(SNAP_DIR.glob("*.json"))
    if len(snaps) < 2:
        raise SystemExit("Zu wenige Snapshots gefunden.")
    return snaps[-2], snaps[-1]

def files_by_path(lst):
    return {x["path"]: x for x in lst}

def route_key(r): 
    return f'{",".join(r.get("methods", []))} {r.get("path","")}'

def compare(base: dict, head: dict) -> str:
    b_files = files_by_path(base.get("files", []))
    h_files = files_by_path(head.get("files", []))

    added = sorted(set(h_files) - set(b_files))
    removed = sorted(set(b_files) - set(h_files))
    modified = sorted([p for p in set(h_files) & set(b_files) if h_files[p]["sha256"] != b_files[p]["sha256"]])

    # Routen
    b_routes = {route_key(r) for r in base.get("routes", [])}
    h_routes = {route_key(r) for r in head.get("routes", [])}
    r_added = sorted(h_routes - b_routes)
    r_removed = sorted(b_routes - h_routes)

    lines = []
    title = f'## {head.get("created_utc")} – Snapshot-Vergleich'
    lines.append(title)
    lines.append("")
    git_b = base.get("git", {})
    git_h = head.get("git", {})
    lines.append(f"- Git: {git_b.get('commit')} → {git_h.get('commit')} (Branch: {git_h.get('branch')})")
    lines.append("")

    def bullet(header, items):
        lines.append(f"### {header} ({len(items)})")
        if not items:
            lines.append("_keine Änderungen_")
        else:
            for it in items:
                lines.append(f"- {it}")
        lines.append("")

    bullet("Dateien hinzugekommen", added)
    bullet("Dateien entfernt", removed)
    bullet("Dateien geändert", modified)

    bullet("Routen hinzugekommen", r_added)
    bullet("Routen entfernt", r_removed)

    # Requirements diffs (nur Hash-Änderungen listen)
    b_req = base.get("requirements", {})
    h_req = head.get("requirements", {})
    for fn in sorted(set(h_req) | set(b_req)):
        b = b_req.get(fn, {})
        h = h_req.get(fn, {})
        if b.get("sha256") != h.get("sha256"):
            lines.append(f"### Dependencies geändert: {fn}")
            b_txt = (b.get("content") or "").splitlines()
            h_txt = (h.get("content") or "").splitlines()
            diff = difflib.unified_diff(b_txt, h_txt, fromfile=f"{fn}(alt)", tofile=f"{fn}(neu)", lineterm="")
            lines.append("```diff")
            lines.extend(list(diff)[:300])  # diff kürzen
            lines.append("```")
            lines.append("")

    return "\n".join(lines)

def main():
    if len(sys.argv) == 3:
        base_p = Path(sys.argv[1])
        head_p = Path(sys.argv[2])
    else:
        base_p, head_p = pick_two_latest()

    base = load_snap(base_p)
    head = load_snap(head_p)
    md = compare(base, head)

    header = f"# Changelog für {head.get('created_utc')}\n\n"
    if CHANGELOG.exists():
        with CHANGELOG.open("a", encoding="utf-8") as f:
            f.write("\n\n")
            f.write(md)
            f.write("\n")
    else:
        CHANGELOG.write_text(header + md + "\n", encoding="utf-8")

    print(f"[changelog] aktualisiert: {CHANGELOG}")
    print(md)

if __name__ == "__main__":
    main()

