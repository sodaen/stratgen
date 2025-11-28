# -*- coding: utf-8 -*-
import sys, os, json, sqlite3, csv
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
      period_start TEXT, period_end TEXT, citation TEXT,
      brand TEXT, region TEXT, channel TEXT, provider TEXT
    )""")

def upsert_asset(cur, p:Path, provider:str)->int:
    cur.execute(f"SELECT id FROM {ASSETS} WHERE path=?", (str(p),))
    r=cur.fetchone()
    if r: return int(r[0])
    cur.execute(
      f"INSERT INTO {ASSETS}(customer,path,name,type,size,tags,section_hint,source,created_at) "
      f"VALUES(?,?,?,?,?,?,?, ?, strftime('%s','now'))",
      ("Acme GmbH", str(p), p.name, p.suffix.lstrip('.').lower(), p.stat().st_size if p.exists() else None,
       "[]","kpis", provider)
    )
    return cur.lastrowid

def push_fact(cur, asset_id, rec, provider, citation):
    metric = (rec.get("metric") or "").strip().lower().replace(" ", "_")
    value  = rec.get("value"); unit = rec.get("unit") or None
    try:
        value = float(str(value).replace("%","").replace(",",".")) if value not in ("",None) else None
    except: value=None
    period = rec.get("period") or None
    brand  = rec.get("brand") or None
    region = rec.get("region") or None
    channel= rec.get("channel") or None
    if metric and value is not None:
        cur.execute(
          f"INSERT INTO {FACTS}(asset_id,metric,value,unit,period_start,period_end,citation,brand,region,channel,provider) "
          f"VALUES(?,?,?,?,?,?,?,?,?,?,?)",
          (str(asset_id), metric, value, unit, period, None, citation, brand, region, channel, provider)
        )
        return 1
    return 0

def load_csv(path:Path)->list[dict]:
    with open(path, newline='', encoding="utf-8") as f:
        return list(csv.DictReader(f))

def load_jsonl_or_json(path:Path)->list[dict]:
    s=path.read_text(encoding="utf-8")
    if s.strip().startswith("["): return json.loads(s)
    rows=[]
    for line in s.splitlines():
        line=line.strip()
        if not line: continue
        try: rows.append(json.loads(line))
        except: pass
    return rows

def main():
    DB.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(str(DB)); cur=con.cursor(); ensure_schema(cur)

    roots = [Path("samples/providers"), Path("data/raw/providers")]
    inserted=0; assets=0
    for root in roots:
        if not root.exists(): continue
        for p in root.rglob("*"):
            if not p.is_file(): continue
            provider = p.name.split("_",1)[0].lower()
            if p.suffix.lower()==".csv":
                rows = load_csv(p)
            elif p.suffix.lower() in (".json",".jsonl"):
                rows = load_jsonl_or_json(p)
            else:
                continue
            asset_id = upsert_asset(cur, p, provider); assets+=1
            for r in rows:
                inserted += push_fact(cur, asset_id, r, provider, p.name)
    con.commit(); con.close()
    print(json.dumps({"ok":True,"assets":assets,"facts_inserted":inserted}))
if __name__=="__main__":
    main()
