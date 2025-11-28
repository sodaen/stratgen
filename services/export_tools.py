from __future__ import annotations
import subprocess, shutil, json, zipfile, os
from pathlib import Path
from typing import Optional, Dict, Any, List

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXPORT_DIR   = PROJECT_ROOT / "data/exports"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

def has_soffice() -> bool:
    return shutil.which("soffice") is not None

def to_pdf(pptx_path: str, out_dir: Optional[str] = None, timeout: int = 60) -> str:
    """Konvertiert PPTX -> PDF via LibreOffice (headless)."""
    if not has_soffice():
        raise RuntimeError("LibreOffice (soffice) nicht gefunden. Bitte 'sudo apt install -y libreoffice' ausführen.")
    in_path = Path(pptx_path).resolve()
    if not in_path.exists():
        raise FileNotFoundError(str(in_path))
    out = Path(out_dir).resolve() if out_dir else EXPORT_DIR
    out.mkdir(parents=True, exist_ok=True)
    cmd = [
        "soffice",
        "--headless", "--invisible", "--nologo", "--nodefault", "--nolockcheck", "--norestore",
        "--convert-to", "pdf:impress_pdf_Export",
        "--outdir", str(out),
        str(in_path)
    ]
    subprocess.run(cmd, check=True, timeout=timeout)
    pdf_path = out / (in_path.stem + ".pdf")
    if not pdf_path.exists():
        raise RuntimeError(f"PDF wurde nicht erzeugt: {pdf_path}")
    return str(pdf_path)

def _write_json(path: Path, obj: Any):
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")

def make_bundle(
    base_name: str,
    pptx_path: str,
    pdf_path: Optional[str] = None,
    agenda: Optional[Any] = None,
    content_map: Optional[Dict[str, Dict[str, Any]]] = None,
    sources: Optional[List[str]] = None,
    extra_files: Optional[List[str]] = None
) -> str:
    """Erzeugt ZIP-Bundle in data/exports/: <base>.zip"""
    base = "".join(c if c.isalnum() or c in "-_." else "_" for c in base_name)
    zip_path = EXPORT_DIR / f"{base}.zip"
    tmp_json_agenda = EXPORT_DIR / f"{base}_agenda.json"
    tmp_json_content = EXPORT_DIR / f"{base}_content.json"
    tmp_json_sources = EXPORT_DIR / f"{base}_sources.json"

    if agenda is not None: _write_json(tmp_json_agenda, agenda)
    if content_map is not None: _write_json(tmp_json_content, content_map)
    if sources is not None: _write_json(tmp_json_sources, sources)

    with zipfile.ZipFile(str(zip_path), "w", compression=zipfile.ZIP_DEFLATED) as z:
        # PPTX & PDF
        if pptx_path and Path(pptx_path).exists():
            z.write(pptx_path, arcname=Path(pptx_path).name)
        if pdf_path and Path(pdf_path).exists():
            z.write(pdf_path, arcname=Path(pdf_path).name)
        # JSONs
        if tmp_json_agenda.exists():  z.write(tmp_json_agenda, arcname=tmp_json_agenda.name)
        if tmp_json_content.exists(): z.write(tmp_json_content, arcname=tmp_json_content.name)
        if tmp_json_sources.exists(): z.write(tmp_json_sources, arcname=tmp_json_sources.name)
        # Extra Dateien (z. B. generierte Bilder)
        for p in (extra_files or []):
            pp = Path(p)
            if pp.exists() and pp.is_file():
                z.write(pp, arcname=pp.name)

    # Aufräumen temporärer JSONs
    for p in [tmp_json_agenda, tmp_json_content, tmp_json_sources]:
        if p.exists():
            try: p.unlink()
            except Exception: pass

    return str(zip_path)
