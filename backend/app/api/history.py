import os
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from backend.app.database.database import get_db
from backend.app.database.models import TaskModel, StepModel, CommandHistoryModel
from backend.app.config import settings

router = APIRouter(prefix="/history", tags=["Command History"])

class RecordHistoryRequest(BaseModel):
    user_prompt: str
    command: str
    task_name: Optional[str] = "CLI Command"
    working_directory: Optional[str] = "."
    risk_level: Optional[str] = "low"
    status: Optional[str] = "completed"
    exit_code: Optional[int] = 0
    stdout: Optional[str] = ""
    stderr: Optional[str] = ""
    duration_seconds: Optional[float] = 0.0

def prune_old_records_and_logs(db: Session, days: int = 10):
    """Automatically prune database history and log files older than 10 days"""
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        
        # Prune DB command history
        db.query(CommandHistoryModel).filter(CommandHistoryModel.created_at < cutoff).delete()
        
        # Prune DB tasks
        old_tasks = db.query(TaskModel).filter(TaskModel.created_at < cutoff).all()
        for t in old_tasks:
            db.delete(t)
            
        db.commit()

        # Prune disk log files in logs directory older than 10 days
        log_dir = os.path.join(settings.BASE_DIR, "logs")
        if os.path.exists(log_dir):
            cutoff_timestamp = (datetime.now() - timedelta(days=days)).timestamp()
            for filename in os.listdir(log_dir):
                filepath = os.path.join(log_dir, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff_timestamp:
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
    except Exception as e:
        db.rollback()

@router.get("")
def get_history(
    search: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    # Auto-prune records older than 10 days
    prune_old_records_and_logs(db, days=10)

    # Query command history table
    query = db.query(CommandHistoryModel)
    
    if status and status.lower() != 'all':
        query = query.filter(CommandHistoryModel.status == status)
    if search:
        query = query.filter(
            (CommandHistoryModel.user_prompt.like(f"%{search}%")) |
            (CommandHistoryModel.command.like(f"%{search}%")) |
            (CommandHistoryModel.task_name.like(f"%{search}%"))
        )
        
    records = query.order_by(CommandHistoryModel.created_at.desc()).limit(limit).all()
    
    # Also fetch tasks if command history is sparse
    results = []
    for r in records:
        results.append({
            "id": r.id,
            "task_name": r.task_name,
            "user_prompt": r.user_prompt,
            "command": r.command,
            "working_directory": r.working_directory,
            "risk_level": r.risk_level,
            "status": r.status,
            "exit_code": r.exit_code,
            "stdout": r.stdout,
            "stderr": r.stderr,
            "duration_seconds": r.duration_seconds,
            "created_at": r.created_at.isoformat() + "Z" if r.created_at and not r.created_at.isoformat().endswith("Z") else (r.created_at.isoformat() if r.created_at else "")
        })
        
    return {"history": results, "retention_days": 10}

@router.post("")
def record_command(req: RecordHistoryRequest, db: Session = Depends(get_db)):
    """API endpoint to log CLI or single-command executions into history"""
    prune_old_records_and_logs(db, days=10)

    record_id = f"cmd-{uuid.uuid4().hex[:8]}"
    history_entry = CommandHistoryModel(
        id=record_id,
        user_prompt=req.user_prompt,
        command=req.command,
        task_name=req.task_name or "CLI Command",
        working_directory=req.working_directory or ".",
        risk_level=req.risk_level or "low",
        status=req.status or "completed",
        exit_code=req.exit_code or 0,
        stdout=req.stdout or "",
        stderr=req.stderr or "",
        duration_seconds=req.duration_seconds or 0.0,
        created_at=datetime.utcnow()
    )

    db.add(history_entry)
    db.commit()

    return {"status": "success", "id": record_id}

@router.delete("")
def clear_history(db: Session = Depends(get_db)):
    """Clear all command history records and log files"""
    db.query(CommandHistoryModel).delete()
    db.query(TaskModel).delete()
    db.commit()
    prune_old_records_and_logs(db, days=0)  # Prune all logs
    return {"status": "cleared"}
