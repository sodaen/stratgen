"""
STRATGEN Query Optimizer
Verbessert Suchanfragen für höhere Relevanz-Scores.
"""

from typing import List, Dict, Tuple
import re
import httpx


# Umfangreiche Synonym-Tabelle für Marketing/Business
SYNONYMS = {
    # Marketing
    "marketing": ["vermarktung", "werbung", "promotion", "absatzförderung"],
    "werbung": ["marketing", "anzeigen", "ads", "promotion"],
    "kampagne": ["campaign", "aktion", "maßnahme", "initiative"],
    "content": ["inhalt", "inhalte", "beiträge", "material"],
    "social media": ["soziale medien", "social networks", "social"],
    
    # Strategie
    "strategie": ["strategy", "plan", "konzept", "ansatz", "vorgehen"],
    "framework": ["rahmenwerk", "modell", "struktur", "template", "vorlage"],
    "analyse": ["analysis", "untersuchung", "auswertung", "bewertung"],
    "optimierung": ["optimization", "verbesserung", "enhancement"],
    
    # Business
    "b2b": ["business-to-business", "geschäftskunden", "firmenkunden"],
    "b2c": ["business-to-consumer", "endkunden", "privatkunden"],
    "saas": ["software-as-a-service", "cloud software", "subscription software"],
    "startup": ["gründung", "neugründung", "jungunternehmen"],
    
    # KPIs & Metrics
    "kpi": ["kennzahl", "metrik", "leistungsindikator", "key performance indicator"],
    "roi": ["return on investment", "rendite", "kapitalrendite"],
    "conversion": ["konversion", "umwandlung", "konvertierung"],
    "ctr": ["click-through-rate", "klickrate"],
    "cac": ["customer acquisition cost", "kundenakquisitionskosten"],
    "ltv": ["lifetime value", "kundenlebenswert", "clv"],
    
    # Zielgruppe
    "zielgruppe": ["target audience", "zielmarkt", "kundensegment"],
    "persona": ["kundenprofil", "buyer persona", "zielgruppenprofil"],
    "kunde": ["customer", "client", "käufer", "abnehmer"],
    
    # Kanäle
    "email": ["e-mail", "newsletter", "mailing"],
    "seo": ["suchmaschinenoptimierung", "search engine optimization"],
    "sem": ["suchmaschinenmarketing", "search engine marketing"],
    "ppc": ["pay-per-click", "paid search", "bezahlte suche"],
    
    # Produkt
    "produkt": ["product", "angebot", "lösung"],
    "feature": ["funktion", "merkmal", "eigenschaft"],
    "benefit": ["nutzen", "vorteil", "mehrwert"],
    "usp": ["unique selling proposition", "alleinstellungsmerkmal"],
    
    # Vertrieb
    "vertrieb": ["sales", "verkauf", "absatz"],
    "funnel": ["trichter", "verkaufstrichter", "sales funnel"],
    "lead": ["interessent", "kontakt", "potentieller kunde"],
    "pipeline": ["vertriebspipeline", "sales pipeline"],
    
    # Positionierung
    "positionierung": ["positioning", "marktpositionierung"],
    "brand": ["marke", "branding", "markenführung"],
    "wettbewerb": ["competition", "konkurrenz", "mitbewerber"],
}

# Verwandte Konzepte (semantische Erweiterung)
RELATED_CONCEPTS = {
    "marketing strategie": ["go-to-market", "marketingplan", "marketingkonzept"],
    "content marketing": ["inbound marketing", "content strategie", "storytelling"],
    "social media marketing": ["influencer marketing", "community management"],
    "email marketing": ["marketing automation", "newsletter strategie", "drip campaign"],
    "seo": ["content optimierung", "keyword recherche", "backlinks"],
    "conversion": ["landing page", "call-to-action", "user experience"],
    "b2b marketing": ["account based marketing", "lead generation", "demand generation"],
    "b2c marketing": ["retail marketing", "consumer marketing", "direct-to-consumer"],
    "brand": ["corporate identity", "brand awareness", "brand equity"],
    "analytics": ["web analytics", "marketing analytics", "data-driven marketing"],
}


def expand_query_synonyms(query: str) -> str:
    """
    Erweitert Query mit Synonymen.
    Fügt relevante Synonyme in Klammern hinzu für bessere Matches.
    """
    query_lower = query.lower()
    expansions = []
    
    for term, synonyms in SYNONYMS.items():
        if term in query_lower:
            # Füge 1-2 relevante Synonyme hinzu
            relevant_syns = [s for s in synonyms[:2] if s not in query_lower]
            expansions.extend(relevant_syns)
    
    # Prüfe auch related concepts
    for concept, related in RELATED_CONCEPTS.items():
        if all(word in query_lower for word in concept.split()):
            expansions.extend(related[:2])
    
    if expansions:
        # Dedupliziere und limitiere
        unique_expansions = list(dict.fromkeys(expansions))[:5]
        return f"{query} ({' '.join(unique_expansions)})"
    
    return query


def expand_query_llm(query: str, context: str = "marketing") -> str:
    """
    Erweitert Query mit LLM für semantisch reichere Suche.
    """
    try:
        prompt = f"""Du bist ein Such-Optimierer. Erweitere diese Suchanfrage mit 3-5 relevanten Begriffen.
Kontext: {context}
Original: {query}

Antworte NUR mit der erweiterten Suchanfrage, keine Erklärungen.
Beispiel: "Marketing Strategie" → "Marketing Strategie Konzept Plan Maßnahmen Zielgruppe"
"""
        
        response = httpx.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 50}
            },
            timeout=10.0
        )
        
        if response.status_code == 200:
            expanded = response.json().get("response", "").strip()
            # Bereinige
            expanded = expanded.replace('"', '').replace("'", "")
            if len(expanded) > len(query) and len(expanded) < 200:
                return expanded
    except:
        pass
    
    return query


def optimize_query(query: str, 
                   use_synonyms: bool = True,
                   use_llm: bool = False,
                   use_stemming: bool = True) -> Dict:
    """
    Vollständige Query-Optimierung.
    
    Returns:
        Dict mit original, optimized, expansions
    """
    result = {
        "original": query,
        "optimized": query,
        "expansions": [],
        "methods_used": []
    }
    
    current = query
    
    # 1. Synonym-Expansion
    if use_synonyms:
        expanded = expand_query_synonyms(current)
        if expanded != current:
            result["methods_used"].append("synonyms")
            result["expansions"].append(f"Synonyms: {expanded}")
            current = expanded
    
    # 2. LLM-Expansion (optional, langsamer)
    if use_llm:
        llm_expanded = expand_query_llm(query)
        if llm_expanded != query:
            result["methods_used"].append("llm")
            result["expansions"].append(f"LLM: {llm_expanded}")
            # Kombiniere
            current = f"{current} {llm_expanded}"
    
    # 3. Stemming/Normalisierung
    if use_stemming:
        # Einfaches Stemming: Entferne typische Endungen
        words = current.split()
        stemmed = []
        for word in words:
            w = word.lower()
            # Deutsche Endungen
            for ending in ['ung', 'heit', 'keit', 'tion', 'ieren', 'lich', 'isch']:
                if w.endswith(ending) and len(w) > len(ending) + 3:
                    stemmed.append(w[:-len(ending)])
                    break
            else:
                stemmed.append(w)
        
        if stemmed != [w.lower() for w in words]:
            result["methods_used"].append("stemming")
    
    result["optimized"] = current
    
    return result


def get_query_variants(query: str, num_variants: int = 3) -> List[str]:
    """
    Generiert mehrere Varianten einer Query für Multi-Query Search.
    """
    variants = [query]
    
    # Variante 1: Mit Synonymen
    syn_expanded = expand_query_synonyms(query)
    if syn_expanded != query:
        variants.append(syn_expanded)
    
    # Variante 2: Umformulierung
    words = query.split()
    if len(words) > 2:
        # Reihenfolge ändern
        variants.append(" ".join(reversed(words)))
    
    # Variante 3: Keyword-Extraktion
    keywords = [w for w in words if len(w) > 3 and w.lower() not in 
                {'für', 'mit', 'und', 'oder', 'der', 'die', 'das', 'ein', 'eine'}]
    if keywords:
        variants.append(" ".join(keywords))
    
    return variants[:num_variants]
