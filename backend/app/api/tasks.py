from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict
from backend.app.database.database import get_db
from backend.app.database.models import TaskModel, StepModel
from backend.app.execution.task_manager import task_manager

router = APIRouter(prefix="/tasks", tags=["Task Engine"])

@router.get("/{task_id}")
def get_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    steps = db.query(StepModel).filter(StepModel.task_id == task_id).order_by(StepModel.step_index).all()
    
    return {
        "id": task.id,
        "task_name": task.task_name,
        "user_prompt": task.user_prompt,
        "summary": task.summary,
        "status": task.status,
        "working_directory": task.working_directory,
        "created_at": task.created_at.isoformat(),
        "steps": [
            {
                "id": s.id,
                "step_index": s.step_index,
                "description": s.description,
                "command": s.command,
                "shell": s.shell,
                "working_directory": s.working_directory,
                "depends_on": s.depends_on,
                "risk_level": s.risk_level,
                "requires_approval": s.requires_approval,
                "status": s.status,
                "exit_code": s.exit_code,
                "stdout": s.stdout,
                "stderr": s.stderr,
                "duration_seconds": s.duration_seconds
            } for s in steps
        ]
    }

@router.post("/{task_id}/approve")
def approve_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    task.status = "approved"
    db.commit()
    return {"status": "approved", "task_id": task_id}

@router.post("/{task_id}/reject")
def reject_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    task.status = "rejected"
    db.commit()
    return {"status": "rejected", "task_id": task_id}

@router.post("/{task_id}/execute")
def execute_task(task_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    task = db.query(TaskModel).filter(TaskModel.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found.")

    if task.status not in ["approved", "pending"]:
        raise HTTPException(status_code=400, detail=f"Cannot execute task in state '{task.status}'")

    background_tasks.add_task(task_manager.execute_task_sync, task_id)
    return {"status": "execution_started", "task_id": task_id}
