# -*- coding: utf-8 -*-
import os, re, sqlite3, math, time
from pathlib import Path
from typing import List, Tuple, Dict, Optional

DB=Path("data/manifest.db")
CHDIR=Path("data/charts"); CHDIR.mkdir(parents=True, exist_ok=True)

def ensure_schema(cur):
    cur.execute("""CREATE TABLE IF NOT EXISTS charts(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        metric TEXT,
        kind TEXT,
        title TEXT,
        unit TEXT,
        period_start TEXT,
        period_end TEXT,
        group_by TEXT,
        path TEXT,
        width INTEGER,
        height INTEGER,
        citation TEXT,
        alt_text TEXT,
        created_at REAL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS chart_insights(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chart_id INTEGER,
        text TEXT,
        FOREIGN KEY(chart_id) REFERENCES charts(id) ON DELETE CASCADE
    )""")

def parse_period_key(p: str) -> Tuple[int,int]:
    if not p: return (0,0)
    p=p.strip()
    m=re.match(r"^(\d{4})[Qq]([1-4])$", p)
    if m:
        y=int(m.group(1)); q=int(m.group(2))
        return (y, q*3)  # Quartal -> Ersatzmonat
    m=re.match(r"^(\d{4})[-/\.](\d{1,2})$", p)
    if m:
        return (int(m.group(1)), int(m.group(2)))
    m=re.match(r"^(\d{4})$", p)
    if m:
        return (int(m.group(1)), 1)
    # Fallback: lexikalisch
    try:
        return (int(p),1)
    except:
        return (0,0)

def choose_kind(n_points:int, unit:str)->str:
    unit=(unit or "").lower()
    if n_points>=6: return "line"
    if unit in ("%", "percent", "pct"): return "line" if n_points>=3 else "bar"
    return "bar" if n_points<=6 else "line"

def pct_change(a: float, b: float) -> Optional[float]:
    try:
        if a==0: return None
        return (b-a)/abs(a)*100.0
    except:
        return None

def sanitize(s:str)->str:
    return re.sub(r"[^A-Za-z0-9_\-]+","_", s).strip("_")

def collect_series(cur, metric:str):
    rows=cur.execute("""SELECT value, unit, period_start, citation
                        FROM facts WHERE metric=? AND period_start IS NOT NULL""",(metric,)).fetchall()
    if not rows: return None
    # group by period
    series={}
    unit=None; cits=set()
    for v,u,p,c in rows:
        unit=unit or u
        key=parse_period_key(p)
        if key==(0,0): continue
        series.setdefault((key,p),[]).append(float(v))
        if c: cits.add(c)
    if not series: return None
    # avg if multiple per period
    points=[]
    for (key,p), vals in series.items():
        points.append((key,p, sum(vals)/len(vals)))
    points.sort(key=lambda x: (x[0][0], x[0][1]))
    return {
        "unit": unit,
        "points": [(p,v) for _,p,v in points],
        "cit": ", ".join(sorted(cits)) if cits else None
    }

def render_chart(metric:str, unit:str, points:List[Tuple[str,float]], kind:str, out_path:Path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    xs=[p for p,_ in points]; ys=[v for _,v in points]
    fig=plt.figure(figsize=(6.8,4.2), dpi=150)  # ~1020x630
    ax=plt.gca()
    title=f"{metric.upper()} — {xs[0]} … {xs[-1]}" if xs else metric.upper()
    if kind=="line":
        ax.plot(xs, ys, marker="o")
    elif kind=="bar":
        ax.bar(xs, ys)
    else:
        ax.plot(xs, ys, marker="o")

    ax.set_title(title)
    ax.set_ylabel(f"{metric} ({unit})" if unit else metric)
    ax.set_xlabel("Period")
    ax.grid(True, linestyle="--", alpha=0.3)
    plt.tight_layout()
    fig.savefig(out_path)
    w,h=fig.get_size_inches()
    px=(int(w*fig.dpi), int(h*fig.dpi))
    plt.close(fig)
    return title, px

def build_insights(metric:str, unit:str, points:List[Tuple[str,float]])->List[str]:
    if len(points)<2: return []
    (p0,v0),(p1,v1) = points[-2], points[-1]
    pc = pct_change(v0, v1)
    dir_ = "↑" if (pc or 0)>=0 else "↓"
    unit_disp = unit or ""
    if unit_disp.lower()=="%": unit_disp="%"
    bullet1 = (f"{metric.upper()} {dir_} {abs(pc):.1f}% ({v0:g}{unit_disp} → {v1:g}{unit_disp}) QoQ"
               if pc is not None else f"{metric.upper()}: {v0:g}{unit_disp} → {v1:g}{unit_disp}")
    # zweite Insight: Spannweite
    vv=[v for _,v in points]
    rng=max(vv)-min(vv) if vv else 0
    bullet2 = f"Spannweite {rng:.2g}{unit_disp} über {len(points)} Perioden"
    return [bullet1, bullet2]

def main():
    if not DB.exists():
        print("[ERR] manifest.db fehlt – Wave 1 zuerst"); return
    con=sqlite3.connect(DB); cur=con.cursor()
    ensure_schema(cur)

    # verfügbare Metriken
    metrics=[m for (m,) in cur.execute("SELECT DISTINCT metric FROM facts WHERE period_start IS NOT NULL")]
    made=0
    for metric in metrics:
        series=collect_series(cur, metric)
        if not series: continue
        unit=series["unit"] or ""
        pts=series["points"]
        if len(pts)<2: continue
        kind=choose_kind(len(pts), unit)
        fname = f"{sanitize(metric)}_{sanitize(pts[0][0])}-{sanitize(pts[-1][0])}_{kind}.png"
        out=CHDIR/fname
        title, (w,h)=render_chart(metric, unit, pts, kind, out)
        cur.execute("""INSERT INTO charts(metric,kind,title,unit,period_start,period_end,group_by,
                      path,width,height,citation,alt_text,created_at)
                      VALUES(?,?,?,?,?,?,?,?,?,?,?,?,strftime('%s','now'))""",
                    (metric, kind, title, unit, pts[0][0], pts[-1][0], None,
                     str(out), w, h, series["cit"], f"{kind} chart of {metric} from {pts[0][0]} to {pts[-1][0]}"))
        chart_id=cur.lastrowid
        for t in build_insights(metric, unit, pts):
            cur.execute("INSERT INTO chart_insights(chart_id, text) VALUES(?,?)",(chart_id, t))
        con.commit()
        made+=1
    con.close()
    print(f"[ok] charts: {made} erstellt nach data/charts/")
if __name__=="__main__":
    main()
