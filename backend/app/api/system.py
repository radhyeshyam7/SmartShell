from fastapi import APIRouter, HTTPException
from backend.app.services.process_service import process_service

router = APIRouter(prefix="/system", tags=["System Monitor"])

@router.get("/metrics")
def get_metrics():
    return process_service.get_system_metrics()

@router.get("/processes")
def get_processes(limit: int = 50):
    return {"processes": process_service.list_processes(limit)}

@router.post("/processes/{pid}/terminate")
def terminate_process(pid: int):
    try:
        success = process_service.terminate_process(pid)
        if not success:
            raise HTTPException(status_code=404, detail=f"Process {pid} not found.")
        return {"status": "terminated", "pid": pid}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
