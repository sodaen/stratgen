from __future__ import annotations

import os
import uuid
import json
from pathlib import Path
from typing import Iterable, List, Dict

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer


# ---- Konfiguration ----
DATA_DIR = Path(os.getenv("DATA_DIR", "data/raw")).resolve()
COLL     = os.getenv("QDRANT_COLLECTION", "knowledge_base")
QDRANT_URL = os.getenv("QDRANT_URL", "http://127.0.0.1:6333").rstrip("/")
EMBED_MODEL = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")  # 384-Dim


# ---- Helpers ----
def get_qdrant() -> QdrantClient:
    return QdrantClient(url=QDRANT_URL, api_key=os.getenv("QDRANT_API_KEY") or None)

_model: SentenceTransformer | None = None
def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL)
    return _model

def discover_files(root: str | Path = DATA_DIR) -> List[Path]:
    root = Path(root)
    if not root.exists():
        return []
    exts = {".txt", ".md"}  # später: .pdf/.docx/.pptx ergänzen
    files = [p for p in root.rglob("*") if p.suffix.lower() in exts and p.is_file()]
    return sorted(files)

def load_text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return p.read_text(errors="ignore")

def chunk_text(txt: str, max_chars: int = 900) -> List[str]:
    # simple, robuste Chunking-Logik
    txt = txt.strip().replace("\r\n", "\n")
    if not txt:
        return []
    paragraphs = [t.strip() for t in txt.split("\n\n") if t.strip()]
    chunks: List[str] = []
    buff = ""
    for para in paragraphs:
        if len(buff) + 1 + len(para) <= max_chars:
            buff = f"{buff}\n{para}" if buff else para
        else:
            if buff:
                chunks.append(buff)
            if len(para) <= max_chars:
                buff = para
            else:
                # hart splitten, wenn Absatz sehr lang ist
                for i in range(0, len(para), max_chars):
                    chunks.append(para[i:i+max_chars])
                buff = ""
    if buff:
        chunks.append(buff)
    return chunks

def embed(texts: List[str]) -> List[List[float]]:
    m = get_model()
    vecs = m.encode(texts, normalize_embeddings=True)
    return [v.tolist() for v in (vecs if hasattr(vecs, "__iter__") else [vecs])]

def ensure_collection(client: QdrantClient, dim: int, recreate: bool = False) -> None:
    if recreate:
        try:
            client.delete_collection(COLL)
        except Exception:
            pass
    # neu anlegen wenn nicht vorhanden
    try:
        info = client.get_collection(COLL)
        # dimension prüfen
        size = info.vectors_count or info.config.params.vectors.size  # je nach Qdrant-Version
        # Wenn size nicht verlässlich ermittelbar ist, überspringen wir Check.
        # Ansonsten könnte man notfalls recreate=True erzwingen.
    except Exception:
        client.recreate_collection(
            collection_name=COLL,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )

def make_uuid(file_path: Path, idx: int, text: str) -> str:
    base = f"{file_path.as_posix()}::{idx}::{text[:120]}"
    return str(uuid.uuid5(uuid.NAMESPACE_URL, base))

def reindex(recreate: bool = False) -> Dict:
    files = discover_files(DATA_DIR)
    if not files:
        return {"ok": True, "indexed": 0, "warning": f"Keine Dateien in {DATA_DIR}"}

    # Dimension aus Modell ableiten
    dim = get_model().get_sentence_embedding_dimension()
    client = get_qdrant()
    ensure_collection(client, dim, recreate=recreate)

    total_chunks = 0
    batch_points: List[PointStruct] = []
    BATCH_SIZE = 128

    for f in files:
        txt = load_text(f)
        chunks = chunk_text(txt, max_chars=900)
        total_chunks += len(chunks)
        if not chunks:
            continue
        vecs = embed(chunks)
        for i, (ch, v) in enumerate(zip(chunks, vecs)):
            pid = make_uuid(f, i, ch)
            payload = {
                "file": f.as_posix(),
                "idx": i,
                "text": ch
            }
            batch_points.append(PointStruct(id=pid, vector=v, payload=payload))

            if len(batch_points) >= BATCH_SIZE:
                client.upsert(collection_name=COLL, points=batch_points)
                batch_points.clear()

    if batch_points:
        client.upsert(collection_name=COLL, points=batch_points)

    # Count zurückgeben
    try:
        cnt = client.count(COLL, exact=True).count
    except Exception:
        cnt = None

    return {"ok": True, "files": len(files), "chunks": total_chunks, "collection": COLL, "count_after": cnt}
