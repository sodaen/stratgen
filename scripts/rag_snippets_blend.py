# -*- coding: utf-8 -*-
import json, re
from pathlib import Path

def load_texts():
  texts = []
  for path in [
    "samples/wave1_upload_demo/market_notes.txt",
    "samples/wave1_upload_demo/insights.json",
    "data/raw/providers/talkwalker_trend.json",
    "data/raw/providers/statista_market.json"
  ]:
    p = Path(path)
    if p.exists():
      try:
        if p.suffix.lower()==".json":
          obj = json.loads(p.read_text(encoding="utf-8"))
          # einfache Extraktion von text/headline Feldern
          for k in ("text","headline","summary","note"):
            v = obj.get(k)
            if isinstance(v,str): texts.append(v)
          # Arrays von Headlines
          for k in ("highlights","bullets","headlines"):
            seq = obj.get(k) or []
            for s in seq:
              if isinstance(s,str): texts.append(s)
        else:
          texts.append(p.read_text(encoding="utf-8"))
      except Exception:
        pass
  return texts

def load_facts():
  try:
    man = json.loads(Path("data/manifest.json").read_text(encoding="utf-8"))
    return man.get("facts") or []
  except Exception:
    return []

def key_bullets(topic, texts, facts):
  topic_l = (topic or "").lower()
  picks = []
  # naive: wähle Sätze aus Text, die Topic-Keywords enthalten
  kws = [w for w in re.split(r"[^a-z0-9]+", topic_l) if w]
  for t in texts:
    for sent in re.split(r"[.\n]+", t):
      sl = sent.lower().strip()
      if sl and any(k in sl for k in kws):
        picks.append(sent.strip())
        if len(picks)>=3: break
    if len(picks)>=3: break
  # ergänze 2 datenbasierte Bullets (falls facts vorhanden)
  facts_picks = []
  for f in facts:
    m = (f.get("metric") or "").lower()
    if m in ("ctr","cpc","cac","roas") and f.get("value") is not None:
      unit = f.get("unit") or ""
      per  = f.get("period_start") or ""
      facts_picks.append(f"{m.upper()}: {f['value']}{unit and ' '+unit} ({per})")
      if len(facts_picks)>=2: break
  bullets = picks[:3] + facts_picks[:2]
  if not bullets:
    bullets = ["[PLATZHALTER] RAG-Bullet (zu wenig Wissen/Fakten vorhanden)"]
  return bullets

def main():
  comp = {}
  try:
    comp = json.loads(Path("assets_tmp/comp_wave3c.json").read_text(encoding="utf-8"))
  except Exception:
    pass
  texts = load_texts()
  facts = load_facts()
  topic = comp.get("topic") or comp.get("title") or ""
  bullets = key_bullets(topic, texts, facts)
  out = {"bullets": bullets}
  Path("assets_tmp/rag_bullets.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
  print(json.dumps({"ok": True, "bullets": bullets}, ensure_ascii=False))
if __name__=="__main__":
  main()
