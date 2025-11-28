import os
from fastapi import FastAPI, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from services.ppt_renderer import generate_pptx
from services.rag_pipeline import generate_sections

APP_NAME = os.getenv("APP_NAME", "stratgen")

class GenerateRequest(BaseModel):
    customer_name: str = Field(..., example="Acme GmbH")
    project_title: str = Field("Ganzheitliche Marketingstrategie")
    mode: str = Field("facts", description="facts|ideation")
    # weitere Felder: branche, region, budget, ziele, etc.

app = FastAPI(title=APP_NAME)

@app.get("/healthz")
def healthz():
    return {"status": "ok", "app": APP_NAME}

@app.post("/generate")
def generate(req: GenerateRequest = Body(...)):
    # (MVP) Sektionen ermitteln (später: echte Inhalte)
    sections = generate_sections(req.model_dump())
    out_path = f"export/{req.customer_name.replace(' ', '_')}_{req.project_title.replace(' ', '_')}.pptx"
    generate_pptx(out_path, title=req.project_title, sections=sections)
    return JSONResponse({"ok": True, "pptx_path": out_path})
