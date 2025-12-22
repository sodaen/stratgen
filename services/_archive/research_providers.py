from typing import List, Dict, Any

def fetch_from_urls(urls: List[str]) -> List[Dict[str, Any]]:
    # TODO: echte Fetch- & Parsing-Pipeline (Readability, Boilerplate-Removal, Chunking)
    return [{"type":"url","url":u,"status":"stub"} for u in urls]

def fetch_from_providers(providers: List[str], topic: str, customer: str) -> List[Dict[str, Any]]:
    # TODO: echte Integrationen (Brandwatch, Talkwalker, Statista, ...)
    return [{"type":"provider","provider":p,"topic":topic,"customer":customer,"status":"stub"} for p in providers]
