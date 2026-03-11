# -*- coding: utf-8 -*-
"""
services/research_ingest.py
============================
Ingestiert Deep-Research-Ergebnisse in die Qdrant knowledge_base Collection.

Funktionen:
  - Deduplizierung via URL-Hash (kein doppeltes Indexieren)
  - Chunking: Snippets direkt, Volltexte in 900-Wort-Chunks
  - Metadaten: source_type=deep_research, session_id, quality_score
  - Vollständig Offline-sicher (wird nur aufgerufen wenn Session gelaufen)

Author: StratGen Sprint 5
"""
from __future__ import annotations

import hashlib
import logging
import os
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from services.deep_research import ResearchSession, ResearchResult

log = logging.getLogger(__name__)

RESEARCH_COLL = os.getenv("QDRANT_RESEARCH_COLLECTION", "knowledge_base")
CHUNK_SIZE    = int(os.getenv("RESEARCH_CHUNK_SIZE", "900"))
CHUNK_OVERLAP = int(os.getenv("RESEARCH_CHUNK_OVERLAP", "100"))

# Hash-Store: verhindert Re-Ingest bei mehrfachem Aufruf
_HASH_STORE_PATH = Path("data/research/.ingested_hashes.txt")


def _load_ingested_hashes() -> set[str]:
    if _HASH_STORE_PATH.exists():
        return set(_HASH_STORE_PATH.read_text().splitlines())
    return set()


def _save_hash(url_hash: str) -> None:
    _HASH_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_HASH_STORE_PATH, "a") as f:
        f.write(url_hash + "\n")


def _chunk_text(text: str) -> list[str]:
    """Teilt Text in überlappende Chunks auf."""
    words = text.split()
    if not words:
        return []
    chunks = []
    i = 0
    while i < len(words):
        chunk = words[i:i + CHUNK_SIZE]
        chunks.append(" ".join(chunk))
        i += CHUNK_SIZE - CHUNK_OVERLAP if CHUNK_SIZE > CHUNK_OVERLAP else CHUNK_SIZE
    return chunks


def _encode_vectors(emb, texts: list[str]) -> list:
    if hasattr(emb, "encode"):
        out = emb.encode(texts, show_progress_bar=False)
    elif callable(emb):
        out = emb(texts)
    else:
        raise ValueError("Embedder: weder encode() noch callable")
    try:
        return out.tolist()
    except AttributeError:
        return list(out)


def ingest_result(result: "ResearchResult", session_id: str, customer_name: str) -> int:
    """
    Ingestiert ein einzelnes ResearchResult in Qdrant.
    Gibt Anzahl der eingefügten Punkte zurück.
    """
    try:
        from services.rag_pipeline import get_qdrant, get_embedder
        from qdrant_client.models import PointStruct
        from qdrant_client.http.models import Distance, VectorParams
    except ImportError as e:
        log.error("rag_pipeline import failed: %s", e)
        return 0

    ingested_hashes = _load_ingested_hashes()
    if result.url_hash in ingested_hashes:
        log.debug("Skipping already ingested: %s", result.url)
        return 0

    # Texte vorbereiten: Snippet + optionaler Volltext
    texts: list[str] = []
    labels: list[str] = []

    if result.snippet:
        combined = f"{result.title}\n{result.snippet}" if result.title else result.snippet
        texts.append(combined)
        labels.append("snippet")

    if result.full_text and len(result.full_text) > 200:
        chunks = _chunk_text(result.full_text)
        texts.extend(chunks)
        labels.extend([f"chunk_{i}" for i in range(len(chunks))])

    if not texts:
        return 0

    try:
        emb = get_embedder()
        qdr = get_qdrant()

        # Collection sicherstellen
        try:
            qdr.get_collection(RESEARCH_COLL)
        except Exception:
            vec = (emb(["ping"])[0] if callable(emb) else emb.encode(["ping"])[0])
            qdr.create_collection(
                collection_name=RESEARCH_COLL,
                vectors_config=VectorParams(size=len(vec), distance=Distance.COSINE),
            )

        vectors = _encode_vectors(emb, texts)
        points = []
        for v, t, label in zip(vectors, texts, labels):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=v,
                payload={
                    # Standard-Kompatibilität mit bestehendem RAG
                    "customer":       customer_name,
                    "customer_name":  customer_name,
                    "text":           t,
                    "title":          result.title,
                    # Deep-Research spezifische Metadaten
                    "source_type":    "deep_research",
                    "source_subtype": result.source_type,
                    "url":            result.url,
                    "domain":         result.domain,
                    "quality_score":  result.quality_score,
                    "session_id":     session_id,
                    "result_id":      result.id,
                    "chunk_label":    label,
                    "retrieved_at":   result.retrieved_at,
                }
            ))

        qdr.upsert(collection_name=RESEARCH_COLL, points=points)
        _save_hash(result.url_hash)
        return len(points)

    except Exception as e:
        log.error("ingest_result failed for %s: %s", result.url, e)
        return 0


def ingest_session(session: "ResearchSession") -> int:
    """
    Ingestiert alle Ergebnisse einer Research-Session.
    Gibt Gesamtanzahl der eingefügten Punkte zurück.
    """
    total = 0
    for result in session.results:
        count = ingest_result(result, session.session_id, session.customer_name)
        total += count
        log.info("Ingested %d points from %s", count, result.url)

    log.info("Session %s: %d total points ingested into %s",
             session.session_id, total, RESEARCH_COLL)
    return total


def get_ingest_stats() -> dict:
    """Gibt Statistiken über ingestierte Research-Ergebnisse zurück."""
    try:
        from services.rag_pipeline import get_qdrant
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        qdr = get_qdrant()
        result = qdr.count(
            collection_name=RESEARCH_COLL,
            count_filter=Filter(must=[
                FieldCondition(key="source_type", match=MatchValue(value="deep_research"))
            ])
        )
        ingested_hashes = _load_ingested_hashes()
        return {
            "total_points": result.count,
            "unique_urls": len(ingested_hashes),
            "collection": RESEARCH_COLL,
        }
    except Exception as e:
        return {"error": str(e)}
