#!/usr/bin/env python3
"""
Patch: Integriert multimodal_export.py in agent_v3_api.py
Agent V3.4 → V3.5
"""
import re

filepath = "/home/sodaen/stratgen/backend/agent_v3_api.py"

with open(filepath, "r") as f:
    content = f.read()

# ============================================
# PATCH 1: Import hinzufügen
# ============================================

old_learning_import = '''# Learning & Adaptation (Stufe 4)
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

new_learning_import = '''# Learning & Adaptation (Stufe 4)
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
    get_merged_style = None

# Multi-Modal Export (Stufe 5)
try:
    from services.multimodal_export import (
        export_to_html,
        export_to_pdf,
        export_to_markdown,
        export_to_json,
        export_presentation,
        get_available_formats,
        check_status as export_status
    )
    HAS_MULTIMODAL_EXPORT = True
except ImportError:
    HAS_MULTIMODAL_EXPORT = False
    export_to_html = None
    export_to_pdf = None'''

if old_learning_import in content:
    content = content.replace(old_learning_import, new_learning_import)
    print("✓ Patch 1: Multi-Modal Export Import hinzugefügt")
else:
    print("⚠ Patch 1: Learning Import nicht gefunden")


# ============================================
# PATCH 2: Version aktualisieren
# ============================================

old_version = '"version": "3.4",'
new_version = '"version": "3.5",'

if old_version in content:
    content = content.replace(old_version, new_version)
    print("✓ Patch 2: Version auf 3.5 aktualisiert")


# ============================================
# PATCH 3: Services erweitern
# ============================================

old_services = '"learning_adaptation": HAS_LEARNING,'
new_services = '''"learning_adaptation": HAS_LEARNING,
            "multimodal_export": HAS_MULTIMODAL_EXPORT,'''

if old_services in content:
    content = content.replace(old_services, new_services)
    print("✓ Patch 3: multimodal_export zu services hinzugefügt")


# ============================================
# PATCH 4: Request um export_formats erweitern
# ============================================

old_request_export = 'export_pptx: bool = True'
new_request_export = '''export_pptx: bool = True
    export_html: bool = False      # HTML/Reveal.js Export
    export_pdf: bool = False       # PDF Export
    export_markdown: bool = False  # Markdown Export
    export_json: bool = False      # JSON Export'''

if old_request_export in content:
    content = content.replace(old_request_export, new_request_export)
    print("✓ Patch 4: Request um export_formats erweitert")


# ============================================
# PATCH 5: Response um export URLs erweitern
# ============================================

old_response_urls = '''pptx_url: Optional[str] = None
    pdf_url: Optional[str] = None'''

new_response_urls = '''pptx_url: Optional[str] = None
    pdf_url: Optional[str] = None
    html_url: Optional[str] = None      # Stufe 5
    markdown_url: Optional[str] = None  # Stufe 5
    json_url: Optional[str] = None      # Stufe 5
    exports: Optional[Dict[str, Any]] = None  # Alle Exports'''

if old_response_urls in content:
    content = content.replace(old_response_urls, new_response_urls)
    print("✓ Patch 5: Response um export URLs erweitert")


# ============================================
# PATCH 6: Multi-Format Export nach Render-Phase
# ============================================

# Suche nach dem PPTX-Export und füge Multi-Format hinzu
old_pptx_export = '''# PPTX Export
    pptx_url = None
    if req.export_pptx:'''

new_pptx_export = '''# === MULTI-FORMAT EXPORT (Stufe 5) ===
    exports_result = {}
    html_url = None
    markdown_url = None
    json_url = None
    
    if HAS_MULTIMODAL_EXPORT and export_presentation:
        # Sammle gewünschte Formate
        export_formats = []
        if req.export_html:
            export_formats.append("html")
        if req.export_pdf:
            export_formats.append("pdf")
        if req.export_markdown:
            export_formats.append("markdown")
        if req.export_json:
            export_formats.append("json")
        
        if export_formats:
            try:
                multi_export = export_presentation(
                    slides=slides,
                    title=req.topic,
                    formats=export_formats,
                    options={
                        "theme": "white",
                        "include_notes": True
                    }
                )
                exports_result = multi_export.get("exports", {})
                
                if exports_result.get("html", {}).get("ok"):
                    html_url = exports_result["html"].get("url")
                if exports_result.get("markdown", {}).get("ok"):
                    markdown_url = exports_result["markdown"].get("url")
                if exports_result.get("json", {}).get("ok"):
                    json_url = exports_result["json"].get("url")
            except Exception:
                pass
    
    # PPTX Export
    pptx_url = None
    if req.export_pptx:'''

if old_pptx_export in content:
    content = content.replace(old_pptx_export, new_pptx_export)
    print("✓ Patch 6: Multi-Format Export hinzugefügt")
else:
    print("⚠ Patch 6: PPTX Export nicht gefunden")


# ============================================
# PATCH 7: URLs in Response einfügen
# ============================================

old_response_return = '''pptx_url=pptx_url,
        pdf_url=pdf_url,'''

new_response_return = '''pptx_url=pptx_url,
        pdf_url=pdf_url,
        html_url=html_url,
        markdown_url=markdown_url,
        json_url=json_url,
        exports=exports_result if exports_result else None,'''

if old_response_return in content:
    content = content.replace(old_response_return, new_response_return)
    print("✓ Patch 7: Export URLs in Response eingefügt")


# Speichern
with open(filepath, "w") as f:
    f.write(content)

print("\n✓ Alle Patches angewendet!")
print("  Agent V3.4 → V3.5 (Multi-Modal Export)")
