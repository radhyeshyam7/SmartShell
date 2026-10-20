import asyncio
import uuid
import logging
from typing import Dict, List, Optional, Callable
from datetime import datetime
from backend.app.ai.planner import TaskPlan, StepPlan
from backend.app.execution.executor import executor
from backend.app.execution.risk_analyzer import risk_analyzer
from backend.app.ai.error_diagnosis import error_diagnosis
from backend.app.ai.context_manager import context_manager
from backend.app.database.database import SessionLocal
from backend.app.database.models import TaskModel, StepModel

class TaskExecutionManager:
    """Sequential DAG task manager with real-time streaming updates and SQLite persistence"""
    
    def __init__(self):
        self.active_tasks: Dict[str, TaskPlan] = {}
        self.listeners: List[Callable[[dict], None]] = []

    def register_listener(self, callback: Callable[[dict], None]):
        self.listeners.append(callback)

    def broadcast_event(self, event_type: str, data: dict):
        payload = {"event_type": event_type, "timestamp": datetime.utcnow().isoformat(), "data": data}
        for cb in self.listeners:
            try:
                cb(payload)
            except Exception:
                pass

    def create_task(self, prompt: str, task_plan: TaskPlan) -> str:
        task_id = f"task_{uuid.uuid4().hex[:8]}"
        db = SessionLocal()
        try:
            task_model = TaskModel(
                id=task_id,
                user_prompt=prompt,
                task_name=task_plan.task_name,
                summary=task_plan.summary,
                status="pending",
                working_directory=task_plan.working_directory
            )
            db.add(task_model)

            for idx, step in enumerate(task_plan.steps):
                step_model = StepModel(
                    id=step.id or f"{task_id}_s{idx+1}",
                    task_id=task_id,
                    step_index=idx + 1,
                    description=step.description,
                    command=step.command,
                    shell=step.shell,
                    working_directory=step.working_directory,
                    depends_on=step.depends_on,
                    risk_level=step.risk_level,
                    requires_approval=step.requires_approval,
                    status="pending"
                )
                db.add(step_model)

            db.commit()
            self.active_tasks[task_id] = task_plan
            return task_id
        finally:
            db.close()

    def execute_task_sync(self, task_id: str) -> dict:
        """Execute all steps sequentially in order with dependency checks"""
        db = SessionLocal()
        try:
            task_model = db.query(TaskModel).filter(TaskModel.id == task_id).first()
            if not task_model:
                raise ValueError(f"Task '{task_id}' not found.")

            task_model.status = "running"
            db.commit()

            self.broadcast_event("task_started", {"task_id": task_id, "task_name": task_model.task_name})

            step_results = {}
            has_failed = False
            current_work_dir = task_model.working_directory

            sorted_steps = db.query(StepModel).filter(StepModel.task_id == task_id).order_by(StepModel.step_index).all()

            for step in sorted_steps:
                # Check dependency status
                deps_failed = any(step_results.get(dep_id, {}).get("status") != "completed" for dep_id in (step.depends_on or []))
                
                if deps_failed or has_failed:
                    step.status = "skipped"
                    db.commit()
                    self.broadcast_event("step_skipped", {"task_id": task_id, "step_id": step.id, "reason": "Prerequisite step failed"})
                    continue

                step.status = "running"
                db.commit()
                self.broadcast_event("step_started", {
                    "task_id": task_id, 
                    "step_id": step.id, 
                    "command": step.command,
                    "description": step.description
                })

                # Determine effective working directory
                eff_cwd = step.working_directory if step.working_directory != "." else current_work_dir

                # Execute
                exit_code, stdout, stderr, duration = executor.execute_command(
                    command=step.command,
                    working_dir=eff_cwd,
                    shell=step.shell,
                    output_callback=lambda stream, text: self.broadcast_event("step_output", {
                        "task_id": task_id, "step_id": step.id, "stream": stream, "text": text
                    })
                )

                step.exit_code = exit_code
                step.stdout = stdout
                step.stderr = stderr
                step.duration_seconds = duration

                if exit_code == 0:
                    step.status = "completed"
                    step_results[step.id] = {"status": "completed"}
                    
                    # Update tracking venv / working dir if cd or venv was created
                    if step.command.strip().startswith("cd ") or step.command.strip().startswith("mkdir "):
                        target = step.command.split(maxsplit=1)[-1]
                        current_work_dir = target
                        
                else:
                    step.status = "failed"
                    step_results[step.id] = {"status": "failed"}
                    has_failed = True
                    
                    # Diagnose failure using AI
                    diag = error_diagnosis.diagnose_failure(step.command, stderr, stdout, eff_cwd)
                    self.broadcast_event("step_failed", {
                        "task_id": task_id,
                        "step_id": step.id,
                        "exit_code": exit_code,
                        "stderr": stderr,
                        "diagnosis": diag
                    })

                db.commit()

            task_model.status = "failed" if has_failed else "completed"
            db.commit()

            # Record session context
            context_manager.add_turn(task_model.user_prompt, task_model.summary, current_work_dir)

            self.broadcast_event("task_finished", {
                "task_id": task_id,
                "status": task_model.status,
                "task_name": task_model.task_name
            })

            return {"task_id": task_id, "status": task_model.status}

        finally:
            db.close()

task_manager = TaskExecutionManager()
