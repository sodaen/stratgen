"""
Data Services für Stratgen.
Kostenlose externe Datenquellen für reichhaltigere Präsentationen.
"""

import httpx
import logging
from typing import Dict, Any, List, Optional
from functools import lru_cache
import json

logger = logging.getLogger(__name__)

# === WIKIPEDIA ===

@lru_cache(maxsize=100)
def get_wikipedia_summary(topic: str, lang: str = "de") -> Dict[str, Any]:
    """
    Holt Wikipedia-Summary für ein Thema.
    Cached für Performance.
    """
    try:
        # URL-encode the topic
        from urllib.parse import quote
        encoded_topic = quote(topic.replace(" ", "_"))
        url = f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{encoded_topic}"
        response = httpx.get(url, timeout=10, follow_redirects=True)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "ok": True,
                "title": data.get("title"),
                "summary": data.get("extract"),
                "image": data.get("thumbnail", {}).get("source"),
                "url": data.get("content_urls", {}).get("desktop", {}).get("page"),
                "source": "wikipedia"
            }
        else:
            return {"ok": False, "error": f"Status {response.status_code}"}
            
    except Exception as e:
        logger.warning(f"Wikipedia lookup failed: {e}")
        return {"ok": False, "error": str(e)}


def search_wikipedia(query: str, limit: int = 5, lang: str = "de") -> List[Dict]:
    """Sucht Wikipedia-Artikel."""
    try:
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "opensearch",
            "search": query,
            "limit": limit,
            "format": "json"
        }
        response = httpx.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            # Format: [query, [titles], [descriptions], [urls]]
            results = []
            if len(data) >= 4:
                for i, title in enumerate(data[1]):
                    results.append({
                        "title": title,
                        "description": data[2][i] if i < len(data[2]) else "",
                        "url": data[3][i] if i < len(data[3]) else ""
                    })
            return results
        return []
        
    except Exception as e:
        logger.warning(f"Wikipedia search failed: {e}")
        return []


# === UNSPLASH (Free Images) ===

UNSPLASH_ACCESS_KEY = None  # Optional: Für höhere Limits

def search_unsplash_images(query: str, count: int = 5) -> List[Dict]:
    """
    Sucht kostenlose Bilder auf Unsplash.
    Ohne API Key: Source-URL (niedriger Res)
    Mit API Key: Voller Zugriff
    """
    try:
        # Ohne API Key: Nutze die öffentliche Source-URL
        # Diese ist für nicht-kommerzielle Nutzung OK
        images = []
        
        # Alternative: Unsplash Source (random images by query)
        for i in range(count):
            images.append({
                "url": f"https://source.unsplash.com/800x600/?{query.replace(' ', ',')}",
                "thumb": f"https://source.unsplash.com/400x300/?{query.replace(' ', ',')}",
                "credit": "Unsplash",
                "query": query
            })
        
        return images
        
    except Exception as e:
        logger.warning(f"Unsplash search failed: {e}")
        return []


# === PEXELS (Free Images) ===

def search_pexels_images(query: str, count: int = 5) -> List[Dict]:
    """Sucht Bilder auf Pexels (benötigt API Key für beste Ergebnisse)."""
    # Fallback ohne API Key
    return [{
        "url": f"https://images.pexels.com/photos/search?query={query}",
        "source": "pexels",
        "note": "API Key empfohlen für direkte Bilder"
    }]


# === GOOGLE TRENDS (via pytrends) ===

def get_trend_data(keywords: List[str], timeframe: str = "today 3-m") -> Dict[str, Any]:
    """
    Holt Google Trends Daten.
    Benötigt: pip install pytrends
    """
    try:
        from pytrends.request import TrendReq
        
        pytrends = TrendReq(hl='de-DE', tz=360)
        pytrends.build_payload(keywords[:5], timeframe=timeframe)  # Max 5 keywords
        
        interest = pytrends.interest_over_time()
        
        if interest.empty:
            return {"ok": False, "error": "No data"}
        
        # Konvertiere zu Chart-Daten
        chart_data = []
        for date, row in interest.iterrows():
            point = {"date": date.strftime("%Y-%m-%d")}
            for kw in keywords[:5]:
                if kw in row:
                    point[kw] = int(row[kw])
            chart_data.append(point)
        
        return {
            "ok": True,
            "keywords": keywords[:5],
            "timeframe": timeframe,
            "data": chart_data[-30:],  # Letzte 30 Datenpunkte
            "source": "google_trends"
        }
        
    except ImportError:
        return {"ok": False, "error": "pytrends not installed"}
    except Exception as e:
        logger.warning(f"Google Trends failed: {e}")
        return {"ok": False, "error": str(e)}


# === OPEN DATA SOURCES ===

def get_world_bank_data(indicator: str, country: str = "WLD", years: int = 10) -> Dict[str, Any]:
    """
    Holt Daten von der World Bank API.
    Beispiel Indikatoren:
    - NY.GDP.MKTP.CD (GDP)
    - SP.POP.TOTL (Population)
    - IT.NET.USER.ZS (Internet Users %)
    """
    try:
        url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
        params = {
            "format": "json",
            "per_page": years,
            "date": f"{2024-years}:2024"
        }
        
        response = httpx.get(url, params=params, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if len(data) > 1 and data[1]:
                chart_data = []
                for item in reversed(data[1]):
                    if item.get("value") is not None:
                        chart_data.append({
                            "year": item["date"],
                            "value": item["value"],
                            "country": item["country"]["value"]
                        })
                
                return {
                    "ok": True,
                    "indicator": indicator,
                    "country": country,
                    "data": chart_data,
                    "source": "world_bank"
                }
        
        return {"ok": False, "error": "No data found"}
        
    except Exception as e:
        logger.warning(f"World Bank API failed: {e}")
        return {"ok": False, "error": str(e)}


# === QR CODE GENERATOR ===

def generate_qr_code(url: str, size: int = 200) -> Dict[str, Any]:
    """
    Generiert QR Code als Base64 PNG.
    Benötigt: pip install qrcode pillow
    """
    try:
        import qrcode
        import io
        import base64
        
        qr = qrcode.QRCode(version=1, box_size=10, border=2)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize
        img = img.resize((size, size))
        
        # To Base64
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        b64 = base64.b64encode(buffer.getvalue()).decode()
        
        return {
            "ok": True,
            "base64": f"data:image/png;base64,{b64}",
            "url": url,
            "size": size
        }
        
    except ImportError:
        return {"ok": False, "error": "qrcode not installed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === COLOR EXTRACTION ===

def extract_colors_from_image(image_path: str, num_colors: int = 5) -> Dict[str, Any]:
    """
    Extrahiert dominante Farben aus einem Bild.
    Benötigt: pip install colorthief
    """
    try:
        from colorthief import ColorThief
        
        ct = ColorThief(image_path)
        dominant = ct.get_color(quality=1)
        palette = ct.get_palette(color_count=num_colors, quality=1)
        
        def rgb_to_hex(rgb):
            return '#{:02x}{:02x}{:02x}'.format(*rgb)
        
        return {
            "ok": True,
            "dominant": rgb_to_hex(dominant),
            "palette": [rgb_to_hex(c) for c in palette],
            "source": image_path
        }
        
    except ImportError:
        return {"ok": False, "error": "colorthief not installed"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


# === NEWS (RSS Feeds - komplett kostenlos) ===

def get_news_rss(topic: str, source: str = "google") -> List[Dict]:
    """
    Holt News via RSS Feeds (kostenlos, keine API Key nötig).
    """
    try:
        import feedparser
        
        feeds = {
            "google": f"https://news.google.com/rss/search?q={topic}&hl=de&gl=DE&ceid=DE:de",
            "bing": f"https://www.bing.com/news/search?q={topic}&format=rss",
        }
        
        url = feeds.get(source, feeds["google"])
        feed = feedparser.parse(url)
        
        articles = []
        for entry in feed.entries[:10]:
            articles.append({
                "title": entry.get("title", ""),
                "link": entry.get("link", ""),
                "published": entry.get("published", ""),
                "summary": entry.get("summary", "")[:200]
            })
        
        return articles
        
    except ImportError:
        return [{"error": "feedparser not installed"}]
    except Exception as e:
        logger.warning(f"RSS fetch failed: {e}")
        return []


# === SERVICE STATUS ===

def check_data_services() -> Dict[str, Any]:
    """Prüft alle Data Services."""
    status = {}
    
    # Wikipedia
    result = get_wikipedia_summary("Marketing")
    status["wikipedia"] = {"available": result.get("ok", False)}
    
    # World Bank
    result = get_world_bank_data("NY.GDP.MKTP.CD", "DEU", 1)
    status["world_bank"] = {"available": result.get("ok", False)}
    
    # Unsplash (immer verfügbar via Source URL)
    status["unsplash"] = {"available": True, "note": "Source URL (no API key)"}
    
    # Google Trends
    try:
        from pytrends.request import TrendReq
        status["google_trends"] = {"available": True}
    except ImportError:
        status["google_trends"] = {"available": False, "note": "pytrends not installed"}
    
    # QR Code
    try:
        import qrcode
        status["qr_code"] = {"available": True}
    except ImportError:
        status["qr_code"] = {"available": False, "note": "qrcode not installed"}
    
    # RSS/News
    try:
        import feedparser
        status["news_rss"] = {"available": True}
    except ImportError:
        status["news_rss"] = {"available": False, "note": "feedparser not installed"}
    
    return status
