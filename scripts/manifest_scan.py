# -*- coding: utf-8 -*-
from __future__ import annotations
import os, re, json, csv, hashlib, time, uuid, sqlite3, zipfile, io
from pathlib import Path
from typing import Dict, Any, List, Optional

ROOT = Path(".").resolve()
DB = ROOT / "data" / "manifest.db"
JSON_OUT = ROOT / "data" / "manifest.json"
RAW_DIR = ROOT / "data" / "raw" / "uploads"
SAMPLES = ROOT / "samples" / "wave1_upload_demo"

def sha256_file(p: Path) -> str:
    h=hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1<<20), b""):
            h.update(chunk)
    return h.hexdigest()

def parse_filename_hints(name: str) -> Dict[str, Any]:
    """
    Unterstützt zwei Modi:
    1) Explizit: section=insights topic=gtm kpi=cac unit=EUR period=2024H1 tags=[paid,search] -- filename.ext
    2) Heuristik: insights_[paid].pdf, kpis_paid_2024H1.csv, logo_brand.png
    """
    base = name
    hints: Dict[str, Any] = {"tags": []}

    # Explizites Muster vor " -- "
    if " -- " in base:
        left, _right = base.split(" -- ", 1)
        for token in left.split():
            if "=" in token:
                k,v = token.split("=",1)
                if k=="tags" and v.startswith("[") and v.endswith("]"):
                    # naive JSON-ähnlich -> Liste
                    v=v.strip("[]")
                    tags=[t.strip().strip(",") for t in v.split(",") if t.strip()]
                    hints["tags"] = tags
                else:
                    hints[k] = v
    else:
        # Heuristiken
        low = base.lower()
        if low.startswith("insights"):
            hints["section_hint"]="insights"
        if "kpi" in low or "kpis" in low:
            hints["section_hint"]="kpis"
        if "logo" in low or "brand" in low:
            hints["section_hint"]="visual"
            hints["tags"] = list(set(hints.get("tags",[])+["logo"]))
        m=re.search(r"\[(.*?)\]", base)
        if m:
            tags=[t.strip() for t in m.group(1).split(",") if t.strip()]
            hints["tags"] = list(set(hints.get("tags",[])+tags))
        m2=re.search(r"(20\d{2}(H[12]|Q[1-4])?)", base)
        if m2:
            hints["period"]=m2.group(1)
    return hints

def detect_type(p: Path) -> str:
    ext = p.suffix.lower()
    if ext in {".csv",".tsv",".xlsx"}: return "table"
    if ext in {".txt",".md"}: return "text"
    if ext in {".pdf"}: return "pdf"
    if ext in {".png",".jpg",".jpeg",".webp",".svg"}: return "image"
    return "file"

def read_csv_facts(p: Path) -> List[Dict[str,Any]]:
    facts=[]
    try:
        with p.open("r", encoding="utf-8", errors="ignore") as f:
            # Auto-Delimiter
            sample = f.read(4096); f.seek(0)
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t") if sample else csv.excel
            reader = csv.DictReader(f, dialect=dialect)
            rows = list(reader)
            # einfache Heuristik: jede numerische Zelle wird als fact erfasst
            for row in rows:
                period = row.get("period") or row.get("date") or row.get("month") or row.get("year")
                for k,v in row.items():
                    if v is None: 
                        continue
                    sv=str(v).strip().replace(",",".")
                    try:
                        val=float(sv)
                    except Exception:
                        continue
                    unit=None
                    lk=k.lower()
                    if any(u in lk for u in ["ctr","rate","%"]): unit="%"
                    if "eur" in lk or "€" in lk: unit="EUR"
                    facts.append({
                        "metric": k,
                        "value": val,
                        "unit": unit,
                        "period_start": period,
                        "period_end": period,
                        "citation": str(p)
                    })
    except Exception:
        pass
    return facts

def iter_bundle(path: Path):
    """liefert (virt_path, data_bytes) aus einem ZIP, sonst None"""
    if path.suffix.lower()!=".zip": 
        return None
    try:
        with zipfile.ZipFile(path, "r") as z:
            for n in z.namelist():
                if n.endswith("/"): 
                    continue
                yield n, z.read(n)
    except Exception:
        return None

def upsert(con, table, key, row):
    cols=sorted(row.keys())
    placeholders=",".join(["?"]*len(cols))
    updates=",".join([f"{c}=excluded.{c}" for c in cols if c!=key])
    sql=f"INSERT INTO {table} ({','.join(cols)}) VALUES ({placeholders}) ON CONFLICT({key}) DO UPDATE SET {updates}"
    con.execute(sql, [row[c] for c in cols])

def ensure_uuid() -> str:
    return str(uuid.uuid4())

def scan_paths(paths: List[Path], customer: str="Acme GmbH"):
    con=sqlite3.connect(DB)
    con.execute("PRAGMA journal_mode=WAL;")
    assets=[]
    facts_all=[]
    for p in paths:
        if not p.exists(): continue

        # ZIP-Bundle?
        bundle = iter_bundle(p) if p.is_file() else None
        if bundle:
            for n, data in bundle:
                virt = Path(n)
                name = virt.name
                tmp = Path("assets_tmp")/("unz_"+hashlib.md5((str(p)+n).encode()).hexdigest()+virt.suffix)
                tmp.parent.mkdir(parents=True, exist_ok=True)
                try:
                    with tmp.open("wb") as f: f.write(data)
                except Exception:
                    continue
                file_path = tmp
                file_type = detect_type(file_path)
                hints = parse_filename_hints(name)
                size = file_path.stat().st_size
                aid = ensure_uuid()
                aset = {
                    "id": aid,
                    "customer": customer,
                    "path": str(file_path),
                    "name": name,
                    "type": file_type,
                    "size": size,
                    "hash": sha256_file(file_path),
                    "tags": json.dumps(hints.get("tags",[]), ensure_ascii=False),
                    "section_hint": hints.get("section_hint"),
                    "topic_hint": hints.get("topic_hint"),
                    "source": str(p),
                    "created_at": time.time(),
                }
                upsert(con,"assets","id",aset)
                assets.append(aset)
                # Facts aus CSV
                if file_type=="table" and file_path.suffix.lower()==".csv":
                    for fct in read_csv_facts(file_path):
                        fid=ensure_uuid()
                        row={"id":fid,"asset_id":aid,**fct}
                        upsert(con,"facts","id",row)
                        facts_all.append(row)
        else:
            # einzelnes File/Ordner scannen
            scan_list=[]
            if p.is_dir():
                for root,_,files in os.walk(p):
                    for fn in files:
                        scan_list.append(Path(root)/fn)
            else:
                scan_list=[p]

            for file_path in scan_list:
                name=file_path.name
                file_type=detect_type(file_path)
                hints=parse_filename_hints(name)
                try:
                    size=file_path.stat().st_size
                except Exception:
                    size=None
                aid=ensure_uuid()
                aset={
                    "id": aid,
                    "customer": customer,
                    "path": str(file_path),
                    "name": name,
                    "type": file_type,
                    "size": size,
                    "hash": sha256_file(file_path) if file_path.is_file() else None,
                    "tags": json.dumps(hints.get("tags",[]), ensure_ascii=False),
                    "section_hint": hints.get("section_hint"),
                    "topic_hint": hints.get("topic_hint"),
                    "source": "scan",
                    "created_at": time.time(),
                }
                upsert(con,"assets","id",aset)
                assets.append(aset)
                if file_type=="table" and file_path.suffix.lower()==".csv":
                    for fct in read_csv_facts(file_path):
                        fid=ensure_uuid()
                        row={"id":fid,"asset_id":aid,**fct}
                        upsert(con,"facts","id",row)
                        facts_all.append(row)
    con.commit(); con.close()
    # JSON Export (vereinfachte Sicht)
    JSON_OUT.parent.mkdir(parents=True, exist_ok=True)
    with JSON_OUT.open("w", encoding="utf-8") as f:
        json.dump({"assets":assets,"facts":facts_all}, f, ensure_ascii=False, indent=2)
    print(f"[ok] manifest: {JSON_OUT}  (assets={len(assets)}, facts={len(facts_all)})")

if __name__=="__main__":
    # Standard-Scan: samples + letzte Uploads (Ordner & ZIP)
    paths=[]
    if SAMPLES.exists(): paths.append(SAMPLES)
    if RAW_DIR.exists():
        for fn in sorted(RAW_DIR.glob("*"), key=lambda p:p.stat().st_mtime, reverse=True)[:20]:
            paths.append(fn)
    # manuelle Zusatzpfade via ENV
    extra=os.environ.get("MANIFEST_SCAN_EXTRA","").strip()
    if extra:
        for part in extra.split(":"):
            if part: paths.append(Path(part))
    # init schema falls nötig
    os.system("bash scripts/manifest_init.sh >/dev/null 2>&1 || true")
    scan_paths(paths)
