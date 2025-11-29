# -*- coding: utf-8 -*-
"""
services/visual_intelligence.py
===============================
Stufe 3: Visual Intelligence

Features:
1. Smart Chart Selection - LLM wählt passenden Chart-Typ
2. Auto-Data Extraction - Extrahiert Daten aus Content für Charts
3. Image Recommendations - Schlägt passende Bilder vor
4. Layout Optimization - Wählt optimales Slide-Layout
5. Visual Consistency - Einheitlicher visueller Stil

Author: StratGen Agent V3.2
"""
from __future__ import annotations
import os
import re
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

# ============================================
# CONFIGURATION
# ============================================

CHARTS_DIR = os.getenv("STRATGEN_CHARTS_DIR", "data/charts")
UPLOADS_DIR = os.getenv("STRATGEN_UPLOADS_DIR", "data/uploads")
ASSETS_DIR = os.getenv("STRATGEN_ASSETS_DIR", "data/assets")

# ============================================
# ENUMS & DATA CLASSES
# ============================================

class ChartType(str, Enum):
    BAR = "bar"
    BAR_HORIZONTAL = "bar_horizontal"
    LINE = "line"
    PIE = "pie"
    DONUT = "donut"
    TIMELINE = "timeline"
    FUNNEL = "funnel"
    GAUGE = "gauge"
    MATRIX = "matrix"
    PROCESS = "process"
    NONE = "none"


class LayoutType(str, Enum):
    TITLE = "title"
    TITLE_CONTENT = "title_content"
    TWO_COLUMN = "two_column"
    TITLE_CHART = "title_chart"
    TITLE_IMAGE = "title_image"
    CHART_ONLY = "chart_only"
    COMPARISON = "comparison"
    FULL_IMAGE = "full_image"


@dataclass
class ChartSpec:
    """Spezifikation für ein Chart."""
    chart_type: ChartType
    title: str = ""
    labels: List[str] = field(default_factory=list)
    values: List[float] = field(default_factory=list)
    series: List[Dict[str, Any]] = field(default_factory=list)  # Für Multi-Series
    colors: List[str] = field(default_factory=list)
    rationale: str = ""
    confidence: float = 0.7


@dataclass 
class ImageRecommendation:
    """Empfehlung für ein Bild."""
    path: str
    title: str
    relevance_score: float
    keywords: List[str] = field(default_factory=list)
    source: str = "local"  # local, stock, generated


@dataclass
class LayoutRecommendation:
    """Empfehlung für ein Slide-Layout."""
    layout_type: LayoutType
    rationale: str
    chart_position: str = "right"  # left, right, bottom, center
    image_position: str = "right"
    text_width: float = 0.6  # Anteil der Slide-Breite für Text


# ============================================
# IMPORTS - Services
# ============================================

# Chart Generator
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

# Asset Tagger
try:
    from services.asset_tagger import (
        get_asset_suggestions,
        search_assets,
        get_asset_by_id
    )
    HAS_ASSET_TAGGER = True
except ImportError:
    HAS_ASSET_TAGGER = False

# LLM
try:
    from services.llm import generate as llm_generate, is_enabled as llm_enabled
    HAS_LLM = True
except ImportError:
    llm_generate = None
    HAS_LLM = False


# ============================================
# CHART TYPE DETECTION
# ============================================

# Slide-Typ zu Chart-Typ Mapping (Regel-basiert)
SLIDE_CHART_MAPPING = {
    "roi": [ChartType.BAR, ChartType.LINE],
    "roadmap": [ChartType.TIMELINE],
    "timeline": [ChartType.TIMELINE],
    "kpis": [ChartType.GAUGE, ChartType.BAR],
    "metrics": [ChartType.BAR, ChartType.GAUGE],
    "funnel": [ChartType.FUNNEL],
    "pipeline": [ChartType.FUNNEL],
    "competitive": [ChartType.MATRIX, ChartType.BAR_HORIZONTAL],
    "comparison": [ChartType.MATRIX, ChartType.BAR],
    "market": [ChartType.PIE, ChartType.BAR],
    "distribution": [ChartType.PIE, ChartType.DONUT],
    "process": [ChartType.PROCESS, ChartType.TIMELINE],
    "growth": [ChartType.LINE, ChartType.BAR],
    "trend": [ChartType.LINE],
    "budget": [ChartType.PIE, ChartType.BAR],
    "cost": [ChartType.BAR, ChartType.PIE],
}

# Keywords für Chart-Typ Detection
CHART_KEYWORDS = {
    ChartType.BAR: ["vergleich", "compare", "ranking", "top", "versus", "vs", "unterschied"],
    ChartType.LINE: ["trend", "entwicklung", "growth", "verlauf", "zeit", "time", "year", "month"],
    ChartType.PIE: ["anteil", "share", "verteilung", "distribution", "prozent", "%", "markt"],
    ChartType.TIMELINE: ["roadmap", "timeline", "phasen", "phases", "meilenstein", "milestone", "plan"],
    ChartType.FUNNEL: ["funnel", "pipeline", "conversion", "trichter", "stages", "stufen"],
    ChartType.GAUGE: ["kpi", "score", "index", "rate", "quote", "ziel", "target"],
    ChartType.MATRIX: ["matrix", "vergleich", "bewertung", "kriterien", "scoring"],
}


def detect_chart_type_rule_based(
    slide_type: str,
    title: str,
    bullets: List[str]
) -> Tuple[ChartType, float]:
    """
    Erkennt den passenden Chart-Typ regel-basiert.
    
    Returns:
        Tuple von (ChartType, Confidence)
    """
    # 1. Check Slide-Typ Mapping
    slide_type_lower = slide_type.lower()
    if slide_type_lower in SLIDE_CHART_MAPPING:
        return SLIDE_CHART_MAPPING[slide_type_lower][0], 0.8
    
    # 2. Keyword-Analyse in Titel und Bullets
    text = f"{title} {' '.join(bullets)}".lower()
    
    scores = {}
    for chart_type, keywords in CHART_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            scores[chart_type] = score
    
    if scores:
        best_type = max(scores, key=scores.get)
        confidence = min(0.9, 0.5 + scores[best_type] * 0.1)
        return best_type, confidence
    
    # 3. Zahlen-Analyse
    numbers = re.findall(r'\d+(?:[.,]\d+)?(?:\s*%)?', text)
    if len(numbers) >= 3:
        # Mehrere Zahlen → wahrscheinlich Bar oder Pie
        if "%" in text or "anteil" in text:
            return ChartType.PIE, 0.6
        return ChartType.BAR, 0.6
    
    return ChartType.NONE, 0.0


def detect_chart_type_llm(
    slide_type: str,
    title: str,
    bullets: List[str],
    context: Dict[str, Any] = None
) -> Tuple[ChartType, float, str]:
    """
    Erkennt den passenden Chart-Typ via LLM.
    
    Returns:
        Tuple von (ChartType, Confidence, Rationale)
    """
    if not HAS_LLM or not llm_enabled or not llm_enabled():
        chart_type, conf = detect_chart_type_rule_based(slide_type, title, bullets)
        return chart_type, conf, "Rule-based detection"
    
    prompt = f"""Analysiere diesen Slide-Content und empfehle eine Visualisierung:

Slide-Typ: {slide_type}
Titel: {title}
Inhalt: {chr(10).join(bullets[:5])}

Verfügbare Chart-Typen:
- bar: Balkendiagramm (für Vergleiche, Rankings)
- line: Liniendiagramm (für Trends, Zeitreihen)
- pie: Kreisdiagramm (für Anteile, Verteilungen)
- timeline: Zeitstrahl (für Roadmaps, Phasen)
- funnel: Trichter (für Sales Funnel, Conversion)
- gauge: Tacho (für KPIs, Zielerreichung)
- matrix: Matrix (für Vergleichstabellen)
- none: Keine Visualisierung nötig

Antworte NUR mit JSON:
{{"chart_type": "...", "confidence": 0.8, "rationale": "..."}}"""

    try:
        result = llm_generate(prompt, max_tokens=150)
        if result.get("ok"):
            response = result.get("response", "")
            # JSON extrahieren
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                chart_type_str = data.get("chart_type", "none").lower()
                
                # String zu Enum
                try:
                    chart_type = ChartType(chart_type_str)
                except ValueError:
                    chart_type = ChartType.NONE
                
                confidence = float(data.get("confidence", 0.7))
                rationale = data.get("rationale", "LLM recommendation")
                
                return chart_type, confidence, rationale
    except Exception:
        pass
    
    # Fallback
    chart_type, conf = detect_chart_type_rule_based(slide_type, title, bullets)
    return chart_type, conf, "Rule-based fallback"


# ============================================
# DATA EXTRACTION FOR CHARTS
# ============================================

def extract_chart_data(
    bullets: List[str],
    chart_type: ChartType
) -> Dict[str, Any]:
    """
    Extrahiert Daten aus Bullets für ein Chart.
    
    Returns:
        Dictionary mit labels, values, etc.
    """
    data = {
        "labels": [],
        "values": [],
        "series": []
    }
    
    if chart_type == ChartType.NONE:
        return data
    
    # Zahlen und Labels extrahieren
    for bullet in bullets:
        # Pattern: "Label: 123" oder "Label (45%)" oder "Label - 67"
        patterns = [
            r'^(.+?):\s*(\d+(?:[.,]\d+)?)\s*(%)?',
            r'^(.+?)\s*\((\d+(?:[.,]\d+)?)\s*(%)?',
            r'^(.+?)\s*[-–]\s*(\d+(?:[.,]\d+)?)\s*(%)?',
            r'^(.+?)\s+(\d+(?:[.,]\d+)?)\s*(%)?$',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, bullet)
            if match:
                label = match.group(1).strip()
                value = float(match.group(2).replace(",", "."))
                is_percent = match.group(3) == "%" if match.lastindex >= 3 else False
                
                data["labels"].append(label[:30])  # Max 30 Zeichen
                data["values"].append(value)
                break
    
    # Wenn keine strukturierten Daten gefunden, generiere Beispieldaten
    if not data["labels"] and chart_type != ChartType.NONE:
        if chart_type == ChartType.TIMELINE:
            data["labels"] = ["Phase 1", "Phase 2", "Phase 3", "Phase 4"]
            data["values"] = [1, 2, 3, 4]
        elif chart_type == ChartType.FUNNEL:
            data["labels"] = ["Awareness", "Interest", "Decision", "Action"]
            data["values"] = [1000, 600, 300, 100]
        elif chart_type == ChartType.PIE:
            data["labels"] = ["Segment A", "Segment B", "Segment C"]
            data["values"] = [45, 35, 20]
        elif chart_type in [ChartType.BAR, ChartType.BAR_HORIZONTAL]:
            data["labels"] = ["Kategorie 1", "Kategorie 2", "Kategorie 3", "Kategorie 4"]
            data["values"] = [75, 60, 45, 30]
        elif chart_type == ChartType.GAUGE:
            data["labels"] = ["Aktuell"]
            data["values"] = [72]
    
    return data


def extract_chart_data_llm(
    bullets: List[str],
    chart_type: ChartType,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Extrahiert Chart-Daten via LLM (intelligenter).
    """
    # Erst regel-basiert versuchen
    data = extract_chart_data(bullets, chart_type)
    
    # Wenn Daten gefunden, fertig
    if data["labels"] and data["values"]:
        return data
    
    # LLM-basierte Extraktion
    if not HAS_LLM or not llm_enabled or not llm_enabled():
        return data
    
    prompt = f"""Extrahiere Daten für ein {chart_type.value}-Chart aus diesem Content:

{chr(10).join(bullets)}

Generiere realistische Beispieldaten basierend auf dem Kontext.
Kontext: {json.dumps(context or {}, ensure_ascii=False)[:200]}

Antworte NUR mit JSON:
{{"labels": ["Label1", "Label2", ...], "values": [10, 20, ...]}}"""

    try:
        result = llm_generate(prompt, max_tokens=200)
        if result.get("ok"):
            response = result.get("response", "")
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                llm_data = json.loads(json_match.group())
                if llm_data.get("labels") and llm_data.get("values"):
                    return {
                        "labels": llm_data["labels"][:8],
                        "values": [float(v) for v in llm_data["values"][:8]],
                        "series": []
                    }
    except Exception:
        pass
    
    return data


# ============================================
# CHART GENERATION
# ============================================

def generate_chart_for_slide(
    slide_type: str,
    title: str,
    bullets: List[str],
    context: Dict[str, Any] = None,
    use_llm: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Generiert ein passendes Chart für einen Slide.
    
    Returns:
        Dictionary mit path, chart_type, data oder None
    """
    if not HAS_CHART_GEN:
        return None
    
    # 1. Chart-Typ bestimmen
    if use_llm:
        chart_type, confidence, rationale = detect_chart_type_llm(
            slide_type, title, bullets, context
        )
    else:
        chart_type, confidence = detect_chart_type_rule_based(
            slide_type, title, bullets
        )
        rationale = "Rule-based"
    
    if chart_type == ChartType.NONE or confidence < 0.5:
        return None
    
    # 2. Daten extrahieren
    if use_llm:
        data = extract_chart_data_llm(bullets, chart_type, context)
    else:
        data = extract_chart_data(bullets, chart_type)
    
    if not data["labels"] or not data["values"]:
        return None
    
    # 3. Chart generieren
    result = None
    try:
        if chart_type == ChartType.BAR:
            result = create_bar_chart(
                labels=data["labels"],
                values=data["values"],
                title=title[:50],
                horizontal=False
            )
        elif chart_type == ChartType.BAR_HORIZONTAL:
            result = create_bar_chart(
                labels=data["labels"],
                values=data["values"],
                title=title[:50],
                horizontal=True
            )
        elif chart_type == ChartType.PIE:
            result = create_pie_chart(
                labels=data["labels"],
                values=data["values"],
                title=title[:50]
            )
        elif chart_type == ChartType.LINE:
            result = create_line_chart(
                labels=data["labels"],
                values=data["values"],
                title=title[:50]
            )
        elif chart_type == ChartType.TIMELINE:
            phases = [
                {"name": label, "duration": f"{i+1} Wo", "description": ""}
                for i, label in enumerate(data["labels"])
            ]
            result = create_timeline(phases=phases, title=title[:50])
        elif chart_type == ChartType.FUNNEL:
            result = create_funnel_chart(
                stages=data["labels"],
                values=[int(v) for v in data["values"]],
                title=title[:50]
            )
        elif chart_type == ChartType.GAUGE:
            value = data["values"][0] if data["values"] else 50
            result = create_gauge_chart(
                value=value,
                max_value=100,
                title=title[:50]
            )
        elif chart_type == ChartType.MATRIX:
            result = create_comparison_matrix(
                items=data["labels"][:4],
                criteria=["Kriterium 1", "Kriterium 2", "Kriterium 3"],
                scores=[[7, 8, 6]] * min(4, len(data["labels"])),
                title=title[:50]
            )
    except Exception as e:
        return None
    
    if result and result.get("ok"):
        return {
            "path": result.get("path"),
            "chart_type": chart_type.value,
            "confidence": confidence,
            "rationale": rationale,
            "data": data
        }
    
    return None


# ============================================
# IMAGE RECOMMENDATIONS
# ============================================

def extract_keywords_from_content(
    title: str,
    bullets: List[str],
    slide_type: str
) -> List[str]:
    """Extrahiert relevante Keywords für Bildsuche."""
    keywords = []
    
    # Aus Titel
    title_words = re.findall(r'\b\w{4,}\b', title.lower())
    keywords.extend(title_words[:3])
    
    # Aus Bullets
    for bullet in bullets[:3]:
        words = re.findall(r'\b\w{4,}\b', bullet.lower())
        keywords.extend(words[:2])
    
    # Slide-Typ spezifische Keywords
    type_keywords = {
        "team": ["team", "people", "business", "office"],
        "solution": ["solution", "innovation", "technology"],
        "problem": ["challenge", "problem", "obstacle"],
        "benefits": ["success", "growth", "achievement"],
        "roi": ["money", "finance", "chart", "growth"],
        "contact": ["contact", "handshake", "communication"],
    }
    
    if slide_type.lower() in type_keywords:
        keywords.extend(type_keywords[slide_type.lower()])
    
    # Deduplizieren
    seen = set()
    unique = []
    for kw in keywords:
        if kw not in seen and len(kw) >= 4:
            seen.add(kw)
            unique.append(kw)
    
    return unique[:10]


def search_local_images(keywords: List[str], k: int = 5) -> List[ImageRecommendation]:
    """Sucht lokale Bilder basierend auf Keywords."""
    results = []
    
    # Durchsuche uploads und assets
    search_dirs = [
        Path(UPLOADS_DIR),
        Path(ASSETS_DIR),
        Path("data/images")
    ]
    
    image_extensions = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"]
    
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        for file_path in search_dir.rglob("*"):
            if file_path.suffix.lower() in image_extensions:
                filename_lower = file_path.stem.lower()
                
                # Score basierend auf Keyword-Matches
                score = 0.0
                matched_keywords = []
                
                for kw in keywords:
                    if kw in filename_lower:
                        score += 0.3
                        matched_keywords.append(kw)
                
                if score > 0:
                    results.append(ImageRecommendation(
                        path=str(file_path),
                        title=file_path.stem,
                        relevance_score=min(1.0, score),
                        keywords=matched_keywords,
                        source="local"
                    ))
    
    # Nach Score sortieren
    results.sort(key=lambda x: x.relevance_score, reverse=True)
    return results[:k]


def recommend_images_for_slide(
    slide_type: str,
    title: str,
    bullets: List[str],
    k: int = 3
) -> List[Dict[str, Any]]:
    """
    Empfiehlt Bilder für einen Slide.
    
    Returns:
        Liste von Image-Empfehlungen
    """
    # Keywords extrahieren
    keywords = extract_keywords_from_content(title, bullets, slide_type)
    
    # Lokale Bilder suchen
    local_images = search_local_images(keywords, k=k)
    
    # Asset Tagger nutzen (wenn verfügbar)
    if HAS_ASSET_TAGGER:
        try:
            suggestions = get_asset_suggestions(
                keywords=keywords,
                slide_type=slide_type,
                k=k
            )
            if suggestions.get("ok"):
                for asset in suggestions.get("assets", []):
                    local_images.append(ImageRecommendation(
                        path=asset.get("path", ""),
                        title=asset.get("title", ""),
                        relevance_score=asset.get("score", 0.5),
                        keywords=asset.get("tags", []),
                        source="asset_tagger"
                    ))
        except Exception:
            pass
    
    # Deduplizieren und sortieren
    seen_paths = set()
    unique = []
    for img in local_images:
        if img.path not in seen_paths:
            seen_paths.add(img.path)
            unique.append(img)
    
    unique.sort(key=lambda x: x.relevance_score, reverse=True)
    
    return [asdict(img) for img in unique[:k]]


# ============================================
# LAYOUT OPTIMIZATION
# ============================================

def recommend_layout(
    slide_type: str,
    bullet_count: int,
    has_chart: bool,
    has_image: bool,
    avg_bullet_length: float = 50
) -> LayoutRecommendation:
    """
    Empfiehlt das optimale Layout für einen Slide.
    """
    # Title Slide
    if slide_type.lower() == "title":
        return LayoutRecommendation(
            layout_type=LayoutType.TITLE,
            rationale="Titel-Slide ohne Content",
            text_width=1.0
        )
    
    # Chart + Content
    if has_chart and bullet_count > 0:
        return LayoutRecommendation(
            layout_type=LayoutType.TITLE_CHART,
            rationale="Chart mit erklärenden Bullets",
            chart_position="right",
            text_width=0.55
        )
    
    # Nur Chart
    if has_chart and bullet_count == 0:
        return LayoutRecommendation(
            layout_type=LayoutType.CHART_ONLY,
            rationale="Chart als Hauptinhalt",
            chart_position="center",
            text_width=0.0
        )
    
    # Image + Content
    if has_image and bullet_count > 0:
        return LayoutRecommendation(
            layout_type=LayoutType.TITLE_IMAGE,
            rationale="Bild mit erklärenden Bullets",
            image_position="right",
            text_width=0.55
        )
    
    # Viele Bullets → Two Column
    if bullet_count > 6:
        return LayoutRecommendation(
            layout_type=LayoutType.TWO_COLUMN,
            rationale="Viele Punkte, aufgeteilt in zwei Spalten",
            text_width=1.0
        )
    
    # Lange Bullets → Mehr Platz
    if avg_bullet_length > 80:
        return LayoutRecommendation(
            layout_type=LayoutType.TITLE_CONTENT,
            rationale="Lange Texte, volle Breite",
            text_width=0.9
        )
    
    # Comparison Slide
    if slide_type.lower() in ["competitive", "comparison"]:
        return LayoutRecommendation(
            layout_type=LayoutType.COMPARISON,
            rationale="Vergleichs-Layout",
            text_width=1.0
        )
    
    # Standard
    return LayoutRecommendation(
        layout_type=LayoutType.TITLE_CONTENT,
        rationale="Standard-Layout",
        text_width=0.8
    )


# ============================================
# MAIN API FUNCTIONS
# ============================================

def enhance_slide_visuals(
    slide: Dict[str, Any],
    context: Dict[str, Any] = None,
    generate_charts: bool = True,
    recommend_images_flag: bool = True,
    use_llm: bool = True
) -> Dict[str, Any]:
    """
    Erweitert einen Slide um visuelle Elemente.
    
    Args:
        slide: Der Slide-Daten
        context: Projekt-Kontext
        generate_charts: Charts generieren?
        recommend_images_flag: Bilder empfehlen?
        use_llm: LLM für intelligente Auswahl nutzen?
    
    Returns:
        Erweiterter Slide mit chart, images, layout
    """
    slide_type = slide.get("type", "content")
    title = slide.get("title", "")
    bullets = slide.get("bullets", [])
    
    result = {
        **slide,
        "visual_enhanced": True
    }
    
    # 1. Chart generieren
    if generate_charts and not slide.get("chart"):
        chart_result = generate_chart_for_slide(
            slide_type=slide_type,
            title=title,
            bullets=bullets,
            context=context,
            use_llm=use_llm
        )
        if chart_result:
            result["chart"] = chart_result.get("path")
            result["chart_type"] = chart_result.get("chart_type")
            result["chart_confidence"] = chart_result.get("confidence")
            result["has_chart"] = True
    
    # 2. Bilder empfehlen
    if recommend_images_flag and not slide.get("image"):
        images = recommend_images_for_slide(
            slide_type=slide_type,
            title=title,
            bullets=bullets,
            k=3
        )
        if images:
            result["recommended_images"] = images
            # Erstes Bild automatisch zuweisen wenn Score hoch genug
            if images[0].get("relevance_score", 0) >= 0.5:
                result["suggested_image"] = images[0].get("path")
    
    # 3. Layout optimieren
    layout = recommend_layout(
        slide_type=slide_type,
        bullet_count=len(bullets),
        has_chart=result.get("has_chart", False),
        has_image=result.get("suggested_image") is not None,
        avg_bullet_length=sum(len(b) for b in bullets) / max(1, len(bullets))
    )
    result["recommended_layout"] = asdict(layout)
    
    return result


def enhance_all_slides(
    slides: List[Dict[str, Any]],
    context: Dict[str, Any] = None,
    generate_charts: bool = True,
    recommend_images_flag: bool = True,
    use_llm: bool = True
) -> List[Dict[str, Any]]:
    """
    Erweitert alle Slides um visuelle Elemente.
    """
    enhanced = []
    
    for slide in slides:
        enhanced_slide = enhance_slide_visuals(
            slide=slide,
            context=context,
            generate_charts=generate_charts,
            recommend_images_flag=recommend_images_flag,
            use_llm=use_llm
        )
        enhanced.append(enhanced_slide)
    
    return enhanced


def check_status() -> Dict[str, Any]:
    """Gibt den Status der Visual Intelligence zurück."""
    return {
        "ok": True,
        "services": {
            "chart_generator": HAS_CHART_GEN,
            "asset_tagger": HAS_ASSET_TAGGER,
            "llm": HAS_LLM and (llm_enabled() if llm_enabled else False)
        },
        "supported_charts": [ct.value for ct in ChartType if ct != ChartType.NONE],
        "supported_layouts": [lt.value for lt in LayoutType]
    }
