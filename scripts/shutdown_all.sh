#!/usr/bin/env bash
# =============================================
# StratGen: System Shutdown
# =============================================

echo "Stoppe StratGen Services..."

# API stoppen
pkill -f "uvicorn backend.api:app" 2>/dev/null && echo "✓ API gestoppt" || echo "  API war nicht aktiv"

# Ollama stoppen (optional - läuft oft systemweit)
# pkill -f "ollama serve" 2>/dev/null && echo "✓ Ollama gestoppt" || true

echo "✓ Shutdown abgeschlossen"
