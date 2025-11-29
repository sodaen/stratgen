#!/usr/bin/env python3
"""
Patch: Korrigiert den LLM-Aufruf in agent_v3_api.py
Problem: _ollama_generate() hat andere Signatur als erwartet
Lösung: Direkt services/llm.py generate() nutzen
"""
import re

filepath = "/home/sodaen/stratgen/backend/agent_v3_api.py"

with open(filepath, "r") as f:
    content = f.read()

# Fix 1: Import korrigieren - llm.generate statt llm_content._ollama_generate
old_import = '''# LLM Content Generation
try:
    from services.llm_content import (
        generate_bullets,
        generate_summary,
        generate_persona,
        generate_critique,
        generate_metrics,
        generate_slide_content,
        generate_from_template,
        check_ollama,
        _ollama_generate
    )
    HAS_LLM_CONTENT = True
except ImportError:
    HAS_LLM_CONTENT = False
    _ollama_generate = None'''

new_import = '''# LLM Content Generation
try:
    from services.llm_content import (
        generate_bullets,
        generate_summary,
        generate_persona,
        generate_critique,
        generate_metrics,
        generate_slide_content,
        generate_from_template,
        check_ollama,
    )
    HAS_LLM_CONTENT = True
except ImportError:
    HAS_LLM_CONTENT = False

# Direkter LLM-Zugriff über services/llm.py
try:
    from services.llm import generate as llm_generate, is_enabled as llm_enabled
    HAS_LLM = True
except ImportError:
    llm_generate = None
    llm_enabled = None
    HAS_LLM = False'''

if old_import in content:
    content = content.replace(old_import, new_import)
    print("✓ Fix 1: Import korrigiert")
else:
    print("⚠ Fix 1: Import-Block nicht gefunden (evtl. bereits gepatcht)")

# Fix 2: _llm_call Funktion korrigieren
old_llm_call = '''def _llm_call(prompt: str, task: str = "default", model_override: str = "", max_tokens: int = 1000) -> str:
    """Zentraler LLM-Call mit Model-Selection."""
    if not HAS_LLM_CONTENT or not _ollama_generate:
        return ""
    
    model = _select_model(task, model_override)
    result = _ollama_generate(prompt, model=model, max_tokens=max_tokens)
    return result.get("text", "") if isinstance(result, dict) else str(result)'''

new_llm_call = '''def _llm_call(prompt: str, task: str = "default", model_override: str = "", max_tokens: int = 1000) -> str:
    """Zentraler LLM-Call mit Model-Selection."""
    # Nutze services/llm.py generate() direkt
    if not HAS_LLM or not llm_generate:
        return ""
    
    if llm_enabled and not llm_enabled():
        return ""
    
    model = _select_model(task, model_override)
    
    try:
        result = llm_generate(
            prompt=prompt,
            model=model,
            max_tokens=max_tokens
        )
        if isinstance(result, dict):
            if result.get("ok"):
                return result.get("response", "")
            return ""
        return str(result)
    except Exception as e:
        return ""'''

if old_llm_call in content:
    content = content.replace(old_llm_call, new_llm_call)
    print("✓ Fix 2: _llm_call korrigiert")
else:
    print("⚠ Fix 2: _llm_call nicht gefunden")

# Fix 3: model_override umbenennen (Pydantic warning)
old_model = 'model_override: str = ""     # Spezifisches Modell erzwingen'
new_model = 'llm_model: str = ""     # Spezifisches Modell erzwingen (z.B. "llama3:8b")'

if old_model in content:
    content = content.replace(old_model, new_model)
    # Auch alle Referenzen auf model_override ändern
    content = content.replace('model_override=req.model_override', 'model_override=req.llm_model')
    content = content.replace('req.model_override', 'req.llm_model')
    print("✓ Fix 3: model_override → llm_model umbenannt")

# Speichern
with open(filepath, "w") as f:
    f.write(content)

print("\n✓ Patch angewendet!")
print("  Starte API neu mit: pkill -f gunicorn && ~/stratgen/scripts/startup_prod.sh")
