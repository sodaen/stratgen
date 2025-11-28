# -*- coding: utf-8 -*-
import sys, re, sqlite3, os
from pathlib import Path

DB = Path("data/manifest.db"); ASSETS="assets"; FACTS="facts"

def is_real_pdf(path: Path) -> bool:
    try:
        with open(path, "rb") as f:
            head = f.read(5)
        return head.startswith(b"%PDF")
    except Exception:
        return False

def try_extract_text(path: Path) -> str:
    """
    Bevorzugt pdfminer, fällt sonst auf Plaintext zurück.
    Dadurch crashen pseudo-PDFs (umbenannte .txt) nicht.
    """
    # 1) echter PDF?
    if is_real_pdf(path):
        try:
            from pdfminer.high_level import extract_text
            t = extract_text(str(path)) or ""
            if t.strip():
                return t
        except Exception:
            pass
    # 2) Plaintext-Fallback (robust)
    try:
        data = path.read_bytes()
        try:
            return data.decode("utf-8", errors="ignore")
        except Exception:
            return data.decode("latin-1", errors="ignore")
    except Exception:
        return ""

METRIC_PATTERNS = [
    # CTR: 2,9%  | CTR %: 2.9
    (r"\bctr\b[:\s]+([\d.,]+)\s*%","ctr","%"),
    (r"\bctr\s*%[:\s]+([\d.,]+)","ctr","%"),
    # CPC/CAC/ROAS
    (r"\bcpc\b[:\s]+([\d.,]+)\s*(?:eur|€|usd|\$)?","cpc",None),
    (r"\bcac\b[:\s]+([\d.,]+)\s*(?:eur|€|usd|\$)?","cac",None),
    (r"\broas\b[:\s]+([\d.,]+)","roas",None),
    # Volumina
    (r"\bimpressions?\b[:\s]+([\d.,]+)","impressions",None),
    (r"\bclicks?\b[:\s]+([\d.,]+)","clicks",None),
    (r"\bspend\b[:\s]+([\d.,]+)\s*(?:eur|€|usd|\$)?","spend",None),
]

def upsert_asset(cur, path, customer="(unknown)", section="insights", tags="[]", atype="pdf"):
    cur.execute(f"SELECT id FROM {ASSETS} WHERE path=?",(path,))
    row = cur.fetchone()
    if row: return row[0]
    size = os.path.getsize(path) if os.path.exists(path) else 0
    cur.execute(f"""INSERT INTO {ASSETS}
        (customer,path,type,size,hash,tags,section_hint,topic_hint,source,created_at)
        VALUES(?,?,?,?,?,?,?,?,?,strftime('%s','now'))""",
        (customer, path, atype, size, None, tags, section, None, "pdf_to_facts"))
    return cur.lastrowid

def main(paths):
    if not DB.exists():
        print("[ERR] manifest.db fehlt – bitte Wave 1 zuerst"); sys.exit(1)
    con=sqlite3.connect(DB); cur=con.cursor()
    for p in paths:
        p=Path(p)
        if not p.exists():
            print(f"[skip] {p} fehlt"); 
            continue
        text = try_extract_text(p)
        text_low = text.lower()
        asset_id = upsert_asset(cur, str(p), section="insights", atype="pdf")
        rows=0
        for pat, metric, unit in METRIC_PATTERNS:
            m=re.search(pat, text_low)
            if not m: continue
            raw = m.group(1)
            try:
                # große Zahlen mit Punkten / Kommas tolerant
                if metric in ("impressions","clicks"):
                    v=float(str(raw).replace(".","").replace(",",".")) 
                else:
                    v=float(str(raw).replace(",",".")) 
            except:
                continue
            cur.execute(f"""INSERT INTO {FACTS}
                (asset_id,metric,value,unit,period_start,period_end,citation)
                VALUES(?,?,?,?,?,?,?)""",
                (asset_id, metric, v, unit, None, None, p.name))
            rows+=1
        con.commit()
        print(f"[ok] {p.name}: {rows} facts")
    con.close()

if __name__=="__main__":
    main(sys.argv[1:] or [])
