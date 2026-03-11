# -*- coding: utf-8 -*-
"""
services/deep_research.py
=========================
Deep Research Engine – aktive Web-Recherche für StratGen.

Ablauf:
  1. Suchanfragen generieren (LLM oder manuell)
  2. Web-Suche via Tavily (primär) oder DuckDuckGo (kostenloser Fallback)
  3. Seiten-Inhalte abrufen + bereinigen
  4. Quellenqualität bewerten
  5. Ergebnisse strukturieren für RAG-Ingest

Offline-Sicherheit:
  Alle externen Calls prüfen zuerst is_offline().
  Bei STRATGEN_OFFLINE=true sofortiger Abbruch mit offline_result().

Author: StratGen Sprint 5
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import re
import time
import uuid
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Generator, Optional

log = logging.getLogger(__name__)

# ── Offline Guard ────────────────────────────────────────────────────────────
try:
    from services.offline import is_offline, offline_result
except ImportError:
    def is_offline() -> bool:
        return os.getenv("STRATGEN_OFFLINE", "false").lower() == "true"
    def offline_result(service: str) -> dict:
        return {"ok": False, "error": f"offline_mode", "service": service}

# ── Konfiguration ─────────────────────────────────────────────────────────────
TAVILY_API_KEY    = os.getenv("TAVILY_API_KEY", "")
MAX_QUERIES       = int(os.getenv("RESEARCH_MAX_QUERIES", "10"))
MAX_RESULTS       = int(os.getenv("RESEARCH_MAX_RESULTS", "20"))
AUTO_INGEST       = os.getenv("RESEARCH_AUTO_INGEST", "true").lower() == "true"
SESSION_DIR       = Path(os.getenv("RESEARCH_SESSION_DIR", "data/research"))
SESSION_DIR.mkdir(parents=True, exist_ok=True)

# Qualitäts-Domains (erhöhen Score)
QUALITY_DOMAINS = {
    "statista.com", "mckinsey.com", "hbr.org", "bcg.com", "deloitte.com",
    "pwc.com", "gartner.com", "forrester.com", "reuters.com", "bloomberg.com",
    "ft.com", "economist.com", "forbes.com", "wikipedia.org", "arxiv.org",
    "oecd.org", "worldbank.org", "imf.org", "bundesbank.de", "destatis.de",
}

# ── Datenstrukturen ───────────────────────────────────────────────────────────
@dataclass
class ResearchResult:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    query: str = ""
    url: str = ""
    title: str = ""
    snippet: str = ""
    full_text: str = ""
    source_type: str = "web_page"   # web_page | news_article | wiki | academic
    domain: str = ""
    quality_score: float = 0.5      # 0.0 – 1.0
    retrieved_at: int = field(default_factory=lambda: int(time.time()))
    url_hash: str = ""

    def __post_init__(self):
        if self.url and not self.url_hash:
            self.url_hash = hashlib.sha1(self.url.encode()).hexdigest()
        if self.url and not self.domain:
            m = re.search(r"https?://(?:www\.)?([^/]+)", self.url)
            self.domain = m.group(1) if m else ""


@dataclass
class ResearchSession:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    topic: str = ""
    customer_name: str = ""
    queries: list[str] = field(default_factory=list)
    depth: str = "standard"          # quick | standard | deep
    language: str = "de"
    status: str = "created"          # created | running | done | failed | cancelled
    progress: int = 0                # 0–100
    queries_done: int = 0
    results: list[ResearchResult] = field(default_factory=list)
    ingested: bool = False
    ingest_count: int = 0
    error: Optional[str] = None
    created_at: int = field(default_factory=lambda: int(time.time()))
    finished_at: Optional[int] = None

    @property
    def result_count(self) -> int:
        return len(self.results)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["result_count"] = self.result_count
        return d


# ── Session Store ─────────────────────────────────────────────────────────────
def _session_path(session_id: str) -> Path:
    return SESSION_DIR / f"{session_id}.json"


def save_session(session: ResearchSession) -> None:
    _session_path(session.session_id).write_text(
        json.dumps(session.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def load_session(session_id: str) -> Optional[ResearchSession]:
    p = _session_path(session_id)
    if not p.exists():
        return None
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        results = [ResearchResult(**r) for r in data.pop("results", [])]
        data.pop("result_count", None)
        session = ResearchSession(**data)
        session.results = results
        return session
    except Exception as e:
        log.error("load_session %s: %s", session_id, e)
        return None


def list_sessions() -> list[dict]:
    sessions = []
    for p in sorted(SESSION_DIR.glob("*.json"), key=lambda x: x.stat().st_mtime, reverse=True):
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            sessions.append({
                "session_id": data.get("session_id"),
                "topic": data.get("topic"),
                "customer_name": data.get("customer_name"),
                "status": data.get("status"),
                "progress": data.get("progress", 0),
                "result_count": len(data.get("results", [])),
                "ingested": data.get("ingested", False),
                "created_at": data.get("created_at"),
            })
        except Exception:
            pass
    return sessions


# ── Query Generator ───────────────────────────────────────────────────────────
def generate_queries(topic: str, depth: str = "standard", language: str = "de") -> list[str]:
    """
    Generiert Suchanfragen aus einem Thema.
    Versucht LLM-Generierung, Fallback: regelbasiert.
    """
    n = {"quick": 3, "standard": 6, "deep": 10}.get(depth, 6)

    try:
        queries = _llm_generate_queries(topic, n, language)
        if queries:
            return queries[:MAX_QUERIES]
    except Exception as e:
        log.warning("LLM query generation failed: %s", e)

    # Regelbasierter Fallback
    base = topic.strip()
    queries = [base]
    if language == "de":
        queries += [
            f"{base} Marktanalyse",
            f"{base} Trends 2025",
            f"{base} Wettbewerber",
            f"{base} Statistiken",
            f"{base} Zukunft Prognose",
        ]
    else:
        queries += [
            f"{base} market analysis",
            f"{base} trends 2025",
            f"{base} competitors",
            f"{base} statistics",
            f"{base} future outlook",
        ]
    return queries[:n]


def _llm_generate_queries(topic: str, n: int, language: str) -> list[str]:
    """LLM generiert optimierte Suchanfragen."""
    import requests as req
    provider = os.getenv("LLM_PROVIDER", "ollama")
    model    = os.getenv("LLM_MODEL", "mistral")
    host     = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")

    lang_hint = "German" if language == "de" else "English"
    prompt = (
        f"Generate exactly {n} specific web search queries for researching the topic: \"{topic}\"\n"
        f"Language: {lang_hint}\n"
        f"Return ONLY a JSON array of strings, no explanation:\n"
        f"[\"query1\", \"query2\", ...]"
    )

    if provider == "ollama":
        r = req.post(f"{host}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False,
                  "options": {"num_predict": 300, "temperature": 0.3}},
            timeout=30)
        raw = r.json().get("response", "").strip()
    elif provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY", "")
        oai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        r = req.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": oai_model, "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": 300, "temperature": 0.3},
            timeout=30)
        raw = r.json()["choices"][0]["message"]["content"].strip()
    else:
        return []

    # JSON extrahieren
    m = re.search(r"\[.*?\]", raw, re.DOTALL)
    if m:
        return json.loads(m.group(0))
    return []


# ── Web Search ────────────────────────────────────────────────────────────────
def search_tavily(query: str, max_results: int = 5) -> list[dict]:
    """Tavily API – beste Qualität, braucht API-Key."""
    import requests as req
    r = req.post(
        "https://api.tavily.com/search",
        json={
            "api_key": TAVILY_API_KEY,
            "query": query,
            "search_depth": "basic",
            "max_results": max_results,
            "include_raw_content": False,
        },
        timeout=15
    )
    r.raise_for_status()
    data = r.json()
    return data.get("results", [])


def search_duckduckgo(query: str, max_results: int = 5, language: str = "de") -> list[dict]:
    """DuckDuckGo Suche via ddgs Library."""
    try:
        from ddgs import DDGS
    except ImportError:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            log.error("ddgs nicht installiert. Bitte: pip install ddgs")
            return []

    region = "de-de" if language == "de" else "en-us"
    try:
        with DDGS() as ddgs:
            raw = list(ddgs.text(query, region=region, max_results=max_results))
        return [{"url": r.get("href",""), "title": r.get("title",""), "content": r.get("body","")} for r in raw]
    except Exception as e:
        log.warning("DuckDuckGo search failed for '%s': %s", query, e)
        return []


def _fetch_page_text(url: str, timeout: int = 10) -> str:
    """Ruft Seiteinhalt ab und extrahiert lesbaren Text."""
    import requests as req
    try:
        headers = {"User-Agent": "StratGen/3.5 Research Bot"}
        r = req.get(url, headers=headers, timeout=timeout)
        r.raise_for_status()
        text = r.text
    except Exception:
        return ""

    # HTML bereinigen
    text = re.sub(r"(?is)<(script|style|nav|footer|header|aside)[^>]*>.*?</\1>", " ", text)
    text = re.sub(r"(?is)<[^>]+>", " ", text)
    text = re.sub(r"[\t\r\f]+", " ", text)
    text = re.sub(r" {2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()[:8000]  # max 8K Zeichen


def _score_result(url: str, title: str, snippet: str) -> tuple[float, str]:
    """Bewertet Qualität und Typ einer Quelle."""
    score = 0.4
    source_type = "web_page"

    domain = ""
    m = re.search(r"https?://(?:www\.)?([^/]+)", url)
    if m:
        domain = m.group(1).lower()

    # Domain-Qualität
    if any(d in domain for d in QUALITY_DOMAINS):
        score += 0.3
    elif any(ext in domain for ext in [".gov", ".edu", ".org"]):
        score += 0.2

    # Typ erkennen
    if "wikipedia" in domain:
        source_type = "wiki"
        score = min(score + 0.1, 0.85)
    elif any(w in url.lower() for w in ["news", "press", "article"]):
        source_type = "news_article"
    elif any(w in domain for w in ["arxiv", "pubmed", "scholar"]):
        source_type = "academic"
        score = min(score + 0.25, 0.95)

    # Titel-Qualität
    if title and len(title) > 20:
        score += 0.05
    if snippet and len(snippet) > 80:
        score += 0.05

    return round(min(score, 1.0), 3), source_type


# ── Hauptfunktion: Session ausführen ─────────────────────────────────────────
def run_session(session: ResearchSession) -> Generator[dict, None, None]:
    """
    Führt eine Research-Session aus.
    Generator – yield dict bei jedem Schritt für SSE-Streaming.
    Speichert Session nach jedem Query.
    """
    if is_offline():
        session.status = "failed"
        session.error = "Offline-Modus aktiv – Deep Research nicht verfügbar"
        save_session(session)
        yield {"type": "error", "message": session.error}
        return

    session.status = "running"
    session.progress = 0
    save_session(session)
    yield {"type": "status", "status": "running", "session_id": session.session_id}

    # Queries generieren falls leer
    if not session.queries:
        session.queries = generate_queries(session.topic, session.depth, session.language)
        save_session(session)

    yield {"type": "queries", "queries": session.queries, "count": len(session.queries)}

    total = len(session.queries)
    seen_hashes: set[str] = set()
    results_per_query = max(2, MAX_RESULTS // max(total, 1))

    use_tavily = bool(TAVILY_API_KEY)

    for i, query in enumerate(session.queries):
        if session.status == "cancelled":
            yield {"type": "cancelled"}
            return

        yield {"type": "query_start", "query": query, "index": i, "total": total}

        raw_results = []
        try:
            if use_tavily:
                raw_results = search_tavily(query, results_per_query)
            else:
                raw_results = search_duckduckgo(query, results_per_query, session.language)
        except Exception as e:
            log.warning("Search failed for '%s': %s", query, e)
            yield {"type": "query_error", "query": query, "error": str(e)}

        for raw in raw_results:
            url = raw.get("url", "")
            if not url:
                continue

            url_hash = hashlib.sha1(url.encode()).hexdigest()
            if url_hash in seen_hashes:
                continue
            seen_hashes.add(url_hash)

            title   = raw.get("title", "")
            snippet = raw.get("content", raw.get("snippet", ""))
            score, stype = _score_result(url, title, snippet)

            # Volltext nur bei deep oder standard + hoher Qualität
            full_text = ""
            if session.depth == "deep" or (session.depth == "standard" and score >= 0.6):
                full_text = _fetch_page_text(url)

            result = ResearchResult(
                query=query,
                url=url,
                title=title,
                snippet=snippet,
                full_text=full_text,
                source_type=stype,
                quality_score=score,
                url_hash=url_hash,
            )
            session.results.append(result)

            yield {
                "type": "result",
                "result": {
                    "id": result.id,
                    "url": result.url,
                    "title": result.title,
                    "snippet": result.snippet[:200],
                    "domain": result.domain,
                    "quality_score": result.quality_score,
                    "source_type": result.source_type,
                }
            }

        session.queries_done = i + 1
        session.progress = int(((i + 1) / total) * 100)
        save_session(session)
        yield {"type": "query_done", "query": query, "index": i,
               "progress": session.progress, "results_so_far": session.result_count}

    session.status = "done"
    session.finished_at = int(time.time())
    save_session(session)

    yield {
        "type": "done",
        "session_id": session.session_id,
        "result_count": session.result_count,
        "progress": 100,
        "auto_ingest": AUTO_INGEST,
    }

    # Auto-Ingest wenn konfiguriert
    if AUTO_INGEST and session.results:
        try:
            from services.research_ingest import ingest_session
            count = ingest_session(session)
            session.ingested = True
            session.ingest_count = count
            save_session(session)
            yield {"type": "ingested", "count": count}
        except Exception as e:
            log.error("Auto-ingest failed: %s", e)
            yield {"type": "ingest_error", "error": str(e)}
