from pydantic import BaseModel
from typing import Optional

class ExportItem(BaseModel):
    name: str
    size: int
    mtime: float
    url: Optional[str] = None
    checksum: Optional[str] = None
    ext: Optional[str] = None
    path: Optional[str] = None

class LatestExport(BaseModel):
    name: str
    url: str
    size: int
    mtime: float
    checksum: Optional[str] = None
