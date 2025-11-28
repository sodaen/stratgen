# -*- coding: utf-8 -*-
import sys, os, json, re, sqlite3
from pathlib import Path

DB = Path("data/manifest.db")
ASSETS="assets"; FACTS="facts"

def ensure_schema(cur):
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {ASSETS}(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer TEXT, path TEXT, name TEXT, type TEXT,
        size INTEGER, hash TEXT, tags TEXT,
        section_hint TEXT, topic_hint TEXT, source TEXT,
        created_at REAL
    )""")
    cur.execute(f"""CREATE TABLE IF NOT EXISTS {FACTS}(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asset_id TEXT, metric TEXT, value REAL, unit TEXT,
        period_start TEXT, period_end TEXT, citation TEXT
    )""")

def upsert_asset(cur, path:str)->int:
    p=Path(path)
    cur.execute(f"SELECT id FROM {ASSETS} WHERE path=?", (str(p),))
    row=cur.fetchone()
    if row: return int(row[0])
    cur.execute(f"INSERT INTO {ASSETS}(customer,path,name,type,size,tags,source,created_at) VALUES(?,?,?,?,?,?,?,strftime('%s','now'))",
                ("(unknown)", str(p), p.name, "pdf", p.stat().st_size if p.exists() else None, "[]", "pdf_tables_to_facts"))
    return cur.lastrowid

def parse_period(cell:str)->str|None:
    if not cell: return None
    s=str(cell).strip()
    # 2024Q1, 2024-Q2, Q2 2024, 2024 H1, 2024H1
    if re.match(r"^\d{4}\s*Q[1-4]$", s, re.I): return s.replace(" ","").upper()
    m=re.match(r"^(\d{4})\s*-\s*Q([1-4])$", s, re.I)
    if m: return f"{m.group(1)}Q{m.group(2)}"
    m=re.match(r"^Q([1-4])\s*(\d{4})$", s, re.I)
    if m: return f"{m.group(2)}Q{m.group(1)}"
    m=re.match(r"^(\d{4})\s*H([12])$", s, re.I)
    if m: return f"{m.group(1)}H{m.group(2)}"
    m=re.match(r"^(\d{4})H([12])$", s, re.I)
    if m: return f"{m.group(1)}H{m.group(2)}"
    return None

def canon_metric(h:str)->tuple[str,str|None]:
    s=h.strip().lower()
    s = s.replace(" ", "").replace("-", "")
    if "ctr" in s: return ("ctr", "%")
    if "cpc" in s: return ("cpc", "eur" if "€" in h or "eur" in h.lower() else None)
    if "cac" in s: return ("cac", "eur" if "€" in h or "eur" in h.lower() else None)
    if "roas" in s: return ("roas", None)
    if "impressions" in s or "impr" in s: return ("impressions", None)
    if "clicks" in s: return ("clicks", None)
    return (re.sub(r"[^a-z0-9_]+","", s) or "value", None)

def try_float(v):
    if v is None: return None
    if isinstance(v,(int,float)): return float(v)
    s=str(v).strip().replace("%","").replace("€","").replace(",",".")
    try: return float(s)
    except: return None

def extract_tables_one(pdf_path:Path)->list[dict]:
    try:
        import pdfplumber
    except Exception:
        return []
    if not pdf_path.exists(): return []
    out=[]
    with pdfplumber.open(str(pdf_path)) as pdf:
        for page in pdf.pages:
            tables=page.extract_tables()
            for t in tables or []:
                # normalize rows
                rows=[[ (c if c is not None else "").strip() for c in r] for r in t if any(c not in (None,"") for c in r)]
                if not rows: continue
                # header = first non-numeric row
                header = rows[0]
                data   = rows[1:] if len(rows)>1 else []
                out.append({"header":header,"rows":data})
    return out

def insert_facts_from_tables(cur, asset_id:int, tables:list[dict], citation:str):
    total=0
    for tbl in tables:
        header=tbl["header"]
        rows=tbl["rows"]
        # find period column
        period_idx=None
        for i,h in enumerate(header):
            if parse_period(str(h)) or re.search(r"(period|quarter|q[1-4]|zeit|monat|jahr)", str(h), re.I):
                period_idx=i; break
        # iterate numeric columns as metrics
        for j, h in enumerate(header):
            if j==period_idx: continue
            metric, unit_hint = canon_metric(h or f"col{j}")
            for r in rows:
                if j>=len(r): continue
                period = None
                if period_idx is not None and period_idx < len(r):
                    period=parse_period(r[period_idx]) or None
                val = try_float(r[j])
                if val is None: continue
                unit = unit_hint
                # percent if cell had %
                if "%" in str(r[j]): unit = "%"
                cur.execute(f"INSERT INTO {FACTS}(asset_id,metric,value,unit,period_start,period_end,citation) VALUES(?,?,?,?,?,?,?)",
                            (str(asset_id), metric, float(val), unit, period, None, citation))
                total+=1
    return total

def main(paths:list[str]):
    DB.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(str(DB)); cur=con.cursor(); ensure_schema(cur)
    scanned=0; inserted=0
    # collect pdfs
    candidates=[]
    if paths:
        candidates=[Path(p) for p in paths]
    else:
        for root in ("samples","data/raw/uploads"):
            for p in Path(root).rglob("*.pdf"):
                candidates.append(p)
    for p in candidates:
        asset_id = upsert_asset(cur, str(p))
        tables = extract_tables_one(p)
        ins = insert_facts_from_tables(cur, asset_id, tables, p.name)
        inserted += ins; scanned += 1
    con.commit(); con.close()
    print(json.dumps({"ok": True, "pdfs_scanned": scanned, "facts_inserted": inserted}))
if __name__=="__main__":
    main(sys.argv[1:])
