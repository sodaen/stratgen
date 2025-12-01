#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
patch_agent_v3_integration.py
=============================
Patcht den Agent V3 um den Feature Orchestrator zu integrieren.

Änderungen:
1. Import des Orchestrators
2. Erweiterte Analyze-Phase
3. Erweiterte Critique-Phase mit QA
4. Enhanced Prompts mit Kontext
"""
import re

AGENT_FILE = "backend/agent_v3_api.py"

def patch_file():
    with open(AGENT_FILE, "r") as f:
        content = f.read()
    
    patches_applied = []
    
    # ========================================
    # PATCH 1: Orchestrator Import hinzufügen
    # ========================================
    
    if "feature_orchestrator" not in content:
        # Finde die Stelle nach den Advanced Features Imports
        old_import = '''except ImportError as e:
    HAS_ADVANCED_FEATURES = False
    print(f"Advanced Features nicht verfügbar: {e}")

# Multi-Modal Export'''
        
        new_import = '''except ImportError as e:
    HAS_ADVANCED_FEATURES = False
    print(f"Advanced Features nicht verfügbar: {e}")

# Feature Orchestrator (Integration Layer)
try:
    from services.feature_orchestrator import (
        orchestrator,
        orchestrate_analysis,
        orchestrate_quality_check,
        check_status as orchestrator_status
    )
    HAS_ORCHESTRATOR = True
except ImportError as e:
    HAS_ORCHESTRATOR = False
    orchestrator = None
    print(f"Feature Orchestrator nicht verfügbar: {e}")

# Multi-Modal Export'''
        
        if old_import in content:
            content = content.replace(old_import, new_import)
            patches_applied.append("PATCH 1: Orchestrator Import")
    
    # ========================================
    # PATCH 2: Services Dictionary erweitern
    # ========================================
    
    if '"orchestrator":' not in content:
        old_services = '"live_generator": HAS_ADVANCED_FEATURES,'
        new_services = '''"live_generator": HAS_ADVANCED_FEATURES,
            "orchestrator": HAS_ORCHESTRATOR,'''
        
        if old_services in content:
            content = content.replace(old_services, new_services)
            patches_applied.append("PATCH 2: Services erweitert")
    
    # ========================================
    # PATCH 3: Version Update
    # ========================================
    
    if '"version": "3.7"' in content:
        content = content.replace('"version": "3.7"', '"version": "3.8"')
        patches_applied.append("PATCH 3: Version auf 3.8")
    
    # ========================================
    # PATCH 4: Enhanced Analyze Phase
    # ========================================
    # Dieser Patch erweitert die _phase_analyze Funktion
    
    # Wir fügen eine neue Hilfsfunktion hinzu statt die bestehende zu ändern
    enhanced_analyze_func = '''
# ============================================
# ENHANCED ANALYSIS (Orchestrator Integration)
# ============================================

def _run_orchestrated_analysis(
    topic: str,
    brief: str,
    customer_name: str = "",
    industry: str = "",
    audience: str = "",
    deck_size: str = "medium"
) -> Dict[str, Any]:
    """
    Führt erweiterte Analyse mit Feature Orchestrator durch.
    
    Returns:
        Dictionary mit orchestrierten Analyse-Ergebnissen
    """
    if not HAS_ORCHESTRATOR or orchestrator is None:
        return {"ok": False, "reason": "Orchestrator nicht verfügbar"}
    
    try:
        analysis = orchestrator.analyze(
            topic=topic,
            brief=brief,
            customer_name=customer_name,
            industry=industry,
            audience=audience,
            deck_size=deck_size
        )
        
        return {
            "ok": True,
            "briefing_quality": analysis.briefing_quality,
            "briefing_intent": analysis.briefing_intent,
            "recommended_framework": analysis.recommended_framework,
            "recommended_structure": analysis.recommended_structure,
            "audience_archetype": analysis.audience_archetype,
            "writing_guidelines": analysis.writing_guidelines,
            "relevant_facts": analysis.relevant_facts,
            "knowledge_gaps": analysis.knowledge_gaps,
            "similar_slides": analysis.similar_slides,
            "template_recommendation": analysis.template_recommendation,
            "personas": analysis.personas,
            "swot": analysis.swot,
            "business_case": analysis.business_case,
            "features_used": analysis.features_used,
            "analysis_time_ms": analysis.analysis_time_ms,
            "_prompt_context": orchestrator.get_enhanced_prompt_context(analysis)
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _run_orchestrated_qa(
    slides: List[Dict[str, Any]],
    topic: str = "",
    industry: str = ""
) -> Dict[str, Any]:
    """
    Führt orchestrierte Qualitätsprüfung durch.
    
    Returns:
        Dictionary mit QA-Ergebnissen
    """
    if not HAS_ORCHESTRATOR or orchestrator is None:
        return {"ok": False, "reason": "Orchestrator nicht verfügbar"}
    
    try:
        qa = orchestrator.quality_check(slides, topic, industry)
        
        return {
            "ok": True,
            "consistency_score": qa.consistency_score,
            "consistency_issues": qa.consistency_issues,
            "complexity_score": qa.complexity_score,
            "complex_slides": qa.complex_slides,
            "evidence_score": qa.evidence_score,
            "unlinked_claims": qa.unlinked_claims,
            "objections": qa.objections,
            "overall_quality": qa.overall_quality,
            "recommendations": qa.recommendations
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}

'''
    
    # Füge die Funktionen vor der ersten Phase-Funktion ein
    if "_run_orchestrated_analysis" not in content:
        # Finde eine gute Stelle zum Einfügen
        marker = "# ============================================\n# PHASE FUNCTIONS"
        if marker in content:
            content = content.replace(marker, enhanced_analyze_func + "\n" + marker)
            patches_applied.append("PATCH 4: Enhanced Analysis Functions")
        else:
            # Alternative: Vor der ersten async def
            alt_marker = "\nasync def _phase_analyze"
            if alt_marker in content:
                content = content.replace(alt_marker, enhanced_analyze_func + alt_marker)
                patches_applied.append("PATCH 4: Enhanced Analysis Functions (alt)")
    
    # ========================================
    # Speichern
    # ========================================
    
    with open(AGENT_FILE, "w") as f:
        f.write(content)
    
    return patches_applied


if __name__ == "__main__":
    patches = patch_file()
    
    if patches:
        print("✓ Patches angewendet:")
        for p in patches:
            print(f"  - {p}")
    else:
        print("⚠ Keine Patches angewendet (bereits vorhanden oder Marker nicht gefunden)")
    
    # Syntax-Check
    import py_compile
    try:
        py_compile.compile(AGENT_FILE, doraise=True)
        print("✓ Syntax OK")
    except py_compile.PyCompileError as e:
        print(f"✗ Syntax-Fehler: {e}")
