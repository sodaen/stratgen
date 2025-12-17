"""
Research Enrichment Service für Stratgen.
Kombiniert alle externen Datenquellen für reichhaltigere Präsentationen.

Quellen:
- Wikipedia (Definitionen, Hintergrund)
- News RSS (Aktuelle Nachrichten)
- Google Trends (Suchtrends)
- World Bank (Wirtschaftsdaten)
- Unsplash (Bilder)
"""

import logging
from typing import Dict, Any, List, Optional
from functools import lru_cache

logger = logging.getLogger(__name__)


def enrich_topic(topic: str, industry: str = "", include_news: bool = True) -> Dict[str, Any]:
    """
    Reichert ein Thema mit externen Daten an.
    
    Returns:
        Dict mit wikipedia, news, trends, stats
    """
    result = {
        "topic": topic,
        "wikipedia": None,
        "news": [],
        "trends": None,
        "stats": None,
        "related_topics": []
    }
    
    # Wikipedia
    try:
        from services.data_services import get_wikipedia_summary, search_wikipedia
        
        wiki = get_wikipedia_summary(topic)
        if wiki.get("ok"):
            result["wikipedia"] = {
                "title": wiki.get("title"),
                "summary": wiki.get("summary", "")[:500],
                "url": wiki.get("url"),
                "image": wiki.get("image")
            }
        
        # Verwandte Themen
        related = search_wikipedia(topic, limit=3)
        result["related_topics"] = [r.get("title") for r in related if r.get("title") != topic]
        
    except Exception as e:
        logger.warning(f"Wikipedia enrichment failed: {e}")
    
    # News
    if include_news:
        try:
            from services.data_services import get_news_rss
            
            news = get_news_rss(topic, source="google")
            if news:
                result["news"] = [
                    {"title": n.get("title"), "source": n.get("source"), "date": n.get("date")}
                    for n in news[:5]
                ]
        except Exception as e:
            logger.warning(f"News enrichment failed: {e}")
    
    # World Bank Stats (für wirtschaftliche Themen)
    if any(kw in topic.lower() for kw in ["markt", "wirtschaft", "growth", "umsatz", "branche"]):
        try:
            from services.data_services import get_worldbank_data
            
            # GDP Growth als Beispiel
            stats = get_worldbank_data("NY.GDP.MKTP.KD.ZG", "DEU", years=5)
            if stats.get("ok"):
                result["stats"] = stats.get("data", [])[:5]
        except Exception as e:
            logger.warning(f"World Bank enrichment failed: {e}")
    
    return result


def get_market_context(industry: str, region: str = "DACH") -> Dict[str, Any]:
    """
    Holt Marktkontext für eine Branche.
    """
    context = {
        "industry": industry,
        "region": region,
        "wikipedia_info": None,
        "trends": [],
        "news": []
    }
    
    # Wikipedia für Branchendefinition
    try:
        from services.data_services import get_wikipedia_summary
        
        wiki = get_wikipedia_summary(industry)
        if wiki.get("ok"):
            context["wikipedia_info"] = wiki.get("summary", "")[:400]
    except:
        pass
    
    # Aktuelle News
    try:
        from services.data_services import get_news_rss
        
        news = get_news_rss(f"{industry} {region}", source="google")
        context["news"] = [n.get("title") for n in (news or [])[:3]]
    except:
        pass
    
    return context


def generate_research_prompt_context(topic: str, industry: str = "") -> str:
    """
    Generiert einen Kontext-String für LLM-Prompts basierend auf Research.
    """
    enriched = enrich_topic(topic, industry)
    
    context_parts = []
    
    if enriched.get("wikipedia"):
        wiki = enriched["wikipedia"]
        context_parts.append(f"HINTERGRUND (Wikipedia): {wiki.get('summary', '')[:300]}")
    
    if enriched.get("news"):
        news_titles = [n.get("title") for n in enriched["news"][:3]]
        context_parts.append(f"AKTUELLE NEWS: {'; '.join(news_titles)}")
    
    if enriched.get("related_topics"):
        context_parts.append(f"VERWANDTE THEMEN: {', '.join(enriched['related_topics'])}")
    
    return "\n\n".join(context_parts)


def get_slide_enrichment(slide_type: str, chapter: str, topic: str) -> Dict[str, Any]:
    """
    Holt spezifische Anreicherung für einen Slide-Typ.
    """
    enrichment = {}
    
    # Markt-Slides: Wikipedia + Stats
    if chapter in ["market", "competition"] or "markt" in chapter.lower():
        try:
            from services.data_services import get_wikipedia_summary
            wiki = get_wikipedia_summary(topic)
            if wiki.get("ok"):
                enrichment["background"] = wiki.get("summary", "")[:200]
        except:
            pass
    
    # News für aktuelle Themen
    if slide_type in ["text", "bullets"] and chapter in ["market", "strategy"]:
        try:
            from services.data_services import get_news_rss
            news = get_news_rss(topic, limit=3)
            if news:
                enrichment["recent_news"] = [n.get("title") for n in news[:2]]
        except:
            pass
    
    return enrichment


# Test
if __name__ == "__main__":
    print("=== Test Research Enrichment ===")
    
    result = enrich_topic("Künstliche Intelligenz", "Healthcare")
    print(f"Wikipedia: {result.get('wikipedia', {}).get('title', 'N/A')}")
    print(f"News: {len(result.get('news', []))} Artikel")
    print(f"Verwandte Themen: {result.get('related_topics', [])}")
