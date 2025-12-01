# -*- coding: utf-8 -*-
"""
workers/tasks/llm_tasks.py
==========================
LLM Tasks für Celery Worker

Diese Tasks sind GPU-intensiv und können auf GPU-Rechnern
priorisiert werden.

Tasks:
- generate_content: Text-Generierung
- generate_embedding: Embedding-Generierung
- analyze_with_llm: LLM-basierte Analyse
"""
from celery import shared_task
from typing import Dict, Any, List, Optional
import time

# ============================================
# LLM SERVICE IMPORT
# ============================================

def get_llm_service():
    """Lazy Import des LLM Service."""
    try:
        from services.llm import generate as llm_generate, LLM_AVAILABLE
        return llm_generate, LLM_AVAILABLE
    except ImportError:
        return None, False


def get_embedding_service():
    """Lazy Import des Embedding Service."""
    try:
        from services.semantic_slide_matcher import get_embedding
        return get_embedding
    except ImportError:
        return None


# ============================================
# TASKS
# ============================================

@shared_task(
    bind=True,
    name="llm.generate_content",
    max_retries=3,
    default_retry_delay=5,
    autoretry_for=(Exception,),
    retry_backoff=True
)
def generate_content(
    self,
    prompt: str,
    model: str = "mistral",
    max_tokens: int = 500,
    temperature: float = 0.7,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generiert Text-Content mit LLM.
    
    Args:
        prompt: Der Prompt
        model: Das Modell (mistral, llama3, qwen)
        max_tokens: Maximale Tokens
        temperature: Kreativität (0-1)
        context: Zusätzlicher Kontext
    
    Returns:
        Dictionary mit Response
    """
    start_time = time.time()
    
    llm_generate, is_available = get_llm_service()
    
    if not is_available or llm_generate is None:
        return {
            "ok": False,
            "error": "LLM Service nicht verfügbar",
            "task_id": self.request.id
        }
    
    try:
        # Context zum Prompt hinzufügen
        full_prompt = prompt
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            full_prompt = f"{context_str}\n\n{prompt}"
        
        result = llm_generate(
            full_prompt,
            model=model,
            max_tokens=max_tokens,
            temperature=temperature
        )
        
        elapsed = time.time() - start_time
        
        return {
            "ok": result.get("ok", False),
            "response": result.get("response", ""),
            "model": model,
            "elapsed_ms": int(elapsed * 1000),
            "task_id": self.request.id
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "task_id": self.request.id
        }


@shared_task(
    bind=True,
    name="llm.generate_embedding",
    max_retries=2,
    default_retry_delay=3
)
def generate_embedding(
    self,
    text: str,
    model: str = "nomic-embed-text"
) -> Dict[str, Any]:
    """
    Generiert Embedding für Text.
    
    Args:
        text: Der zu embedende Text
        model: Das Embedding-Modell
    
    Returns:
        Dictionary mit Embedding-Vektor
    """
    get_embedding = get_embedding_service()
    
    if get_embedding is None:
        return {
            "ok": False,
            "error": "Embedding Service nicht verfügbar",
            "task_id": self.request.id
        }
    
    try:
        embedding = get_embedding(text)
        
        return {
            "ok": True,
            "embedding": embedding,
            "dimensions": len(embedding) if embedding else 0,
            "task_id": self.request.id
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "task_id": self.request.id
        }


@shared_task(
    bind=True,
    name="llm.generate_slide_content",
    max_retries=3,
    default_retry_delay=5
)
def generate_slide_content(
    self,
    slide_type: str,
    title: str,
    topic: str,
    brief: str,
    context: Optional[Dict[str, Any]] = None,
    voice_guidelines: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generiert Content für einen Slide.
    
    Args:
        slide_type: Typ des Slides (problem, solution, etc.)
        title: Slide-Titel
        topic: Hauptthema
        brief: Briefing
        context: Zusätzlicher Kontext
        voice_guidelines: Schreibstil-Richtlinien
    
    Returns:
        Dictionary mit Slide-Content
    """
    llm_generate, is_available = get_llm_service()
    
    if not is_available:
        return {"ok": False, "error": "LLM nicht verfügbar"}
    
    # Prompt bauen
    voice_instruction = ""
    if voice_guidelines:
        tone = voice_guidelines.get("tone", "")
        power_words = voice_guidelines.get("power_words_to_use", [])[:5]
        if tone:
            voice_instruction = f"\nSchreibstil: {tone}"
        if power_words:
            voice_instruction += f"\nVerwende Power-Words: {', '.join(power_words)}"
    
    prompt = f"""Generiere Bullet Points für einen {slide_type}-Slide:

Thema: {topic}
Slide-Titel: {title}
Briefing: {brief[:500]}
{voice_instruction}

Generiere 3-5 prägnante Bullet Points (jeweils 10-20 Wörter).
Sprache: Deutsch

Antworte NUR mit JSON:
{{"bullets": ["Punkt 1", "Punkt 2", "Punkt 3"]}}"""

    try:
        result = llm_generate(prompt, max_tokens=400)
        
        if result.get("ok"):
            import json
            import re
            
            response = result.get("response", "")
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            
            if json_match:
                data = json.loads(json_match.group())
                bullets = data.get("bullets", [])[:5]
                
                return {
                    "ok": True,
                    "type": slide_type,
                    "title": title,
                    "bullets": bullets,
                    "task_id": self.request.id
                }
        
        return {
            "ok": False,
            "error": "Konnte JSON nicht parsen",
            "raw_response": result.get("response", "")[:200]
        }
        
    except Exception as e:
        return {
            "ok": False,
            "error": str(e),
            "task_id": self.request.id
        }


@shared_task(
    bind=True,
    name="llm.batch_generate",
    max_retries=2
)
def batch_generate(
    self,
    prompts: List[Dict[str, Any]],
    model: str = "mistral"
) -> Dict[str, Any]:
    """
    Batch-Generierung für mehrere Prompts.
    
    Args:
        prompts: Liste von {id, prompt, max_tokens}
        model: Das Modell
    
    Returns:
        Dictionary mit allen Responses
    """
    llm_generate, is_available = get_llm_service()
    
    if not is_available:
        return {"ok": False, "error": "LLM nicht verfügbar"}
    
    results = []
    
    for item in prompts:
        try:
            result = llm_generate(
                item.get("prompt", ""),
                model=model,
                max_tokens=item.get("max_tokens", 300)
            )
            
            results.append({
                "id": item.get("id"),
                "ok": result.get("ok", False),
                "response": result.get("response", "")
            })
            
        except Exception as e:
            results.append({
                "id": item.get("id"),
                "ok": False,
                "error": str(e)
            })
    
    return {
        "ok": True,
        "results": results,
        "total": len(prompts),
        "successful": sum(1 for r in results if r.get("ok")),
        "task_id": self.request.id
    }
