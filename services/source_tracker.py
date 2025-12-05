"""
Source Tracker für Stratgen.
Sammelt und verwaltet Quellen während der Content-Generierung.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class Source:
    """Eine Quellenangabe."""
    name: str
    type: str  # rag, wikipedia, news, data, expert, internal
    url: Optional[str] = None
    relevance_score: Optional[float] = None
    accessed_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "type": self.type,
            "url": self.url,
            "relevance_score": self.relevance_score,
            "accessed_at": self.accessed_at
        }
    
    def __str__(self) -> str:
        if self.url:
            return f"{self.name} ({self.url})"
        return self.name


class SourceTracker:
    """Sammelt Quellen während der Content-Generierung."""
    
    def __init__(self):
        self.sources: Dict[str, List[Source]] = {}  # slide_id -> sources
        self.global_sources: List[Source] = []
    
    def add_source(self, slide_id: str, source: Source):
        """Fügt Quelle zu einem Slide hinzu."""
        if slide_id not in self.sources:
            self.sources[slide_id] = []
        self.sources[slide_id].append(source)
        self.global_sources.append(source)
    
    def add_rag_sources(self, slide_id: str, rag_results: List[Any]):
        """Fügt RAG-Suchergebnisse als Quellen hinzu."""
        for result in rag_results:
            if hasattr(result, 'payload'):
                payload = result.payload
                source = Source(
                    name=payload.get('source', payload.get('filename', 'Knowledge Base')),
                    type="rag",
                    url=payload.get('url'),
                    relevance_score=result.score if hasattr(result, 'score') else None
                )
                self.add_source(slide_id, source)
    
    def add_wikipedia_source(self, slide_id: str, wiki_data: Dict):
        """Fügt Wikipedia als Quelle hinzu."""
        if wiki_data.get('ok'):
            source = Source(
                name=f"Wikipedia: {wiki_data.get('title', 'Artikel')}",
                type="wikipedia",
                url=wiki_data.get('url')
            )
            self.add_source(slide_id, source)
    
    def add_news_source(self, slide_id: str, article: Dict):
        """Fügt News-Artikel als Quelle hinzu."""
        source = Source(
            name=article.get('title', 'News Article')[:50],
            type="news",
            url=article.get('link')
        )
        self.add_source(slide_id, source)
    
    def add_data_source(self, slide_id: str, source_name: str, url: str = None):
        """Fügt Datenquelle hinzu."""
        source = Source(
            name=source_name,
            type="data",
            url=url
        )
        self.add_source(slide_id, source)
    
    def get_sources_for_slide(self, slide_id: str) -> List[str]:
        """Gibt formatierte Quellen für einen Slide zurück."""
        sources = self.sources.get(slide_id, [])
        # Deduplizieren und formatieren
        seen = set()
        result = []
        for s in sources:
            key = s.name
            if key not in seen:
                seen.add(key)
                result.append(str(s))
        return result[:5]  # Max 5 Quellen pro Slide
    
    def get_all_sources(self) -> List[str]:
        """Gibt alle Quellen für die Übersicht zurück."""
        seen = set()
        result = []
        for s in self.global_sources:
            key = s.name
            if key not in seen:
                seen.add(key)
                result.append(str(s))
        return result
    
    def get_sources_summary(self) -> Dict[str, Any]:
        """Gibt Zusammenfassung der Quellen zurück."""
        by_type = {}
        for s in self.global_sources:
            by_type[s.type] = by_type.get(s.type, 0) + 1
        
        return {
            "total": len(set(s.name for s in self.global_sources)),
            "by_type": by_type,
            "slides_with_sources": len(self.sources)
        }
    
    def enrich_slides_with_sources(self, slides: List[Dict]) -> List[Dict]:
        """Fügt Quellen zu Slide-Dicts hinzu."""
        for i, slide in enumerate(slides):
            slide_id = slide.get('id', f'slide_{i}')
            sources = self.get_sources_for_slide(slide_id)
            if sources:
                slide['sources'] = sources
        return slides
    
    def to_json(self) -> str:
        """Exportiert alle Quellen als JSON."""
        return json.dumps({
            "sources": [s.to_dict() for s in self.global_sources],
            "by_slide": {k: [s.to_dict() for s in v] for k, v in self.sources.items()},
            "summary": self.get_sources_summary()
        }, indent=2)


# Global instance
_tracker = None

def get_source_tracker() -> SourceTracker:
    """Gibt globalen Source Tracker zurück."""
    global _tracker
    if _tracker is None:
        _tracker = SourceTracker()
    return _tracker

def new_source_tracker() -> SourceTracker:
    """Erstellt neuen Source Tracker (für neue Session)."""
    global _tracker
    _tracker = SourceTracker()
    return _tracker
