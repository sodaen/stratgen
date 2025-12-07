#!/bin/bash
#
# STRATGEN VOLLSTÄNDIGES SHUTDOWN SCRIPT
#

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║           STRATGEN - SYSTEM SHUTDOWN                              ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

echo "→ Stoppe Frontend..."
sudo systemctl stop stratgen-frontend 2>/dev/null || true

echo "→ Stoppe Backend..."
sudo systemctl stop stratgen 2>/dev/null || true

echo "→ Stoppe Celery..."
sudo systemctl stop stratgen-celery 2>/dev/null || true
pkill -f "celery.*worker" 2>/dev/null || true

echo "→ Stoppe Qdrant..."
sudo systemctl stop qdrant 2>/dev/null || true
pkill -x qdrant 2>/dev/null || true

echo "→ Stoppe Ollama (optional - Modelle werden entladen)..."
# Ollama läuft oft als User-Service, nicht stoppen um Modelle geladen zu halten
# sudo systemctl stop ollama 2>/dev/null || true

echo "→ Stoppe Redis..."
# Redis oft als System-Service, optional stoppen
# sudo systemctl stop redis-server 2>/dev/null || true

echo ""
echo "✅ Stratgen Services gestoppt"
echo "   (Redis und Ollama laufen weiter für schnelleren Neustart)"
