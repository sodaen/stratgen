#!/usr/bin/env python3
"""
Patch: Integriert knowledge_enhanced.py in agent_v3_api.py
"""
import re

filepath = "/home/sodaen/stratgen/backend/agent_v3_api.py"

with open(filepath, "r") as f:
    content = f.read()

# ============================================
# PATCH 1: Import hinzufügen
# ============================================

old_knowledge_import = '''# Knowledge/RAG
try:
    from services.knowledge import search as knowledge_search, scan_dir as scan_knowledge
    HAS_KNOWLEDGE = True
except ImportError:
    knowledge_search = None
    HAS_KNOWLEDGE = False'''

new_knowledge_import = '''# Knowledge/RAG (Basic)
try:
    from services.knowledge import search as knowledge_search, scan_dir as scan_knowledge
    HAS_KNOWLEDGE = True
except ImportError:
    knowledge_search = None
    HAS_KNOWLEDGE = False

# Knowledge Enhanced (Stufe 2)
try:
    from services.knowledge_enhanced import (
        multi_source_search,
        extract_facts_from_results,
        build_research_context,
        research_for_slide,
        CitationManager,
        check_status as knowledge_status
    )
    HAS_KNOWLEDGE_ENHANCED = True
except ImportError:
    HAS_KNOWLEDGE_ENHANCED = False
    multi_source_search = None
    CitationManager = None'''

if old_knowledge_import in content:
    content = content.replace(old_knowledge_import, new_knowledge_import)
    print("✓ Patch 1: Knowledge Enhanced Import hinzugefügt")
else:
    print("⚠ Patch 1: Knowledge Import nicht gefunden")


# ============================================
# PATCH 2: phase_research erweitern
# ============================================

old_phase_research = '''def phase_research(req: AgentV3Request, plan: AgentPlan) -> Dict[str, Any]:
    """
    Phase 2: Sucht relevantes Wissen aus Knowledge Base.
    Nutzt die geplanten Research-Queries.
    """
    result = {
        "sources": [],
        "facts": [],
        "citations": [],
        "template_insights": [],
    }
    
    if not req.use_rag:
        return result
    
    # Knowledge Base durchsuchen
    if HAS_KNOWLEDGE and knowledge_search:
        all_results = []
        for query in plan.research_queries[:5]:
            try:
                search_result = knowledge_search(query, limit=3, semantic=1)
                if search_result.get("ok"):
                    all_results.extend(search_result.get("results", []))
            except Exception:
                pass
        
        # Deduplizieren
        seen_paths = set()
        for item in all_results:
            path = item.get("path", "")
            if path not in seen_paths:
                seen_paths.add(path)
                result["sources"].append({
                    "path": path,
                    "title": item.get("title") or Path(path).stem,
                    "snippet": item.get("snippet", "")[:300]
                })
                if item.get("snippet"):
                    result["facts"].append(item["snippet"][:400])
    
    # Template-Insights (Quick Win 2)
    if req.learn_from_templates and HAS_TEMPLATE_LEARNER:
        try:
            # Templates scannen falls noch nicht geschehen
            scan_templates(RAW_DIR)
            
            # Statistiken holen
            stats = get_template_stats()
            if stats.get("ok") and stats.get("patterns"):
                patterns = stats["patterns"]
                result["template_insights"] = [
                    f"Durchschnittlich {patterns.get('avg_bullets_per_slide', 4)} Bullets pro Slide",
                    f"Durchschnittlich {patterns.get('avg_slides_per_deck', 15)} Slides pro Deck",
                ]
        except Exception:
            pass
    
    return result'''

new_phase_research = '''def phase_research(req: AgentV3Request, plan: AgentPlan) -> Dict[str, Any]:
    """
    Phase 2: Enhanced Research mit Multi-Source RAG und Fact Extraction.
    Nutzt knowledge_enhanced.py für bessere Ergebnisse.
    """
    result = {
        "sources": [],
        "facts": [],
        "citations": [],
        "template_insights": [],
        "citation_manager": None,
    }
    
    if not req.use_rag:
        return result
    
    context = {
        "topic": req.topic,
        "industry": req.industry,
        "customer_name": req.customer_name,
        "brief": req.brief
    }
    
    # === ENHANCED RESEARCH (Stufe 2) ===
    if HAS_KNOWLEDGE_ENHANCED and multi_source_search:
        try:
            # Citation Manager erstellen
            result["citation_manager"] = CitationManager() if CitationManager else None
            
            # Multi-Source-Suche
            for query in plan.research_queries[:5]:
                research = multi_source_search(
                    query=query,
                    context=context,
                    sources=["knowledge", "templates", "uploads"],
                    k=5
                )
                
                # Ergebnisse sammeln
                for res in research.results:
                    if res.path not in [s.get("path") for s in result["sources"]]:
                        result["sources"].append({
                            "path": res.path,
                            "title": res.title,
                            "snippet": res.snippet[:400],
                            "score": res.score,
                            "source_type": res.source_type
                        })
                        
                        # Citation hinzufügen
                        if result["citation_manager"]:
                            result["citation_manager"].add_source(
                                res.path, res.title, res.snippet
                            )
                
                # Fakten extrahieren
                if research.results:
                    extracted_facts = extract_facts_from_results(research.results)
                    for fact in extracted_facts:
                        if fact.text not in result["facts"]:
                            result["facts"].append(fact.text)
            
        except Exception as e:
            # Fallback zu Basic Search
            pass
    
    # === FALLBACK: Basic Knowledge Search ===
    if not result["sources"] and HAS_KNOWLEDGE and knowledge_search:
        all_results = []
        for query in plan.research_queries[:5]:
            try:
                search_result = knowledge_search(query, limit=3, semantic=1)
                if search_result.get("ok"):
                    all_results.extend(search_result.get("results", []))
            except Exception:
                pass
        
        # Deduplizieren
        seen_paths = set()
        for item in all_results:
            path = item.get("path", "")
            if path not in seen_paths:
                seen_paths.add(path)
                result["sources"].append({
                    "path": path,
                    "title": item.get("title") or Path(path).stem,
                    "snippet": item.get("snippet", "")[:300]
                })
                if item.get("snippet"):
                    result["facts"].append(item["snippet"][:400])
    
    # === Template-Insights (Quick Win 2) ===
    if req.learn_from_templates and HAS_TEMPLATE_LEARNER:
        try:
            scan_templates(RAW_DIR)
            stats = get_template_stats()
            if stats.get("ok") and stats.get("patterns"):
                patterns = stats["patterns"]
                result["template_insights"] = [
                    f"Durchschnittlich {patterns.get('avg_bullets_per_slide', 4)} Bullets pro Slide",
                    f"Durchschnittlich {patterns.get('avg_slides_per_deck', 15)} Slides pro Deck",
                ]
        except Exception:
            pass
    
    return result'''

if old_phase_research in content:
    content = content.replace(old_phase_research, new_phase_research)
    print("✓ Patch 2: phase_research enhanced")
else:
    print("⚠ Patch 2: phase_research nicht gefunden")


# ============================================
# PATCH 3: Status-Endpoint erweitern
# ============================================

old_status = '''@router.get("/v3/status")
def agent_v3_status():
    """Gibt den Status aller Services zurück."""
    return {
        "version": "3.1",'''

new_status = '''@router.get("/v3/status")
def agent_v3_status():
    """Gibt den Status aller Services zurück."""
    
    # Knowledge Enhanced Status
    ke_status = {}
    if HAS_KNOWLEDGE_ENHANCED:
        try:
            ke_status = knowledge_status()
        except Exception:
            ke_status = {"ok": False}
    
    return {
        "version": "3.2",'''

if old_status in content:
    content = content.replace(old_status, new_status)
    print("✓ Patch 3: Version auf 3.2 aktualisiert")

# Füge knowledge_enhanced zum services dict hinzu
old_services = '"knowledge": HAS_KNOWLEDGE,'
new_services = '"knowledge": HAS_KNOWLEDGE,\n            "knowledge_enhanced": HAS_KNOWLEDGE_ENHANCED,'

if old_services in content:
    content = content.replace(old_services, new_services)
    print("✓ Patch 3b: knowledge_enhanced zu services hinzugefügt")


# ============================================
# PATCH 4: Citations in Response hinzufügen
# ============================================

# Füge citations_data in phases hinzu
old_research_phase = '''phases["research"] = {
        "duration_ms": int((time.time() - t2) * 1000),
        "sources_found": len(research.get("sources", [])),
        "facts_gathered": len(research.get("facts", []))
    }'''

new_research_phase = '''phases["research"] = {
        "duration_ms": int((time.time() - t2) * 1000),
        "sources_found": len(research.get("sources", [])),
        "facts_gathered": len(research.get("facts", [])),
        "enhanced": HAS_KNOWLEDGE_ENHANCED
    }'''

if old_research_phase in content:
    content = content.replace(old_research_phase, new_research_phase)
    print("✓ Patch 4: Research phase enhanced flag hinzugefügt")


# Speichern
with open(filepath, "w") as f:
    f.write(content)

print("\n✓ Alle Patches angewendet!")
print("  Nächster Schritt: knowledge_enhanced.py nach services/ kopieren")
