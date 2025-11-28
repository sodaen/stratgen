# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import Any, Dict
from . import register

@register("risks_mitigations")
def risks_mitigations(project: Dict[str, Any], facts: Dict[str, Any]) -> Dict[str, Any]:
    bullets = [
        "Risiko: Kanal-CPMs steigen → Mitigation: Mix/Creatives anpassen",
        "Risiko: Lead-Qualität → Mitigation: Scoring/Nurture/CRO",
        "Risiko: Sales-Kapazität → Mitigation: Enablement/Priorisierung",
        "Risiko: Messbarkeit → Mitigation: Events/Consent/Modeling",
        "Risiko: Budget-Cut → Mitigation: Stufenplan/Minimum-Portfolio"
    ]
    return {"title": "Risiken & Gegenmaßnahmen", "bullets": bullets, "notes":"Impact × Wahrscheinlichkeit klassifizieren."}
