"""
STRATGEN Re-Ranker Service
Verbessert Search-Scores durch LLM-basiertes Re-Ranking

Strategie:
1. Schnelle Vektor-Suche (Top 20)
2. LLM bewertet Relevanz (Top 5)
3. Optional: Cross-Encoder für Präzision
"""

import httpx
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import time
import re

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434"


@dataclass
class RankedResult:
    """Ein re-ranked Suchergebnis."""
    text: str
    original_score: float
    rerank_score: float
    final_score: float
    source: str
    metadata: Dict[str, Any]


class ReRanker:
    """
    LLM-basierter Re-Ranker für bessere Suchergebnisse.
    """
    
    def __init__(self, model: str = "mistral:latest"):
        self.model = model
        self.client = httpx.Client(timeout=30.0)
    
    def rerank(self, 
               query: str, 
               results: List[Dict[str, Any]], 
               top_k: int = 5) -> List[RankedResult]:
        """
        Re-ranked Suchergebnisse basierend auf LLM-Bewertung.
        
        Args:
            query: Die ursprüngliche Suchanfrage
            results: Liste von Qdrant-Ergebnissen
            top_k: Anzahl der finalen Ergebnisse
        
        Returns:
            Liste von RankedResult, sortiert nach final_score
        """
        if not results:
            return []
        
        start = time.time()
        ranked = []
        
        for result in results[:20]:  # Max 20 für Re-Ranking
            payload = result.payload if hasattr(result, 'payload') else result.get('payload', {})
            text = payload.get('text', payload.get('content', ''))[:1000]  # Limit für LLM
            original_score = result.score if hasattr(result, 'score') else result.get('score', 0)
            
            # LLM-Bewertung
            rerank_score = self._score_relevance(query, text)
            
            # Kombinierter Score (gewichtet)
            final_score = 0.4 * original_score + 0.6 * rerank_score
            
            ranked.append(RankedResult(
                text=text,
                original_score=original_score,
                rerank_score=rerank_score,
                final_score=final_score,
                source=payload.get('source_file', 'unknown'),
                metadata=payload
            ))
        
        # Sortieren nach final_score
        ranked.sort(key=lambda x: x.final_score, reverse=True)
        
        latency = (time.time() - start) * 1000
        logger.info(f"Re-ranking completed in {latency:.0f}ms for {len(results)} results")
        
        return ranked[:top_k]
    
    def _score_relevance(self, query: str, text: str) -> float:
        """
        Bewertet die Relevanz eines Texts für eine Query.
        
        Returns:
            Score zwischen 0.0 und 1.0
        """
        prompt = f"""Bewerte die Relevanz des folgenden Textes für die Suchanfrage.
Antworte NUR mit einer Zahl zwischen 0 und 10 (0 = nicht relevant, 10 = perfekt relevant).

Suchanfrage: {query}

Text: {text[:800]}

Relevanz-Score (0-10):"""

        try:
            response = self.client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.1,
                        "num_predict": 10
                    }
                }
            )
            
            if response.status_code == 200:
                answer = response.json().get("response", "").strip()
                # Extrahiere Zahl
                match = re.search(r'(\d+(?:\.\d+)?)', answer)
                if match:
                    score = float(match.group(1))
                    return min(score / 10.0, 1.0)  # Normalisieren auf 0-1
            
            return 0.5  # Fallback
            
        except Exception as e:
            logger.error(f"Re-rank scoring failed: {e}")
            return 0.5


class FastReRanker:
    """
    Schnellerer Re-Ranker ohne LLM-Calls.
    Nutzt Keyword-Matching und BM25-ähnliche Scores.
    """
    
    def rerank(self,
               query: str,
               results: List[Dict[str, Any]],
               top_k: int = 5) -> List[RankedResult]:
        """
        Schnelles Re-Ranking basierend auf Keyword-Overlap.
        """
        query_words = set(query.lower().split())
        ranked = []
        
        for result in results:
            payload = result.payload if hasattr(result, 'payload') else result.get('payload', {})
            text = payload.get('text', payload.get('content', '')).lower()
            original_score = result.score if hasattr(result, 'score') else result.get('score', 0)
            
            # Keyword Overlap Score
            text_words = set(text.split())
            overlap = len(query_words & text_words)
            keyword_score = overlap / max(len(query_words), 1)
            
            # Exact Phrase Bonus
            phrase_bonus = 0.1 if query.lower() in text else 0
            
            # Kombinierter Score
            rerank_score = min(keyword_score + phrase_bonus, 1.0)
            final_score = 0.7 * original_score + 0.3 * rerank_score
            
            ranked.append(RankedResult(
                text=payload.get('text', '')[:500],
                original_score=original_score,
                rerank_score=rerank_score,
                final_score=final_score,
                source=payload.get('source_file', 'unknown'),
                metadata=payload
            ))
        
        ranked.sort(key=lambda x: x.final_score, reverse=True)
        return ranked[:top_k]


def search_with_rerank(query: str, 
                       collection: str = "knowledge_base",
                       limit: int = 5,
                       use_llm: bool = True) -> Dict[str, Any]:
    """
    Führt Suche mit Re-Ranking durch.
    
    Args:
        query: Suchanfrage
        collection: Qdrant Collection
        limit: Anzahl Ergebnisse
        use_llm: LLM-basiertes Re-Ranking (langsamer aber besser)
    
    Returns:
        Dict mit results, scores, latencies
    """
    from qdrant_client import QdrantClient
    
    start = time.time()
    
    # 1. Embedding erstellen
    emb_start = time.time()
    resp = httpx.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": query},
        timeout=30.0
    )
    embedding = resp.json().get("embedding", [])
    emb_latency = (time.time() - emb_start) * 1000
    
    # 2. Vektor-Suche (Top 20 für Re-Ranking)
    search_start = time.time()
    client = QdrantClient(host="localhost", port=6333)
    vector_results = client.search(
        collection_name=collection,
        query_vector=embedding,
        limit=20  # Mehr für Re-Ranking
    )
    search_latency = (time.time() - search_start) * 1000
    
    # 3. Re-Ranking
    rerank_start = time.time()
    if use_llm:
        ranker = ReRanker()
    else:
        ranker = FastReRanker()
    
    ranked_results = ranker.rerank(query, vector_results, top_k=limit)
    rerank_latency = (time.time() - rerank_start) * 1000
    
    total_latency = (time.time() - start) * 1000
    
    # Berechne Score-Verbesserung
    original_avg = sum(r.original_score for r in ranked_results) / max(len(ranked_results), 1)
    final_avg = sum(r.final_score for r in ranked_results) / max(len(ranked_results), 1)
    improvement = final_avg - original_avg
    
    return {
        "query": query,
        "results": [
            {
                "text": r.text,
                "source": r.source,
                "original_score": round(r.original_score, 3),
                "rerank_score": round(r.rerank_score, 3),
                "final_score": round(r.final_score, 3)
            }
            for r in ranked_results
        ],
        "scores": {
            "original_avg": round(original_avg, 3),
            "final_avg": round(final_avg, 3),
            "improvement": round(improvement, 3)
        },
        "latency": {
            "embedding_ms": round(emb_latency),
            "search_ms": round(search_latency),
            "rerank_ms": round(rerank_latency),
            "total_ms": round(total_latency)
        },
        "config": {
            "use_llm": use_llm,
            "collection": collection
        }
    }


if __name__ == "__main__":
    # Test
    print("=== Re-Ranker Test ===\n")
    
    query = "Marketing Strategie für B2B SaaS"
    
    print(f"Query: {query}\n")
    
    # Fast Re-Ranking
    print("--- Fast Re-Ranking (no LLM) ---")
    result = search_with_rerank(query, use_llm=False)
    print(f"Original Avg Score: {result['scores']['original_avg']}")
    print(f"Final Avg Score: {result['scores']['final_avg']}")
    print(f"Improvement: {result['scores']['improvement']:+.3f}")
    print(f"Total Latency: {result['latency']['total_ms']}ms")
    
    print("\n--- LLM Re-Ranking ---")
    result = search_with_rerank(query, use_llm=True)
    print(f"Original Avg Score: {result['scores']['original_avg']}")
    print(f"Final Avg Score: {result['scores']['final_avg']}")
    print(f"Improvement: {result['scores']['improvement']:+.3f}")
    print(f"Total Latency: {result['latency']['total_ms']}ms")
    
    print("\nTop 3 Results:")
    for i, r in enumerate(result['results'][:3]):
        print(f"{i+1}. [{r['final_score']:.3f}] {r['source']}: {r['text'][:80]}...")
