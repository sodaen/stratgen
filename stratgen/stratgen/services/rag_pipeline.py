from typing import Dict, Any

# Platzhalter für spätere RAG-Implementierung (LlamaIndex + Qdrant + Ollama)
def generate_sections(payload: Dict[str, Any]) -> list[str]:
    """
    Nimmt Formulardaten entgegen und liefert Abschnittstitel (MVP).
    Später: echte Inhalte via Retrieval + LLM.
    """
    base = [
        "Executive Summary",
        "Markt & Kategorie",
        "Zielgruppe & Archetypen",
        "Brand Narrative",
        "Kanäle & Content",
        "Maßnahmenplan",
        "KPIs",
        "Roadmap",
        "Budgetrahmen",
    ]
    return base
