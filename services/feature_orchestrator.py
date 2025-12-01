# -*- coding: utf-8 -*-
"""
services/feature_orchestrator.py
================================
Feature Orchestrator - Integriert alle Features automatisch

Orchestriert:
- Briefing Analysis (Quality, Intent, Gaps)
- Structure Optimization (DNA, Semantic, Persona)
- Content Enhancement (Voice, Evidence, Arguments)
- Quality Assurance (Consistency, Complexity, Objections)

Author: StratGen Agent V3.7
"""
from __future__ import annotations
import os
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

# ============================================
# FEATURE IMPORTS
# ============================================

# Briefing Analysis
try:
    from services.briefing_analyzer import analyze as analyze_briefing
    HAS_BRIEFING_ANALYZER = True
except ImportError:
    HAS_BRIEFING_ANALYZER = False
    analyze_briefing = None

# Story Engine
try:
    from services.story_engine import create_story_structure, detect_best_framework
    HAS_STORY_ENGINE = True
except ImportError:
    HAS_STORY_ENGINE = False

# Persona Engine
try:
    from services.persona_engine import analyze_audience, generate_personas
    HAS_PERSONA_ENGINE = True
except ImportError:
    HAS_PERSONA_ENGINE = False

# Competitive Intelligence
try:
    from services.competitive_intelligence import analyze_competition, generate_swot
    HAS_COMPETITIVE = True
except ImportError:
    HAS_COMPETITIVE = False

# ROI Calculator
try:
    from services.roi_calculator import calculate_project_roi
    HAS_ROI = True
except ImportError:
    HAS_ROI = False

# Slide DNA
try:
    from services.slide_dna_analyzer import get_optimal_structure, extract_slide_dna
    HAS_DNA = True
except ImportError:
    HAS_DNA = False

# Semantic Matcher
try:
    from services.semantic_slide_matcher import get_slide_suggestions, find_similar_slides
    HAS_SEMANTIC = True
except ImportError:
    HAS_SEMANTIC = False

# Brand Voice
try:
    from services.brand_voice_extractor import get_writing_guidelines, load_profile
    HAS_VOICE = True
except ImportError:
    HAS_VOICE = False

# Argument Engine
try:
    from services.argument_engine import build_argument_chain, generate_objections, check_deck_consistency
    HAS_ARGUMENTS = True
except ImportError:
    HAS_ARGUMENTS = False

# Content Intelligence
try:
    from services.content_intelligence import (
        link_all_claims,
        score_deck_complexity,
        recommend_template,
        adapt_to_meeting_context,
        detect_knowledge_gaps
    )
    HAS_CONTENT_INTEL = True
except ImportError:
    HAS_CONTENT_INTEL = False

# Knowledge Enhanced
try:
    from services.knowledge_enhanced import search_knowledge_base, extract_facts, check_knowledge_available
    HAS_KNOWLEDGE = True
except ImportError:
    HAS_KNOWLEDGE = False


# ============================================
# DATA CLASSES
# ============================================

@dataclass
class OrchestratedAnalysis:
    """Ergebnis der orchestrierten Analyse."""
    # Briefing Quality
    briefing_quality: float = 0.0
    briefing_intent: str = "inform"
    briefing_gaps: List[str] = field(default_factory=list)
    
    # Audience
    audience_archetype: str = ""
    personas: List[Dict] = field(default_factory=list)
    
    # Structure
    recommended_framework: str = "problem_solution"
    recommended_structure: List[Dict] = field(default_factory=list)
    dna_confidence: float = 0.0
    
    # Similar Content
    similar_slides: List[Dict] = field(default_factory=list)
    template_recommendation: str = ""
    
    # Voice
    writing_guidelines: Dict = field(default_factory=dict)
    
    # Competitive
    swot: Dict = field(default_factory=dict)
    competitors: List[Dict] = field(default_factory=list)
    
    # ROI
    business_case: Dict = field(default_factory=dict)
    
    # Knowledge
    relevant_facts: List[Dict] = field(default_factory=list)
    knowledge_gaps: List[str] = field(default_factory=list)
    
    # Metadata
    features_used: List[str] = field(default_factory=list)
    analysis_time_ms: int = 0


@dataclass
class OrchestratedQA:
    """Ergebnis der orchestrierten Qualitätssicherung."""
    consistency_score: float = 100.0
    consistency_issues: List[Dict] = field(default_factory=list)
    
    complexity_score: float = 0.5
    complex_slides: List[int] = field(default_factory=list)
    
    evidence_score: float = 0.0
    unlinked_claims: List[Dict] = field(default_factory=list)
    
    objections: List[Dict] = field(default_factory=list)
    
    overall_quality: float = 0.0
    recommendations: List[str] = field(default_factory=list)


# ============================================
# ORCHESTRATOR CLASS
# ============================================

class FeatureOrchestrator:
    """
    Orchestriert alle Features automatisch.
    """
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self._log_features()
    
    def _log_features(self):
        """Loggt verfügbare Features."""
        features = {
            "briefing_analyzer": HAS_BRIEFING_ANALYZER,
            "story_engine": HAS_STORY_ENGINE,
            "persona_engine": HAS_PERSONA_ENGINE,
            "competitive": HAS_COMPETITIVE,
            "roi": HAS_ROI,
            "dna": HAS_DNA,
            "semantic": HAS_SEMANTIC,
            "voice": HAS_VOICE,
            "arguments": HAS_ARGUMENTS,
            "content_intel": HAS_CONTENT_INTEL,
            "knowledge": check_knowledge_available()
        }
        
        if self.verbose:
            available = [k for k, v in features.items() if v]
            print(f"[Orchestrator] {len(available)}/{len(features)} Features verfügbar")
    
    # ==========================================
    # PHASE 1: ENHANCED ANALYSIS
    # ==========================================
    
    def analyze(
        self,
        topic: str,
        brief: str,
        customer_name: str = "",
        industry: str = "",
        audience: str = "",
        deck_size: str = "medium",
        meeting_type: str = ""
    ) -> OrchestratedAnalysis:
        """
        Führt erweiterte Analyse mit allen Features durch.
        
        Returns:
            OrchestratedAnalysis mit allen Erkenntnissen
        """
        start_time = time.time()
        result = OrchestratedAnalysis()
        
        # 1. Briefing Analysis
        if HAS_BRIEFING_ANALYZER:
            try:
                ba = analyze_briefing(brief, topic, industry, customer_name)
                if ba.get("ok"):
                    result.briefing_quality = ba.get("quality", {}).get("score", 0)
                    result.briefing_intent = ba.get("intent", {}).get("type", "inform")
                    result.briefing_gaps = [m.get("suggestion", "") for m in ba.get("missing", [])]
                    result.features_used.append("briefing_analyzer")
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] Briefing Analyzer Error: {e}")
        
        # 2. Story Framework Detection
        if HAS_STORY_ENGINE:
            try:
                story = create_story_structure(brief, topic, audience, "", deck_size)
                if story.get("ok"):
                    result.recommended_framework = story.get("framework", {}).get("id", "problem_solution")
                    result.recommended_structure = story.get("recommended_slides", [])
                    result.features_used.append("story_engine")
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] Story Engine Error: {e}")
        
        # 3. Persona/Audience Analysis
        if HAS_PERSONA_ENGINE and audience:
            try:
                aud = analyze_audience(brief, industry, audience)
                if aud.get("ok"):
                    result.audience_archetype = aud.get("primary_archetype", "")
                    result.features_used.append("persona_engine")
                
                # Personas generieren für komplexe Briefings
                if result.briefing_quality > 50:
                    personas = generate_personas(brief, industry, audience, count=2)
                    result.personas = [
                        {"name": p.name, "archetype": p.primary_archetype.value, "goals": p.goals[:3]}
                        for p in personas
                    ]
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] Persona Engine Error: {e}")
        
        # 4. Slide DNA - Optimale Struktur
        if HAS_DNA:
            try:
                dna = get_optimal_structure(topic, deck_size, industry)
                if dna.get("ok"):
                    # Merge mit Story-Struktur wenn besser
                    if dna.get("confidence", 0) > result.dna_confidence:
                        result.dna_confidence = dna.get("confidence", 0)
                        if not result.recommended_structure:
                            result.recommended_structure = dna.get("recommended_structure", [])
                    result.features_used.append("slide_dna")
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] DNA Analyzer Error: {e}")
        
        # 5. Semantic Slide Matching
        if HAS_SEMANTIC:
            try:
                similar = get_slide_suggestions(brief, industry=industry)
                if similar.get("ok"):
                    result.similar_slides = similar.get("suggestions", [])[:5]
                    if similar.get("best_match"):
                        result.template_recommendation = similar["best_match"].get("template", "")
                    result.features_used.append("semantic_matcher")
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] Semantic Matcher Error: {e}")
        
        # 6. Template Recommendation
        if HAS_CONTENT_INTEL and not result.template_recommendation:
            try:
                recs = recommend_template(brief, topic, industry, deck_size)
                if recs:
                    result.template_recommendation = recs[0].template_name
                    result.features_used.append("template_recommender")
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] Template Recommender Error: {e}")
        
        # 7. Brand Voice Guidelines
        if HAS_VOICE:
            try:
                voice = get_writing_guidelines("default")
                if voice.get("ok"):
                    result.writing_guidelines = voice.get("guidelines", {})
                    result.features_used.append("brand_voice")
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] Brand Voice Error: {e}")
        
        # 8. Knowledge Search
        if HAS_KNOWLEDGE:
            try:
                facts = extract_facts(f"{topic} {industry} {brief[:200]}")
                if facts:
                    result.relevant_facts = facts[:10]
                    result.features_used.append("knowledge_enhanced")
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] Knowledge Error: {e}")
        
        # 9. Knowledge Gaps
        if HAS_CONTENT_INTEL:
            try:
                gaps = detect_knowledge_gaps(brief, topic, industry)
                result.knowledge_gaps = [g.suggestion for g in gaps]
            except Exception as e:
                pass
        
        # 10. Competitive Intelligence (wenn Wettbewerber genannt)
        if HAS_COMPETITIVE and any(kw in brief.lower() for kw in ["wettbewerb", "konkurrenz", "vergleich", "vs", "versus"]):
            try:
                comp = analyze_competition(brief, topic, industry)
                if comp.get("ok"):
                    result.competitors = comp.get("competitors", [])[:3]
                    result.swot = comp.get("swot", {})
                    result.features_used.append("competitive_intel")
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] Competitive Intel Error: {e}")
        
        # 11. ROI/Business Case (wenn Zahlen/Budget genannt)
        if HAS_ROI and any(kw in brief.lower() for kw in ["roi", "kosten", "budget", "invest", "€", "euro", "business case"]):
            try:
                roi = calculate_project_roi(brief, topic, industry)
                if roi.get("ok"):
                    result.business_case = roi.get("business_case", {})
                    result.features_used.append("roi_calculator")
            except Exception as e:
                if self.verbose:
                    print(f"[Orchestrator] ROI Calculator Error: {e}")
        
        result.analysis_time_ms = int((time.time() - start_time) * 1000)
        
        return result
    
    # ==========================================
    # PHASE 2: CONTENT ENHANCEMENT
    # ==========================================
    
    def enhance_slide_content(
        self,
        slide: Dict[str, Any],
        analysis: OrchestratedAnalysis,
        slide_index: int = 0
    ) -> Dict[str, Any]:
        """
        Erweitert Slide-Content mit allen verfügbaren Features.
        
        Args:
            slide: Der ursprüngliche Slide
            analysis: Die Analyse-Ergebnisse
            slide_index: Position im Deck
        
        Returns:
            Erweiterter Slide
        """
        enhanced = slide.copy()
        
        # 1. Similar Slide Content einfließen lassen
        if analysis.similar_slides and HAS_SEMANTIC:
            slide_type = slide.get("type", "content")
            matching = [s for s in analysis.similar_slides if s.get("type") == slide_type]
            if matching:
                enhanced["_similar_reference"] = matching[0].get("preview", "")[:100]
        
        # 2. Relevante Fakten hinzufügen
        if analysis.relevant_facts:
            # Finde passende Fakten für diesen Slide
            slide_text = f"{slide.get('title', '')} {' '.join(slide.get('bullets', []))}"
            relevant = [f for f in analysis.relevant_facts if any(
                kw.lower() in f.get("content", "").lower() 
                for kw in slide_text.split()[:5]
            )]
            if relevant:
                enhanced["_evidence"] = relevant[:2]
        
        # 3. Voice-Anpassung in Notes
        if analysis.writing_guidelines:
            tone = analysis.writing_guidelines.get("tone", "")
            if tone and "notes" in enhanced:
                enhanced["notes"] = f"[Ton: {tone}] {enhanced.get('notes', '')}"
        
        return enhanced
    
    # ==========================================
    # PHASE 3: QUALITY ASSURANCE
    # ==========================================
    
    def quality_check(
        self,
        slides: List[Dict[str, Any]],
        topic: str = "",
        industry: str = ""
    ) -> OrchestratedQA:
        """
        Führt umfassende Qualitätsprüfung durch.
        
        Args:
            slides: Die generierten Slides
            topic: Thema
            industry: Branche
        
        Returns:
            OrchestratedQA mit allen Prüfungsergebnissen
        """
        result = OrchestratedQA()
        recommendations = []
        
        # 1. Consistency Check
        if HAS_ARGUMENTS:
            try:
                consistency = check_deck_consistency(slides)
                if consistency.get("ok"):
                    result.consistency_score = consistency.get("consistency_score", 100)
                    result.consistency_issues = consistency.get("issues", [])
                    recommendations.extend(consistency.get("recommendations", []))
            except Exception as e:
                pass
        
        # 2. Complexity Scoring
        if HAS_CONTENT_INTEL:
            try:
                complexity = score_deck_complexity(slides)
                if complexity.get("ok"):
                    result.complexity_score = complexity.get("average_complexity", 0.5)
                    result.complex_slides = [
                        s["slide_index"] for s in complexity.get("slides", [])
                        if s.get("overall_score", 0) > 0.7
                    ]
                    recommendations.extend(complexity.get("recommendations", []))
            except Exception as e:
                pass
        
        # 3. Evidence Linking
        if HAS_CONTENT_INTEL:
            try:
                evidence = link_all_claims(slides)
                if evidence.get("ok"):
                    result.evidence_score = evidence.get("evidence_score", 0)
                    result.unlinked_claims = evidence.get("unlinked_claims", [])
                    
                    if result.evidence_score < 0.5:
                        recommendations.append("Mehr als 50% der Behauptungen haben keine Belege")
            except Exception as e:
                pass
        
        # 4. Objection Handling
        if HAS_ARGUMENTS:
            try:
                objections = generate_objections(topic, industry)
                result.objections = [asdict(o) for o in objections[:5]]
            except Exception as e:
                pass
        
        # Overall Quality Score
        scores = [
            result.consistency_score / 100,  # 0-1
            1 - result.complexity_score,  # Weniger komplex = besser
            result.evidence_score
        ]
        result.overall_quality = sum(scores) / len(scores) * 100
        
        result.recommendations = recommendations[:10]
        
        return result
    
    # ==========================================
    # HELPER: PROMPT ENHANCEMENT
    # ==========================================
    
    def get_enhanced_prompt_context(self, analysis: OrchestratedAnalysis) -> str:
        """
        Generiert zusätzlichen Kontext für LLM-Prompts.
        
        Args:
            analysis: Die Analyse-Ergebnisse
        
        Returns:
            String mit zusätzlichem Kontext
        """
        parts = []
        
        # Voice Guidelines
        if analysis.writing_guidelines:
            tone = analysis.writing_guidelines.get("tone", "")
            verbs = analysis.writing_guidelines.get("preferred_verbs", [])[:5]
            if tone:
                parts.append(f"Schreibstil: {tone}")
            if verbs:
                parts.append(f"Bevorzugte Verben: {', '.join(verbs)}")
        
        # Audience
        if analysis.audience_archetype:
            parts.append(f"Zielgruppen-Archetyp: {analysis.audience_archetype}")
        
        # Framework
        if analysis.recommended_framework:
            parts.append(f"Story-Framework: {analysis.recommended_framework}")
        
        # Relevante Fakten
        if analysis.relevant_facts:
            facts = [f.get("content", "")[:80] for f in analysis.relevant_facts[:3]]
            parts.append(f"Relevante Fakten:\n- " + "\n- ".join(facts))
        
        return "\n".join(parts) if parts else ""
    
    def get_slide_type_hints(self, analysis: OrchestratedAnalysis) -> Dict[str, str]:
        """
        Gibt Hints für jeden Slide-Typ basierend auf DNA.
        
        Returns:
            Dictionary mit {slide_type: hint}
        """
        hints = {}
        
        for slide in analysis.recommended_structure:
            slide_type = slide.get("type", "content")
            hints[slide_type] = {
                "recommended_bullets": slide.get("recommended_bullets", 4),
                "typical_titles": slide.get("typical_titles", []),
                "purpose": slide.get("purpose", "")
            }
        
        return hints


# ============================================
# GLOBAL INSTANCE
# ============================================

orchestrator = FeatureOrchestrator(verbose=True)


# ============================================
# API FUNCTIONS
# ============================================

def orchestrate_analysis(
    topic: str,
    brief: str,
    customer_name: str = "",
    industry: str = "",
    audience: str = "",
    deck_size: str = "medium"
) -> Dict[str, Any]:
    """
    Hauptfunktion für orchestrierte Analyse.
    
    Returns:
        Dictionary mit allen Analyse-Ergebnissen
    """
    result = orchestrator.analyze(
        topic=topic,
        brief=brief,
        customer_name=customer_name,
        industry=industry,
        audience=audience,
        deck_size=deck_size
    )
    
    return {
        "ok": True,
        "analysis": asdict(result),
        "features_used": result.features_used,
        "analysis_time_ms": result.analysis_time_ms
    }


def orchestrate_quality_check(
    slides: List[Dict[str, Any]],
    topic: str = "",
    industry: str = ""
) -> Dict[str, Any]:
    """
    Hauptfunktion für orchestrierte Qualitätsprüfung.
    
    Returns:
        Dictionary mit QA-Ergebnissen
    """
    result = orchestrator.quality_check(slides, topic, industry)
    
    return {
        "ok": True,
        "qa": asdict(result),
        "overall_quality": result.overall_quality,
        "recommendations": result.recommendations
    }


def check_status() -> Dict[str, Any]:
    """Gibt den Status des Orchestrators zurück."""
    features = {
        "briefing_analyzer": HAS_BRIEFING_ANALYZER,
        "story_engine": HAS_STORY_ENGINE,
        "persona_engine": HAS_PERSONA_ENGINE,
        "competitive": HAS_COMPETITIVE,
        "roi": HAS_ROI,
        "dna": HAS_DNA,
        "semantic": HAS_SEMANTIC,
        "voice": HAS_VOICE,
        "arguments": HAS_ARGUMENTS,
        "content_intel": HAS_CONTENT_INTEL,
        "knowledge": check_knowledge_available()
    }
    
    available = sum(1 for v in features.values() if v)
    
    return {
        "ok": True,
        "features_available": available,
        "features_total": len(features),
        "features": features
    }
