from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel

class CitationRef(BaseModel):
    doc_id: str
    chunk_idx: Optional[int] = None
    span: Optional[Tuple[int,int]] = None
    url: Optional[str] = None
    title: Optional[str] = None

class OutlineSection(BaseModel):
    id: Optional[str] = None
    title: str
    bullets: Optional[List[str]] = None
    children: Optional[List["OutlineSection"]] = None
OutlineSection.model_rebuild()

class PreviewDiagnostics(BaseModel):
    citations_count: Optional[int] = None
    retrieval_k: Optional[int] = None
    rerank_enabled: Optional[bool] = None
    dedup_count: Optional[int] = None
    extra: Optional[Dict[str, Any]] = None

class PreviewResponse(BaseModel):
    outline: Optional[Dict[str, Any]] = None
    bullets: Optional[List[str]] = None
    citations: Optional[List[CitationRef]] = None
    diagnostics: Optional[PreviewDiagnostics] = None

class PreviewRequest(BaseModel):
    project_id: str
