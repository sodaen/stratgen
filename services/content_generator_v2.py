"""
Content Generator v2 für Stratgen.
Generiert Slide-Inhalte mit:
- RAG-basiertem Wissen
- Externen Datenquellen (Wikipedia, News, Trends)
- Automatischer Quellenerfassung
- Dynamischer Slide-Anzahl basierend auf Themen-Komplexität
"""

import os
import logging
import time
import json
import httpx
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass

from services.source_tracker import SourceTracker, new_source_tracker, Source

logger = logging.getLogger(__name__)

DATA_ROOT = Path(os.getenv("STRATGEN_DATA", "/home/sodaen/stratgen/data"))

# Cache für externe Daten
_cache: Dict[str, Any] = {}
CACHE_TTL = 3600  # 1 Stunde


@dataclass
class SlideContent:
    """Generierter Slide-Inhalt."""
    id: str
    type: str
    title: str
    content: str
    bullets: List[str] = None
    sources: List[str] = None
    data_points: List[Dict] = None
    metadata: Dict = None
    
    def to_dict(self) -> Dict:
        d = {
            "id": self.id,
            "type": self.type,
            "title": self.title,
            "content": self.content
        }
        if self.bullets:
            d["bullets"] = self.bullets
        if self.sources:
            d["sources"] = self.sources
        if self.data_points:
            d["data_points"] = self.data_points
        if self.metadata:
            d["metadata"] = self.metadata
        return d


class ContentGeneratorV2:
    """
    Generiert Slide-Inhalte mit RAG, externen Daten und Quellen.
    """
    
    def __init__(self, session_config: Dict = None):
        self.config = session_config or {}
        self.source_tracker = new_source_tracker()
        self.ollama_url = "http://localhost:11434/api/generate"
        self.qdrant_url = "http://localhost:6333"
        
    def _get_cached(self, key: str) -> Optional[Any]:
        """Holt gecachte Daten."""
        if key in _cache:
            data, timestamp = _cache[key]
            if time.time() - timestamp < CACHE_TTL:
                return data
        return None
    
    def _set_cached(self, key: str, data: Any):
        """Speichert Daten im Cache."""
        _cache[key] = (data, time.time())
    
    def _search_rag(self, query: str, limit: int = 5) -> List[Dict]:
        """Sucht in der Knowledge Base."""
        try:
            from services.unified_knowledge import search
            results = search(query, limit=limit)
            
            # Track sources
            for r in results:
                if hasattr(r, 'payload') and hasattr(r, 'score'):
                    source_name = r.payload.get('source', r.payload.get('filename', 'Knowledge Base'))
                    self.source_tracker.global_sources.append(Source(
                        name=source_name,
                        type="rag",
                        relevance_score=r.score
                    ))
            
            return results
        except Exception as e:
            logger.warning(f"RAG search failed: {e}")
            return []
    
    def _get_wikipedia(self, topic: str) -> Optional[Dict]:
        """Holt Wikipedia-Daten mit Cache."""
        cache_key = f"wiki_{topic}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            from services.data_services import get_wikipedia_summary
            # Cache leeren für frische Daten
            get_wikipedia_summary.cache_clear()
            result = get_wikipedia_summary(topic)
            
            if result.get('ok'):
                self._set_cached(cache_key, result)
                self.source_tracker.global_sources.append(Source(
                    name=f"Wikipedia: {result.get('title', topic)}",
                    type="wikipedia",
                    url=result.get('url')
                ))
            return result
        except Exception as e:
            logger.warning(f"Wikipedia fetch failed: {e}")
            return None
    
    def _get_news(self, topic: str, limit: int = 3) -> List[Dict]:
        """Holt aktuelle News."""
        cache_key = f"news_{topic}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            from services.data_services import get_news_rss
            articles = get_news_rss(topic)[:limit]
            
            if articles:
                self._set_cached(cache_key, articles)
                for a in articles:
                    if not a.get('error'):
                        self.source_tracker.global_sources.append(Source(
                            name=a.get('title', 'News')[:50],
                            type="news",
                            url=a.get('link')
                        ))
            return articles
        except Exception as e:
            logger.warning(f"News fetch failed: {e}")
            return []
    
    def _get_trends(self, keywords: List[str]) -> Optional[Dict]:
        """Holt Google Trends Daten."""
        cache_key = f"trends_{','.join(keywords)}"
        cached = self._get_cached(cache_key)
        if cached:
            return cached
        
        try:
            from services.data_services import get_trend_data
            result = get_trend_data(keywords)
            
            if result.get('ok'):
                self._set_cached(cache_key, result)
                self.source_tracker.global_sources.append(Source(
                    name="Google Trends",
                    type="data",
                    url="https://trends.google.com"
                ))
            return result
        except Exception as e:
            logger.warning(f"Trends fetch failed: {e}")
            return None
    
    def _generate_with_llm(self, prompt: str, max_tokens: int = 1000) -> str:
        """Generiert Text mit Ollama/Mistral."""
        try:
            response = httpx.post(
                self.ollama_url,
                json={
                    "model": "mistral",
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": max_tokens
                    }
                },
                timeout=60.0
            )
            
            if response.status_code == 200:
                return response.json().get("response", "")
        except Exception as e:
            logger.warning(f"LLM generation failed: {e}")
        return ""
    
    def _assess_topic_complexity(self, topic: str, brief: str) -> int:
        """
        Bestimmt die empfohlene Slide-Anzahl basierend auf Themen-Komplexität.
        Returns: 1-5 Slides
        """
        # Einfache Heuristik basierend auf:
        # 1. Länge des Briefings
        # 2. Anzahl der genannten Aspekte
        # 3. Keyword-Analyse
        
        complexity_score = 1
        
        # Briefing-Länge
        brief_len = len(brief) if brief else 0
        if brief_len > 500:
            complexity_score += 1
        if brief_len > 1000:
            complexity_score += 1
        
        # Aspekte zählen (Aufzählungen, Kommas, "und", etc.)
        aspects = brief.count(',') + brief.count('und') + brief.count('sowie') + brief.count('\n')
        if aspects > 3:
            complexity_score += 1
        if aspects > 6:
            complexity_score += 1
        
        # Keywords die auf Komplexität hindeuten
        complex_keywords = ['strategie', 'analyse', 'vergleich', 'übersicht', 'zusammenfassung',
                          'komplett', 'umfassend', 'detailliert', 'ausführlich', 'ganzheitlich']
        for kw in complex_keywords:
            if kw in topic.lower() or kw in brief.lower():
                complexity_score += 1
                break
        
        return min(max(complexity_score, 1), 5)
    
    def generate_slide_content(self, 
                               slide_type: str,
                               topic: str,
                               brief: str = "",
                               industry: str = "",
                               keywords: List[str] = None,
                               slide_index: int = 0,
                               total_slides: int = 1) -> SlideContent:
        """
        Generiert Inhalt für einen einzelnen Slide.
        """
        slide_id = f"slide_{slide_index}"
        keywords = keywords or []
        
        # Sammle Kontext
        context_parts = []
        
        # 1. RAG-Suche
        rag_query = f"{topic} {' '.join(keywords[:3])} {industry}"
        rag_results = self._search_rag(rag_query)
        if rag_results:
            for r in rag_results[:3]:
                if hasattr(r, 'payload'):
                    text = r.payload.get('text', '')[:500]
                    context_parts.append(f"Wissen: {text}")
        
        # 2. Wikipedia für Definitionen
        if slide_type in ['content', 'title'] and topic:
            wiki = self._get_wikipedia(topic.split()[0])
            if wiki and wiki.get('ok'):
                context_parts.append(f"Definition: {wiki.get('summary', '')[:300]}")
        
        # 3. News für aktuelle Bezüge
        if slide_type == 'content' and industry:
            news = self._get_news(f"{topic} {industry}")
            if news:
                for n in news[:2]:
                    if not n.get('error'):
                        context_parts.append(f"Aktuell: {n.get('title', '')}")
        
        # Erstelle LLM-Prompt
        context = "\n".join(context_parts) if context_parts else "Keine zusätzlichen Informationen verfügbar."
        
        if slide_type == "title":
            prompt = f"""Erstelle einen packenden Titel und Untertitel für eine Präsentation.

Thema: {topic}
Briefing: {brief}
Branche: {industry}

Ausgabe als JSON:
{{"title": "Haupttitel", "subtitle": "Untertitel"}}"""
        
        elif slide_type == "bullets":
            prompt = f"""Erstelle 4-5 prägnante Bullet Points zu folgendem Thema.

Thema: {topic}
Briefing: {brief}
Kontext: {context}

Ausgabe als JSON:
{{"title": "Slide-Titel", "bullets": ["Punkt 1", "Punkt 2", "Punkt 3", "Punkt 4"]}}"""
        
        elif slide_type == "data":
            prompt = f"""Erstelle 3-4 wichtige Datenpunkte/Metriken zum Thema.

Thema: {topic}
Briefing: {brief}
Branche: {industry}
Kontext: {context}

Ausgabe als JSON:
{{"title": "Slide-Titel", "data_points": [{{"value": "€1.2M", "label": "Beschreibung"}}, ...]}}"""
        
        else:  # content
            prompt = f"""Erstelle informativen Slide-Inhalt.

Thema: {topic}
Briefing: {brief}
Slide {slide_index + 1} von {total_slides}
Kontext: {context}

Ausgabe als JSON:
{{"title": "Slide-Titel", "content": "Ausführlicher Inhalt mit 2-3 Absätzen"}}"""
        
        # Generiere mit LLM
        response = self._generate_with_llm(prompt)
        
        # Parse JSON Response
        try:
            # Versuche JSON zu extrahieren
            import re
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {"title": topic, "content": response}
        except:
            data = {"title": topic, "content": response}
        
        # Erstelle SlideContent
        sources = self.source_tracker.get_sources_for_slide(slide_id)
        
        return SlideContent(
            id=slide_id,
            type=slide_type,
            title=data.get("title", topic),
            content=data.get("content", ""),
            bullets=data.get("bullets"),
            sources=sources if sources else self._get_default_sources(),
            data_points=data.get("data_points"),
            metadata={"generated_at": time.strftime("%Y-%m-%d %H:%M:%S")}
        )
    
    def _get_default_sources(self) -> List[str]:
        """Gibt Default-Quellen zurück wenn keine gefunden."""
        sources = []
        for s in self.source_tracker.global_sources[-5:]:
            sources.append(str(s))
        return sources if sources else ["Stratgen Knowledge Base"]
    
    def generate_presentation_content(self,
                                      topic: str,
                                      brief: str = "",
                                      industry: str = "",
                                      customer: str = "",
                                      keywords: List[str] = None,
                                      min_slides: int = 3,
                                      max_slides: int = 10) -> Tuple[List[Dict], Dict]:
        """
        Generiert kompletten Präsentationsinhalt.
        
        Returns:
            (slides, metadata) - Liste von Slide-Dicts und Metadaten
        """
        keywords = keywords or []
        
        # Bestimme Slide-Anzahl basierend auf Komplexität
        complexity = self._assess_topic_complexity(topic, brief)
        num_content_slides = max(min_slides - 1, min(complexity + 2, max_slides - 1))
        
        slides = []
        
        # 1. Title Slide
        title_slide = self.generate_slide_content(
            "title", topic, brief, industry, keywords, 0, num_content_slides + 1
        )
        slides.append(title_slide.to_dict())
        
        # 2. Content Slides basierend auf Komplexität
        slide_types = self._determine_slide_types(num_content_slides, brief)
        
        for i, slide_type in enumerate(slide_types):
            slide = self.generate_slide_content(
                slide_type, topic, brief, industry, keywords, i + 1, num_content_slides + 1
            )
            slides.append(slide.to_dict())
        
        # Füge Quellen zu allen Slides hinzu
        slides = self.source_tracker.enrich_slides_with_sources(slides)
        
        # Metadaten
        metadata = {
            "topic": topic,
            "industry": industry,
            "customer": customer,
            "slides_count": len(slides),
            "complexity_score": complexity,
            "sources_summary": self.source_tracker.get_sources_summary(),
            "all_sources": self.source_tracker.get_all_sources()
        }
        
        return slides, metadata
    
    def _determine_slide_types(self, count: int, brief: str) -> List[str]:
        """Bestimmt die Slide-Typen basierend auf Anzahl und Briefing."""
        if count <= 2:
            return ["content", "bullets"][:count]
        elif count <= 4:
            return ["content", "bullets", "data", "content"][:count]
        else:
            types = ["content", "bullets", "data", "content", "bullets"]
            # Wiederhole wenn nötig
            while len(types) < count:
                types.extend(["content", "bullets"])
            return types[:count]


def generate_presentation(topic: str, brief: str = "", industry: str = "",
                         customer: str = "", keywords: List[str] = None,
                         config: Dict = None) -> Tuple[List[Dict], Dict]:
    """
    Hauptfunktion zum Generieren einer Präsentation.
    """
    generator = ContentGeneratorV2(session_config=config)
    return generator.generate_presentation_content(
        topic, brief, industry, customer, keywords
    )
