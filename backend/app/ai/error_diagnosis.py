from typing import Dict
from backend.app.ai.gemini_client import gemini_client

class ErrorDiagnosis:
    """AI Error Diagnosis and Fix Suggestion Engine"""
    
    def diagnose_failure(self, command: str, stderr: str, stdout: str = "", working_dir: str = ".") -> Dict[str, str]:
        if not gemini_client.client:
            return {
                "problem": "Command failed with an error.",
                "suggested_fix": "Review the error output above.",
                "status": "AI Diagnosis unavailable (no API key configured)."
            }

        prompt = f"""
An OS command failed during execution. Analyze the sanitized output and explain the failure concisely.

Command: {command}
Working Directory: {working_dir}
Stdout: {stdout or '<none>'}
Stderr: {stderr or '<none>'}

Return JSON format:
{{
    "problem": "Clear 1-2 sentence explanation of why the command failed",
    "suggested_fix": "Concrete corrected command or action to fix the error"
}}
"""

        try:
            res = gemini_client.generate_content(prompt)
            if '{' in res and '}' in res:
                import json
                json_str = res[res.find('{'):res.rfind('}')+1]
                return json.loads(json_str)
        except Exception:
            pass

        return {
            "problem": f"Command returned error output: {stderr[:200] if stderr else 'Non-zero exit code'}",
            "suggested_fix": "Check path, permissions, or dependency installation."
        }

error_diagnosis = ErrorDiagnosis()
