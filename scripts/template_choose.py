# -*- coding: utf-8 -*-
import json, re
from pathlib import Path

STY = json.loads(Path("data/templates/styles.json").read_text(encoding="utf-8"))
manj = {}
try:
  manj = json.loads(Path("data/manifest.json").read_text(encoding="utf-8"))
except Exception:
  manj = {}

def infer_brand_and_industry(comp, manifest):
  title = (comp.get("title") or "") + " " + (comp.get("topic") or "")
  title_l = title.lower()
  brand = "acme" if "acme" in title_l else None
  # aus facts.tags/section ableiten (einfach)
  industry = None
  for a in (manifest.get("assets") or []):
    n = (a.get("name") or a.get("path") or "").lower()
    if any(k in n for k in ["b2b","saas","it","tech"]): industry="b2b"; break
  if industry is None and "b2b" in title_l: industry="b2b"
  return brand, industry

def choose_profile(brand, industry):
  for p in STY["profiles"]:
    mc = p.get("match",{})
    bc = [x.lower() for x in mc.get("brand_contains",[])]
    ic = [x.lower() for x in mc.get("industry_contains",[])]
    if brand and any(b in brand.lower() for b in bc): return p
    if industry and any(i in (industry or "").lower() for i in ic): return p
  return STY["profiles"][-1]  # default_minimal

def main():
  comp = {}
  try:
    comp = json.loads(Path("assets_tmp/comp_wave3c.json").read_text(encoding="utf-8"))
  except Exception:
    pass
  brand, industry = infer_brand_and_industry(comp, manj)
  prof = choose_profile(brand, industry)
  out = {"brand": brand, "industry": industry, "profile": prof}
  Path("assets_tmp/style_choice.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
  print(json.dumps({"ok": True, "style_id": prof["id"], "brand": brand, "industry": industry}, ensure_ascii=False))

if __name__=="__main__":
  main()
