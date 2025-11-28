#!/usr/bin/env bash
set -euo pipefail
REPO="${REPO:-$HOME/stratgen}"
cd "$REPO"

git config user.name  "${GIT_USER_NAME:-Stratgen Bot}"
git config user.email "${GIT_USER_EMAIL:-bot@local}"

# Snapshots/Changelog – vorhanden im Repo
python3 scripts/snapshot_repo.py   --quick  || true
python3 scripts/changelog_append.py         || true

git add -A
if ! git diff --cached --quiet; then
  msg="auto: snapshot $(date -Iseconds)"
  git commit -m "$msg"
  # Push nur, wenn Upstream gesetzt ist
  if git rev-parse --abbrev-ref --symbolic-full-name @{u} >/dev/null 2>&1; then
    git push || echo "Warn: push failed (kein Remote oder Auth?)"
  else
    echo "Hinweis: kein Upstream gesetzt – skip push"
  fi
else
  echo "Keine Änderungen – skip commit"
fi
