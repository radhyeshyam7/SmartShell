from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.app.ai.planner import task_planner, TaskPlan
from backend.app.execution.task_manager import task_manager
from backend.app.ai.context_manager import context_manager

router = APIRouter(prefix="/ai", tags=["AI Terminal"])

class PromptRequest(BaseModel):
    prompt: str
    working_directory: str = "."

class PlanResponse(BaseModel):
    task_id: str
    task_plan: TaskPlan

@router.post("/plan", response_model=PlanResponse)
def generate_plan(req: PromptRequest):
    if not req.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty.")

    try:
        ctx_summary = context_manager.get_context_summary()
        task_plan = task_planner.plan_task(req.prompt, req.working_directory, ctx_summary)
        
        # Save pending task to database
        task_id = task_manager.create_task(req.prompt, task_plan)
        
        return PlanResponse(task_id=task_id, task_plan=task_plan)
    except Exception as e:
        error_msg = str(e)
        if "503" in error_msg or "UNAVAILABLE" in error_msg:
            raise HTTPException(status_code=503, detail="Gemini API is currently busy. Please try again in a moment or change the model in Settings.")
        elif "GEMINI_API_KEY" in error_msg:
            raise HTTPException(status_code=400, detail="Gemini API Key is missing. Please configure it in Settings.")
        else:
            raise HTTPException(status_code=500, detail=f"Failed to generate task plan: {error_msg}")
