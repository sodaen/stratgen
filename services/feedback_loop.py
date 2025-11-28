# -*- coding: utf-8 -*-
"""
services/feedback_loop.py
=========================
Verarbeitet User-Feedback und ermöglicht Reinforcement Learning.
Speichert Bewertungen, lernt aus Korrekturen, verbessert zukünftige Generierungen.

Funktionen:
- record_feedback(): Speichert User-Bewertung für ein Deck
- record_correction(): Speichert manuelle Korrekturen
- get_quality_score(): Berechnet Qualitätsscore für ein Deck
- get_improvement_suggestions(): Gibt Verbesserungsvorschläge
- analyze_patterns(): Analysiert Feedback-Muster
"""
from __future__ import annotations
import os
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from collections import Counter, defaultdict

# ============================================
# KONFIGURATION
# ============================================

FEEDBACK_DB = os.getenv("STRATGEN_FEEDBACK_DB", "data/feedback.json")
QUALITY_WEIGHTS = {
    "structure": 0.20,      # Struktur/Aufbau
    "content": 0.25,        # Inhaltliche Qualität
    "relevance": 0.20,      # Relevanz zum Briefing
    "design": 0.15,         # Visuelle Qualität
    "clarity": 0.20,        # Klarheit/Verständlichkeit
}

# ============================================
# STORAGE
# ============================================

def _load_db() -> Dict[str, Any]:
    """Lädt die Feedback-Datenbank."""
    if os.path.exists(FEEDBACK_DB):
        try:
            with open(FEEDBACK_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "feedback": {},           # project_id -> feedback records
        "corrections": {},        # project_id -> corrections
        "patterns": {
            "common_issues": {},
            "successful_patterns": {},
            "slide_type_scores": {},
        },
        "global_stats": {
            "total_ratings": 0,
            "avg_score": 0,
            "score_distribution": {},
        },
        "updated_at": None
    }


def _save_db(db: Dict[str, Any]) -> None:
    """Speichert die Feedback-Datenbank."""
    os.makedirs(os.path.dirname(FEEDBACK_DB), exist_ok=True)
    db["updated_at"] = datetime.now().isoformat()
    with open(FEEDBACK_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


# ============================================
# FEEDBACK RECORDING
# ============================================

def record_feedback(
    project_id: str,
    overall_score: int,
    dimension_scores: Dict[str, int] = None,
    comments: str = "",
    slide_feedback: List[Dict[str, Any]] = None,
    user_id: str = None
) -> Dict[str, Any]:
    """
    Speichert User-Feedback für ein Deck.
    
    Args:
        project_id: ID des Projekts/Decks
        overall_score: Gesamtbewertung (1-10)
        dimension_scores: Bewertungen pro Dimension (structure, content, etc.)
        comments: Freitext-Kommentar
        slide_feedback: Feedback pro Slide [{slide_idx, score, comment}]
        user_id: Optionale User-ID
    
    Returns:
        Dict mit: ok, feedback_id
    """
    db = _load_db()
    
    # Validierung
    overall_score = max(1, min(10, int(overall_score)))
    
    # Feedback-Record erstellen
    feedback_id = f"fb_{project_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    record = {
        "id": feedback_id,
        "project_id": project_id,
        "overall_score": overall_score,
        "dimension_scores": dimension_scores or {},
        "comments": comments,
        "slide_feedback": slide_feedback or [],
        "user_id": user_id,
        "created_at": datetime.now().isoformat()
    }
    
    # In DB speichern
    if project_id not in db["feedback"]:
        db["feedback"][project_id] = []
    db["feedback"][project_id].append(record)
    
    # Globale Stats aktualisieren
    _update_global_stats(db)
    
    # Patterns analysieren
    _analyze_feedback_patterns(db, record)
    
    _save_db(db)
    
    return {"ok": True, "feedback_id": feedback_id, "message": "Feedback gespeichert"}


def record_correction(
    project_id: str,
    slide_idx: int,
    field: str,
    original_value: Any,
    corrected_value: Any,
    reason: str = ""
) -> Dict[str, Any]:
    """
    Speichert eine manuelle Korrektur durch den User.
    
    Args:
        project_id: ID des Projekts
        slide_idx: Index des Slides
        field: Feld das korrigiert wurde (title, bullets, notes)
        original_value: Ursprünglicher Wert
        corrected_value: Korrigierter Wert
        reason: Grund für die Korrektur
    
    Returns:
        Dict mit: ok, correction_id
    """
    db = _load_db()
    
    correction_id = f"corr_{project_id}_{slide_idx}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    correction = {
        "id": correction_id,
        "project_id": project_id,
        "slide_idx": slide_idx,
        "field": field,
        "original": original_value,
        "corrected": corrected_value,
        "reason": reason,
        "created_at": datetime.now().isoformat()
    }
    
    if project_id not in db["corrections"]:
        db["corrections"][project_id] = []
    db["corrections"][project_id].append(correction)
    
    # Pattern lernen
    _learn_from_correction(db, correction)
    
    _save_db(db)
    
    return {"ok": True, "correction_id": correction_id}


# ============================================
# QUALITY SCORING
# ============================================

def get_quality_score(
    project_id: str = None,
    content: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Berechnet einen Qualitätsscore für ein Deck.
    
    Args:
        project_id: Projekt-ID für historisches Feedback
        content: Deck-Content für automatische Analyse
    
    Returns:
        Dict mit: score, dimension_scores, confidence, suggestions
    """
    db = _load_db()
    
    result = {
        "score": 0,
        "dimension_scores": {},
        "confidence": 0,
        "suggestions": [],
        "based_on_feedback": False
    }
    
    # Wenn Feedback vorhanden, nutze das
    if project_id and project_id in db["feedback"]:
        feedbacks = db["feedback"][project_id]
        if feedbacks:
            scores = [f["overall_score"] for f in feedbacks]
            result["score"] = round(sum(scores) / len(scores), 1)
            result["confidence"] = min(len(feedbacks) * 0.2, 1.0)  # Max 1.0 bei 5+ Feedbacks
            result["based_on_feedback"] = True
            
            # Dimension-Scores aggregieren
            dim_scores = defaultdict(list)
            for f in feedbacks:
                for dim, score in f.get("dimension_scores", {}).items():
                    dim_scores[dim].append(score)
            
            result["dimension_scores"] = {
                dim: round(sum(s) / len(s), 1) 
                for dim, s in dim_scores.items()
            }
            
            return result
    
    # Automatische Analyse basierend auf Content
    if content:
        score, dims, suggestions = _auto_score_content(content, db)
        result["score"] = score
        result["dimension_scores"] = dims
        result["suggestions"] = suggestions
        result["confidence"] = 0.5  # Automatische Scores haben mittlere Konfidenz
    
    return result


def _auto_score_content(
    content: Dict[str, Any], 
    db: Dict[str, Any]
) -> Tuple[float, Dict[str, float], List[str]]:
    """Automatische Qualitätsbewertung basierend auf Content-Analyse."""
    scores = {}
    suggestions = []
    
    slides = content.get("slides", []) or content.get("slide_plan", [])
    
    # Structure Score
    structure_score = 7.0
    if not slides:
        structure_score = 3.0
        suggestions.append("Keine Slides gefunden")
    elif len(slides) < 5:
        structure_score = 5.0
        suggestions.append("Sehr kurzes Deck - mehr Tiefe empfohlen")
    elif len(slides) > 40:
        structure_score = 6.0
        suggestions.append("Sehr langes Deck - Fokussierung empfohlen")
    
    # Prüfe Slide-Typen Vielfalt
    types = [s.get("type") or s.get("layout_hint", "").lower() for s in slides]
    if len(set(types)) < 3:
        structure_score -= 1
        suggestions.append("Mehr Slide-Typ-Vielfalt empfohlen")
    
    scores["structure"] = structure_score
    
    # Content Score
    content_score = 7.0
    total_bullets = 0
    empty_slides = 0
    
    for s in slides:
        bullets = s.get("bullets", [])
        total_bullets += len(bullets)
        if not bullets:
            empty_slides += 1
    
    if slides:
        avg_bullets = total_bullets / len(slides)
        if avg_bullets < 2:
            content_score -= 2
            suggestions.append("Mehr Inhalt pro Slide empfohlen")
        elif avg_bullets > 8:
            content_score -= 1
            suggestions.append("Weniger Text pro Slide - mehr Fokus")
    
    if empty_slides > len(slides) * 0.3:
        content_score -= 2
        suggestions.append(f"{empty_slides} Slides ohne Inhalt")
    
    scores["content"] = content_score
    
    # Relevance Score (braucht Briefing-Vergleich)
    scores["relevance"] = 7.0  # Default
    
    # Design Score (vereinfacht)
    design_score = 7.0
    has_images = any(s.get("has_image") or s.get("image") for s in slides)
    has_charts = any(s.get("has_chart") or s.get("chart") for s in slides)
    
    if not has_images and not has_charts:
        design_score -= 1
        suggestions.append("Visuelle Elemente (Bilder/Charts) empfohlen")
    
    scores["design"] = design_score
    
    # Clarity Score
    clarity_score = 7.0
    for s in slides:
        title = s.get("title", "")
        if len(title) > 60:
            clarity_score -= 0.5
        if not title:
            clarity_score -= 0.5
    
    scores["clarity"] = min(10, max(1, clarity_score))
    
    # Gewichteter Gesamtscore
    total = sum(scores[d] * w for d, w in QUALITY_WEIGHTS.items() if d in scores)
    total_weight = sum(w for d, w in QUALITY_WEIGHTS.items() if d in scores)
    overall = round(total / total_weight, 1) if total_weight else 5.0
    
    return overall, scores, suggestions


# ============================================
# IMPROVEMENT SUGGESTIONS
# ============================================

def get_improvement_suggestions(
    project_id: str = None,
    content: Dict[str, Any] = None,
    slide_types: List[str] = None
) -> List[Dict[str, Any]]:
    """
    Gibt Verbesserungsvorschläge basierend auf gelernten Mustern.
    
    Args:
        project_id: Projekt-ID für historisches Feedback
        content: Aktueller Deck-Content
        slide_types: Liste von Slide-Typen im Deck
    
    Returns:
        Liste von Suggestion-Dicts
    """
    db = _load_db()
    suggestions = []
    
    patterns = db.get("patterns", {})
    common_issues = patterns.get("common_issues", {})
    
    # Häufige Issues als Suggestions
    for issue, count in sorted(common_issues.items(), key=lambda x: -x[1])[:5]:
        suggestions.append({
            "type": "common_issue",
            "message": issue,
            "frequency": count,
            "priority": "high" if count > 5 else "medium"
        })
    
    # Slide-Typ-spezifische Suggestions
    slide_type_scores = patterns.get("slide_type_scores", {})
    for st in (slide_types or []):
        if st in slide_type_scores:
            avg = slide_type_scores[st].get("avg_score", 7)
            if avg < 6:
                suggestions.append({
                    "type": "slide_type",
                    "message": f"'{st}'-Slides haben oft niedrigere Bewertungen ({avg:.1f}/10)",
                    "slide_type": st,
                    "priority": "high"
                })
    
    # Content-basierte Suggestions
    if content:
        slides = content.get("slides", []) or content.get("slide_plan", [])
        
        # Fehlende essentielle Slides
        essential_types = {"title", "executive_summary", "next_steps"}
        present_types = set(s.get("type", "") for s in slides)
        missing = essential_types - present_types
        
        for m in missing:
            suggestions.append({
                "type": "missing_slide",
                "message": f"Essentieller Slide-Typ fehlt: {m}",
                "slide_type": m,
                "priority": "high"
            })
    
    return suggestions


# ============================================
# PATTERN ANALYSIS
# ============================================

def _update_global_stats(db: Dict[str, Any]) -> None:
    """Aktualisiert globale Statistiken."""
    all_scores = []
    for feedbacks in db["feedback"].values():
        for f in feedbacks:
            all_scores.append(f["overall_score"])
    
    if all_scores:
        db["global_stats"]["total_ratings"] = len(all_scores)
        db["global_stats"]["avg_score"] = round(sum(all_scores) / len(all_scores), 2)
        
        # Score-Verteilung
        dist = Counter(all_scores)
        db["global_stats"]["score_distribution"] = dict(dist)


def _analyze_feedback_patterns(db: Dict[str, Any], record: Dict[str, Any]) -> None:
    """Analysiert Feedback für Pattern-Erkennung."""
    # Extrahiere Issues aus Kommentaren
    comments = record.get("comments", "").lower()
    
    issue_keywords = {
        "zu lang": "Deck zu lang",
        "zu kurz": "Deck zu kurz",
        "mehr details": "Mehr Details gewünscht",
        "weniger text": "Zu viel Text",
        "unstrukturiert": "Bessere Struktur nötig",
        "irrelevant": "Relevanz verbessern",
        "langweilig": "Mehr visuelle Elemente",
        "unklar": "Klarere Formulierungen",
        "fehlt": "Fehlende Inhalte",
    }
    
    for keyword, issue in issue_keywords.items():
        if keyword in comments:
            if issue not in db["patterns"]["common_issues"]:
                db["patterns"]["common_issues"][issue] = 0
            db["patterns"]["common_issues"][issue] += 1
    
    # Slide-Feedback analysieren
    for sf in record.get("slide_feedback", []):
        slide_type = sf.get("slide_type", "unknown")
        score = sf.get("score", 0)
        
        if slide_type not in db["patterns"]["slide_type_scores"]:
            db["patterns"]["slide_type_scores"][slide_type] = {
                "total_score": 0,
                "count": 0,
                "avg_score": 0
            }
        
        db["patterns"]["slide_type_scores"][slide_type]["total_score"] += score
        db["patterns"]["slide_type_scores"][slide_type]["count"] += 1
        db["patterns"]["slide_type_scores"][slide_type]["avg_score"] = (
            db["patterns"]["slide_type_scores"][slide_type]["total_score"] / 
            db["patterns"]["slide_type_scores"][slide_type]["count"]
        )


def _learn_from_correction(db: Dict[str, Any], correction: Dict[str, Any]) -> None:
    """Lernt aus einer Korrektur für zukünftige Verbesserungen."""
    field = correction.get("field", "")
    reason = correction.get("reason", "").lower()
    
    # Pattern: Welche Felder werden oft korrigiert?
    if "field_corrections" not in db["patterns"]:
        db["patterns"]["field_corrections"] = {}
    
    if field not in db["patterns"]["field_corrections"]:
        db["patterns"]["field_corrections"][field] = 0
    db["patterns"]["field_corrections"][field] += 1
    
    # Reason-basierte Patterns
    if reason:
        if "reasons" not in db["patterns"]:
            db["patterns"]["reasons"] = {}
        
        # Extrahiere Keywords
        for keyword in ["falsch", "unklar", "zu lang", "zu kurz", "irrelevant", "fehlt"]:
            if keyword in reason:
                if keyword not in db["patterns"]["reasons"]:
                    db["patterns"]["reasons"][keyword] = 0
                db["patterns"]["reasons"][keyword] += 1


def analyze_patterns() -> Dict[str, Any]:
    """
    Analysiert alle gesammelten Feedback-Patterns.
    
    Returns:
        Dict mit: insights, top_issues, recommendations
    """
    db = _load_db()
    
    insights = []
    recommendations = []
    
    # Top Issues
    common_issues = db["patterns"].get("common_issues", {})
    top_issues = sorted(common_issues.items(), key=lambda x: -x[1])[:10]
    
    if top_issues:
        insights.append(f"Top Issue: '{top_issues[0][0]}' ({top_issues[0][1]}x gemeldet)")
    
    # Slide-Typ Performance
    slide_scores = db["patterns"].get("slide_type_scores", {})
    worst_types = sorted(
        [(t, d["avg_score"]) for t, d in slide_scores.items()],
        key=lambda x: x[1]
    )[:3]
    
    for slide_type, score in worst_types:
        if score < 6:
            insights.append(f"'{slide_type}'-Slides performen schlecht (Ø {score:.1f})")
            recommendations.append(f"Verbessere {slide_type}-Slide-Generierung")
    
    # Korrektur-Patterns
    field_corrections = db["patterns"].get("field_corrections", {})
    if field_corrections:
        most_corrected = max(field_corrections.items(), key=lambda x: x[1])
        insights.append(f"Feld '{most_corrected[0]}' wird am häufigsten korrigiert ({most_corrected[1]}x)")
        recommendations.append(f"LLM-Prompt für '{most_corrected[0]}' verbessern")
    
    # Globale Stats
    global_stats = db.get("global_stats", {})
    avg_score = global_stats.get("avg_score", 0)
    
    if avg_score:
        if avg_score < 6:
            insights.append(f"Durchschnittliche Bewertung niedrig: {avg_score:.1f}/10")
            recommendations.append("Grundlegende Qualitätsverbesserungen nötig")
        elif avg_score > 8:
            insights.append(f"Gute durchschnittliche Bewertung: {avg_score:.1f}/10")
    
    return {
        "ok": True,
        "insights": insights,
        "top_issues": [{"issue": i, "count": c} for i, c in top_issues],
        "recommendations": recommendations,
        "global_stats": global_stats,
        "patterns": db["patterns"]
    }


# ============================================
# STATISTICS
# ============================================

def get_feedback_stats() -> Dict[str, Any]:
    """
    Gibt Feedback-Statistiken zurück.
    """
    db = _load_db()
    
    total_projects = len(db["feedback"])
    total_feedbacks = sum(len(f) for f in db["feedback"].values())
    total_corrections = sum(len(c) for c in db["corrections"].values())
    
    return {
        "ok": True,
        "total_projects_rated": total_projects,
        "total_feedback_records": total_feedbacks,
        "total_corrections": total_corrections,
        "global_stats": db.get("global_stats", {}),
        "updated_at": db.get("updated_at")
    }


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print("=== Feedback Loop Test ===\n")
    
    # Test Feedback
    print("--- Recording Feedback ---")
    result = record_feedback(
        project_id="test_project_001",
        overall_score=7,
        dimension_scores={"structure": 8, "content": 6, "clarity": 7},
        comments="Gute Struktur, aber zu wenig Details bei ROI",
        slide_feedback=[
            {"slide_idx": 0, "score": 9, "slide_type": "title"},
            {"slide_idx": 3, "score": 5, "slide_type": "roi", "comment": "Mehr Zahlen"},
        ]
    )
    print(f"Feedback: {result}")
    
    # Test Correction
    print("\n--- Recording Correction ---")
    result = record_correction(
        project_id="test_project_001",
        slide_idx=3,
        field="bullets",
        original_value=["Generischer ROI Text"],
        corrected_value=["ROI von 150% in 12 Monaten erwartet", "Payback nach 6 Monaten"],
        reason="Zu unspezifisch, Zahlen fehlten"
    )
    print(f"Correction: {result}")
    
    # Test Quality Score
    print("\n--- Quality Score ---")
    score = get_quality_score(project_id="test_project_001")
    print(f"Score: {score}")
    
    # Test Suggestions
    print("\n--- Improvement Suggestions ---")
    suggestions = get_improvement_suggestions(
        slide_types=["title", "executive_summary", "roi", "next_steps"]
    )
    for s in suggestions[:3]:
        print(f"  - {s['message']} ({s['priority']})")
    
    # Test Pattern Analysis
    print("\n--- Pattern Analysis ---")
    patterns = analyze_patterns()
    for insight in patterns.get("insights", [])[:3]:
        print(f"  • {insight}")
    
    # Stats
    print("\n--- Stats ---")
    stats = get_feedback_stats()
    print(f"Total projects rated: {stats.get('total_projects_rated')}")
    print(f"Total feedbacks: {stats.get('total_feedback_records')}")
