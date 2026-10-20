import json
import os
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from backend.app.ai.gemini_client import gemini_client
from backend.app.execution.risk_analyzer import risk_analyzer
from backend.app.config import settings

class StepPlan(BaseModel):
    id: str = Field(description="Unique step identifier, e.g. step_1")
    description: str = Field(description="Clear explanation of what this step does")
    command: str = Field(description="Raw OS command to execute")
    shell: str = Field(default="auto", description="Target shell: cmd, powershell, bash, or auto")
    working_directory: str = Field(default=".", description="Relative or absolute working directory for this step")
    depends_on: List[str] = Field(default_factory=list, description="IDs of steps that must complete successfully before this step runs")
    risk_level: str = Field(default="low", description="Evaluated risk level: low, medium, high, critical")
    requires_approval: bool = Field(default=True, description="Whether explicit user approval is required")

class TaskPlan(BaseModel):
    task_name: str = Field(description="Short descriptive name for the overall task")
    summary: str = Field(description="High-level summary of what will be accomplished")
    working_directory: str = Field(default=".", description="Root working directory for the task")
    steps: List[StepPlan] = Field(default_factory=list, description="Ordered execution steps")

class TaskPlanner:
    """AI Multi-Command DAG Task Planner"""
    
    def plan_task(self, user_prompt: str, current_dir: str = ".", context: str = "") -> TaskPlan:
        os_name = "Windows (PowerShell/CMD)" if os.name == 'nt' else "Linux/macOS (Bash)"
        
        system_instruction = f"""
You are an expert OS system administrator and software engineer.
Convert the user request into an ordered, multi-step execution plan for {os_name}.

CRITICAL REQUIREMENTS:
1. Return ONLY a single valid JSON object matching this schema:
{{
  "task_name": "Task Title",
  "summary": "Brief summary",
  "working_directory": ".",
  "steps": [
    {{
      "id": "step_1",
      "description": "Description of step 1",
      "command": "command_to_run",
      "shell": "auto",
      "working_directory": ".",
      "depends_on": []
    }}
  ]
}}
2. For multi-command requests, break down every logical operation into an individual step step_1, step_2... with depends_on linking prerequisite steps.
3. For Windows commands:
   - For file listing: use `dir` or `Get-ChildItem`
   - For file creation: use `type nul > filename` or `New-Item -ItemType File -Name filename`
   - For folder creation: use `mkdir folder_name`
   - For Python virtual environments: step_1 = `python -m venv venv_name`, step_2 = `pip install pkg1 pkg2`
4. Maintain relative working_directory accurately between steps (e.g. if step_1 is `mkdir ML_Project`, step_2 working_directory is `ML_Project`).
5. Max steps limit: {settings.MAX_STEPS_PER_TASK}.

Current working directory: {current_dir}
Session Context: {context}

User Request: {user_prompt}
"""

        raw_response = gemini_client.generate_content(system_instruction)
        
        # Parse JSON
        parsed_json = self._extract_json(raw_response)
        
        if not parsed_json or "steps" not in parsed_json:
            # Fallback for single command or parsing failure
            cmd = gemini_client.generate_content(f"Convert to a single raw shell command for {os_name}: {user_prompt}").strip()
            if cmd.startswith("```"):
                cmd = "\n".join([l for l in cmd.split('\n') if not l.startswith("```")]).strip()
            
            parsed_json = {
                "task_name": "Execute Command",
                "summary": f"Process request: {user_prompt}",
                "working_directory": current_dir,
                "steps": [
                    {
                        "id": "step_1",
                        "description": f"Execute {cmd}",
                        "command": cmd or "dir",
                        "shell": "auto",
                        "working_directory": current_dir,
                        "depends_on": []
                    }
                ]
            }

        # Independent Deterministic Safety Classification
        task_plan = TaskPlan(**parsed_json)
        for step in task_plan.steps:
            risk, req_app, _ = risk_analyzer.analyze_command(step.command, step.working_directory)
            step.risk_level = risk
            step.requires_approval = req_app

        return task_plan

    def _extract_json(self, text: str) -> Dict:
        try:
            if '{' in text and '}' in text:
                json_str = text[text.find('{'):text.rfind('}')+1]
                return json.loads(json_str)
        except Exception:
            pass
        return {}

task_planner = TaskPlanner()
