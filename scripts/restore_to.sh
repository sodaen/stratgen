#!/usr/bin/env bash
set -euo pipefail

TAG="${1:-e2e-stable}"   # Standard: beweglicher Tag 'e2e-stable'
STAMP="$(date +%Y%m%d-%H%M%S)"
BRANCH="restore/${TAG}-${STAMP}"

echo "== Safety: stash working tree (falls uncommitted Änderungen) =="
git stash push -u -m "auto-stash before restore ${TAG}" >/dev/null 2>&1 || true

echo "== Checkout neues Restore-Branch von Tag =="
git fetch --tags >/dev/null 2>&1 || true
git checkout -b "$BRANCH" "$TAG"

echo "== Fertig. Du bist jetzt auf $BRANCH (Quelle: $TAG) =="
git --no-pager log -1 --oneline
