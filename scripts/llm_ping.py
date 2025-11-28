import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))
import json
try:
    from services import llm
    out = llm.health()
except Exception as e:
    out = {"ok": False, "error": f"{type(e).__name__}: {e}", "hint": "LLM optional; aktiviere später via Ollama"}
print(json.dumps(out, indent=2, ensure_ascii=False))
