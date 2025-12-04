"""
Template Learner Service für Stratgen.
Analysiert Master-Präsentationen in /raw mit Vision-Modell
und extrahiert Design-Patterns für die Generierung.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("STRATGEN_DATA", "/home/sodaen/stratgen/data"))
RAW_DIR = DATA_ROOT / "raw"
TEMPLATE_CACHE = DATA_ROOT / "knowledge" / "templates_learned.json"


class TemplateLearner:
    """Lernt Design-Patterns aus Master-Präsentationen."""
    
    def __init__(self):
        self._vision = None
        self._cache = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Lädt den Template-Cache."""
        if TEMPLATE_CACHE.exists():
            try:
                with open(TEMPLATE_CACHE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"templates": {}, "patterns": {}, "last_scan": None}
    
    def _save_cache(self):
        """Speichert den Template-Cache."""
        TEMPLATE_CACHE.parent.mkdir(parents=True, exist_ok=True)
        with open(TEMPLATE_CACHE, 'w') as f:
            json.dump(self._cache, f, indent=2, default=str)
    
    def _get_vision(self):
        """Lazy-load Vision-Analyzer."""
        if self._vision is None:
            try:
                from services.vision_analyzer import analyze_slide, is_available
                if is_available():
                    self._vision = analyze_slide
            except Exception as e:
                logger.warning(f"Vision not available: {e}")
        return self._vision
    
    def _file_hash(self, path: Path) -> str:
        """Berechnet Hash einer Datei."""
        return hashlib.md5(f"{path}:{path.stat().st_mtime}".encode()).hexdigest()[:12]
    
    def analyze_presentation(self, pptx_path: str, max_slides: int = 5) -> Dict[str, Any]:
        """
        Analysiert eine einzelne Präsentation.
        """
        from services.vision_analyzer import extract_pptx_slides_as_images
        
        path = Path(pptx_path)
        if not path.exists():
            return {"ok": False, "error": "File not found"}
        
        file_hash = self._file_hash(path)
        
        # Check Cache
        if file_hash in self._cache["templates"]:
            logger.info(f"Using cached analysis for {path.name}")
            return {"ok": True, "cached": True, **self._cache["templates"][file_hash]}
        
        logger.info(f"Analyzing presentation: {path.name}")
        
        # Extrahiere Slides als Bilder
        extraction = extract_pptx_slides_as_images(str(path))
        if not extraction.get("ok"):
            return extraction
        
        # Analysiere mit Vision
        vision = self._get_vision()
        if not vision:
            return {"ok": False, "error": "Vision model not available"}
        
        slide_analyses = []
        for img_path in extraction.get("images", [])[:max_slides]:
            try:
                analysis = vision(img_path)
                if analysis.get("ok"):
                    slide_analyses.append({
                        "slide": Path(img_path).name,
                        "analysis": analysis.get("analysis", ""),
                        "structured": analysis.get("structured")
                    })
            except Exception as e:
                logger.warning(f"Failed to analyze slide: {e}")
        
        # Extrahiere Patterns
        patterns = self._extract_patterns(slide_analyses)
        
        result = {
            "file": str(path),
            "name": path.stem,
            "slides_total": extraction.get("slides", 0),
            "slides_analyzed": len(slide_analyses),
            "analyses": slide_analyses,
            "patterns": patterns,
            "analyzed_at": datetime.now().isoformat()
        }
        
        # Cache speichern
        self._cache["templates"][file_hash] = result
        self._save_cache()
        
        return {"ok": True, **result}
    
    def _extract_patterns(self, analyses: List[Dict]) -> Dict[str, Any]:
        """Extrahiert Design-Patterns aus den Analysen."""
        patterns = {
            "colors": [],
            "layouts": [],
            "fonts": [],
            "styles": []
        }
        
        for analysis in analyses:
            text = analysis.get("analysis", "").lower()
            structured = analysis.get("structured", {})
            
            # Versuche strukturierte Daten zu nutzen
            if structured:
                if "colors" in structured:
                    patterns["colors"].extend(structured["colors"] if isinstance(structured["colors"], list) else [structured["colors"]])
                if "layout" in structured:
                    patterns["layouts"].append(structured["layout"])
            
            # Fallback: Textanalyse
            if "corporate" in text:
                patterns["styles"].append("corporate")
            if "minimal" in text:
                patterns["styles"].append("minimal")
            if "bold" in text or "modern" in text:
                patterns["styles"].append("modern")
            if "two-column" in text:
                patterns["layouts"].append("two-column")
            if "title slide" in text:
                patterns["layouts"].append("title")
        
        # Deduplizieren
        for key in patterns:
            patterns[key] = list(set(patterns[key]))[:5]
        
        return patterns
    
    def scan_raw_presentations(self, limit: int = 10) -> Dict[str, Any]:
        """
        Scannt alle Präsentationen in /raw und analysiert sie.
        """
        if not RAW_DIR.exists():
            return {"ok": False, "error": f"Raw directory not found: {RAW_DIR}"}
        
        pptx_files = list(RAW_DIR.rglob("*.pptx"))[:limit]
        logger.info(f"Found {len(pptx_files)} PPTX files in {RAW_DIR}")
        
        results = []
        success = 0
        
        for pptx in pptx_files:
            result = self.analyze_presentation(str(pptx))
            results.append({
                "file": pptx.name,
                "ok": result.get("ok", False),
                "cached": result.get("cached", False),
                "patterns": result.get("patterns", {})
            })
            if result.get("ok"):
                success += 1
        
        # Update aggregierte Patterns
        self._aggregate_patterns()
        self._cache["last_scan"] = datetime.now().isoformat()
        self._save_cache()
        
        return {
            "ok": True,
            "scanned": len(pptx_files),
            "successful": success,
            "results": results,
            "aggregated_patterns": self._cache.get("patterns", {})
        }
    
    def _aggregate_patterns(self):
        """Aggregiert Patterns aus allen analysierten Templates."""
        all_patterns = {
            "colors": [],
            "layouts": [],
            "fonts": [],
            "styles": []
        }
        
        for template in self._cache.get("templates", {}).values():
            patterns = template.get("patterns", {})
            for key in all_patterns:
                all_patterns[key].extend(patterns.get(key, []))
        
        # Häufigkeiten zählen und Top-Items behalten
        for key in all_patterns:
            from collections import Counter
            counts = Counter(all_patterns[key])
            all_patterns[key] = [item for item, _ in counts.most_common(10)]
        
        self._cache["patterns"] = all_patterns
    
    def get_design_guidance(self, slide_type: str = None) -> Dict[str, Any]:
        """
        Gibt Design-Empfehlungen basierend auf gelernten Patterns zurück.
        """
        patterns = self._cache.get("patterns", {})
        
        guidance = {
            "colors": patterns.get("colors", ["#1E40AF", "#3B82F6", "#60A5FA"]),
            "layouts": patterns.get("layouts", ["title", "content", "two-column"]),
            "styles": patterns.get("styles", ["corporate", "modern"]),
            "recommendations": []
        }
        
        # Slide-spezifische Empfehlungen
        if slide_type:
            if slide_type in ["title", "executive_summary"]:
                guidance["recommendations"].append("Use large, bold title with minimal text")
            elif slide_type in ["data", "roi"]:
                guidance["recommendations"].append("Include charts or data visualizations")
            elif slide_type == "comparison":
                guidance["recommendations"].append("Use two-column or grid layout")
        
        return guidance
    
    def get_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über gelernte Templates zurück."""
        return {
            "templates_learned": len(self._cache.get("templates", {})),
            "patterns": self._cache.get("patterns", {}),
            "last_scan": self._cache.get("last_scan"),
            "cache_file": str(TEMPLATE_CACHE)
        }


# Singleton
_learner = None

def get_template_learner() -> TemplateLearner:
    global _learner
    if _learner is None:
        _learner = TemplateLearner()
    return _learner

# Convenience-Funktionen
def analyze_presentation(path: str) -> Dict:
    return get_template_learner().analyze_presentation(path)

def scan_raw_presentations(limit: int = 10) -> Dict:
    return get_template_learner().scan_raw_presentations(limit)

def get_design_guidance(slide_type: str = None) -> Dict:
    return get_template_learner().get_design_guidance(slide_type)

def get_stats() -> Dict:
    return get_template_learner().get_stats()
