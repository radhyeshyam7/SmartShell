from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.app.config import settings
from backend.app.ai.gemini_client import gemini_client

router = APIRouter(prefix="/settings", tags=["Settings"])

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    gemini_model: Optional[str] = None
    execution_timeout: Optional[int] = None
    allow_all_directories: Optional[bool] = None

@router.get("")
def get_settings():
    masked_key = ""
    if settings.GEMINI_API_KEY:
        masked_key = settings.GEMINI_API_KEY[:6] + "..." + settings.GEMINI_API_KEY[-4:]
        
    return {
        "gemini_api_key_masked": masked_key,
        "gemini_api_key_configured": bool(settings.GEMINI_API_KEY),
        "gemini_model": settings.GEMINI_MODEL,
        "execution_timeout": settings.EXECUTION_TIMEOUT,
        "allow_all_directories": settings.ALLOW_ALL_DIRECTORIES,
        "authorized_roots": settings.AUTHORIZED_ROOTS
    }

@router.put("")
def update_settings(req: SettingsUpdateRequest):
    if req.gemini_api_key is not None and req.gemini_api_key.strip():
        settings.GEMINI_API_KEY = req.gemini_api_key.strip()
        gemini_client.update_key(req.gemini_api_key.strip())
        
    if req.gemini_model is not None:
        settings.GEMINI_MODEL = req.gemini_model.strip()
        gemini_client.model_name = req.gemini_model.strip()
        
    if req.execution_timeout is not None:
        settings.EXECUTION_TIMEOUT = req.execution_timeout
        
    if req.allow_all_directories is not None:
        settings.ALLOW_ALL_DIRECTORIES = req.allow_all_directories
        
    return {"status": "updated"}

@router.post("/test-gemini")
def test_gemini_connection():
    if not settings.GEMINI_API_KEY:
        raise HTTPException(status_code=400, detail="GEMINI_API_KEY is not configured.")
        
    try:
        res = gemini_client.generate_content("Convert this command to shell: check python version")
        return {
            "status": "success",
            "model": settings.GEMINI_MODEL,
            "sample_response": res
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Gemini API Error: {str(e)}")
