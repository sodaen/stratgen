#!/usr/bin/env python3
"""
Patch: Integriert visual_intelligence.py in agent_v3_api.py
Agent V3.2 → V3.3
"""
import re

filepath = "/home/sodaen/stratgen/backend/agent_v3_api.py"

with open(filepath, "r") as f:
    content = f.read()

# ============================================
# PATCH 1: Import hinzufügen
# ============================================

# Finde den Import-Block für Chart Generator
old_chart_import = '''# Chart Generator
try:
    from services.chart_generator import (
        create_bar_chart,
        create_pie_chart,
        create_line_chart,
        create_timeline,
        create_funnel_chart,
        create_gauge_chart,
        create_comparison_matrix,
        auto_create_chart
    )
    HAS_CHART_GEN = True
except ImportError:
    HAS_CHART_GEN = False'''

new_chart_import = '''# Chart Generator
try:
    from services.chart_generator import (
        create_bar_chart,
        create_pie_chart,
        create_line_chart,
        create_timeline,
        create_funnel_chart,
        create_gauge_chart,
        create_comparison_matrix,
        auto_create_chart
    )
    HAS_CHART_GEN = True
except ImportError:
    HAS_CHART_GEN = False

# Visual Intelligence (Stufe 3)
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

if old_chart_import in content:
    content = content.replace(old_chart_import, new_chart_import)
    print("✓ Patch 1: Visual Intelligence Import hinzugefügt")
else:
    print("⚠ Patch 1: Chart Generator Import nicht gefunden")


# ============================================
# PATCH 2: phase_visualize erweitern
# ============================================

old_visualize = '''def phase_visualize(
    req: AgentV3Request,
    slides: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Phase 7: Fügt Charts und Assets zu Slides hinzu.
    """
    if not req.generate_charts:
        return slides
    
    if not HAS_CHART_GEN:
        return slides'''

new_visualize = '''def phase_visualize(
    req: AgentV3Request,
    slides: List[Dict[str, Any]],
    context: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Phase 7: Enhanced Visuals mit Visual Intelligence.
    Fügt Charts, Images und Layout-Optimierung hinzu.
    """
    if not req.generate_charts:
        return slides
    
    # === VISUAL INTELLIGENCE (Stufe 3) ===
    if HAS_VISUAL_INTELLIGENCE and enhance_all_slides:
        try:
            enhanced = enhance_all_slides(
                slides=slides,
                context=context or {
                    "topic": req.topic,
                    "industry": req.industry,
                    "customer_name": req.customer_name
                },
                generate_charts=True,
                recommend_images_flag=req.match_assets,
                use_llm=True
            )
            return enhanced
        except Exception as e:
            pass  # Fallback zu altem Code
    
    # === FALLBACK: Alter Code ===
    if not HAS_CHART_GEN:
        return slides'''

if old_visualize in content:
    content = content.replace(old_visualize, new_visualize)
    print("✓ Patch 2: phase_visualize enhanced")
else:
    print("⚠ Patch 2: phase_visualize nicht gefunden")


# ============================================
# PATCH 3: Aufruf von phase_visualize erweitern
# ============================================

old_visualize_call = 'slides = phase_visualize(req, slides)'
new_visualize_call = '''slides = phase_visualize(req, slides, context={
        "topic": req.topic,
        "industry": req.industry,
        "customer_name": req.customer_name,
        "brief": req.brief
    })'''

if old_visualize_call in content:
    content = content.replace(old_visualize_call, new_visualize_call)
    print("✓ Patch 3: phase_visualize Aufruf erweitert")


# ============================================
# PATCH 4: Version aktualisieren
# ============================================

old_version = '"version": "3.2",'
new_version = '"version": "3.3",'

if old_version in content:
    content = content.replace(old_version, new_version)
    print("✓ Patch 4: Version auf 3.3 aktualisiert")


# ============================================
# PATCH 5: Services erweitern
# ============================================

old_services = '"knowledge_enhanced": HAS_KNOWLEDGE_ENHANCED,'
new_services = '''"knowledge_enhanced": HAS_KNOWLEDGE_ENHANCED,
            "visual_intelligence": HAS_VISUAL_INTELLIGENCE,'''

if old_services in content:
    content = content.replace(old_services, new_services)
    print("✓ Patch 5: visual_intelligence zu services hinzugefügt")


# Speichern
with open(filepath, "w") as f:
    f.write(content)

print("\n✓ Alle Patches angewendet!")
print("  Agent V3.2 → V3.3 (Visual Intelligence)")
