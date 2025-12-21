"""
Unsplash Image Service für Stratgen.
Lädt passende Stock-Fotos basierend auf Slide-Kontext.
"""

import os
import requests
import hashlib
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY", "moK2jVfu4dsOnnm-gM_7e-ydJzoWy9nSxtw6jxA72oQ")
CACHE_DIR = Path("data/images/unsplash_cache")


# Keyword-Mappings für Slide-Typen - VERBESSERT v3.41
SLIDE_TYPE_KEYWORDS = {
    # Title & Chapter - dunkle, kontrastreiche Bilder
    "title": "dark corporate skyline night",
    "chapter": "dark abstract minimal geometric",
    
    # Strategie & Analyse
    "executive_summary": "aerial city view modern",
    "context": "landscape horizon perspective",
    "situation": "cityscape urban modern",
    "market": "trading floor financial",
    "analysis": "data visualization abstract",
    "competition": "chess strategy game",
    
    # People & Team
    "persona": "professional portrait headshot",
    "team": "diverse team collaboration",
    "stakeholder": "business meeting conference",
    
    # Process & Planning
    "timeline": "road highway perspective",
    "roadmap": "mountain path journey",
    "process": "workflow automation factory",
    "milestones": "steps climbing achievement",
    
    # Data & Metrics
    "chart": "abstract data lines",
    "data": "digital technology abstract",
    "metrics": "dashboard analytics screen",
    "kpi": "performance measurement gauge",
    
    # Solutions & Benefits
    "solution": "light bulb innovation idea",
    "benefits": "growth plant nature success",
    "features": "technology circuit modern",
    "approach": "bridge connection architecture",
    
    # Risk & Budget
    "risks": "storm weather dramatic",
    "mitigation": "shield protection security",
    "budget": "coins investment finance",
    "roi": "growth chart profit arrow",
    
    # Conclusion & Contact
    "conclusion": "sunrise horizon optimism",
    "next_steps": "arrow direction forward",
    "contact": "handshake partnership deal",
    "quote": "minimal typography dark",
}

# Industrie-spezifische Keywords
INDUSTRY_KEYWORDS = {
    "technology": ["digital", "circuit", "code", "server"],
    "finance": ["trading", "coins", "wealth", "banking"],
    "healthcare": ["medical", "hospital", "health", "care"],
    "manufacturing": ["factory", "industrial", "production"],
    "retail": ["shopping", "store", "commerce", "market"],
    "consulting": ["strategy", "meeting", "professional"],
    "energy": ["solar", "wind", "power", "sustainable"],
    "automotive": ["car", "vehicle", "automotive", "road"],
    "real_estate": ["building", "architecture", "property"],
    "media": ["camera", "broadcast", "entertainment"],
}


def get_image_for_slide(
    slide_type: str,
    title: str = "",
    keywords: List[str] = None,
    orientation: str = "landscape",
    download: bool = True
) -> Optional[Dict]:
    """
    Holt ein passendes Bild für einen Slide.
    
    Args:
        slide_type: Typ des Slides (title, chapter, persona, etc.)
        title: Slide-Titel für bessere Suche
        keywords: Zusätzliche Suchbegriffe
        orientation: landscape, portrait, squarish
        download: Bild herunterladen und cachen
    
    Returns:
        Dict mit Bild-Infos oder None
    """
    # Query zusammenbauen
    base_query = SLIDE_TYPE_KEYWORDS.get(slide_type.lower(), SLIDE_TYPE_KEYWORDS.get("context", "professional business"))
    
    # Industrie-Keywords hinzufügen wenn verfügbar
    industry = ""
    if keywords:
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in INDUSTRY_KEYWORDS:
                industry = " ".join(INDUSTRY_KEYWORDS[kw_lower][:2])
                break
    
    # Relevante Wörter aus Titel extrahieren (keine Stoppwörter)
    stopwords = {"der", "die", "das", "und", "für", "von", "mit", "zu", "im", "the", "and", "for", "to", "in", "a", "an"}
    title_words = [w for w in title.lower().split() if len(w) > 3 and w not in stopwords][:2] if title else []
    
    # Finale Query: Base + Industrie + Titel-Keywords
    query_parts = [base_query]
    if industry:
        query_parts.append(industry)
    query_parts.extend(title_words)
    if keywords:
        query_parts.extend([k for k in keywords if k.lower() not in INDUSTRY_KEYWORDS][:2])
    
    query = " ".join(query_parts[:6])  # Max 6 Begriffe
    
    # API aufrufen
    url = "https://api.unsplash.com/search/photos"
    params = {
        "query": query,
        "per_page": 1,
        "orientation": orientation,
    }
    headers = {
        "Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code != 200:
            logger.warning(f"Unsplash API error: {response.status_code}")
            return None
        
        data = response.json()
        results = data.get("results", [])
        
        if not results:
            logger.info(f"No images found for: {query}")
            return None
        
        img = results[0]
        
        result = {
            "id": img.get("id"),
            "description": img.get("alt_description", ""),
            "url_full": img.get("urls", {}).get("full"),
            "url_regular": img.get("urls", {}).get("regular"),
            "url_small": img.get("urls", {}).get("small"),
            "url_thumb": img.get("urls", {}).get("thumb"),
            "photographer": img.get("user", {}).get("name"),
            "photographer_url": img.get("user", {}).get("links", {}).get("html"),
            "width": img.get("width"),
            "height": img.get("height"),
        }
        
        # Download und Cache
        if download:
            local_path = download_and_cache(result)
            if local_path:
                result["local_path"] = str(local_path)
        
        return result
        
    except Exception as e:
        logger.error(f"Unsplash error: {e}")
        return None


def download_and_cache(image_info: Dict, size: str = "regular") -> Optional[Path]:
    """
    Lädt Bild herunter und cached es lokal.
    
    Args:
        image_info: Dict mit Bild-URLs
        size: full, regular, small, thumb
    
    Returns:
        Pfad zur lokalen Datei
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    
    image_id = image_info.get("id", "unknown")
    url = image_info.get(f"url_{size}")
    
    if not url:
        return None
    
    # Cache-Pfad
    cache_file = CACHE_DIR / f"{image_id}_{size}.jpg"
    
    # Bereits gecached?
    if cache_file.exists():
        return cache_file
    
    # Download
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            cache_file.write_bytes(response.content)
            logger.info(f"Downloaded: {cache_file}")
            return cache_file
    except Exception as e:
        logger.error(f"Download error: {e}")
    
    return None


def get_images_for_presentation(slides: List[Dict], max_images: int = 10) -> Dict[int, Dict]:
    """
    Holt Bilder für eine ganze Präsentation.
    
    Args:
        slides: Liste von Slide-Daten
        max_images: Maximale Anzahl Bilder
    
    Returns:
        Dict mit Slide-Index -> Bild-Info
    """
    images = {}
    count = 0
    
    # Priorität: chapter, title, persona zuerst
    priority_types = ["chapter", "title", "persona", "quote"]
    
    # Sortiere nach Priorität
    indexed_slides = list(enumerate(slides))
    indexed_slides.sort(key=lambda x: (
        0 if x[1].get("type") in priority_types else 1
    ))
    
    for idx, slide in indexed_slides:
        if count >= max_images:
            break
        
        slide_type = slide.get("type", "bullets")
        title = slide.get("title", "")
        
        # Nur für bestimmte Typen Bilder holen
        if slide_type in ["chapter", "title", "persona", "quote", "conclusion"]:
            img = get_image_for_slide(slide_type, title)
            if img:
                images[idx] = img
                count += 1
    
    return images


# Test
if __name__ == "__main__":
    print("=== Unsplash Service Test ===")
    
    result = get_image_for_slide("chapter", "Marktanalyse")
    if result:
        print(f"Bild gefunden: {result.get('description')}")
        print(f"Fotograf: {result.get('photographer')}")
        print(f"Lokal: {result.get('local_path')}")
    else:
        print("Kein Bild gefunden")
