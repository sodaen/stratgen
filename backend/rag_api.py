"""
RAG & Knowledge API für Stratgen.
Endpoints für Knowledge Base Status und Suche.
"""

from fastapi import APIRouter
from datetime import datetime

router = APIRouter(prefix="/rag", tags=["rag"])


@router.get("/status")
async def get_rag_status():
    """Detaillierter RAG-System Status."""
    try:
        from services.unified_knowledge import get_stats
        stats = get_stats()
        
        return {
            "ok": True,
            "rag": {
                "qdrant": stats.get("qdrant_available", False),
                "embedder": stats.get("embedder_available", False),
                "vision": stats.get("vision_available", False)
            },
            "collections": stats.get("collections", {}),
            "directories": stats.get("directories", {}),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/search")
async def search_knowledge(q: str, limit: int = 5):
    """Suche in der Knowledge Base."""
    try:
        from services.unified_knowledge import search
        results = search(q, limit)
        return {
            "ok": True,
            "query": q,
            "results": [
                {
                    "id": r.id,
                    "score": r.score,
                    "text": r.text_content[:300] if r.text_content else "",
                    "source": r.source
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/ingest")
async def ingest_file(file_path: str):
    """Indexiert eine Datei in die Knowledge Base."""
    try:
        from services.unified_knowledge import ingest_file
        result = ingest_file(file_path)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === Template Learning ===
@router.get("/templates/stats")
async def get_template_stats():
    """Statistiken über gelernte Templates."""
    try:
        from services.template_learner import get_stats
        return {"ok": True, **get_stats()}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.post("/templates/scan")
async def scan_templates(limit: int = 10):
    """Scannt /raw Präsentationen und lernt Design-Patterns."""
    try:
        from services.template_learner import scan_raw_presentations
        result = scan_raw_presentations(limit)
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/templates/guidance")
async def get_guidance(slide_type: str = None):
    """Gibt Design-Empfehlungen für einen Slide-Typ."""
    try:
        from services.template_learner import get_design_guidance
        return {"ok": True, **get_design_guidance(slide_type)}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === Knowledge Chat ===
@router.post("/chat")
async def knowledge_chat(request: dict):
    """
    Chat-Endpoint für Knowledge Bot.
    Kombiniert RAG-Suche mit LLM-Generierung.
    """
    try:
        query = request.get("query", "")
        
        if not query:
            return {"ok": False, "error": "Query required"}
        
        # 1. RAG-Suche
        from services.unified_knowledge import search
        results = search(query, limit=5)
        
        context_texts = []
        sources = []
        for r in results:
            if r.text_content and r.score >= 0.4:
                context_texts.append(r.text_content[:400])
                sources.append({
                    "text": r.text_content[:200],
                    "source": r.source,
                    "score": r.score
                })
        
        context = "\n\n".join(context_texts) if context_texts else ""
        
        # 2. LLM-Generierung
        import httpx
        
        prompt = f"""Du bist ein hilfreicher Marketing-Strategie-Assistent.
Beantworte die Frage basierend auf dem folgenden Kontext aus der Knowledge Base.

KONTEXT:
{context if context else 'Kein spezifischer Kontext gefunden.'}

FRAGE: {query}

Antworte präzise und hilfreich auf Deutsch. Beziehe dich auf den Kontext wenn relevant."""

        try:
            llm_response = httpx.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"num_predict": 500}
                },
                timeout=60.0
            )
            
            if llm_response.status_code == 200:
                answer = llm_response.json().get("response", "")
            else:
                # Fallback ohne LLM
                if sources:
                    answer = "Hier sind relevante Informationen:\n\n" + "\n\n".join([s["text"] for s in sources[:3]])
                else:
                    answer = "Ich konnte leider keine relevanten Informationen finden."
        except Exception as e:
            if sources:
                answer = "Hier sind relevante Informationen:\n\n" + "\n\n".join([s["text"] for s in sources[:3]])
            else:
                answer = f"LLM nicht erreichbar: {e}"
        
        return {
            "ok": True,
            "answer": answer,
            "sources": sources[:3],
            "context_used": len(context_texts) > 0
        }
        
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === Chat Feedback ===
@router.post("/chat/feedback")
async def save_chat_feedback(request: dict):
    """Speichert Feedback zu einer Chat-Antwort."""
    try:
        from services.chat_learner import save_chat_feedback
        
        result = save_chat_feedback(
            query=request.get("query", ""),
            answer=request.get("answer", ""),
            sources=request.get("sources", []),
            rating=request.get("rating", "neutral"),
            user_correction=request.get("correction")
        )
        return result
    except Exception as e:
        return {"ok": False, "error": str(e)}


@router.get("/chat/feedback/stats")
async def get_feedback_stats():
    """Gibt Feedback-Statistiken zurück."""
    try:
        from services.chat_learner import get_feedback_stats
        return {"ok": True, **get_feedback_stats()}
    except Exception as e:
        return {"ok": False, "error": str(e)}
