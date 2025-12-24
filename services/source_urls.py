"""
Mapping von Quellenkürzeln zu vollständigen URLs.
Wird für die Quellenfolie verwendet.
"""

SOURCE_URLS = {
    # Statistik-Portale
    "statista": "https://de.statista.com",
    "destatis": "https://www.destatis.de",
    
    # Wirtschaftspresse
    "faz": "https://www.faz.net",
    "handelsblatt": "https://www.handelsblatt.com",
    "horizont": "https://www.horizont.net",
    "wiwo": "https://www.wiwo.de",
    
    # Beratungen
    "mckinsey": "https://www.mckinsey.com/de",
    "bcg": "https://www.bcg.com/de-de",
    "bain": "https://www.bain.com/de",
    "deloitte": "https://www2.deloitte.com/de",
    "pwc": "https://www.pwc.de",
    "kpmg": "https://home.kpmg/de",
    "ey": "https://www.ey.com/de_de",
    
    # Tech-Analysten
    "gartner": "https://www.gartner.com/de",
    "forrester": "https://www.forrester.com",
    "idc": "https://www.idc.com/de",
    
    # Verbände & Institute
    "vdma": "https://www.vdma.org",
    "vdi": "https://www.vdi.de",
    "bitkom": "https://www.bitkom.org",
    "dihk": "https://www.dihk.de",
    "ihk": "https://www.ihk.de",
    "bdi": "https://bdi.eu",
    "fraunhofer": "https://www.fraunhofer.de",
    "idw": "https://idw-online.de",
    
    # Regierung & EU
    "bundesregierung": "https://www.bundesregierung.de",
    "bmwk": "https://www.bmwk.de",
    "eu-kommission": "https://ec.europa.eu/info/index_de",
    "eurostat": "https://ec.europa.eu/eurostat/de",
    
    # Nachhaltigkeit
    "umweltbundesamt": "https://www.umweltbundesamt.de",
    "bmu": "https://www.bmuv.de",
    
    # Branchenspezifisch
    "silicon": "https://www.silicon.de",
    "onlinemarketing": "https://onlinemarketing.de",
    "t3n": "https://t3n.de",
    "heise": "https://www.heise.de",
}

def get_source_url(source_name: str) -> str:
    """
    Gibt die URL für eine Quellenangabe zurück.
    
    Args:
        source_name: Name der Quelle (z.B. "Statista 2024", "McKinsey Report")
    
    Returns:
        URL oder leerer String wenn nicht gefunden
    """
    source_lower = source_name.lower()
    
    for key, url in SOURCE_URLS.items():
        if key in source_lower:
            return url
    
    return ""

def format_source_with_url(source_name: str) -> str:
    """
    Formatiert eine Quelle mit URL wenn verfügbar.
    
    Args:
        source_name: Name der Quelle
    
    Returns:
        Formatierter String: "Quelle (URL)" oder nur "Quelle"
    """
    url = get_source_url(source_name)
    if url:
        return f"{source_name} - {url}"
    return source_name

def enrich_sources(sources: list) -> list:
    """
    Reichert eine Liste von Quellen mit URLs an.
    
    Args:
        sources: Liste von Quellennamen
    
    Returns:
        Liste von angereicherten Quellen
    """
    return [format_source_with_url(s) for s in sources]
