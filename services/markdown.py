from __future__ import annotations
from typing import Dict, Any, List
def project_to_markdown(p: Dict[str, Any]) -> str:
    title = p.get("title") or p.get("topic") or f"Project {p.get('id','')}"
    out = [f"# {title}"]
    sub = (p.get("subtitle") or (p.get("outline") or {}).get("subtitle"))
    if sub: out.append(f"_{sub}_")
    out.append("")
    sections: List[Dict[str, Any]] = (p.get("agenda") or (p.get("outline") or {}).get("sections") or [])
    for sec in sections:
        st = sec.get("title") or "Section"
        out.append(f"## {st}")
        for b in (sec.get("bullets") or []):
            out.append(f"- {b}")
        out.append("")
    return "\n".join(out).strip() + "\n"
