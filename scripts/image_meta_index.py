# -*- coding: utf-8 -*-
import sqlite3
from pathlib import Path
try:
    from PIL import Image
except Exception:
    print("[skip] Pillow nicht installiert – Bild-Meta übersprungen"); raise SystemExit(0)

DB=Path("data/manifest.db")
if not DB.exists(): print("[ERR] manifest.db fehlt"); raise SystemExit(1)
con=sqlite3.connect(DB); cur=con.cursor()
for ddl in ("img_w INTEGER","img_h INTEGER","orientation TEXT","crop_hint TEXT","hero_score REAL"):
    try: cur.execute(f"ALTER TABLE assets ADD COLUMN {ddl}")
    except Exception: pass

rows=cur.execute("""SELECT id, path, COALESCE(name,'') FROM assets 
                    WHERE lower(path) GLOB '*.png' OR lower(path) GLOB '*.jpg' 
                       OR lower(path) GLOB '*.jpeg' OR lower(path) GLOB '*.webp'""").fetchall()
n=0
for aid, p, nm in rows:
    pth=Path(p)
    if not pth.exists(): continue
    try:
        with Image.open(pth) as im:
            w,h = im.size
        orient = "landscape" if w>=h else "portrait"
        ratio = (w/h) if h else 1.0
        if ratio>=1.6: crop="full-bleed 16:9"
        elif ratio<=1.2: crop="contain / side-by-side"
        else: crop="center crop 4:3"
        base=(pth.name+" "+nm).lower()
        hero=0.3 + (0.4 if any(k in base for k in ("hero","visual","banner","cover")) else 0.0) + (0.3 if "logo" in base else 0.0)
        cur.execute("UPDATE assets SET img_w=?, img_h=?, orientation=?, crop_hint=?, hero_score=? WHERE id=?",
                    (w,h,orient,crop,round(min(hero,1.0),2),aid))
        n+=1
    except Exception:
        pass
con.commit(); con.close()
print(f"[ok] image-meta: {n} Assets aktualisiert")
