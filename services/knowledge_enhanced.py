# -*- coding: utf-8 -*-
"""
services/knowledge_enhanced.py
==============================
Stufe 2: Knowledge Enhancement

Features:
1. Multi-Source RAG (Knowledge Base + Templates + Web)
2. Fact Extraction & Verification
3. Citation Management
4. Intelligent Query Expansion
5. Context-Aware Retrieval
6. Source Quality Scoring

Author: StratGen Agent V3.1
"""
from __future__ import annotations
import os
import re
import json
import hashlib
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime

# ============================================
# CONFIGURATION
# ============================================

KNOWLEDGE_DIR = os.getenv("STRATGEN_KNOWLEDGE_DIR", "data/knowledge")
RAW_DIR = os.getenv("STRATGEN_RAW_DIR", "data/raw")
UPLOADS_DIR = os.getenv("STRATGEN_UPLOADS_DIR", "data/uploads")
CACHE_DIR = os.getenv("STRATGEN_CACHE_DIR", "data/cache")

# Quality thresholds
MIN_RELEVANCE_SCORE = 0.3
MIN_FACT_CONFIDENCE = 0.6
MAX_SOURCES_PER_SLIDE = 3
MAX_FACTS_PER_QUERY = 10

# ============================================
# DATA CLASSES
# ============================================

@dataclass
class Fact:
    """Ein extrahierter Fakt."""
    text: str
    fact_type: str = "claim"  # claim, number, date, quote
    confidence: float = 0.7
    source_path: str = ""
    source_title: str = ""
    verification_status: str = "unverified"  # unverified, verified, disputed
    extracted_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Citation:
    """Eine Quellenangabe."""
    index: int
    source_path: str
    source_title: str
    snippet: str = ""
    page: Optional[int] = None
    url: Optional[str] = None


@dataclass
class SearchResult:
    """Ein Suchergebnis."""
    path: str
    title: str
    snippet: str
    score: float
    source_type: str  # knowledge, template, upload, web
    facts: List[Fact] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ResearchContext:
    """Gesammelter Research-Kontext für eine Slide-Generierung."""
    query: str
    results: List[SearchResult] = field(default_factory=list)
    facts: List[Fact] = field(default_factory=list)
    citations: List[Citation] = field(default_factory=list)
    query_expansions: List[str] = field(default_factory=list)
    total_sources: int = 0
    search_duration_ms: int = 0


# ============================================
# IMPORTS - Internal Services
# ============================================

# Knowledge Base Search
try:
    from services.knowledge import search as kb_search, scan_dir as kb_scan
    HAS_KNOWLEDGE = True
except ImportError:
    kb_search = None
    HAS_KNOWLEDGE = False

# Template Learner
try:
    from services.template_learner import (
        find_similar_slides,
        get_slide_examples,
        scan_templates
    )
    HAS_TEMPLATE_LEARNER = True
except ImportError:
    HAS_TEMPLATE_LEARNER = False

# LLM for Query Expansion & Fact Extraction
try:
    from services.llm import generate as llm_generate, is_enabled as llm_enabled
    HAS_LLM = True
except ImportError:
    llm_generate = None
    HAS_LLM = False


# ============================================
# QUERY EXPANSION
# ============================================

def expand_query(query: str, context: Dict[str, Any] = None) -> List[str]:
    """
    Erweitert eine Suchanfrage um verwandte Begriffe.
    
    Args:
        query: Ursprüngliche Suchanfrage
        context: Zusätzlicher Kontext (topic, industry, etc.)
    
    Returns:
        Liste von erweiterten Queries
    """
    expansions = [query]
    
    # Kontext-basierte Erweiterungen
    if context:
        if context.get("industry"):
            expansions.append(f"{query} {context['industry']}")
        if context.get("topic"):
            expansions.append(f"{context['topic']} {query}")
        if context.get("customer_name"):
            expansions.append(f"{query} Unternehmen")
    
    # LLM-basierte Erweiterung (wenn verfügbar)
    if HAS_LLM and llm_enabled and llm_enabled():
        try:
            prompt = f"""Generiere 3 alternative Suchbegriffe für diese Anfrage:
"{query}"

Kontext: {json.dumps(context or {}, ensure_ascii=False)[:200]}

Gib nur die Suchbegriffe zurück, einen pro Zeile, ohne Nummerierung."""

            result = llm_generate(prompt, max_tokens=100)
            if result.get("ok"):
                text = result.get("response", "")
                for line in text.strip().split("\n"):
                    line = line.strip().strip("-").strip("•").strip()
                    if line and line != query and len(line) > 3:
                        expansions.append(line)
        except Exception:
            pass
    
    # Deduplizieren und begrenzen
    seen = set()
    unique = []
    for q in expansions:
        q_lower = q.lower().strip()
        if q_lower not in seen and q_lower:
            seen.add(q_lower)
            unique.append(q)
    
    return unique[:5]


# ============================================
# MULTI-SOURCE SEARCH
# ============================================

def search_knowledge_base(query: str, k: int = 5) -> List[SearchResult]:
    """Sucht in der Knowledge Base (data/knowledge)."""
    results = []
    
    if not HAS_KNOWLEDGE or not kb_search:
        return results
    
    try:
        search_result = kb_search(query, limit=k, semantic=1)
        if search_result.get("ok"):
            for item in search_result.get("results", []):
                path = item.get("path", "")
                results.append(SearchResult(
                    path=path,
                    title=item.get("title") or Path(path).stem if path else "Unbekannt",
                    snippet=item.get("snippet", "")[:400],
                    score=item.get("score", 0.5),
                    source_type="knowledge",
                    metadata={"original": item}
                ))
    except Exception as e:
        pass
    
    return results


def search_templates(query: str, k: int = 3) -> List[SearchResult]:
    """Sucht in gelernten Templates (data/raw)."""
    results = []
    
    if not HAS_TEMPLATE_LEARNER:
        return results
    
    try:
        # Ähnliche Slides finden
        similar = find_similar_slides(query, k=k)
        if similar.get("ok"):
            for item in similar.get("slides", []):
                results.append(SearchResult(
                    path=item.get("source_file", ""),
                    title=item.get("title", "Template Slide"),
                    snippet="\n".join(item.get("bullets", [])[:3]),
                    score=item.get("similarity", 0.5),
                    source_type="template",
                    metadata={
                        "slide_type": item.get("type"),
                        "bullet_count": len(item.get("bullets", []))
                    }
                ))
    except Exception:
        pass
    
    return results


def search_uploads(query: str, k: int = 3) -> List[SearchResult]:
    """Sucht in hochgeladenen Dateien (data/uploads)."""
    results = []
    
    uploads_path = Path(UPLOADS_DIR)
    if not uploads_path.exists():
        return results
    
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    for file_path in uploads_path.glob("*"):
        if file_path.is_file():
            filename = file_path.name.lower()
            
            # Simple keyword matching
            score = 0.0
            for word in query_words:
                if word in filename:
                    score += 0.3
            
            # Content-based matching für Textdateien
            if file_path.suffix in [".txt", ".md", ".csv"]:
                try:
                    content = file_path.read_text(encoding="utf-8")[:2000].lower()
                    for word in query_words:
                        if word in content:
                            score += 0.2
                except Exception:
                    pass
            
            if score >= MIN_RELEVANCE_SCORE:
                results.append(SearchResult(
                    path=str(file_path),
                    title=file_path.stem,
                    snippet=f"Uploaded file: {file_path.name}",
                    score=min(1.0, score),
                    source_type="upload",
                    metadata={"size": file_path.stat().st_size}
                ))
    
    # Nach Score sortieren
    results.sort(key=lambda x: x.score, reverse=True)
    return results[:k]


def multi_source_search(
    query: str,
    context: Dict[str, Any] = None,
    sources: List[str] = None,
    k: int = 5
) -> ResearchContext:
    """
    Führt Multi-Source-Suche durch.
    
    Args:
        query: Suchanfrage
        context: Zusätzlicher Kontext
        sources: Liste der zu durchsuchenden Quellen ["knowledge", "templates", "uploads"]
        k: Anzahl der Ergebnisse pro Quelle
    
    Returns:
        ResearchContext mit allen Ergebnissen
    """
    t0 = time.time()
    
    if sources is None:
        sources = ["knowledge", "templates", "uploads"]
    
    research = ResearchContext(query=query)
    
    # Query erweitern
    research.query_expansions = expand_query(query, context)
    
    all_results = []
    
    # Für jede Query-Variante suchen
    for q in research.query_expansions[:3]:
        # Knowledge Base
        if "knowledge" in sources:
            kb_results = search_knowledge_base(q, k=k)
            all_results.extend(kb_results)
        
        # Templates
        if "templates" in sources:
            template_results = search_templates(q, k=min(k, 3))
            all_results.extend(template_results)
        
        # Uploads
        if "uploads" in sources:
            upload_results = search_uploads(q, k=min(k, 3))
            all_results.extend(upload_results)
    
    # Deduplizieren nach Pfad
    seen_paths = set()
    unique_results = []
    for r in all_results:
        if r.path not in seen_paths:
            seen_paths.add(r.path)
            unique_results.append(r)
    
    # Nach Score sortieren
    unique_results.sort(key=lambda x: x.score, reverse=True)
    
    # Top-K behalten
    research.results = unique_results[:k * 2]
    research.total_sources = len(research.results)
    research.search_duration_ms = int((time.time() - t0) * 1000)
    
    return research


# ============================================
# FACT EXTRACTION
# ============================================

def extract_facts_from_text(text: str, source_path: str = "", source_title: str = "") -> List[Fact]:
    """
    Extrahiert verifizierbare Fakten aus einem Text.
    
    Args:
        text: Der zu analysierende Text
        source_path: Pfad zur Quelle
        source_title: Titel der Quelle
    
    Returns:
        Liste extrahierter Fakten
    """
    facts = []
    
    if not text or len(text) < 20:
        return facts
    
    # Regel-basierte Extraktion (schnell, kein LLM nötig)
    
    # Zahlen mit Kontext
    number_patterns = [
        r'(\d+(?:[.,]\d+)?)\s*(?:%|Prozent|Euro|EUR|USD|\$|Mio\.?|Mrd\.?)',
        r'(?:etwa|ca\.?|rund|über|unter)\s*(\d+(?:[.,]\d+)?)',
        r'(\d{4})\s*(?:wurde|war|ist)',  # Jahreszahlen
    ]
    
    for pattern in number_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            context_start = max(0, match.start() - 50)
            context_end = min(len(text), match.end() + 50)
            context = text[context_start:context_end].strip()
            
            facts.append(Fact(
                text=context,
                fact_type="number",
                confidence=0.7,
                source_path=source_path,
                source_title=source_title
            ))
    
    # Aussagen mit Signalwörtern
    claim_patterns = [
        r'(?:zeigt|belegt|beweist|ergab|fand)[^.]{10,100}\.',
        r'(?:Studie|Untersuchung|Analyse|Report)[^.]{10,100}\.',
        r'(?:laut|gemäß|nach)[^.]{10,100}\.',
    ]
    
    for pattern in claim_patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            facts.append(Fact(
                text=match.group().strip(),
                fact_type="claim",
                confidence=0.6,
                source_path=source_path,
                source_title=source_title
            ))
    
    # LLM-basierte Extraktion (wenn verfügbar und Text lang genug)
    if HAS_LLM and llm_enabled and llm_enabled() and len(text) > 200:
        try:
            prompt = f"""Extrahiere die wichtigsten faktischen Aussagen aus diesem Text.
Gib maximal 5 Fakten zurück, jeweils in einer Zeile.
Nur verifizierbare Aussagen, keine Meinungen.

Text:
{text[:1500]}

Fakten:"""

            result = llm_generate(prompt, max_tokens=300)
            if result.get("ok"):
                response = result.get("response", "")
                for line in response.strip().split("\n"):
                    line = line.strip().strip("-").strip("•").strip()
                    if line and len(line) > 20:
                        facts.append(Fact(
                            text=line,
                            fact_type="claim",
                            confidence=0.8,
                            source_path=source_path,
                            source_title=source_title
                        ))
        except Exception:
            pass
    
    # Deduplizieren
    seen = set()
    unique_facts = []
    for f in facts:
        f_hash = hashlib.md5(f.text.lower().encode()).hexdigest()[:16]
        if f_hash not in seen:
            seen.add(f_hash)
            unique_facts.append(f)
    
    return unique_facts[:MAX_FACTS_PER_QUERY]


def extract_facts_from_results(results: List[SearchResult]) -> List[Fact]:
    """Extrahiert Fakten aus allen Suchergebnissen."""
    all_facts = []
    
    for result in results:
        # Aus Snippet
        snippet_facts = extract_facts_from_text(
            result.snippet,
            source_path=result.path,
            source_title=result.title
        )
        all_facts.extend(snippet_facts)
        result.facts = snippet_facts
        
        # Aus Datei (für Textdateien)
        if result.source_type in ["knowledge", "upload"]:
            file_path = Path(result.path)
            if file_path.exists() and file_path.suffix in [".txt", ".md"]:
                try:
                    content = file_path.read_text(encoding="utf-8")[:3000]
                    file_facts = extract_facts_from_text(
                        content,
                        source_path=result.path,
                        source_title=result.title
                    )
                    all_facts.extend(file_facts)
                except Exception:
                    pass
    
    return all_facts[:MAX_FACTS_PER_QUERY * 2]


# ============================================
# CITATION MANAGEMENT
# ============================================

class CitationManager:
    """Verwaltet Quellenangaben für eine Präsentation."""
    
    def __init__(self):
        self.citations: Dict[str, Citation] = {}  # path -> Citation
        self.counter = 0
    
    def add_source(self, path: str, title: str, snippet: str = "") -> int:
        """
        Fügt eine Quelle hinzu und gibt den Citation-Index zurück.
        
        Args:
            path: Pfad zur Quelle
            title: Titel der Quelle
            snippet: Relevanter Textausschnitt
        
        Returns:
            Citation-Index (1-basiert)
        """
        if path in self.citations:
            return self.citations[path].index
        
        self.counter += 1
        self.citations[path] = Citation(
            index=self.counter,
            source_path=path,
            source_title=title,
            snippet=snippet[:200]
        )
        return self.counter
    
    def get_citation_marker(self, path: str) -> str:
        """Gibt den Citation-Marker für einen Pfad zurück."""
        if path in self.citations:
            return f"[{self.citations[path].index}]"
        return ""
    
    def format_citation(self, index: int) -> str:
        """Formatiert eine einzelne Citation."""
        for citation in self.citations.values():
            if citation.index == index:
                return f"[{index}] {citation.source_title}"
        return f"[{index}]"
    
    def generate_references_slide(self) -> Dict[str, Any]:
        """
        Generiert Slide-Content für die Quellen-Seite.
        
        Returns:
            Slide-Dictionary mit type, title, bullets
        """
        if not self.citations:
            return None
        
        bullets = []
        for citation in sorted(self.citations.values(), key=lambda c: c.index):
            source_name = citation.source_title or Path(citation.source_path).stem
            bullets.append(f"[{citation.index}] {source_name}")
        
        return {
            "type": "references",
            "title": "Quellen",
            "bullets": bullets[:15],  # Max 15 Quellen pro Slide
            "layout_hint": "Title and Content",
            "notes": "Alle verwendeten Quellen für diese Präsentation."
        }
    
    def get_all_citations(self) -> List[Dict[str, Any]]:
        """Gibt alle Citations als Liste von Dicts zurück."""
        return [asdict(c) for c in sorted(self.citations.values(), key=lambda c: c.index)]
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialisiert den CitationManager."""
        return {
            "count": self.counter,
            "citations": self.get_all_citations()
        }


# ============================================
# CONTEXT-AWARE RESEARCH
# ============================================

def research_for_slide(
    slide_type: str,
    slide_title: str,
    brief: str,
    context: Dict[str, Any] = None,
    citation_manager: CitationManager = None
) -> Dict[str, Any]:
    """
    Führt kontextbezogene Recherche für einen spezifischen Slide durch.
    
    Args:
        slide_type: Typ des Slides (problem, solution, roi, etc.)
        slide_title: Titel des Slides
        brief: Das Projekt-Briefing
        context: Zusätzlicher Kontext
        citation_manager: Optionaler CitationManager für Quellenangaben
    
    Returns:
        Dictionary mit facts, suggestions, citations
    """
    result = {
        "facts": [],
        "suggestions": [],
        "citations": [],
        "source_count": 0
    }
    
    # Query basierend auf Slide-Typ konstruieren
    type_queries = {
        "problem": f"{slide_title} Herausforderung Problem",
        "solution": f"{slide_title} Lösung Ansatz",
        "roi": f"ROI Business Case Kosten Nutzen {context.get('industry', '')}",
        "competitive": f"Wettbewerb Markt {context.get('industry', '')}",
        "risks": f"Risiken Herausforderungen {context.get('topic', '')}",
        "kpis": f"KPI Metriken Kennzahlen {context.get('industry', '')}",
        "personas": f"Zielgruppe Persona {context.get('industry', '')}",
    }
    
    query = type_queries.get(slide_type, f"{slide_title} {brief[:100]}")
    
    # Multi-Source-Suche
    research = multi_source_search(
        query=query,
        context=context,
        sources=["knowledge", "templates"],
        k=5
    )
    
    # Fakten extrahieren
    facts = extract_facts_from_results(research.results)
    result["facts"] = [asdict(f) for f in facts[:5]]
    result["source_count"] = research.total_sources
    
    # Citations hinzufügen
    if citation_manager:
        for res in research.results[:MAX_SOURCES_PER_SLIDE]:
            if res.score >= MIN_RELEVANCE_SCORE:
                idx = citation_manager.add_source(
                    path=res.path,
                    title=res.title,
                    snippet=res.snippet
                )
                result["citations"].append(idx)
    
    # Suggestions aus Template-Beispielen
    for res in research.results:
        if res.source_type == "template" and res.metadata.get("slide_type") == slide_type:
            result["suggestions"].append({
                "type": "template_example",
                "title": res.title,
                "bullets": res.snippet.split("\n")[:3]
            })
    
    return result


def build_research_context(
    topic: str,
    brief: str,
    slide_types: List[str],
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Baut den gesamten Research-Kontext für eine Präsentation.
    
    Args:
        topic: Hauptthema
        brief: Projekt-Briefing
        slide_types: Liste der geplanten Slide-Typen
        context: Zusätzlicher Kontext
    
    Returns:
        Dictionary mit research pro Slide-Typ und globalem Kontext
    """
    citation_manager = CitationManager()
    
    result = {
        "topic": topic,
        "slides": {},
        "global_facts": [],
        "citations": [],
        "total_sources": 0
    }
    
    # Globale Recherche
    global_research = multi_source_search(
        query=f"{topic} {brief[:200]}",
        context=context,
        k=10
    )
    
    global_facts = extract_facts_from_results(global_research.results)
    result["global_facts"] = [asdict(f) for f in global_facts]
    
    # Citations für globale Quellen
    for res in global_research.results[:5]:
        citation_manager.add_source(res.path, res.title, res.snippet)
    
    # Recherche pro Slide-Typ
    for slide_type in slide_types:
        slide_research = research_for_slide(
            slide_type=slide_type,
            slide_title=slide_type.replace("_", " ").title(),
            brief=brief,
            context=context,
            citation_manager=citation_manager
        )
        result["slides"][slide_type] = slide_research
        result["total_sources"] += slide_research["source_count"]
    
    # Finale Citations
    result["citations"] = citation_manager.to_dict()
    result["references_slide"] = citation_manager.generate_references_slide()
    
    return result


# ============================================
# API FUNCTIONS
# ============================================

def search(
    query: str,
    k: int = 5,
    sources: List[str] = None,
    context: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Hauptfunktion für Knowledge-Suche.
    
    Args:
        query: Suchanfrage
        k: Anzahl Ergebnisse
        sources: Quellen (knowledge, templates, uploads)
        context: Zusätzlicher Kontext
    
    Returns:
        Dictionary mit results, facts, query_expansions
    """
    research = multi_source_search(
        query=query,
        context=context,
        sources=sources,
        k=k
    )
    
    # Fakten extrahieren
    facts = extract_facts_from_results(research.results)
    
    return {
        "ok": True,
        "query": query,
        "query_expansions": research.query_expansions,
        "results": [
            {
                "path": r.path,
                "title": r.title,
                "snippet": r.snippet,
                "score": r.score,
                "source_type": r.source_type,
                "facts": [asdict(f) for f in r.facts]
            }
            for r in research.results
        ],
        "facts": [asdict(f) for f in facts],
        "total_sources": research.total_sources,
        "duration_ms": research.search_duration_ms
    }


def get_facts_for_topic(topic: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Sammelt alle relevanten Fakten zu einem Thema.
    
    Args:
        topic: Das Thema
        context: Zusätzlicher Kontext
    
    Returns:
        Dictionary mit facts, sources, citations
    """
    research = multi_source_search(
        query=topic,
        context=context,
        k=10
    )
    
    facts = extract_facts_from_results(research.results)
    
    citation_manager = CitationManager()
    for res in research.results[:10]:
        if res.score >= MIN_RELEVANCE_SCORE:
            citation_manager.add_source(res.path, res.title, res.snippet)
    
    return {
        "ok": True,
        "topic": topic,
        "facts": [asdict(f) for f in facts],
        "sources": [r.path for r in research.results],
        "citations": citation_manager.to_dict()
    }


def check_status() -> Dict[str, Any]:
    """Gibt den Status der Knowledge-Services zurück."""
    return {
        "ok": True,
        "services": {
            "knowledge_base": HAS_KNOWLEDGE,
            "template_learner": HAS_TEMPLATE_LEARNER,
            "llm": HAS_LLM and (llm_enabled() if llm_enabled else False)
        },
        "directories": {
            "knowledge": Path(KNOWLEDGE_DIR).exists(),
            "raw": Path(RAW_DIR).exists(),
            "uploads": Path(UPLOADS_DIR).exists()
        },
        "config": {
            "min_relevance_score": MIN_RELEVANCE_SCORE,
            "min_fact_confidence": MIN_FACT_CONFIDENCE,
            "max_sources_per_slide": MAX_SOURCES_PER_SLIDE
        }
    }
