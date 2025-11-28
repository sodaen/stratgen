#!/usr/bin/env bash
set -euo pipefail

echo "== Preflight =="
./scripts/preflight.sh
echo "== Smoke =="
./scripts/smoke_e2e.sh

# 1) Commit nur wenn Änderungen vorliegen
if [ -n "$(git status --porcelain)" ]; then
  git add -A
  git commit -m "checkpoint: E2E stable (save→generate→render + sidecar + compliance)"
else
  echo "Keine Änderungen – commit wird übersprungen."
fi

# 2) Tag & Branch anlegen
STAMP="$(date +%Y%m%d-%H%M)"
TAG_FULL="e2e-stable-${STAMP}"
TAG_MOVING="e2e-stable"
BRANCH="checkpoint/${TAG_FULL}"

echo "== Tags/Branch setzen =="
git tag -f -a "$TAG_FULL" -m "E2E stable checkpoint ${STAMP}" >/dev/null 2>&1 || true
git tag -f -a "$TAG_MOVING" -m "moving pointer to $TAG_FULL" "$TAG_FULL" >/dev/null 2>&1 || true
git branch -f "$BRANCH" "$TAG_FULL" >/dev/null 2>&1 || true

# 3) (Optional) Snapshot-Tarball
SNAPDIR="$HOME/stratgen_snapshots"
mkdir -p "$SNAPDIR"
TAR="$SNAPDIR/${TAG_FULL}.tar.gz"
git archive --format=tar "$TAG_FULL" | gzip -9 > "$TAR"
echo "Snapshot: $TAR"

echo "== Done. Wiederherstellen: ./scripts/restore_to.sh $TAG_FULL  (oder ohne Arg: e2e-stable) =="
