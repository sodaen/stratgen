"""
STRATGEN Hybrid Search
Kombiniert BM25 (Keyword) + Vector (Semantic) für bessere Ergebnisse.
"""

import re
import math
from collections import Counter, defaultdict
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import hashlib


@dataclass
class SearchResult:
    """Ein Suchergebnis mit kombinierten Scores."""
    id: str
    text: str
    bm25_score: float
    vector_score: float
    hybrid_score: float
    payload: Dict


class BM25Index:
    """
    BM25 (Best Matching 25) Index für Keyword-Suche.
    Klassischer Information Retrieval Algorithmus.
    """
    
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1  # Term frequency saturation
        self.b = b    # Length normalization
        
        self.documents: Dict[str, str] = {}  # id -> text
        self.doc_lengths: Dict[str, int] = {}
        self.avg_doc_length: float = 0
        self.term_frequencies: Dict[str, Dict[str, int]] = {}  # term -> {doc_id -> count}
        self.doc_frequencies: Dict[str, int] = {}  # term -> num_docs_containing
        self.N: int = 0  # Total documents
        
        # Payload storage
        self.payloads: Dict[str, Dict] = {}
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenisiert Text in Wörter."""
        # Lowercase und nur alphanumerisch
        text = text.lower()
        tokens = re.findall(r'\b[a-zäöüß0-9]+\b', text)
        
        # Stopwords entfernen (deutsch + englisch)
        stopwords = {
            'der', 'die', 'das', 'und', 'oder', 'aber', 'ist', 'sind', 'war', 'waren',
            'ein', 'eine', 'einer', 'eines', 'für', 'mit', 'von', 'zu', 'auf', 'in',
            'an', 'bei', 'nach', 'über', 'unter', 'vor', 'durch', 'aus', 'um', 'als',
            'wenn', 'weil', 'dass', 'ob', 'wie', 'was', 'wer', 'wo', 'wann', 'warum',
            'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'was', 'were',
            'for', 'with', 'from', 'to', 'on', 'in', 'at', 'by', 'of', 'as',
            'if', 'because', 'that', 'which', 'who', 'what', 'where', 'when', 'why',
            'this', 'these', 'those', 'it', 'its', 'be', 'been', 'being', 'have', 'has',
            'auch', 'noch', 'schon', 'nur', 'mehr', 'kann', 'können', 'wird', 'werden',
            'ihre', 'ihrer', 'ihren', 'ihrem', 'sein', 'seine', 'seinen', 'seinem',
        }
        
        return [t for t in tokens if t not in stopwords and len(t) > 2]
    
    def add_document(self, doc_id: str, text: str, payload: Dict = None):
        """Fügt ein Dokument zum Index hinzu."""
        tokens = self._tokenize(text)
        
        self.documents[doc_id] = text
        self.doc_lengths[doc_id] = len(tokens)
        self.payloads[doc_id] = payload or {}
        
        # Term frequencies für dieses Dokument
        term_counts = Counter(tokens)
        
        for term, count in term_counts.items():
            if term not in self.term_frequencies:
                self.term_frequencies[term] = {}
            self.term_frequencies[term][doc_id] = count
            
            # Document frequency aktualisieren
            if term not in self.doc_frequencies:
                self.doc_frequencies[term] = 0
            # Nur erhöhen wenn das Dokument neu ist für diesen Term
            if doc_id not in self.term_frequencies[term] or self.term_frequencies[term][doc_id] == count:
                pass  # Already counted
        
        self.N = len(self.documents)
        self.avg_doc_length = sum(self.doc_lengths.values()) / max(self.N, 1)
    
    def build_from_qdrant(self, collection: str = "knowledge_base"):
        """Baut den Index aus einer Qdrant Collection."""
        from qdrant_client import QdrantClient
        
        client = QdrantClient(host="localhost", port=6333)
        
        # Hole alle Dokumente
        offset = None
        batch_size = 500
        
        while True:
            result = client.scroll(
                collection_name=collection,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False
            )
            
            points, offset = result
            
            for point in points:
                doc_id = str(point.id)
                text = point.payload.get("text", "")
                self.add_document(doc_id, text, point.payload)
            
            if offset is None or len(points) < batch_size:
                break
        
        # Berechne Document Frequencies korrekt
        for term, doc_dict in self.term_frequencies.items():
            self.doc_frequencies[term] = len(doc_dict)
        
        print(f"BM25 Index gebaut: {self.N} Dokumente, {len(self.term_frequencies)} unique Terms")
    
    def _idf(self, term: str) -> float:
        """Berechnet Inverse Document Frequency."""
        df = self.doc_frequencies.get(term, 0)
        if df == 0:
            return 0
        return math.log((self.N - df + 0.5) / (df + 0.5) + 1)
    
    def search(self, query: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        Sucht mit BM25.
        Returns: Liste von (doc_id, score) Tupeln.
        """
        query_tokens = self._tokenize(query)
        scores = defaultdict(float)
        
        for term in query_tokens:
            if term not in self.term_frequencies:
                continue
            
            idf = self._idf(term)
            
            for doc_id, tf in self.term_frequencies[term].items():
                doc_len = self.doc_lengths[doc_id]
                
                # BM25 Formel
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * doc_len / self.avg_doc_length)
                
                scores[doc_id] += idf * (numerator / denominator)
        
        # Sortiere nach Score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        return sorted_results[:top_k]


class HybridSearch:
    """
    Kombiniert BM25 und Vector Search für optimale Ergebnisse.
    """
    
    def __init__(self, 
                 bm25_weight: float = 0.3,
                 vector_weight: float = 0.7,
                 collection: str = "knowledge_base"):
        self.bm25_weight = bm25_weight
        self.vector_weight = vector_weight
        self.collection = collection
        
        # BM25 Index
        self.bm25 = BM25Index()
        self._index_built = False
    
    def build_index(self):
        """Baut den BM25 Index."""
        if not self._index_built:
            print(f"Baue BM25 Index für {self.collection}...")
            self.bm25.build_from_qdrant(self.collection)
            self._index_built = True
    
    def search(self, 
               query: str, 
               top_k: int = 10,
               bm25_candidates: int = 50,
               vector_candidates: int = 50) -> List[SearchResult]:
        """
        Führt Hybrid Search durch.
        
        1. BM25 holt Keyword-Matches
        2. Vector Search holt semantische Matches
        3. Scores werden kombiniert (RRF oder gewichtete Summe)
        """
        from services.rag_pipeline import get_embedding
        from qdrant_client import QdrantClient
        
        # Stelle sicher dass Index gebaut ist
        self.build_index()
        
        # 1. BM25 Search
        bm25_results = self.bm25.search(query, top_k=bm25_candidates)
        bm25_scores = {doc_id: score for doc_id, score in bm25_results}
        
        # Normalisiere BM25 Scores auf 0-1
        if bm25_scores:
            max_bm25 = max(bm25_scores.values())
            if max_bm25 > 0:
                bm25_scores = {k: v / max_bm25 for k, v in bm25_scores.items()}
        
        # 2. Vector Search
        client = QdrantClient(host="localhost", port=6333)
        query_embedding = get_embedding(query)
        
        vector_results = client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=vector_candidates,
            with_payload=True
        )
        
        vector_scores = {str(r.id): r.score for r in vector_results}
        vector_payloads = {str(r.id): r.payload for r in vector_results}
        
        # 3. Kombiniere Ergebnisse
        all_doc_ids = set(bm25_scores.keys()) | set(vector_scores.keys())
        
        combined_results = []
        for doc_id in all_doc_ids:
            bm25_score = bm25_scores.get(doc_id, 0)
            vector_score = vector_scores.get(doc_id, 0)
            
            # Gewichtete Kombination
            hybrid_score = (
                self.bm25_weight * bm25_score +
                self.vector_weight * vector_score
            )
            
            # Hole Payload
            if doc_id in vector_payloads:
                payload = vector_payloads[doc_id]
            else:
                payload = self.bm25.payloads.get(doc_id, {})
            
            combined_results.append(SearchResult(
                id=doc_id,
                text=payload.get("text", ""),
                bm25_score=bm25_score,
                vector_score=vector_score,
                hybrid_score=hybrid_score,
                payload=payload
            ))
        
        # Sortiere nach Hybrid Score
        combined_results.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        return combined_results[:top_k]
    
    def search_with_rrf(self, 
                        query: str, 
                        top_k: int = 10,
                        k: int = 60) -> List[SearchResult]:
        """
        Reciprocal Rank Fusion (RRF) - Alternative Kombinationsmethode.
        Oft besser als gewichtete Summe.
        
        RRF Score = Σ 1/(k + rank)
        """
        from services.rag_pipeline import get_embedding
        from qdrant_client import QdrantClient
        
        self.build_index()
        
        # 1. BM25 Rankings
        bm25_results = self.bm25.search(query, top_k=50)
        bm25_ranks = {doc_id: rank + 1 for rank, (doc_id, _) in enumerate(bm25_results)}
        
        # 2. Vector Rankings
        client = QdrantClient(host="localhost", port=6333)
        query_embedding = get_embedding(query)
        
        vector_results = client.search(
            collection_name=self.collection,
            query_vector=query_embedding,
            limit=50,
            with_payload=True
        )
        
        vector_ranks = {str(r.id): rank + 1 for rank, r in enumerate(vector_results)}
        vector_payloads = {str(r.id): r.payload for r in vector_results}
        
        # 3. RRF Scores berechnen
        all_doc_ids = set(bm25_ranks.keys()) | set(vector_ranks.keys())
        
        rrf_scores = {}
        for doc_id in all_doc_ids:
            rrf_score = 0
            
            if doc_id in bm25_ranks:
                rrf_score += 1 / (k + bm25_ranks[doc_id])
            
            if doc_id in vector_ranks:
                rrf_score += 1 / (k + vector_ranks[doc_id])
            
            rrf_scores[doc_id] = rrf_score
        
        # 4. Ergebnisse zusammenstellen
        combined_results = []
        for doc_id, rrf_score in rrf_scores.items():
            if doc_id in vector_payloads:
                payload = vector_payloads[doc_id]
            else:
                payload = self.bm25.payloads.get(doc_id, {})
            
            # Originale Scores für Analyse
            bm25_score = 1 / (k + bm25_ranks.get(doc_id, 1000)) if doc_id in bm25_ranks else 0
            vector_score = 1 / (k + vector_ranks.get(doc_id, 1000)) if doc_id in vector_ranks else 0
            
            combined_results.append(SearchResult(
                id=doc_id,
                text=payload.get("text", ""),
                bm25_score=bm25_score,
                vector_score=vector_score,
                hybrid_score=rrf_score,
                payload=payload
            ))
        
        combined_results.sort(key=lambda x: x.hybrid_score, reverse=True)
        
        return combined_results[:top_k]


# Singleton für Caching
_hybrid_search_instance: Optional[HybridSearch] = None


def get_hybrid_search(collection: str = "knowledge_base") -> HybridSearch:
    """Gibt eine gecachte HybridSearch Instanz zurück."""
    global _hybrid_search_instance
    
    if _hybrid_search_instance is None or _hybrid_search_instance.collection != collection:
        _hybrid_search_instance = HybridSearch(collection=collection)
    
    return _hybrid_search_instance


def hybrid_search(query: str, 
                  top_k: int = 10,
                  method: str = "rrf",
                  collection: str = "knowledge_base") -> List[Dict]:
    """
    Convenience Funktion für Hybrid Search.
    
    Args:
        query: Suchanfrage
        top_k: Anzahl Ergebnisse
        method: "rrf" oder "weighted"
        collection: Qdrant Collection
    
    Returns:
        Liste von Ergebnis-Dicts
    """
    searcher = get_hybrid_search(collection)
    
    if method == "rrf":
        results = searcher.search_with_rrf(query, top_k=top_k)
    else:
        results = searcher.search(query, top_k=top_k)
    
    return [
        {
            "id": r.id,
            "text": r.text,
            "score": r.hybrid_score,
            "bm25_score": r.bm25_score,
            "vector_score": r.vector_score,
            "source": r.payload.get("source_file", "unknown"),
            "payload": r.payload
        }
        for r in results
    ]
