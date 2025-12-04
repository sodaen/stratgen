"""
Vision Analyzer Service für Stratgen.
Analysiert Präsentationen und Bilder mit dem moondream Vision-Modell.
"""

import os
import base64
import json
import httpx
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
VISION_MODEL = os.getenv("VISION_MODEL", "moondream")


def _encode_image(image_path: str) -> str:
    """Kodiert ein Bild als Base64."""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_image(image_path: str, prompt: str = None) -> Dict[str, Any]:
    """
    Analysiert ein Bild mit dem Vision-Modell.
    
    Args:
        image_path: Pfad zum Bild
        prompt: Optionaler Custom-Prompt
    
    Returns:
        Dict mit Analyse-Ergebnis
    """
    if not os.path.exists(image_path):
        return {"ok": False, "error": f"Bild nicht gefunden: {image_path}"}
    
    default_prompt = """Analyze this image and describe:
1. Layout type (title slide, content slide, two-column, etc.)
2. Color scheme (primary colors used)
3. Visual elements (charts, icons, images, shapes)
4. Text structure (headers, bullet points, paragraphs)
5. Overall style (corporate, creative, minimal, etc.)

Be concise and structured."""

    prompt = prompt or default_prompt
    
    try:
        image_b64 = _encode_image(image_path)
        
        response = httpx.post(
            f"{OLLAMA_HOST}/api/generate",
            json={
                "model": VISION_MODEL,
                "prompt": prompt,
                "images": [image_b64],
                "stream": False
            },
            timeout=60.0
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "ok": True,
                "analysis": data.get("response", ""),
                "model": VISION_MODEL,
                "image": image_path
            }
        else:
            return {"ok": False, "error": f"API Error: {response.status_code}"}
            
    except Exception as e:
        logger.error(f"Vision analysis failed: {e}")
        return {"ok": False, "error": str(e)}


def analyze_slide(slide_image_path: str) -> Dict[str, Any]:
    """
    Analysiert einen Präsentations-Slide speziell für Template-Extraktion.
    """
    prompt = """Analyze this presentation slide and extract:

LAYOUT:
- Type: (title, content, two-column, comparison, timeline, etc.)
- Grid: (how content is arranged)

DESIGN:
- Colors: (list main colors as hex if possible)
- Fonts: (serif/sans-serif, sizes)
- Style: (corporate, creative, minimal, bold)

ELEMENTS:
- Headers: (position, style)
- Body text: (bullet style, alignment)
- Visuals: (charts, icons, images, shapes)
- Decorative: (lines, backgrounds, accents)

OUTPUT as JSON."""

    result = analyze_image(slide_image_path, prompt)
    
    if result.get("ok"):
        # Versuche JSON zu extrahieren
        analysis = result.get("analysis", "")
        try:
            # Suche nach JSON im Response
            json_start = analysis.find("{")
            json_end = analysis.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(analysis[json_start:json_end])
                result["structured"] = parsed
        except:
            pass
    
    return result


def extract_pptx_slides_as_images(pptx_path: str, output_dir: str = None) -> Dict[str, Any]:
    """
    Extrahiert alle Slides einer PPTX als Bilder.
    Benötigt LibreOffice oder pdf2image.
    """
    from pathlib import Path
    import subprocess
    import tempfile
    
    pptx_path = Path(pptx_path)
    if not pptx_path.exists():
        return {"ok": False, "error": "PPTX nicht gefunden"}
    
    output_dir = output_dir or tempfile.mkdtemp(prefix="slides_")
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        # Methode 1: LibreOffice (falls verfügbar)
        result = subprocess.run([
            "libreoffice", "--headless", "--convert-to", "pdf",
            "--outdir", str(output_dir), str(pptx_path)
        ], capture_output=True, timeout=120)
        
        pdf_path = output_dir / f"{pptx_path.stem}.pdf"
        
        if pdf_path.exists():
            # PDF zu Bildern konvertieren
            from pdf2image import convert_from_path
            images = convert_from_path(str(pdf_path), dpi=150)
            
            image_paths = []
            for i, img in enumerate(images):
                img_path = output_dir / f"slide_{i+1:03d}.png"
                img.save(str(img_path), "PNG")
                image_paths.append(str(img_path))
            
            return {
                "ok": True,
                "slides": len(image_paths),
                "images": image_paths,
                "output_dir": str(output_dir)
            }
        else:
            return {"ok": False, "error": "PDF-Konvertierung fehlgeschlagen"}
            
    except FileNotFoundError:
        return {"ok": False, "error": "LibreOffice nicht installiert"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def analyze_presentation_template(pptx_path: str) -> Dict[str, Any]:
    """
    Analysiert eine komplette Präsentation und extrahiert Template-Informationen.
    """
    # Erst Slides als Bilder extrahieren
    extraction = extract_pptx_slides_as_images(pptx_path)
    
    if not extraction.get("ok"):
        return extraction
    
    analyses = []
    for img_path in extraction.get("images", [])[:5]:  # Max 5 Slides analysieren
        analysis = analyze_slide(img_path)
        if analysis.get("ok"):
            analyses.append({
                "image": img_path,
                "analysis": analysis.get("analysis"),
                "structured": analysis.get("structured")
            })
    
    # Zusammenfassung erstellen
    return {
        "ok": True,
        "pptx": pptx_path,
        "total_slides": extraction.get("slides", 0),
        "analyzed_slides": len(analyses),
        "analyses": analyses,
        "output_dir": extraction.get("output_dir")
    }


def check_vision_available() -> Dict[str, Any]:
    """Prüft ob das Vision-Modell verfügbar ist."""
    try:
        response = httpx.get(f"{OLLAMA_HOST}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            vision_models = [m for m in models if "moondream" in m.get("name", "").lower() 
                           or "llava" in m.get("name", "").lower()]
            return {
                "ok": len(vision_models) > 0,
                "models": [m.get("name") for m in vision_models],
                "default": VISION_MODEL
            }
        return {"ok": False, "error": "Ollama nicht erreichbar"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# Convenience-Funktionen
def is_available() -> bool:
    return check_vision_available().get("ok", False)
