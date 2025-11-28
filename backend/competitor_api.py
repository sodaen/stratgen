from __future__ import annotations

from typing import List, Dict, Any
from fastapi import APIRouter, Body
from pydantic import BaseModel, Field

router = APIRouter(prefix="/competitors", tags=["competitors"])

class MatrixReq(BaseModel):
    customer_name: str
    competitors: List[str]
    criteria: List[str] = Field(default_factory=lambda: ["Preis","Funktionsumfang","Integrationsaufwand","Support","Sicherheit"])

class MatrixResp(BaseModel):
    ok: bool
    table: List[Dict[str, Any]]
    summary: List[str]

@router.post("/matrix", response_model=MatrixResp)
def matrix(req: MatrixReq = Body(...)):
    table = []
    marks = ["–","•","••","•••"]
    for i, c in enumerate(req.competitors):
        row = {"competitor": c}
        for j, crit in enumerate(req.criteria):
            row[crit] = marks[(i+j) % len(marks)]
        table.append(row)

    summary = [
        "Kurzfazit: Anbieter unterscheiden sich vor allem bei Integrationsaufwand und Support.",
        "Nächster Schritt: externe Quellen (URLs/Provider) anbinden, um die Matrix datenbasiert zu füllen."
    ]
    return MatrixResp(ok=True, table=table, summary=summary)
