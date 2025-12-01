"""
Files API - Dateimanagement für Frontend
"""
from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import os
import shutil
from pathlib import Path
from datetime import datetime

router = APIRouter(prefix="/files", tags=["File Management"])

# Base directories
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
KNOWLEDGE_DIR = DATA_DIR / "knowledge"
UPLOADS_DIR = DATA_DIR / "uploads"
TEMPLATES_DIR = DATA_DIR / "templates"

# Ensure directories exist
for d in [RAW_DIR, KNOWLEDGE_DIR, UPLOADS_DIR, TEMPLATES_DIR]:
    d.mkdir(parents=True, exist_ok=True)


class FileInfo(BaseModel):
    name: str
    path: str
    type: str
    size: int
    modified: str


class DirectoryListing(BaseModel):
    path: str
    files: List[FileInfo]
    directories: List[str]
    total_size: int


@router.get("/list", response_model=DirectoryListing)
async def list_files(path: str = ""):
    """Listet Dateien in einem Verzeichnis"""
    # Sanitize path
    safe_path = path.replace("..", "").strip("/")
    
    # Map to actual directories
    if safe_path.startswith("raw"):
        base = RAW_DIR
        rel_path = safe_path[3:].strip("/")
    elif safe_path.startswith("knowledge"):
        base = KNOWLEDGE_DIR
        rel_path = safe_path[9:].strip("/")
    elif safe_path.startswith("uploads"):
        base = UPLOADS_DIR
        rel_path = safe_path[7:].strip("/")
    elif safe_path.startswith("templates"):
        base = TEMPLATES_DIR
        rel_path = safe_path[9:].strip("/")
    else:
        base = DATA_DIR
        rel_path = safe_path
    
    target = base / rel_path if rel_path else base
    
    if not target.exists():
        raise HTTPException(status_code=404, detail="Directory not found")
    
    if not target.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")
    
    files = []
    directories = []
    total_size = 0
    
    for item in target.iterdir():
        if item.is_file():
            stat = item.stat()
            files.append(FileInfo(
                name=item.name,
                path=str(item.relative_to(DATA_DIR)),
                type=item.suffix.lower(),
                size=stat.st_size,
                modified=datetime.fromtimestamp(stat.st_mtime).isoformat()
            ))
            total_size += stat.st_size
        elif item.is_dir():
            directories.append(item.name)
    
    return DirectoryListing(
        path=safe_path or "data",
        files=sorted(files, key=lambda x: x.name),
        directories=sorted(directories),
        total_size=total_size
    )


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    path: str = Form("uploads")
):
    """Lädt eine Datei hoch"""
    # Determine target directory
    if path.startswith("raw"):
        target_dir = RAW_DIR
    elif path.startswith("knowledge"):
        target_dir = KNOWLEDGE_DIR
    elif path.startswith("templates"):
        target_dir = TEMPLATES_DIR
    else:
        target_dir = UPLOADS_DIR
    
    # Sanitize filename
    safe_name = "".join(c for c in file.filename if c.isalnum() or c in "._- ")
    target_path = target_dir / safe_name
    
    # Handle duplicates
    if target_path.exists():
        stem = target_path.stem
        suffix = target_path.suffix
        counter = 1
        while target_path.exists():
            target_path = target_dir / f"{stem}_{counter}{suffix}"
            counter += 1
    
    # Save file
    try:
        with open(target_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        return {
            "success": True,
            "filename": target_path.name,
            "path": str(target_path.relative_to(DATA_DIR)),
            "size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{file_path:path}")
async def delete_file(file_path: str):
    """Löscht eine Datei"""
    # Sanitize
    safe_path = file_path.replace("..", "").strip("/")
    target = DATA_DIR / safe_path
    
    if not target.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    if not str(target).startswith(str(DATA_DIR)):
        raise HTTPException(status_code=403, detail="Access denied")
    
    try:
        if target.is_file():
            target.unlink()
        else:
            shutil.rmtree(target)
        
        return {"success": True, "deleted": safe_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/index")
async def index_files():
    """Triggert Indexierung aller Dateien"""
    from services.auto_learner import learn_new_files, scan_all_directories
    
    results = {
        "templates_analyzed": 0,
        "documents_indexed": 0,
        "embeddings_generated": 0,
        "errors": []
    }
    
    try:
        # Scan und lerne neue Dateien
        learn_result = learn_new_files(scan_type="manual")
        results["templates_analyzed"] = learn_result.get("templates_learned", 0)
        results["documents_indexed"] = learn_result.get("knowledge_indexed", 0)
        
        # Generiere Embeddings
        try:
            from backend.knowledge_api import embed_local_docs
            embed_result = await embed_local_docs()
            results["embeddings_generated"] = embed_result.get("indexed", 0)
        except Exception as e:
            results["errors"].append(f"Embedding error: {str(e)}")
            
        return results
    except Exception as e:
        results["errors"].append(str(e))
        return results
    
    try:
        # Analyze templates
        if TEMPLATES_DIR.exists():
            dna_analyzer = SlideDNAAnalyzer()
            for pptx_file in TEMPLATES_DIR.glob("**/*.pptx"):
                try:
                    dna_analyzer.analyze_template(str(pptx_file))
                    results["templates_analyzed"] += 1
                except Exception as e:
                    results["errors"].append(f"Template {pptx_file.name}: {e}")
        
        # Index knowledge
        if KNOWLEDGE_DIR.exists():
            kb = KnowledgeBase()
            for doc in KNOWLEDGE_DIR.glob("**/*"):
                if doc.is_file() and doc.suffix in [".md", ".txt", ".pdf", ".docx"]:
                    try:
                        kb.add_document(str(doc))
                        results["documents_indexed"] += 1
                    except Exception as e:
                        results["errors"].append(f"Document {doc.name}: {e}")
        
        # Index raw presentations
        if RAW_DIR.exists():
            learner = AutoLearner()
            for pptx in RAW_DIR.glob("**/*.pptx"):
                try:
                    learner.learn_from_presentation(str(pptx))
                    results["embeddings_generated"] += 1
                except Exception as e:
                    results["errors"].append(f"Presentation {pptx.name}: {e}")
        
        return {
            "success": True,
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/storage")
async def get_storage_info():
    """Gibt Speicherinformationen zurück"""
    def get_dir_size(path: Path) -> int:
        total = 0
        if path.exists():
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
        return total
    
    return {
        "raw": get_dir_size(RAW_DIR),
        "knowledge": get_dir_size(KNOWLEDGE_DIR),
        "uploads": get_dir_size(UPLOADS_DIR),
        "templates": get_dir_size(TEMPLATES_DIR),
        "total": sum([
            get_dir_size(RAW_DIR),
            get_dir_size(KNOWLEDGE_DIR),
            get_dir_size(UPLOADS_DIR),
            get_dir_size(TEMPLATES_DIR)
        ])
    }
