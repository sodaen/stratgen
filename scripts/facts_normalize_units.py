# -*- coding: utf-8 -*-
import sqlite3, re
con=sqlite3.connect("data/manifest.db"); cur=con.cursor()
# Normalisiere €/$ → 'eur'/'usd' in unit
cur.execute("UPDATE facts SET unit='%' WHERE metric='ctr' AND (unit IS NULL OR unit='')")
cur.execute("UPDATE facts SET unit=LOWER(TRIM(unit)) WHERE unit IS NOT NULL")
cur.execute("UPDATE facts SET unit='eur' WHERE unit IN ('€','eur ','euro','€ ','eur/','eur€')")
cur.execute("UPDATE facts SET unit='usd' WHERE unit IN ('$','usd ','$ ','usd/','$usd')")
# Entferne doppelte Leerzeichen
cur.execute("UPDATE facts SET unit=REPLACE(unit,'  ',' ') WHERE unit LIKE '%  %'")
con.commit(); con.close()
print("[ok] facts: units normalisiert")
