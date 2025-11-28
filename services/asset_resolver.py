
# -*- coding: utf-8 -*-
from __future__ import annotations
import json, re, os
from pathlib import Path
from typing import List, Dict, Any, Optional

IMG_EXT = {".png",".jpg",".jpeg",".webp",".svg"}
TAB_EXT = {".csv",".tsv",".xlsx",".xls",".json"}
UPLOAD_DIRS = [Path("data/uploads"), Path("data/images"), Path("static/ui")]

def _norm(s:str)->str: return (s or "").strip().lower()
def _is_logo_name(name:str)->bool:
    n=_norm(name)
    return any(k in n for k in ["logo","brandmark","logotype","wordmark","stratgen-logo"])

def _scan_assets()->List[Path]:
    out=[]
    for base in UPLOAD_DIRS:
        if base.exists():
            for p in base.rglob("*"):
                if p.is_file() and (p.suffix.lower() in IMG_EXT or p.suffix.lower() in TAB_EXT):
                    out.append(p)
    return out

def _pick_logo(paths:List[Path])->Optional[Path]:
    logos=[p for p in paths if p.suffix.lower() in IMG_EXT and _is_logo_name(p.name)]
    if logos: return sorted(logos, key=lambda p: len(p.name))[0]
    # Fallback: vorhandenes UI-Logo
    fallback=Path("static/ui/stratgen-logo.svg")
    return fallback if fallback.exists() else None

def _pick_photos(paths:List[Path], limit:int=8)->List[Path]:
    pics=[p for p in paths if p.suffix.lower() in IMG_EXT and not _is_logo_name(p.name)]
    # leichte Sortierung nach Dateiname
    return sorted(pics, key=lambda p: p.name)[:limit]

def _pick_tables(paths:List[Path], limit:int=4)->List[Path]:
    tabs=[p for p in paths if p.suffix.lower() in TAB_EXT]
    return sorted(tabs, key=lambda p: p.name)[:limit]

def _mk_img_token(path:Path, **kw)->str:
    kv=" ".join(f'{k}="{v}"' for k,v in kw.items())
    return f'#IMG(path="{path.as_posix()}" {kv})'.strip()

def _mk_chart_token(path:Path, chart_type:str="bar", **kw)->str:
    kv=" ".join(f'{k}="{v}"' for k,v in kw.items())
    return f'#CHART(data="{path.as_posix()}" type="{chart_type}" {kv})'.strip()

def _mk_table_token(path:Path, **kw)->str:
    kv=" ".join(f'{k}="{v}"' for k,v in kw.items())
    return f'#TABLE(data="{path.as_posix()}" {kv})'.strip()

def enrich_plan_with_assets(project:Dict[str,Any], plan:List[Dict[str,Any]])->List[Dict[str,Any]]:
    """
    Fügt zu passenden Slides #IMG/#CHART/#TABLE Tokens hinzu.
    - Titelfolie: Logo oben rechts klein
    - Section-Divider: stimmungsvolles Foto als Hintergrund-Bildtoken
    - KPI/Metric/Channel-Slides: falls CSV/JSON/XLSX → CHART/TABLE
    - Content-Slides: Foto neben Bullets
    """
    assets=_scan_assets()
    if not assets: 
        return plan

    logo=_pick_logo(assets)
    photos=_pick_photos(assets, limit=16)
    tables=_pick_tables(assets, limit=8)
    persona_imgs=_pick_persona_imgs(assets, limit=6)
    roadmap_imgs=_pick_roadmap_imgs(assets, limit=4)

    def title_matches(sl:Dict[str,Any], words:List[str])->bool:
        t=_norm(sl.get("title") or "")
        return any(w in t for w in words)

    pi=0  # photo index
    ti=0  # table index

    out=[]
    for idx,sl in enumerate(plan or []):
        sl= dict(sl)  # copy
        # Stelle für Tokens: bevorzugt notes, sonst bullets, sonst title-append
        def _append_token(tok:str):
            if not tok: return
            if isinstance(sl.get("notes"), str):
                sl["notes"] = (sl["notes"] + "\n" + tok).strip()
            elif isinstance(sl.get("bullets"), list) and sl["bullets"]:
                sl["bullets"] = list(sl["bullets"]) + [tok]
            else:
                sl["title"] = (sl.get("title") or "") + f"  {tok}"

        # 1) Titelfolie
        if idx==0 and logo:
            _append_token(_mk_img_token(logo, pos="top-right", size="sm"))

        # 2) Section Divider?
        if _norm(sl.get("kind","")) in {"section","divider"} or title_matches(sl, ["lage","zielbild","strategie","umsetzung","roadmap","kpis","kanäle","kanal","funnel"]):
            if pi < len(photos):
                _append_token(_mk_img_token(photos[pi], fit="cover", layer="background"))
                pi+=1

        # 3) KPI/Metrics/Channel → CHART/TABLE
        # Personas → persona_* Bilder
        if title_matches(sl, ["persona","personas","zielgruppe","audience"]):
            if persona_imgs:
                _append_token(_mk_img_token(persona_imgs[0], pos="left", size="md"))
            persona_imgs = persona_imgs[1:]
        # Roadmap/Journey
        if title_matches(sl, ["roadmap","journey","zeitplan","plan"]):
            if roadmap_imgs:
                _append_token(_mk_img_token(roadmap_imgs[0], pos="bottom", size="lg"))
            roadmap_imgs = roadmap_imgs[1:]
# 3) KPI/Metrics/Channel → CHART/TABLE
        if title_matches(sl, ["kpi","kpis","metric","metriken","metrics","channel","kanäle","kanal","performance"]):
            if ti < len(tables):
                p=tables[ti]; ti+=1
                ext=p.suffix.lower()
                if ext in {".csv",".tsv",".json"}:
                    _append_token(_mk_chart_token(p, chart_type="bar"))
                else:
                    _append_token(_mk_table_token(p))

        # 4) Content-Slides → Bild rechts
        if _norm(sl.get("kind","")) in {"content","content_right","content_left"} or (sl.get("bullets") and not title_matches(sl, ["kpi","metric"])):
            if pi < len(photos):
                _append_token(_mk_img_token(photos[pi], pos="right", size="md"))
                pi+=1

        out.append(sl)
    return out


def _pick_persona_imgs(paths, limit=6):
    return [p for p in paths if any(k in p.name.lower() for k in ["persona","audience","zielgruppe"])][:limit]

def _pick_roadmap_imgs(paths, limit=4):
    return [p for p in paths if any(k in p.name.lower() for k in ["roadmap","journey","timeline","zeitplan"])][:limit]
