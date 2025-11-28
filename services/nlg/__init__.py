# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict, List, Callable

# Registry der NLG-Module
MODULES: Dict[str, Callable[[Dict[str, Any], Dict[str, Any]], Dict[str, Any]]] = {}

def register(name: str):
    def _wrap(fn):
        MODULES[name.strip().lower()] = fn
        return fn
    return _wrap

def bullets_safe(x):
    if not x: return []
    if isinstance(x, (list,tuple)): return [str(i) for i in x]
    return [str(x)]

# auto-import NLG modules so they self-register
from . import personas, gtm_basics, funnel, kpis, market_sizing, competitive, value_proof, channel_mix, execution_roadmap, risks_mitigations, guardrails, go_no_go  # noqa: F401
