#!/usr/bin/env bash
# =============================================
# Fix: GitHub CI "No space left on device"
# =============================================

set -euo pipefail
cd ~/stratgen

echo "╔════════════════════════════════════════════╗"
echo "║  GitHub CI Fix: Disk Space Optimization    ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# 1. Erstelle .github/workflows Verzeichnis
mkdir -p .github/workflows

# 2. CI Workflow kopieren
if [[ -f ~/Downloads/ci.yml ]]; then
    cp ~/Downloads/ci.yml .github/workflows/ci.yml
    echo "✓ .github/workflows/ci.yml erstellt"
else
    echo "✗ ci.yml nicht in Downloads!"
    echo "  Bitte erst herunterladen"
    exit 1
fi

# 3. requirements-ci.txt kopieren (optional)
if [[ -f ~/Downloads/requirements-ci.txt ]]; then
    cp ~/Downloads/requirements-ci.txt requirements-ci.txt
    echo "✓ requirements-ci.txt erstellt"
fi

# 4. Git commit & push
echo ""
echo "Committing changes..."
git add .github/workflows/ci.yml
git add requirements-ci.txt 2>/dev/null || true

git commit -m "fix(ci): Optimize disk space, use minimal dependencies

- Free disk space before installing packages
- Use minimal requirements-ci.txt for testing
- Only install core dependencies needed for tests
- Fixes 'No space left on device' error"

# 5. Push
echo ""
echo "Pushing to staging..."
git push origin staging

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║  ✓ CI Fix deployed!                        ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo "GitHub Actions sollte jetzt neu starten."
echo "Check: https://github.com/danielploetz-glitch/stratgen/actions"
