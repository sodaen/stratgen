"""
STRATGEN Self-Learning System (Phase 8)
Lernt aus erfolgreichen Exports und User-Feedback.
"""

from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
import hashlib
import uuid
import threading
import time

# Konfiguration
GENERATED_OUTPUTS_DIR = Path("/home/sodaen/stratgen/data/generated_outputs")
SESSION_COLLECTIONS_DIR = Path("/home/sodaen/stratgen/data/session_collections")
GENERATED_OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
SESSION_COLLECTIONS_DIR.mkdir(parents=True, exist_ok=True)

QUALITY_THRESHOLD = 0.7  # Minimum für Indexierung
SESSION_TTL_HOURS = 24   # Session-Collections Lebenszeit


class SelfLearningSystem:
    """Lernt aus erfolgreichen Exports und Feedback."""
    
    def __init__(self):
        self.feedback_scores: Dict[str, List[int]] = {}  # chunk_id -> scores
        self._cleanup_thread = None
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """Startet den Cleanup-Thread für alte Sessions."""
        def cleanup_loop():
            while True:
                try:
                    self._cleanup_old_sessions()
                except Exception as e:
                    print(f"Session cleanup error: {e}")
                time.sleep(3600)  # Jede Stunde
        
        self._cleanup_thread = threading.Thread(target=cleanup_loop, daemon=True)
        self._cleanup_thread.start()
    
    # ============================================================
    # 8.1 EXPORT FEEDBACK LOOP
    # ============================================================
    
    def on_export_complete(self, export_path: str, session_id: str, export_type: str = "pptx") -> Dict:
        """
        Wird aufgerufen wenn ein Export abgeschlossen ist.
        Analysiert und indexiert bei guter Qualität.
        """
        from services.rag_pipeline import get_embedding
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
        
        result = {
            "session_id": session_id,
            "export_path": export_path,
            "quality_score": 0,
            "indexed": False,
            "chunks_created": 0
        }
        
        try:
            # 1. Export analysieren
            content_chunks = self._extract_export_content(export_path, export_type)
            
            if not content_chunks:
                result["error"] = "Keine Inhalte extrahiert"
                return result
            
            # 2. Quality Score berechnen
            quality_score = self._assess_quality(content_chunks)
            result["quality_score"] = quality_score
            
            # 3. Bei guter Qualität indexieren
            if quality_score >= QUALITY_THRESHOLD:
                client = QdrantClient(host="localhost", port=6333)
                
                points = []
                for i, chunk in enumerate(content_chunks):
                    # Embedding generieren
                    embedding = get_embedding(chunk["text"])
                    
                    point = PointStruct(
                        id=str(uuid.uuid4()),
                        vector=embedding,
                        payload={
                            "text": chunk["text"],
                            "source": f"export_{session_id}",
                            "source_file": Path(export_path).name,
                            "export_type": export_type,
                            "quality_score": chunk.get("quality", quality_score),
                            "session_id": session_id,
                            "indexed_at": datetime.now().isoformat(),
                            "chunk_index": i,
                            "is_generated": True
                        }
                    )
                    points.append(point)
                
                # In generated_outputs Collection speichern
                if points:
                    client.upsert(
                        collection_name="generated_outputs",
                        points=points
                    )
                    result["indexed"] = True
                    result["chunks_created"] = len(points)
                
                # Log für Analytics
                self._log_learning_event(session_id, quality_score, len(points))
            
            # Speichere Export-Metadata
            self._save_export_metadata(result)
            
            return result
            
        except Exception as e:
            result["error"] = str(e)
            return result
    
    def _extract_export_content(self, export_path: str, export_type: str) -> List[Dict]:
        """Extrahiert Inhalte aus einem Export."""
        chunks = []
        path = Path(export_path)
        
        if not path.exists():
            return chunks
        
        if export_type == "pptx":
            try:
                from pptx import Presentation
                prs = Presentation(str(path))
                
                for slide_num, slide in enumerate(prs.slides):
                    slide_text = []
                    for shape in slide.shapes:
                        if hasattr(shape, "text") and shape.text.strip():
                            slide_text.append(shape.text.strip())
                    
                    if slide_text:
                        chunks.append({
                            "text": "\n".join(slide_text),
                            "slide_number": slide_num + 1,
                            "quality": self._assess_text_quality("\n".join(slide_text))
                        })
            except ImportError:
                print("python-pptx nicht installiert")
            except Exception as e:
                print(f"PPTX extraction error: {e}")
        
        elif export_type == "docx":
            try:
                from docx import Document
                doc = Document(str(path))
                
                current_section = []
                for para in doc.paragraphs:
                    if para.text.strip():
                        current_section.append(para.text.strip())
                        
                        # Chunk bei ~500 Wörtern
                        if len(" ".join(current_section).split()) > 500:
                            chunks.append({
                                "text": "\n".join(current_section),
                                "quality": self._assess_text_quality("\n".join(current_section))
                            })
                            current_section = []
                
                if current_section:
                    chunks.append({
                        "text": "\n".join(current_section),
                        "quality": self._assess_text_quality("\n".join(current_section))
                    })
            except ImportError:
                print("python-docx nicht installiert")
            except Exception as e:
                print(f"DOCX extraction error: {e}")
        
        return chunks
    
    def _assess_quality(self, chunks: List[Dict]) -> float:
        """Bewertet die Gesamtqualität eines Exports."""
        if not chunks:
            return 0.0
        
        scores = [chunk.get("quality", 0.5) for chunk in chunks]
        return sum(scores) / len(scores)
    
    def _assess_text_quality(self, text: str) -> float:
        """Bewertet die Qualität eines Textabschnitts."""
        score = 0.5  # Basis
        
        words = text.split()
        word_count = len(words)
        
        # Länge
        if word_count >= 50:
            score += 0.1
        if word_count >= 100:
            score += 0.1
        
        # Struktur (Aufzählungen, etc.)
        if any(line.strip().startswith(('-', '•', '*', '1.', '2.')) for line in text.split('\n')):
            score += 0.1
        
        # Keywords
        marketing_keywords = ['marketing', 'strategie', 'kunde', 'zielgruppe', 'kampagne', 
                            'content', 'brand', 'conversion', 'roi', 'kpi']
        keyword_count = sum(1 for kw in marketing_keywords if kw.lower() in text.lower())
        score += min(0.15, keyword_count * 0.03)
        
        # Keine zu kurzen Sätze
        sentences = text.split('.')
        avg_sentence_length = word_count / max(len(sentences), 1)
        if avg_sentence_length > 8:
            score += 0.05
        
        return min(1.0, score)
    
    def _log_learning_event(self, session_id: str, quality_score: float, chunks_created: int):
        """Loggt ein Learning-Event für Analytics."""
        try:
            import requests
            requests.post(
                "http://localhost:8011/knowledge/analytics/log/ingestion",
                params={
                    "source": f"self_learning_{session_id}",
                    "chunks_created": chunks_created,
                    "chunks_rejected": 0,
                    "duration_ms": 0,
                    "success": True
                },
                json={"rejection_reasons": {}}
            )
        except:
            pass
    
    def _save_export_metadata(self, result: Dict):
        """Speichert Export-Metadata."""
        meta_file = GENERATED_OUTPUTS_DIR / f"{result['session_id']}.json"
        with open(meta_file, 'w') as f:
            json.dump(result, f, indent=2)
    
    # ============================================================
    # 8.2 USER FEEDBACK INTEGRATION
    # ============================================================
    
    def record_feedback(self, chunk_id: str, score: int, session_id: Optional[str] = None) -> Dict:
        """
        Nimmt User-Feedback auf (1-5 oder thumbs up/down).
        score: 1-5 (1=sehr schlecht, 5=sehr gut) oder -1/+1 für thumbs
        """
        # Normalisiere Score
        if score in [-1, 0]:
            normalized_score = 2  # Thumbs down
        elif score == 1:
            normalized_score = 4  # Thumbs up
        else:
            normalized_score = max(1, min(5, score))
        
        # Speichere Feedback
        if chunk_id not in self.feedback_scores:
            self.feedback_scores[chunk_id] = []
        self.feedback_scores[chunk_id].append(normalized_score)
        
        # Log für Analytics
        try:
            import requests
            requests.post(
                "http://localhost:8011/knowledge/analytics/log/feedback",
                params={
                    "chunk_id": chunk_id,
                    "score": normalized_score,
                    "session_id": session_id or ""
                }
            )
        except:
            pass
        
        # Aktualisiere Quality Score bei genug Feedback
        if len(self.feedback_scores[chunk_id]) >= 3:
            avg_score = sum(self.feedback_scores[chunk_id]) / len(self.feedback_scores[chunk_id])
            self._update_chunk_quality(chunk_id, avg_score / 5.0)  # Normalisiere auf 0-1
        
        return {
            "ok": True,
            "chunk_id": chunk_id,
            "feedback_count": len(self.feedback_scores.get(chunk_id, [])),
            "avg_score": sum(self.feedback_scores.get(chunk_id, [])) / len(self.feedback_scores.get(chunk_id, [1]))
        }
    
    def _update_chunk_quality(self, chunk_id: str, new_quality: float):
        """Aktualisiert den Quality Score eines Chunks basierend auf Feedback."""
        from qdrant_client import QdrantClient
        
        try:
            client = QdrantClient(host="localhost", port=6333)
            
            # Versuche in allen Collections
            for collection in ["knowledge_base", "design_templates", "generated_outputs"]:
                try:
                    # Hole aktuellen Punkt
                    points = client.retrieve(
                        collection_name=collection,
                        ids=[chunk_id],
                        with_payload=True
                    )
                    
                    if points:
                        point = points[0]
                        old_quality = point.payload.get("quality_score", 0.5)
                        
                        # Gewichtete Kombination: 60% alter Score, 40% Feedback
                        updated_quality = 0.6 * old_quality + 0.4 * new_quality
                        
                        # Update Payload
                        client.set_payload(
                            collection_name=collection,
                            payload={"quality_score": round(updated_quality, 3), "feedback_adjusted": True},
                            points=[chunk_id]
                        )
                        
                        print(f"Updated {chunk_id} quality: {old_quality:.3f} → {updated_quality:.3f}")
                        return
                except:
                    continue
        except Exception as e:
            print(f"Quality update error: {e}")
    
    def get_low_quality_chunks(self, threshold: float = 0.4, limit: int = 20) -> List[Dict]:
        """Gibt niedrig bewertete Chunks zurück (Cleanup-Kandidaten)."""
        from qdrant_client import QdrantClient
        
        low_quality = []
        
        try:
            client = QdrantClient(host="localhost", port=6333)
            
            for collection in ["knowledge_base", "generated_outputs"]:
                try:
                    result = client.scroll(
                        collection_name=collection,
                        limit=500,
                        with_payload=True,
                        with_vectors=False
                    )[0]
                    
                    for point in result:
                        quality = point.payload.get("quality_score", 0.5)
                        if quality < threshold:
                            low_quality.append({
                                "id": str(point.id),
                                "collection": collection,
                                "quality_score": quality,
                                "source": point.payload.get("source_file", "unknown"),
                                "text_preview": point.payload.get("text", "")[:100]
                            })
                except:
                    continue
            
            # Sortiere nach Quality (niedrigste zuerst)
            low_quality.sort(key=lambda x: x["quality_score"])
            
        except Exception as e:
            print(f"Low quality fetch error: {e}")
        
        return low_quality[:limit]
    
    # ============================================================
    # 8.3 SESSION/UPLOAD ISOLATION
    # ============================================================
    
    def create_session_collection(self, session_id: str) -> str:
        """Erstellt eine isolierte Collection für eine Session."""
        from qdrant_client import QdrantClient
        from qdrant_client.models import VectorParams, Distance
        
        collection_name = f"session_{session_id}"
        
        try:
            client = QdrantClient(host="localhost", port=6333)
            
            # Prüfe ob existiert
            collections = [c.name for c in client.get_collections().collections]
            if collection_name not in collections:
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=768, distance=Distance.COSINE)
                )
            
            # Registriere Session
            self._register_session(session_id)
            
            return collection_name
        except Exception as e:
            print(f"Session creation error: {e}")
            return ""
    
    def add_to_session(self, session_id: str, text: str, metadata: Dict = None) -> str:
        """Fügt Content zur Session-Collection hinzu."""
        from services.rag_pipeline import get_embedding
        from qdrant_client import QdrantClient
        from qdrant_client.models import PointStruct
        
        collection_name = f"session_{session_id}"
        chunk_id = str(uuid.uuid4())
        
        try:
            client = QdrantClient(host="localhost", port=6333)
            embedding = get_embedding(text)
            
            point = PointStruct(
                id=chunk_id,
                vector=embedding,
                payload={
                    "text": text,
                    "session_id": session_id,
                    "indexed_at": datetime.now().isoformat(),
                    "quality_score": self._assess_text_quality(text),
                    **(metadata or {})
                }
            )
            
            client.upsert(collection_name=collection_name, points=[point])
            
            return chunk_id
        except Exception as e:
            print(f"Session add error: {e}")
            return ""
    
    def search_session(self, session_id: str, query: str, limit: int = 5) -> List[Dict]:
        """Sucht nur in der Session-Collection."""
        from services.rag_pipeline import get_embedding
        from qdrant_client import QdrantClient
        
        collection_name = f"session_{session_id}"
        
        try:
            client = QdrantClient(host="localhost", port=6333)
            query_embedding = get_embedding(query)
            
            results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=limit,
                with_payload=True
            )
            
            return [
                {
                    "id": str(r.id),
                    "score": r.score,
                    "text": r.payload.get("text", ""),
                    "metadata": r.payload
                }
                for r in results
            ]
        except Exception as e:
            print(f"Session search error: {e}")
            return []
    
    def delete_session_collection(self, session_id: str) -> bool:
        """Löscht eine Session-Collection."""
        from qdrant_client import QdrantClient
        
        collection_name = f"session_{session_id}"
        
        try:
            client = QdrantClient(host="localhost", port=6333)
            client.delete_collection(collection_name)
            self._unregister_session(session_id)
            return True
        except Exception as e:
            print(f"Session delete error: {e}")
            return False
    
    def _register_session(self, session_id: str):
        """Registriert eine Session für Auto-Cleanup."""
        sessions_file = SESSION_COLLECTIONS_DIR / "active_sessions.json"
        
        try:
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    sessions = json.load(f)
            else:
                sessions = {}
            
            sessions[session_id] = {
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=SESSION_TTL_HOURS)).isoformat()
            }
            
            with open(sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            print(f"Session register error: {e}")
    
    def _unregister_session(self, session_id: str):
        """Entfernt eine Session aus der Registry."""
        sessions_file = SESSION_COLLECTIONS_DIR / "active_sessions.json"
        
        try:
            if sessions_file.exists():
                with open(sessions_file, 'r') as f:
                    sessions = json.load(f)
                
                if session_id in sessions:
                    del sessions[session_id]
                    
                    with open(sessions_file, 'w') as f:
                        json.dump(sessions, f, indent=2)
        except Exception as e:
            print(f"Session unregister error: {e}")
    
    def _cleanup_old_sessions(self):
        """Löscht abgelaufene Session-Collections."""
        sessions_file = SESSION_COLLECTIONS_DIR / "active_sessions.json"
        
        try:
            if not sessions_file.exists():
                return
            
            with open(sessions_file, 'r') as f:
                sessions = json.load(f)
            
            now = datetime.now()
            expired = []
            
            for session_id, info in sessions.items():
                expires_at = datetime.fromisoformat(info["expires_at"])
                if now > expires_at:
                    expired.append(session_id)
            
            for session_id in expired:
                print(f"Cleaning up expired session: {session_id}")
                self.delete_session_collection(session_id)
            
            if expired:
                print(f"Cleaned up {len(expired)} expired sessions")
                
        except Exception as e:
            print(f"Session cleanup error: {e}")


# Singleton Instance
self_learning = SelfLearningSystem()


# ============================================================
# API ENDPOINTS für Self-Learning
# ============================================================

def register_self_learning_routes(app):
    """Registriert Self-Learning API Endpoints."""
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/learning", tags=["Self-Learning"])
    
    @router.post("/export-complete")
    async def on_export_complete(export_path: str, session_id: str, export_type: str = "pptx"):
        """Callback wenn ein Export abgeschlossen ist."""
        result = self_learning.on_export_complete(export_path, session_id, export_type)
        return result
    
    @router.post("/feedback")
    async def record_feedback(chunk_id: str, score: int, session_id: str = None):
        """Nimmt User-Feedback auf."""
        result = self_learning.record_feedback(chunk_id, score, session_id)
        return result
    
    @router.get("/low-quality")
    async def get_low_quality(threshold: float = 0.4, limit: int = 20):
        """Gibt niedrig bewertete Chunks zurück."""
        chunks = self_learning.get_low_quality_chunks(threshold, limit)
        return {"ok": True, "chunks": chunks, "count": len(chunks)}
    
    @router.post("/session/create")
    async def create_session(session_id: str):
        """Erstellt eine isolierte Session-Collection."""
        collection = self_learning.create_session_collection(session_id)
        return {"ok": bool(collection), "collection": collection}
    
    @router.post("/session/{session_id}/add")
    async def add_to_session(session_id: str, text: str, source: str = None):
        """Fügt Content zur Session hinzu."""
        chunk_id = self_learning.add_to_session(session_id, text, {"source": source} if source else None)
        return {"ok": bool(chunk_id), "chunk_id": chunk_id}
    
    @router.get("/session/{session_id}/search")
    async def search_session(session_id: str, query: str, limit: int = 5):
        """Sucht in der Session-Collection."""
        results = self_learning.search_session(session_id, query, limit)
        return {"ok": True, "results": results}
    
    @router.delete("/session/{session_id}")
    async def delete_session(session_id: str):
        """Löscht eine Session-Collection."""
        success = self_learning.delete_session_collection(session_id)
        return {"ok": success}
    
    return router
