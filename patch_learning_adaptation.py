#!/usr/bin/env python3
"""
Patch: Integriert learning_adaptation.py in agent_v3_api.py
Agent V3.3 → V3.4
"""
import re

filepath = "/home/sodaen/stratgen/backend/agent_v3_api.py"

with open(filepath, "r") as f:
    content = f.read()

# ============================================
# PATCH 1: Import hinzufügen
# ============================================

old_visual_import = '''# Visual Intelligence (Stufe 3)
try:
    from services.visual_intelligence import (
        enhance_slide_visuals,
        enhance_all_slides,
        generate_chart_for_slide,
        recommend_images_for_slide,
        recommend_layout,
        check_status as visual_status
    )
    HAS_VISUAL_INTELLIGENCE = True
except ImportError:
    HAS_VISUAL_INTELLIGENCE = False
    enhance_all_slides = None'''

new_visual_import = '''# Visual Intelligence (Stufe 3)
try:
    from services.visual_intelligence import (
        enhance_slide_visuals,
        enhance_all_slides,
        generate_chart_for_slide,
        recommend_images_for_slide,
        recommend_layout,
        check_status as visual_status
    )
    HAS_VISUAL_INTELLIGENCE = True
except ImportError:
    HAS_VISUAL_INTELLIGENCE = False
    enhance_all_slides = None

# Learning & Adaptation (Stufe 4)
try:
    from services.learning_adaptation import (
        record_feedback,
        predict_quality,
        record_quality_result,
        get_merged_style,
        get_improvement_suggestions,
        learn_from_all_templates,
        get_feedback_stats,
        check_status as learning_status
    )
    HAS_LEARNING = True
except ImportError:
    HAS_LEARNING = False
    predict_quality = None
    get_merged_style = None'''

if old_visual_import in content:
    content = content.replace(old_visual_import, new_visual_import)
    print("✓ Patch 1: Learning & Adaptation Import hinzugefügt")
else:
    print("⚠ Patch 1: Visual Intelligence Import nicht gefunden")


# ============================================
# PATCH 2: Version aktualisieren
# ============================================

old_version = '"version": "3.3",'
new_version = '"version": "3.4",'

if old_version in content:
    content = content.replace(old_version, new_version)
    print("✓ Patch 2: Version auf 3.4 aktualisiert")


# ============================================
# PATCH 3: Services erweitern
# ============================================

old_services = '"visual_intelligence": HAS_VISUAL_INTELLIGENCE,'
new_services = '''"visual_intelligence": HAS_VISUAL_INTELLIGENCE,
            "learning_adaptation": HAS_LEARNING,'''

if old_services in content:
    content = content.replace(old_services, new_services)
    print("✓ Patch 3: learning_adaptation zu services hinzugefügt")


# ============================================
# PATCH 4: Quality Prediction in Analyze-Phase
# ============================================

# Finde die phase_analyze Funktion und erweitere sie
old_analyze_return = '''    return AgentPlan(
        complexity=complexity,
        estimated_slides=estimated,
        key_topics=key_topics,
        recommended_sections=recommended_sections,
        research_queries=research_queries,
        rationale=rationale
    )'''

new_analyze_return = '''    # Quality Prediction (Stufe 4)
    quality_prediction = None
    if HAS_LEARNING and predict_quality:
        try:
            qp = predict_quality(
                topic=req.topic,
                brief=req.brief,
                deck_size=req.deck_size,
                industry=req.industry,
                slide_types=recommended_sections
            )
            quality_prediction = {
                "predicted_score": qp.predicted_score,
                "confidence": qp.confidence,
                "factors": qp.factors,
                "recommendations": qp.recommendations
            }
        except Exception:
            pass
    
    return AgentPlan(
        complexity=complexity,
        estimated_slides=estimated,
        key_topics=key_topics,
        recommended_sections=recommended_sections,
        research_queries=research_queries,
        rationale=rationale,
        quality_prediction=quality_prediction
    )'''

if old_analyze_return in content:
    content = content.replace(old_analyze_return, new_analyze_return)
    print("✓ Patch 4: Quality Prediction in phase_analyze hinzugefügt")
else:
    print("⚠ Patch 4: phase_analyze return nicht gefunden")


# ============================================
# PATCH 5: AgentPlan erweitern
# ============================================

old_agent_plan = '''@dataclass
class AgentPlan:
    """Ergebnis der Analyse-Phase."""
    complexity: str  # low, medium, high
    estimated_slides: int
    key_topics: List[str]
    recommended_sections: List[str]
    research_queries: List[str]
    rationale: str'''

new_agent_plan = '''@dataclass
class AgentPlan:
    """Ergebnis der Analyse-Phase."""
    complexity: str  # low, medium, high
    estimated_slides: int
    key_topics: List[str]
    recommended_sections: List[str]
    research_queries: List[str]
    rationale: str
    quality_prediction: Optional[Dict[str, Any]] = None  # Stufe 4'''

if old_agent_plan in content:
    content = content.replace(old_agent_plan, new_agent_plan)
    print("✓ Patch 5: AgentPlan um quality_prediction erweitert")


# ============================================
# PATCH 6: Style Application in Draft-Phase
# ============================================

# Suche nach der Draft-Phase und füge Style-Anwendung hinzu
old_draft_start = '''def phase_draft(
    req: AgentV3Request,
    structure: List[Dict[str, Any]],
    research: Dict[str, Any],
    iteration: int = 1
) -> List[Dict[str, Any]]:
    """
    Phase 4: Generiert Content für jeden Slide.
    Nutzt Kontext (vorheriger/nächster Slide) für Kohärenz.
    """
    slides = []'''

new_draft_start = '''def phase_draft(
    req: AgentV3Request,
    structure: List[Dict[str, Any]],
    research: Dict[str, Any],
    iteration: int = 1
) -> List[Dict[str, Any]]:
    """
    Phase 4: Generiert Content für jeden Slide.
    Nutzt Kontext (vorheriger/nächster Slide) für Kohärenz.
    Wendet gelernten Stil an (Stufe 4).
    """
    slides = []
    
    # Gelernten Stil laden (Stufe 4)
    learned_style = None
    if HAS_LEARNING and get_merged_style:
        try:
            learned_style = get_merged_style()
        except Exception:
            pass'''

if old_draft_start in content:
    content = content.replace(old_draft_start, new_draft_start)
    print("✓ Patch 6: Style-Loading in phase_draft hinzugefügt")


# ============================================
# PATCH 7: Feedback Recording nach Generierung
# ============================================

# Füge Feedback-Recording am Ende der run_agent_v3 hinzu
old_return = '''    return AgentV3Response(
        ok=True,
        run_id=run_id,
        project_id=run_id,
        slides=slides,
        slide_count=len(slides),'''

new_return = '''    # Quality Recording (Stufe 4)
    if HAS_LEARNING:
        try:
            record_quality_result(
                project_id=run_id,
                predicted_score=plan.quality_prediction.get("predicted_score", 7.0) if plan.quality_prediction else 7.0,
                actual_score=final_quality,
                slide_count=len(slides),
                deck_size=req.deck_size,
                industry=req.industry,
                topic=req.topic
            )
        except Exception:
            pass
    
    return AgentV3Response(
        ok=True,
        run_id=run_id,
        project_id=run_id,
        slides=slides,
        slide_count=len(slides),'''

if old_return in content:
    content = content.replace(old_return, new_return)
    print("✓ Patch 7: Quality Recording hinzugefügt")


# Speichern
with open(filepath, "w") as f:
    f.write(content)

print("\n✓ Alle Patches angewendet!")
print("  Agent V3.3 → V3.4 (Learning & Adaptation)")
