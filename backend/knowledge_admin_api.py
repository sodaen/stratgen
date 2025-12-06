"""
STRATGEN Knowledge Admin API
Endpoints für Knowledge-Management

Speichere als: /home/sodaen/stratgen/backend/knowledge_admin_api.py
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict
from pathlib import Path
import logging
import time

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/knowledge/admin", tags=["knowledge-admin"])

DATA_ROOT = Path("/home/sodaen/stratgen/data")


class IngestRequest(BaseModel):
    path: str
    source_type: str = "knowledge"  # knowledge, template, external, generated
    extensions: List[str] = [".txt", ".md", ".pdf", ".docx", ".pptx"]


class ReindexRequest(BaseModel):
    collection: str
    clear_first: bool = False


# === STATUS & METRICS ===

@router.get("/status")
async def get_knowledge_status():
    """Gibt umfassenden Knowledge-Status zurück."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        
        collections_info = {}
        total_chunks = 0
        
        for coll in client.get_collections().collections:
            info = client.get_collection(coll.name)
            count = info.points_count
            collections_info[coll.name] = {
                "points": count,
                "status": "green" if count > 0 else "yellow"
            }
            total_chunks += count
        
        # Metriken
        from services.knowledge_metrics import get_metrics
        metrics = get_metrics().to_dict()
        
        return {
            "ok": True,
            "collections": collections_info,
            "total_chunks": total_chunks,
            "metrics": metrics
        }
    
    except Exception as e:
        logger.error(f"Status failed: {e}")
        raise HTTPException(500, str(e))


@router.get("/metrics")
async def get_knowledge_metrics():
    """Gibt Knowledge-Metriken zurück."""
    try:
        from services.knowledge_metrics import get_metrics
        return {"ok": True, "metrics": get_metrics().to_dict()}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/metrics/prometheus")
async def get_prometheus_metrics():
    """Exportiert Metriken im Prometheus-Format."""
    from fastapi.responses import PlainTextResponse
    from services.knowledge_metrics import get_metrics
    return PlainTextResponse(
        content=get_metrics().to_prometheus(),
        media_type="text/plain"
    )


# === COLLECTIONS ===

@router.get("/collections")
async def list_collections():
    """Listet alle Qdrant Collections."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        
        collections = []
        for coll in client.get_collections().collections:
            info = client.get_collection(coll.name)
            collections.append({
                "name": coll.name,
                "points": info.points_count,
                "vector_size": info.config.params.vectors.size if hasattr(info.config.params.vectors, 'size') else None
            })
        
        return {"ok": True, "collections": collections}
    
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/collections/{name}")
async def get_collection_details(name: str, sample_size: int = 20):
    """Gibt Details zu einer Collection."""
    try:
        from qdrant_client import QdrantClient
        from collections import Counter
        
        client = QdrantClient(host="localhost", port=6333)
        info = client.get_collection(name)
        
        # Sample holen
        sample = client.scroll(
            collection_name=name,
            limit=sample_size,
            with_payload=True,
            with_vectors=False
        )[0]
        
        sources = Counter()
        source_types = Counter()
        chunk_sizes = []
        quality_scores = []
        
        for point in sample:
            payload = point.payload or {}
            sources[payload.get("source_file", "unknown")] += 1
            source_types[payload.get("source_type", "unknown")] += 1
            
            if "chunk_size_chars" in payload:
                chunk_sizes.append(payload["chunk_size_chars"])
            if "quality_score" in payload:
                quality_scores.append(payload["quality_score"])
        
        return {
            "ok": True,
            "name": name,
            "points": info.points_count,
            "sample_analysis": {
                "top_sources": dict(sources.most_common(10)),
                "source_types": dict(source_types),
                "avg_chunk_size": sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
                "avg_quality_score": sum(quality_scores) / len(quality_scores) if quality_scores else 0
            }
        }
    
    except Exception as e:
        raise HTTPException(500, str(e))


@router.delete("/collections/{name}")
async def delete_collection(name: str):
    """Löscht eine Collection."""
    try:
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333)
        client.delete_collection(name)
        return {"ok": True, "deleted": name}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/collections/{name}/clear")
async def clear_collection(name: str):
    """Leert eine Collection (behält Schema)."""
    try:
        from qdrant_client import QdrantClient
        from qdrant_client.http import models
        
        client = QdrantClient(host="localhost", port=6333)
        
        # Hole Config
        info = client.get_collection(name)
        
        # Lösche und erstelle neu
        client.delete_collection(name)
        client.create_collection(
            collection_name=name,
            vectors_config=models.VectorParams(
                size=768,
                distance=models.Distance.COSINE
            )
        )
        
        return {"ok": True, "cleared": name}
    
    except Exception as e:
        raise HTTPException(500, str(e))


# === INGESTION ===

@router.post("/ingest/file")
async def ingest_file(request: IngestRequest, background_tasks: BackgroundTasks):
    """Indexiert eine einzelne Datei."""
    from services.knowledge_pipeline import KnowledgePipeline
    
    pipeline = KnowledgePipeline()
    result = pipeline.ingest_file(request.path, request.source_type)
    
    return result


@router.post("/ingest/directory")
async def ingest_directory(request: IngestRequest, background_tasks: BackgroundTasks):
    """Indexiert ein Verzeichnis (async)."""
    
    def run_ingestion():
        from services.knowledge_pipeline import KnowledgePipeline
        from services.knowledge_metrics import get_metrics
        
        start = time.time()
        pipeline = KnowledgePipeline()
        result = pipeline.ingest_directory(
            request.path, 
            request.source_type,
            request.extensions
        )
        duration = (time.time() - start) * 1000
        
        # Metriken aufzeichnen
        metrics = get_metrics()
        metrics.record_ingestion(
            source_type=request.source_type,
            success=result.get("ok", False),
            chunks_created=result.get("chunks_total", 0),
            duration_ms=duration
        )
        
        logger.info(f"Ingestion completed: {result.get('files_processed')} files, {result.get('chunks_total')} chunks")
    
    background_tasks.add_task(run_ingestion)
    
    return {
        "ok": True,
        "message": "Ingestion started in background",
        "path": request.path
    }


@router.post("/ingest/knowledge")
async def ingest_knowledge_folder(background_tasks: BackgroundTasks):
    """Indexiert den /knowledge Ordner."""
    request = IngestRequest(
        path=str(DATA_ROOT / "knowledge"),
        source_type="knowledge",
        extensions=[".txt", ".md"]
    )
    return await ingest_directory(request, background_tasks)


@router.post("/ingest/templates")
async def ingest_templates_folder(background_tasks: BackgroundTasks):
    """Indexiert den /raw Ordner (PPTX Templates)."""
    request = IngestRequest(
        path=str(DATA_ROOT / "raw"),
        source_type="template",
        extensions=[".pptx"]
    )
    return await ingest_directory(request, background_tasks)


# === SEARCH & INSPECT ===

@router.get("/search")
async def search_knowledge(
    query: str,
    collection: str = "knowledge_base",
    limit: int = 10
):
    """Sucht in einer Collection."""
    try:
        from qdrant_client import QdrantClient
        import httpx
        from services.knowledge_metrics import get_metrics
        
        start = time.time()
        
        # Embedding
        resp = httpx.post(
            "http://localhost:11434/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": query},
            timeout=30.0
        )
        embedding = resp.json().get("embedding", [])
        
        if not embedding:
            raise HTTPException(500, "Failed to generate embedding")
        
        # Search
        client = QdrantClient(host="localhost", port=6333)
        results = client.search(
            collection_name=collection,
            query_vector=embedding,
            limit=limit,
            with_payload=True
        )
        
        latency = (time.time() - start) * 1000
        top_score = results[0].score if results else 0
        
        # Metriken
        get_metrics().record_search(latency, top_score)
        
        return {
            "ok": True,
            "query": query,
            "collection": collection,
            "latency_ms": latency,
            "results": [
                {
                    "score": r.score,
                    "text": r.payload.get("text", "")[:500],
                    "source": r.payload.get("source_file"),
                    "chunk_index": r.payload.get("chunk_index"),
                    "quality_score": r.payload.get("quality_score")
                }
                for r in results
            ]
        }
    
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/chunks/{collection}/{chunk_id}")
async def get_chunk(collection: str, chunk_id: str):
    """Gibt Details zu einem spezifischen Chunk."""
    try:
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=6333)
        
        # Suche nach ID
        result = client.retrieve(
            collection_name=collection,
            ids=[int(chunk_id)],
            with_payload=True,
            with_vectors=False
        )
        
        if not result:
            raise HTTPException(404, "Chunk not found")
        
        return {
            "ok": True,
            "chunk": {
                "id": chunk_id,
                **result[0].payload
            }
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, str(e))


# === MAINTENANCE ===

@router.post("/rebuild")
async def rebuild_all(background_tasks: BackgroundTasks, clear_first: bool = True):
    """Kompletter Rebuild aller Collections."""
    
    def run_rebuild():
        from services.knowledge_pipeline import run_full_ingestion
        run_full_ingestion()
    
    background_tasks.add_task(run_rebuild)
    
    return {
        "ok": True,
        "message": "Full rebuild started in background"
    }


@router.get("/files/{folder}")
async def list_source_files(folder: str):
    """Listet Quelldateien in einem Ordner."""
    folder_map = {
        "knowledge": DATA_ROOT / "knowledge",
        "raw": DATA_ROOT / "raw",
        "exports": DATA_ROOT / "exports",
        "uploads": DATA_ROOT / "uploads"
    }
    
    path = folder_map.get(folder)
    if not path or not path.exists():
        raise HTTPException(404, f"Folder not found: {folder}")
    
    files = []
    for f in path.iterdir():
        if f.is_file():
            files.append({
                "name": f.name,
                "size_bytes": f.stat().st_size,
                "modified": f.stat().st_mtime
            })
    
    return {
        "ok": True,
        "folder": folder,
        "path": str(path),
        "files": sorted(files, key=lambda x: x["name"])
    }


# === RE-RANKING ENDPOINTS ===

@router.get("/search/rerank")
async def search_with_reranking(
    query: str,
    collection: str = "knowledge_base",
    limit: int = 5,
    use_llm: bool = True
):
    """Suche mit Re-Ranking für bessere Ergebnisse."""
    try:
        from services.reranker import search_with_rerank
        result = search_with_rerank(
            query=query,
            collection=collection,
            limit=limit,
            use_llm=use_llm
        )
        return {"ok": True, **result}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.get("/benchmark")
async def run_benchmark():
    """Führt Benchmark mit Test-Queries durch."""
    from services.reranker import search_with_rerank
    
    test_queries = [
        "Marketing Strategie",
        "B2B SaaS Go-to-Market",
        "Content Marketing Best Practices",
        "Zielgruppen Analyse",
        "Social Media Strategie",
        "Competitive Intelligence",
        "Customer Journey Mapping",
        "Brand Positioning",
        "Lead Generation Taktiken",
        "ROI Marketing Kampagnen"
    ]
    
    results = {
        "without_rerank": {"scores": [], "latencies": []},
        "with_rerank": {"scores": [], "latencies": []}
    }
    
    for query in test_queries:
        # Ohne Re-Ranking
        r1 = search_with_rerank(query, use_llm=False)
        results["without_rerank"]["scores"].append(r1["scores"]["original_avg"])
        results["without_rerank"]["latencies"].append(r1["latency"]["total_ms"])
        
        # Mit Re-Ranking  
        r2 = search_with_rerank(query, use_llm=True)
        results["with_rerank"]["scores"].append(r2["scores"]["final_avg"])
        results["with_rerank"]["latencies"].append(r2["latency"]["total_ms"])
    
    # Durchschnitte berechnen
    avg_score_without = sum(results["without_rerank"]["scores"]) / len(test_queries)
    avg_score_with = sum(results["with_rerank"]["scores"]) / len(test_queries)
    avg_latency_without = sum(results["without_rerank"]["latencies"]) / len(test_queries)
    avg_latency_with = sum(results["with_rerank"]["latencies"]) / len(test_queries)
    
    return {
        "ok": True,
        "queries_tested": len(test_queries),
        "without_rerank": {
            "avg_score": round(avg_score_without, 3),
            "avg_latency_ms": round(avg_latency_without)
        },
        "with_rerank": {
            "avg_score": round(avg_score_with, 3),
            "avg_latency_ms": round(avg_latency_with)
        },
        "improvement": {
            "score": round(avg_score_with - avg_score_without, 3),
            "score_percent": round((avg_score_with - avg_score_without) / avg_score_without * 100, 1)
        },
        "details": {
            "queries": test_queries,
            "scores_without": results["without_rerank"]["scores"],
            "scores_with": results["with_rerank"]["scores"]
        }
    }

# ============================================================
# MANUAL CONTROL ENDPOINTS (Phase 7.3)
# ============================================================

@router.post("/collections/{collection}/clear")
async def clear_collection(collection: str):
    """Löscht alle Chunks aus einer Collection."""
    from qdrant_client import QdrantClient
    from qdrant_client.models import VectorParams, Distance
    
    allowed = ["knowledge_base", "design_templates", "external_sources", "generated_outputs"]
    if collection not in allowed:
        raise HTTPException(400, f"Collection {collection} nicht erlaubt")
    
    try:
        client = QdrantClient(host="localhost", port=6333)
        
        # Hole aktuelle Config
        info = client.get_collection(collection)
        
        # Lösche und erstelle neu
        client.delete_collection(collection)
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )
        
        return {"ok": True, "message": f"Collection {collection} geleert"}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/rebuild")
async def full_rebuild():
    """Startet einen vollständigen Rebuild aller Collections."""
    import subprocess
    import threading
    
    def run_rebuild():
        try:
            # Führe das Rebuild-Script aus
            subprocess.run(
                ["python3", "services/knowledge_pipeline.py"],
                cwd="/home/sodaen/stratgen",
                capture_output=True,
                timeout=600
            )
        except Exception as e:
            print(f"Rebuild error: {e}")
    
    # Starte im Hintergrund
    thread = threading.Thread(target=run_rebuild)
    thread.start()
    
    return {"ok": True, "message": "Rebuild gestartet - prüfe Logs für Status"}


@router.post("/ingest/knowledge")
async def ingest_knowledge():
    """Re-indexiert die Knowledge Base."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["python3", "-c", """
import sys
sys.path.insert(0, '/home/sodaen/stratgen')
from services.knowledge_pipeline import ingest_knowledge_base
stats = ingest_knowledge_base()
print(f"Chunks: {stats.get('chunks_created', 0)}")
"""],
            cwd="/home/sodaen/stratgen",
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {"ok": True, "output": result.stdout, "chunks_created": 0}
    except Exception as e:
        raise HTTPException(500, str(e))


@router.post("/ingest/templates")
async def ingest_templates():
    """Re-indexiert die Design Templates."""
    import subprocess
    
    try:
        result = subprocess.run(
            ["python3", "-c", """
import sys
sys.path.insert(0, '/home/sodaen/stratgen')
from services.knowledge_pipeline import ingest_templates
stats = ingest_templates()
print(f"Chunks: {stats.get('chunks_created', 0)}")
"""],
            cwd="/home/sodaen/stratgen",
            capture_output=True,
            text=True,
            timeout=300
        )
        
        return {"ok": True, "output": result.stdout}
    except Exception as e:
        raise HTTPException(500, str(e))
