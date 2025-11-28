import glob, os
from pathlib import Path

RAW_DIR = "data/raw"

def main():
    files = glob.glob(os.path.join(RAW_DIR, "*"))
    if not files:
        print("Keine Dateien in data/raw gefunden. Bitte Strategien (.pptx/.docx/.pdf) ablegen.")
        return
    print("Gefundene Dateien:")
    for f in files:
        p = Path(f)
        print(f"- {p.name} ({p.stat().st_size/1024:.1f} KB)")
    print("\n(Nächster Schritt: Unstructured-Parsing + Qdrant-Upsert hinzufügen.)")

if __name__ == "__main__":
    main()
