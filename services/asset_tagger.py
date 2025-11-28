# -*- coding: utf-8 -*-
"""
services/asset_tagger.py
========================
Analysiert und taggt hochgeladene Assets (Bilder, Dokumente).
Ermöglicht automatische Zuordnung von Assets zu Slides.

Funktionen:
- analyze_image(): Bild analysieren und Tags extrahieren
- analyze_document(): Dokument analysieren
- match_assets_to_slides(): Assets zu Slides zuordnen
- get_asset_suggestions(): Asset-Vorschläge für Slide-Typ
"""
from __future__ import annotations
import os
import re
import json
import hashlib
import mimetypes
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

# Optional: PIL für Bildanalyse
try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

# Optional: python-magic für Dateityp-Erkennung
try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False

# ============================================
# KONFIGURATION
# ============================================

UPLOADS_DIR = os.getenv("STRATGEN_UPLOADS_DIR", "data/uploads")
ASSETS_DB = os.getenv("STRATGEN_ASSETS_DB", "data/assets.json")

# Bekannte Slide-Typen und passende Asset-Keywords
SLIDE_TYPE_KEYWORDS = {
    "title": ["logo", "brand", "header", "cover", "titel"],
    "executive_summary": ["overview", "summary", "highlight", "key"],
    "use_case": ["workflow", "process", "diagram", "flow", "example", "screenshot"],
    "roi": ["chart", "graph", "numbers", "money", "savings", "cost", "roi"],
    "roadmap": ["timeline", "roadmap", "gantt", "phases", "milestones", "plan"],
    "team": ["team", "people", "person", "portrait", "headshot", "org"],
    "competitive": ["comparison", "matrix", "versus", "competitor", "market"],
    "kpis": ["dashboard", "metrics", "kpi", "chart", "numbers", "data"],
    "risks": ["warning", "risk", "alert", "caution"],
    "next_steps": ["checklist", "action", "todo", "steps", "arrow"],
    "contact": ["contact", "email", "phone", "address", "qr"],
}

# Bildkategorien basierend auf Dateinamen-Mustern
FILENAME_PATTERNS = {
    r"logo|brand": "logo",
    r"chart|graph|diagram": "chart",
    r"screenshot|screen|ui": "screenshot",
    r"team|person|people|headshot|portrait": "people",
    r"icon|symbol": "icon",
    r"photo|image|picture|img": "photo",
    r"infographic": "infographic",
    r"mockup|mock-up": "mockup",
    r"process|workflow|flow": "process",
    r"timeline|roadmap": "timeline",
}

# ============================================
# ASSET STORAGE
# ============================================

def _load_assets_db() -> Dict[str, Any]:
    """Lädt die Assets-Datenbank."""
    if os.path.exists(ASSETS_DB):
        try:
            with open(ASSETS_DB, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"assets": {}, "updated_at": None}


def _save_assets_db(db: Dict[str, Any]) -> None:
    """Speichert die Assets-Datenbank."""
    os.makedirs(os.path.dirname(ASSETS_DB), exist_ok=True)
    db["updated_at"] = datetime.now().isoformat()
    with open(ASSETS_DB, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def _file_hash(path: str) -> str:
    """Berechnet SHA256-Hash einer Datei."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


# ============================================
# BILD-ANALYSE
# ============================================

def _detect_image_type(path: str) -> str:
    """Erkennt den Bildtyp basierend auf Dateiname und Inhalt."""
    filename = os.path.basename(path).lower()
    
    # Pattern-Matching auf Dateinamen
    for pattern, img_type in FILENAME_PATTERNS.items():
        if re.search(pattern, filename):
            return img_type
    
    # Fallback: Generisch
    return "image"


def _extract_image_metadata(path: str) -> Dict[str, Any]:
    """Extrahiert Metadaten aus einem Bild."""
    meta = {
        "width": None,
        "height": None,
        "format": None,
        "mode": None,
        "aspect_ratio": None,
        "orientation": None,  # landscape, portrait, square
    }
    
    if not HAS_PIL:
        return meta
    
    try:
        with Image.open(path) as img:
            meta["width"] = img.width
            meta["height"] = img.height
            meta["format"] = img.format
            meta["mode"] = img.mode
            
            if img.width and img.height:
                ratio = img.width / img.height
                meta["aspect_ratio"] = round(ratio, 2)
                
                if ratio > 1.2:
                    meta["orientation"] = "landscape"
                elif ratio < 0.8:
                    meta["orientation"] = "portrait"
                else:
                    meta["orientation"] = "square"
    except Exception:
        pass
    
    return meta


def _analyze_image_colors(path: str) -> Dict[str, Any]:
    """Analysiert dominante Farben im Bild (vereinfacht)."""
    colors = {
        "dominant": None,
        "is_dark": None,
        "is_colorful": None,
    }
    
    if not HAS_PIL:
        return colors
    
    try:
        with Image.open(path) as img:
            # Verkleinern für schnelle Analyse
            img_small = img.resize((50, 50))
            img_rgb = img_small.convert("RGB")
            
            pixels = list(img_rgb.getdata())
            avg_r = sum(p[0] for p in pixels) / len(pixels)
            avg_g = sum(p[1] for p in pixels) / len(pixels)
            avg_b = sum(p[2] for p in pixels) / len(pixels)
            
            # Helligkeit
            brightness = (avg_r + avg_g + avg_b) / 3
            colors["is_dark"] = brightness < 128
            
            # Farbigkeit (Sättigung approximiert)
            max_diff = max(abs(avg_r - avg_g), abs(avg_g - avg_b), abs(avg_r - avg_b))
            colors["is_colorful"] = max_diff > 50
            
            # Dominante Farbe (vereinfacht)
            if avg_r > avg_g and avg_r > avg_b:
                colors["dominant"] = "red"
            elif avg_g > avg_r and avg_g > avg_b:
                colors["dominant"] = "green"
            elif avg_b > avg_r and avg_b > avg_g:
                colors["dominant"] = "blue"
            elif brightness > 200:
                colors["dominant"] = "white"
            elif brightness < 55:
                colors["dominant"] = "black"
            else:
                colors["dominant"] = "gray"
    except Exception:
        pass
    
    return colors


def analyze_image(path: str, project_id: str = None) -> Dict[str, Any]:
    """
    Analysiert ein Bild und extrahiert Tags.
    
    Args:
        path: Pfad zum Bild
        project_id: Optionale Projekt-ID für Zuordnung
    
    Returns:
        Dict mit: id, path, type, tags, metadata, suitable_for
    """
    if not os.path.exists(path):
        return {"ok": False, "error": "File not found"}
    
    filename = os.path.basename(path)
    file_hash = _file_hash(path)
    file_size = os.path.getsize(path)
    
    # Analyse
    img_type = _detect_image_type(path)
    metadata = _extract_image_metadata(path)
    colors = _analyze_image_colors(path)
    
    # Tags generieren
    tags = [img_type]
    
    # Tags aus Dateinamen extrahieren
    name_parts = re.findall(r"[a-zA-Z]+", os.path.splitext(filename)[0].lower())
    tags.extend([p for p in name_parts if len(p) > 2 and p not in tags])
    
    # Orientierung als Tag
    if metadata.get("orientation"):
        tags.append(metadata["orientation"])
    
    # Farb-Tags
    if colors.get("dominant"):
        tags.append(f"color_{colors['dominant']}")
    if colors.get("is_dark"):
        tags.append("dark")
    else:
        tags.append("light")
    
    # Passende Slide-Typen ermitteln
    suitable_for = []
    for slide_type, keywords in SLIDE_TYPE_KEYWORDS.items():
        for tag in tags:
            if any(kw in tag.lower() for kw in keywords):
                if slide_type not in suitable_for:
                    suitable_for.append(slide_type)
    
    # Asset-Objekt erstellen
    asset = {
        "id": f"asset_{file_hash}",
        "path": path,
        "filename": filename,
        "type": "image",
        "subtype": img_type,
        "tags": list(set(tags)),
        "metadata": {
            **metadata,
            **colors,
            "size_bytes": file_size,
        },
        "suitable_for": suitable_for,
        "project_id": project_id,
        "analyzed_at": datetime.now().isoformat(),
    }
    
    # In DB speichern
    db = _load_assets_db()
    db["assets"][asset["id"]] = asset
    _save_assets_db(db)
    
    return {"ok": True, "asset": asset}


# ============================================
# DOKUMENT-ANALYSE
# ============================================

def analyze_document(path: str, project_id: str = None) -> Dict[str, Any]:
    """
    Analysiert ein Dokument und extrahiert Tags.
    
    Unterstützt: PDF, DOCX, TXT, MD, CSV, XLSX
    """
    if not os.path.exists(path):
        return {"ok": False, "error": "File not found"}
    
    filename = os.path.basename(path)
    ext = os.path.splitext(filename)[1].lower()
    file_hash = _file_hash(path)
    file_size = os.path.getsize(path)
    
    # Dokumenttyp bestimmen
    doc_types = {
        ".pdf": "pdf",
        ".docx": "word",
        ".doc": "word",
        ".txt": "text",
        ".md": "markdown",
        ".csv": "spreadsheet",
        ".xlsx": "spreadsheet",
        ".xls": "spreadsheet",
        ".pptx": "presentation",
        ".ppt": "presentation",
    }
    doc_type = doc_types.get(ext, "document")
    
    # Tags aus Dateinamen
    tags = [doc_type]
    name_parts = re.findall(r"[a-zA-Z]+", os.path.splitext(filename)[0].lower())
    tags.extend([p for p in name_parts if len(p) > 2 and p not in tags])
    
    # Content-Extraktion (vereinfacht für TXT/MD)
    content_preview = ""
    if ext in [".txt", ".md"]:
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                content_preview = f.read(1000)
        except Exception:
            pass
    
    # Keywords aus Content
    if content_preview:
        words = re.findall(r"[a-zA-ZäöüÄÖÜß]{4,}", content_preview.lower())
        word_freq = {}
        for w in words:
            word_freq[w] = word_freq.get(w, 0) + 1
        top_words = sorted(word_freq.items(), key=lambda x: -x[1])[:10]
        tags.extend([w for w, _ in top_words if w not in tags])
    
    asset = {
        "id": f"asset_{file_hash}",
        "path": path,
        "filename": filename,
        "type": "document",
        "subtype": doc_type,
        "tags": list(set(tags))[:20],  # Max 20 Tags
        "metadata": {
            "size_bytes": file_size,
            "extension": ext,
            "content_preview": content_preview[:200] if content_preview else None,
        },
        "suitable_for": [],  # Dokumente sind für alle Slides potenziell relevant
        "project_id": project_id,
        "analyzed_at": datetime.now().isoformat(),
    }
    
    # In DB speichern
    db = _load_assets_db()
    db["assets"][asset["id"]] = asset
    _save_assets_db(db)
    
    return {"ok": True, "asset": asset}


# ============================================
# ASSET-MATCHING
# ============================================

def match_assets_to_slides(
    slides: List[Dict[str, Any]],
    project_id: str = None,
    assets: List[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Ordnet Assets automatisch zu Slides zu.
    
    Args:
        slides: Liste von Slide-Dicts mit title, type, etc.
        project_id: Projekt-ID für Asset-Filter
        assets: Optionale Asset-Liste (sonst aus DB)
    
    Returns:
        Slides mit hinzugefügtem 'suggested_assets' Feld
    """
    if assets is None:
        db = _load_assets_db()
        all_assets = list(db.get("assets", {}).values())
        # Filter nach Projekt wenn angegeben
        if project_id:
            assets = [a for a in all_assets if a.get("project_id") == project_id or not a.get("project_id")]
        else:
            assets = all_assets
    
    for slide in slides:
        slide_type = slide.get("type", "").lower() or slide.get("layout_hint", "").lower()
        slide_title = slide.get("title", "").lower()
        slide_bullets = " ".join(slide.get("bullets", [])).lower()
        
        # Scoring für jedes Asset
        scored_assets = []
        for asset in assets:
            score = 0
            
            # Match auf slide type
            if slide_type in asset.get("suitable_for", []):
                score += 10
            
            # Match auf Tags vs Slide-Titel
            for tag in asset.get("tags", []):
                if tag in slide_title:
                    score += 5
                if tag in slide_bullets:
                    score += 2
            
            # Bilder bevorzugen für visuelle Slides
            if asset.get("type") == "image":
                if slide_type in ["roi", "roadmap", "use_case", "competitive"]:
                    score += 3
            
            if score > 0:
                scored_assets.append((asset, score))
        
        # Top 3 Assets sortiert nach Score
        scored_assets.sort(key=lambda x: -x[1])
        slide["suggested_assets"] = [
            {"asset_id": a["id"], "path": a["path"], "score": s}
            for a, s in scored_assets[:3]
        ]
    
    return slides


def get_asset_suggestions(
    slide_type: str,
    keywords: List[str] = None,
    project_id: str = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    Gibt Asset-Vorschläge für einen Slide-Typ.
    
    Args:
        slide_type: Typ des Slides (roi, roadmap, etc.)
        keywords: Zusätzliche Keywords zum Matchen
        project_id: Projekt-Filter
        limit: Max Anzahl Vorschläge
    
    Returns:
        Liste von Asset-Dicts
    """
    db = _load_assets_db()
    all_assets = list(db.get("assets", {}).values())
    
    # Filter
    if project_id:
        all_assets = [a for a in all_assets if a.get("project_id") == project_id or not a.get("project_id")]
    
    # Scoring
    scored = []
    keywords = keywords or []
    slide_keywords = SLIDE_TYPE_KEYWORDS.get(slide_type.lower(), [])
    all_keywords = set(k.lower() for k in keywords + slide_keywords)
    
    for asset in all_assets:
        score = 0
        asset_tags = set(t.lower() for t in asset.get("tags", []))
        
        # Tag-Matches
        matches = asset_tags & all_keywords
        score += len(matches) * 5
        
        # Suitable-for Match
        if slide_type.lower() in asset.get("suitable_for", []):
            score += 10
        
        # Bilder bevorzugen
        if asset.get("type") == "image":
            score += 2
        
        if score > 0:
            scored.append((asset, score))
    
    scored.sort(key=lambda x: -x[1])
    return [a for a, _ in scored[:limit]]


# ============================================
# SCAN UPLOADS
# ============================================

def scan_uploads_directory(
    directory: str = None,
    project_id: str = None
) -> Dict[str, Any]:
    """
    Scannt ein Verzeichnis und analysiert alle Assets.
    
    Args:
        directory: Zu scannendes Verzeichnis (default: UPLOADS_DIR)
        project_id: Projekt-ID für alle gefundenen Assets
    
    Returns:
        Dict mit: scanned, images, documents, errors
    """
    directory = directory or UPLOADS_DIR
    if not os.path.isdir(directory):
        return {"ok": False, "error": f"Directory not found: {directory}"}
    
    results = {
        "ok": True,
        "scanned": 0,
        "images": 0,
        "documents": 0,
        "skipped": 0,
        "errors": [],
    }
    
    image_extensions = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp"}
    document_extensions = {".pdf", ".docx", ".doc", ".txt", ".md", ".csv", ".xlsx", ".xls"}
    
    for root, _, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            ext = os.path.splitext(filename)[1].lower()
            
            try:
                if ext in image_extensions:
                    result = analyze_image(filepath, project_id)
                    if result.get("ok"):
                        results["images"] += 1
                    else:
                        results["errors"].append(f"{filename}: {result.get('error')}")
                elif ext in document_extensions:
                    result = analyze_document(filepath, project_id)
                    if result.get("ok"):
                        results["documents"] += 1
                    else:
                        results["errors"].append(f"{filename}: {result.get('error')}")
                else:
                    results["skipped"] += 1
                    continue
                
                results["scanned"] += 1
            except Exception as e:
                results["errors"].append(f"{filename}: {str(e)}")
    
    return results


# ============================================
# ASSET RETRIEVAL
# ============================================

def get_asset(asset_id: str) -> Optional[Dict[str, Any]]:
    """Holt ein Asset anhand der ID."""
    db = _load_assets_db()
    return db.get("assets", {}).get(asset_id)


def get_project_assets(project_id: str) -> List[Dict[str, Any]]:
    """Holt alle Assets eines Projekts."""
    db = _load_assets_db()
    return [a for a in db.get("assets", {}).values() if a.get("project_id") == project_id]


def list_all_assets(
    asset_type: str = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Listet alle Assets, optional gefiltert nach Typ."""
    db = _load_assets_db()
    assets = list(db.get("assets", {}).values())
    
    if asset_type:
        assets = [a for a in assets if a.get("type") == asset_type]
    
    # Sortiert nach Analyse-Datum (neueste zuerst)
    assets.sort(key=lambda x: x.get("analyzed_at", ""), reverse=True)
    return assets[:limit]


# ============================================
# TEST
# ============================================

if __name__ == "__main__":
    print("=== Asset Tagger Test ===\n")
    
    # Test Scan
    print("--- Scan uploads directory ---")
    result = scan_uploads_directory()
    print(f"Scanned: {result.get('scanned')}")
    print(f"Images: {result.get('images')}")
    print(f"Documents: {result.get('documents')}")
    print()
    
    # Test Asset-Suggestions
    print("--- Asset suggestions for 'roi' slide ---")
    suggestions = get_asset_suggestions("roi", keywords=["chart", "data"])
    for s in suggestions:
        print(f"  - {s.get('filename')}: {s.get('tags', [])[:5]}")
