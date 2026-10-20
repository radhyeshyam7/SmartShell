from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from backend.app.services.file_service import file_service

router = APIRouter(prefix="/files", tags=["File Explorer"])

class FileCreateRequest(BaseModel):
    path: str
    content: str = ""

class MkdirRequest(BaseModel):
    path: str

class DeleteRequest(BaseModel):
    path: str

@router.get("/list")
def list_files(path: str = Query(".", description="Target directory path")):
    try:
        return {"path": path, "items": file_service.list_files(path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/read")
def read_file(path: str = Query(..., description="Target file path")):
    try:
        content = file_service.read_file(path)
        return {"path": path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/create")
def create_file(req: FileCreateRequest):
    try:
        file_service.create_file(req.path, req.content)
        return {"status": "success", "path": req.path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/mkdir")
def make_directory(req: MkdirRequest):
    try:
        file_service.create_directory(req.path)
        return {"status": "success", "path": req.path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/delete")
def delete_item(req: DeleteRequest):
    try:
        file_service.delete_item(req.path)
        return {"status": "deleted", "path": req.path}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
