"""
Data Services API für Stratgen.
Endpoints für externe Datenquellen.
"""

from fastapi import APIRouter
from typing import Optional, List

router = APIRouter(prefix="/data", tags=["data-services"])


@router.get("/wikipedia")
async def get_wikipedia(topic: str, lang: str = "de"):
    """Wikipedia-Summary für ein Thema."""
    from services.data_services import get_wikipedia_summary
    return get_wikipedia_summary(topic, lang)


@router.get("/wikipedia/search")
async def search_wiki(query: str, limit: int = 5, lang: str = "de"):
    """Sucht Wikipedia-Artikel."""
    from services.data_services import search_wikipedia
    results = search_wikipedia(query, limit, lang)
    return {"ok": True, "results": results}


@router.get("/images")
async def get_images(query: str, count: int = 5, source: str = "unsplash"):
    """Sucht kostenlose Bilder."""
    from services.data_services import search_unsplash_images, search_pexels_images
    
    if source == "pexels":
        images = search_pexels_images(query, count)
    else:
        images = search_unsplash_images(query, count)
    
    return {"ok": True, "images": images, "source": source}


@router.get("/trends")
async def get_trends(keywords: str, timeframe: str = "today 3-m"):
    """Google Trends Daten."""
    from services.data_services import get_trend_data
    keyword_list = [k.strip() for k in keywords.split(",")]
    return get_trend_data(keyword_list, timeframe)


@router.get("/worldbank")
async def get_worldbank(indicator: str, country: str = "WLD", years: int = 10):
    """World Bank Daten."""
    from services.data_services import get_world_bank_data
    return get_world_bank_data(indicator, country, years)


@router.get("/news")
async def get_news(topic: str, source: str = "google"):
    """News via RSS."""
    from services.data_services import get_news_rss
    articles = get_news_rss(topic, source)
    return {"ok": True, "articles": articles}


@router.get("/qrcode")
async def generate_qr(url: str, size: int = 200):
    """Generiert QR Code."""
    from services.data_services import generate_qr_code
    return generate_qr_code(url, size)


@router.get("/status")
async def data_services_status():
    """Status aller Data Services."""
    from services.data_services import check_data_services
    status = check_data_services()
    online = sum(1 for s in status.values() if s.get("available"))
    return {
        "ok": True,
        "services": status,
        "online": online,
        "total": len(status)
    }
