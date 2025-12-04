"""
Chat Learner Service für Stratgen.
Speichert Feedback aus Chat-Interaktionen in die Knowledge Base.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("STRATGEN_DATA", "/home/sodaen/stratgen/data"))
FEEDBACK_DIR = DATA_ROOT / "knowledge" / "chat_feedback"


def save_chat_feedback(
    query: str,
    answer: str,
    sources: list,
    rating: str = "positive",  # positive, negative, neutral
    user_correction: Optional[str] = None
) -> Dict[str, Any]:
    """
    Speichert Chat-Feedback für späteres Learning.
    
    Args:
        query: Die ursprüngliche Frage
        answer: Die generierte Antwort
        sources: Verwendete Quellen
        rating: Bewertung (positive/negative/neutral)
        user_correction: Optional korrigierte Antwort vom User
    """
    try:
        FEEDBACK_DIR.mkdir(parents=True, exist_ok=True)
        
        feedback = {
            "query": query,
            "answer": answer,
            "sources": sources,
            "rating": rating,
            "user_correction": user_correction,
            "timestamp": datetime.now().isoformat()
        }
        
        # Speichere als JSON
        filename = f"feedback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        filepath = FEEDBACK_DIR / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(feedback, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Chat feedback saved: {filename}")
        
        # Bei positiver Bewertung: In Knowledge Base indexieren
        if rating == "positive" and user_correction is None:
            _index_positive_feedback(query, answer)
        
        return {"ok": True, "file": filename}
        
    except Exception as e:
        logger.error(f"Failed to save chat feedback: {e}")
        return {"ok": False, "error": str(e)}


def _index_positive_feedback(query: str, answer: str):
    """Indexiert positive Feedback-Antworten in Qdrant."""
    try:
        from services.ds_ingest import ingest_entry
        
        # Erstelle kombinierten Text
        text = f"Frage: {query}\n\nAntwort: {answer}"
        
        # Speichere temporär als Datei für Ingest
        temp_file = FEEDBACK_DIR / "_temp_feedback.txt"
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(text)
        
        # Indexiere
        entry = {
            "path": str(temp_file),
            "type": "file",
            "source": "chat_feedback"
        }
        result = ingest_entry("stratgen_docs", entry)
        
        # Lösche temp file
        temp_file.unlink(missing_ok=True)
        
        if result.get("ok"):
            logger.info(f"Positive feedback indexed: {result.get('count', 0)} chunks")
        
    except Exception as e:
        logger.warning(f"Failed to index feedback: {e}")


def get_feedback_stats() -> Dict[str, Any]:
    """Gibt Statistiken über Chat-Feedback zurück."""
    try:
        if not FEEDBACK_DIR.exists():
            return {"total": 0, "positive": 0, "negative": 0, "neutral": 0}
        
        files = list(FEEDBACK_DIR.glob("feedback_*.json"))
        
        stats = {"total": len(files), "positive": 0, "negative": 0, "neutral": 0}
        
        for f in files:
            try:
                with open(f) as fp:
                    data = json.load(fp)
                    rating = data.get("rating", "neutral")
                    if rating in stats:
                        stats[rating] += 1
            except:
                pass
        
        return stats
        
    except Exception as e:
        return {"error": str(e)}


def learn_from_corrections() -> Dict[str, Any]:
    """
    Lernt aus User-Korrekturen.
    Indexiert korrigierte Antworten in die Knowledge Base.
    """
    try:
        if not FEEDBACK_DIR.exists():
            return {"ok": True, "learned": 0}
        
        learned = 0
        
        for f in FEEDBACK_DIR.glob("feedback_*.json"):
            try:
                with open(f) as fp:
                    data = json.load(fp)
                
                # Nur Korrekturen verarbeiten
                if data.get("user_correction"):
                    _index_positive_feedback(
                        data["query"], 
                        data["user_correction"]
                    )
                    learned += 1
                    
                    # Markiere als verarbeitet
                    data["correction_indexed"] = True
                    with open(f, 'w') as fp:
                        json.dump(data, fp, ensure_ascii=False, indent=2)
                        
            except:
                pass
        
        return {"ok": True, "learned": learned}
        
    except Exception as e:
        return {"ok": False, "error": str(e)}
