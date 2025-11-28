# -*- coding: utf-8 -*-
import sqlite3, json, re
from pathlib import Path

DB=Path("data/manifest.db")
if not DB.exists(): 
    print("[ERR] manifest.db fehlt – Wave 1 zuerst"); raise SystemExit(1)

def jload(s):
    try:
        return json.loads(s) if isinstance(s,str) else (s or [])
    except Exception:
        return []

REGION_MAP = {
    r"\b(dach|de|germany|deu)\b":"DE",
    r"\b(at|austria)\b":"AT",
    r"\b(ch|switzerland)\b":"CH",
    r"\b(uk|united_?kingdom|gb)\b":"UK",
    r"\b(us|usa|united_?states)\b":"US",
    r"\b(eu|europe|emea)\b":"EU",
}
CHANNEL_TOKENS = ("paid","search","sem","seo","social","display","email","video","brand","retarget")

def detect_region(text:str)->str|None:
    t=text.lower()
    for pat,code in REGION_MAP.items():
        if re.search(pat, t): return code
    return None

def detect_channel(text:str, tags:list[str])->str|None:
    pool=(text.lower()+" "+" ".join(tags)).replace("_"," ")
    for tok in CHANNEL_TOKENS:
        if re.search(rf"\b{re.escape(tok)}\b", pool):
            return tok
    return None

con=sqlite3.connect(DB); cur=con.cursor()
# Spalten (idempotent) ergänzen
for col in ("brand TEXT","region TEXT","channel TEXT"):
    try: cur.execute(f"ALTER TABLE facts ADD COLUMN {col}")
    except Exception: pass

# hole assets + facts verknüpft
rows=cur.execute("""SELECT f.id, f.asset_id, a.customer, a.path, a.name, a.tags
                    FROM facts f 
                    LEFT JOIN assets a ON a.id=f.asset_id""").fetchall()

upd=0
for fid, aid, cust, apath, aname, atags in rows:
    base=" ".join([x for x in (str(apath or ""), str(aname or "")) if x])
    tags = jload(atags) if atags else []
    brand = (cust or "").strip() or None
    region = detect_region(base) or (detect_region(" ".join(tags)) if tags else None)
    channel = detect_channel(base, tags) or None
    if any([brand,region,channel]):
        cur.execute("UPDATE facts SET brand=COALESCE(?,brand), region=COALESCE(?,region), channel=COALESCE(?,channel) WHERE id=?",
                    (brand, region, channel, fid))
        upd+=1

con.commit(); con.close()
print(f"[ok] semantics: {upd} facts angereichert (brand/region/channel)")
