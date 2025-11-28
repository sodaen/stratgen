# -*- coding: utf-8 -*-
import sqlite3, re, time

DB="data/manifest.db"
con=sqlite3.connect(DB); cur=con.cursor()
try: cur.execute("ALTER TABLE charts ADD COLUMN footnote TEXT")
except Exception: pass

def periods(cur, metric):
    rows=cur.execute("SELECT period_start, value, unit FROM facts WHERE metric=? AND period_start IS NOT NULL ORDER BY period_start",(metric,)).fetchall()
    return rows

def alt_for(metric, rows):
    if len(rows)<2: return None
    (p0,v0,u0),(p1,v1,u1)=rows[-2],rows[-1]
    unit=u1 or u0 or ""
    try:
        pc = (v1-v0)/abs(v0)*100 if v0 else None
    except Exception:
        pc=None
    arrow="↑" if (pc or 0)>=0 else "↓"
    if unit.lower()=="%": unit="%"
    if pc is not None:
        return f"{metric.upper()}: {arrow} {abs(pc):.1f}% ({v0:g}{unit} → {v1:g}{unit}) von {p0} zu {p1}"
    return f"{metric.upper()}: {v0:g}{unit} → {v1:g}{unit} von {p0} zu {p1}"

now=time.strftime("%Y-%m-%d")
rows=cur.execute("SELECT id, metric, citation FROM charts").fetchall()
upd=0
for cid, metric, cit in rows:
    pts=periods(cur, metric)
    alt = alt_for(metric, pts) or f"{metric.upper()} Verlauf"
    foot = None
    if cit: foot=f"Quelle: {cit} | Stand: {now}"
    cur.execute("UPDATE charts SET alt_text=COALESCE(?,alt_text), footnote=COALESCE(?,footnote) WHERE id=?",(alt,foot,cid))
    upd+=1
con.commit(); con.close()
print(f"[ok] charts postprocess: {upd} Zeilen alt_text/footnote aktualisiert")
