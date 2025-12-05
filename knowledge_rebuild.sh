#!/bin/bash
#
# STRATGEN KNOWLEDGE SYSTEM REBUILD
# Führe dieses Script auf deinem lokalen Rechner aus
#
# Usage: chmod +x knowledge_rebuild.sh && ./knowledge_rebuild.sh
#

set -e

STRATGEN_DIR="/home/sodaen/stratgen"
cd "$STRATGEN_DIR"

echo "========================================="
echo "  STRATGEN KNOWLEDGE SYSTEM REBUILD"
echo "  Phase 1: Cleanup & Reset"
echo "========================================="
echo ""

# Aktiviere venv
source .venv/bin/activate 2>/dev/null || true

# 1. Export-Ordner leeren
echo "=== 1. Export-Ordner leeren ==="
export_count=$(find data/exports -type f 2>/dev/null | wc -l)
echo "Dateien gefunden: $export_count"

if [ $export_count -gt 0 ]; then
    rm -rf data/exports/*
    echo "✅ Export-Ordner geleert"
fi

# Struktur anlegen
mkdir -p data/exports/pptx
mkdir -p data/exports/json
mkdir -p data/exports/archive
mkdir -p data/external
echo "✅ Ordnerstruktur angelegt"

# 2. Qdrant Backup und Reset
echo ""
echo "=== 2. Qdrant Collections analysieren und sichern ==="

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/sodaen/stratgen')

import json
from datetime import datetime
from pathlib import Path
from qdrant_client import QdrantClient

client = QdrantClient(host="localhost", port=6333)

# Backup erstellen
backup_data = {
    "backup_date": datetime.now().isoformat(),
    "collections": {}
}

collections = client.get_collections().collections
print(f"Gefundene Collections: {len(collections)}")

for coll in collections:
    name = coll.name
    info = client.get_collection(name)
    points_count = info.points_count
    
    print(f"\n--- {name} ---")
    print(f"  Points: {points_count}")
    
    backup_data["collections"][name] = {
        "points_count": points_count,
        "vector_size": info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else 'unknown'
    }
    
    if points_count > 0:
        sample = client.scroll(
            collection_name=name,
            limit=min(50, points_count),
            with_payload=True,
            with_vectors=False
        )[0]
        
        sources = {}
        chunk_sizes = []
        for point in sample:
            payload = point.payload or {}
            source = payload.get('source', payload.get('filename', 'unknown'))
            sources[source] = sources.get(source, 0) + 1
            text = payload.get('text', payload.get('content', ''))
            if text:
                chunk_sizes.append(len(text))
        
        backup_data["collections"][name]["sample_sources"] = dict(list(sources.items())[:20])
        backup_data["collections"][name]["avg_chunk_size"] = int(sum(chunk_sizes)/len(chunk_sizes)) if chunk_sizes else 0

# Speichern
backup_path = Path('/home/sodaen/stratgen/data/qdrant_backup_before_reset.json')
backup_path.write_text(json.dumps(backup_data, indent=2, ensure_ascii=False))
print(f"\n✅ Backup gespeichert: {backup_path}")
PYEOF

# 3. Collections löschen und neu erstellen
echo ""
echo "=== 3. Collections neu erstellen ==="

python3 << 'PYEOF'
import sys
sys.path.insert(0, '/home/sodaen/stratgen')

from qdrant_client import QdrantClient
from qdrant_client.http import models

client = QdrantClient(host="localhost", port=6333)

# Alte Collections löschen
old_collections = ['stratgen_docs', 'strategies', 'knowledge_base', 'design_templates', 'external_sources', 'generated_outputs']

for name in old_collections:
    try:
        client.delete_collection(name)
        print(f"🗑️  Gelöscht: {name}")
    except:
        pass

# Neue Collections mit korrekter Konfiguration erstellen
VECTOR_SIZE = 768  # nomic-embed-text dimension

new_collections = {
    "knowledge_base": "Fachwissen aus /knowledge und /raw Text",
    "design_templates": "Visuelle Patterns aus /raw (Moondream)",
    "external_sources": "Wikipedia, News, API-Daten",
    "generated_outputs": "Eigene Outputs für Self-Learning"
}

for name, description in new_collections.items():
    client.create_collection(
        collection_name=name,
        vectors_config=models.VectorParams(
            size=VECTOR_SIZE,
            distance=models.Distance.COSINE
        ),
        optimizers_config=models.OptimizersConfigDiff(
            indexing_threshold=20000,
        ),
        on_disk_payload=True  # Für große Payloads
    )
    print(f"✅ Erstellt: {name} - {description}")

print("\n✅ Alle Collections neu erstellt")
PYEOF

echo ""
echo "========================================="
echo "  Phase 1 abgeschlossen!"
echo "========================================="
echo ""
echo "Nächster Schritt: Phase 2 - Chunking-Strategie"
echo "Führe aus: python3 scripts/phase2_chunking.py"
