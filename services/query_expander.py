"""
STRATGEN Query Expander
Erweitert Suchanfragen mit Synonymen und verwandten Begriffen.
"""

import httpx
import logging
from typing import List, Set
import re

logger = logging.getLogger(__name__)

OLLAMA_URL = "http://localhost:11434"

# Statische Synonyme für schnelle Expansion
SYNONYMS = {
    "marketing": ["werbung", "vermarktung", "promotion", "advertising"],
    "strategie": ["plan", "konzept", "ansatz", "methode", "vorgehen"],
    "analyse": ["untersuchung", "auswertung", "bewertung", "evaluation"],
    "kunde": ["klient", "abnehmer", "käufer", "consumer", "customer"],
    "zielgruppe": ["target audience", "personas", "kundensegment"],
    "content": ["inhalt", "material", "beitrag"],
    "social media": ["soziale medien", "social networks", "soziale netzwerke"],
    "b2b": ["business-to-business", "geschäftskunden"],
    "b2c": ["business-to-consumer", "endkunden", "privatkunden"],
    "roi": ["return on investment", "rendite", "ertrag"],
    "kpi": ["kennzahl", "metrik", "leistungsindikator"],
    "lead": ["interessent", "potentieller kunde", "kontakt"],
    "conversion": ["konvertierung", "umwandlung"],
    "branding": ["markenbildung", "markenaufbau", "brand building"],
    "seo": ["suchmaschinenoptimierung", "search engine optimization"],
    "campaign": ["kampagne", "aktion", "maßnahme"],
}


class QueryExpander:
    """Erweitert Suchanfragen für bessere Ergebnisse."""
    
    def __init__(self, use_llm: bool = False):
        self.use_llm = use_llm
    
    def expand(self, query: str) -> str:
        """
        Erweitert eine Query mit Synonymen.
        
        Args:
            query: Ursprüngliche Suchanfrage
            
        Returns:
            Erweiterte Query
        """
        words = query.lower().split()
        expanded_terms: Set[str] = set(words)
        
        # Statische Synonyme hinzufügen
        for word in words:
            if word in SYNONYMS:
                expanded_terms.update(SYNONYMS[word])
            # Auch Teilmatches prüfen
            for key, syns in SYNONYMS.items():
                if key in word or word in key:
                    expanded_terms.update(syns)
        
        # LLM-basierte Expansion (optional)
        if self.use_llm:
            llm_terms = self._llm_expand(query)
            expanded_terms.update(llm_terms)
        
        # Kombinierte Query erstellen
        # Original Query bleibt am Anfang für höhere Gewichtung
        expanded = query + " " + " ".join(expanded_terms - set(words))
        
        logger.info(f"Query expanded: '{query}' -> '{expanded[:100]}...'")
        return expanded
    
    def _llm_expand(self, query: str) -> List[str]:
        """Nutzt LLM für Query Expansion."""
        prompt = f"""Gib 5 verwandte Suchbegriffe für folgende Anfrage.
Antworte NUR mit den Begriffen, getrennt durch Kommas.

Anfrage: {query}

Verwandte Begriffe:"""

        try:
            resp = httpx.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": "mistral:latest",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.3, "num_predict": 50}
                },
                timeout=10.0
            )
            
            if resp.status_code == 200:
                answer = resp.json().get("response", "")
                terms = [t.strip().lower() for t in answer.split(",")]
                return [t for t in terms if len(t) > 2 and len(t) < 30]
        
        except Exception as e:
            logger.error(f"LLM expansion failed: {e}")
        
        return []
    
    def get_search_variants(self, query: str, max_variants: int = 3) -> List[str]:
        """
        Generiert verschiedene Such-Varianten.
        
        Returns:
            Liste von Query-Varianten
        """
        variants = [query]  # Original zuerst
        
        # Variante 1: Mit Synonymen
        expanded = self.expand(query)
        if expanded != query:
            variants.append(expanded)
        
        # Variante 2: Nur Kernbegriffe (ohne Stoppwörter)
        stopwords = {'für', 'und', 'oder', 'mit', 'bei', 'von', 'zu', 'der', 'die', 'das', 'ein', 'eine'}
        core_words = [w for w in query.lower().split() if w not in stopwords]
        if core_words and len(core_words) < len(query.split()):
            variants.append(" ".join(core_words))
        
        return variants[:max_variants]


def enhanced_search(query: str, 
                    collection: str = "knowledge_base",
                    limit: int = 5,
                    expand_query: bool = True) -> dict:
    """
    Suche mit Query Expansion.
    """
    from qdrant_client import QdrantClient
    import time
    
    start = time.time()
    
    # Query Expansion
    if expand_query:
        expander = QueryExpander(use_llm=False)  # Schnelle statische Expansion
        expanded_query = expander.expand(query)
    else:
        expanded_query = query
    
    # Embedding
    resp = httpx.post(
        f"{OLLAMA_URL}/api/embeddings",
        json={"model": "nomic-embed-text", "prompt": expanded_query},
        timeout=30.0
    )
    embedding = resp.json().get("embedding", [])
    
    # Suche
    client = QdrantClient(host="localhost", port=6333)
    results = client.search(
        collection_name=collection,
        query_vector=embedding,
        limit=limit
    )
    
    latency = (time.time() - start) * 1000
    
    return {
        "original_query": query,
        "expanded_query": expanded_query,
        "results": [
            {
                "score": r.score,
                "text": r.payload.get("text", "")[:300],
                "source": r.payload.get("source_file", "unknown")
            }
            for r in results
        ],
        "avg_score": sum(r.score for r in results) / max(len(results), 1),
        "latency_ms": round(latency)
    }


if __name__ == "__main__":
    print("=== Query Expander Test ===\n")
    
    expander = QueryExpander()
    
    test_queries = [
        "Marketing Strategie",
        "B2B Kunde",
        "Social Media ROI"
    ]
    
    for q in test_queries:
        expanded = expander.expand(q)
        print(f"Original: {q}")
        print(f"Expanded: {expanded[:80]}...")
        print()
    
    print("=== Enhanced Search Test ===\n")
    result = enhanced_search("Marketing Strategie für B2B")
    print(f"Query: {result['original_query']}")
    print(f"Expanded: {result['expanded_query'][:60]}...")
    print(f"Avg Score: {result['avg_score']:.3f}")
    print(f"Latency: {result['latency_ms']}ms")
