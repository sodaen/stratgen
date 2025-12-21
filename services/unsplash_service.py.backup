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


# Keyword-Mappings für Slide-Typen
SLIDE_TYPE_KEYWORDS = {
    "title": "business presentation professional",
    "chapter": "abstract gradient modern",
    "executive_summary": "business strategy overview",
    "market": "market analysis data charts",
    "competition": "competition business rivalry",
    "persona": "business professional portrait",
    "comparison": "comparison options choice",
    "chart": "data analytics dashboard",
    "timeline": "roadmap journey path",
    "roadmap": "roadmap journey planning",
    "quote": "inspiration motivation",
    "conclusion": "success achievement goal",
    "contact": "handshake partnership team",
    "team": "team collaboration office",
    "benefits": "growth success business",
    "features": "technology innovation",
    "risks": "risk management strategy",
    "budget": "finance money investment",
    "roi": "return investment profit",
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
    base_query = SLIDE_TYPE_KEYWORDS.get(slide_type, "business professional")
    
    # Keywords aus Titel extrahieren
    title_words = title.lower().split()[:3] if title else []
    
    # Finale Query
    query_parts = [base_query] + title_words
    if keywords:
        query_parts.extend(keywords)
    
    query = " ".join(query_parts[:5])  # Max 5 Begriffe
    
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
