from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from backend.app.services.drive_service import drive_service
from backend.app.services.file_service import file_service

router = APIRouter(prefix="/drives", tags=["Multi-Drive Explorer"])

class SearchRequest(BaseModel):
    query: str
    start_path: str = "."
    max_results: int = 100
    max_depth: int = 5
    min_size_mb: float = 0.0

@router.get("/")
def get_drives():
    """Discover all mounted Windows drives and volume capacity metadata"""
    try:
        return {"drives": drive_service.list_drives()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query mounted drives: {str(e)}")

@router.post("/search")
def search_drives(req: SearchRequest):
    """Search files across drives with filters"""
    try:
        results = file_service.search_files(
            query=req.query,
            start_path=req.start_path,
            max_results=req.max_results,
            max_depth=req.max_depth,
            min_size_mb=req.min_size_mb
        )
        return {"query": req.query, "count": len(results), "items": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/duplicates")
def find_duplicates(path: str = Query(".", description="Target directory or drive path")):
    """Scan for duplicate files using size + SHA-256 fingerprinting"""
    try:
        duplicates = file_service.find_duplicates(start_path=path)
        return {"path": path, "duplicate_groups": duplicates, "count": len(duplicates)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplicate search failed: {str(e)}")
