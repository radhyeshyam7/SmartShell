import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from backend.app.database.database import get_db
from backend.app.database.models import WorkflowModel

router = APIRouter(prefix="/workflows", tags=["Saved Workflows"])

class WorkflowCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    category: Optional[str] = "General"
    template_json: dict

DEFAULT_WORKFLOWS = [
    {
        "id": "wf_python_setup",
        "name": "Python ML Project Setup",
        "description": "Creates ML_Project folder, initializes venv, installs numpy, pandas, scikit-learn, and creates main.py",
        "category": "Python",
        "template_json": {
            "task_name": "Initialize ML Project",
            "summary": "Full Python ML environment setup",
            "working_directory": ".",
            "steps": [
                {"id": "step_1", "description": "Create ML_Project directory", "command": "mkdir ML_Project", "working_directory": "."},
                {"id": "step_2", "description": "Create ml_env virtual environment", "command": "python -m venv ml_env", "working_directory": "ML_Project", "depends_on": ["step_1"]},
                {"id": "step_3", "description": "Install ML libraries", "command": "pip install numpy pandas scikit-learn", "working_directory": "ML_Project", "depends_on": ["step_2"]},
                {"id": "step_4", "description": "Create starter main.py", "command": "type nul > main.py", "working_directory": "ML_Project", "depends_on": ["step_1"]}
            ]
        }
    },
    {
        "id": "wf_react_setup",
        "name": "React Vite Project Initialization",
        "description": "Creates frontend project using Vite and installs dependencies",
        "category": "Frontend",
        "template_json": {
            "task_name": "Initialize React Vite App",
            "summary": "Create React Vite frontend application",
            "working_directory": ".",
            "steps": [
                {"id": "step_1", "description": "Initialize Vite React app", "command": "npm create vite@latest frontend -- --template react-ts", "working_directory": "."},
                {"id": "step_2", "description": "Install npm dependencies", "command": "npm install", "working_directory": "frontend", "depends_on": ["step_1"]}
            ]
        }
    },
    {
        "id": "wf_code_audit",
        "name": "Project Code Audit & Report",
        "description": "Finds all Python files, counts them, and generates an audit report",
        "category": "Audit",
        "template_json": {
            "task_name": "Project Code Audit",
            "summary": "Audit codebase structure and generate report",
            "working_directory": ".",
            "steps": [
                {"id": "step_1", "description": "List Python files", "command": "dir *.py /s", "working_directory": "."},
                {"id": "step_2", "description": "Generate audit report file", "command": "echo Code Audit Completed > audit_report.txt", "working_directory": "."}
            ]
        }
    }
]

@router.get("")
def get_workflows(db: Session = Depends(get_db)):
    db_wfs = db.query(WorkflowModel).all()
    results = [
        {
            "id": w.id,
            "name": w.name,
            "description": w.description,
            "category": w.category,
            "template_json": w.template_json,
            "created_at": w.created_at.isoformat()
        } for w in db_wfs
    ]
    
    # Prepend built-in default workflows
    return {"workflows": DEFAULT_WORKFLOWS + results}

@router.post("")
def create_workflow(req: WorkflowCreateRequest, db: Session = Depends(get_db)):
    wf_id = f"wf_{uuid.uuid4().hex[:8]}"
    wf = WorkflowModel(
        id=wf_id,
        name=req.name,
        description=req.description,
        category=req.category,
        template_json=req.template_json,
        created_at=datetime.utcnow()
    )
    db.add(wf)
    db.commit()
    return {"id": wf_id, "name": req.name}
