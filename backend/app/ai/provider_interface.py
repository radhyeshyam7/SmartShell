import json
import logging
import urllib.request
from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from backend.app.config import settings

class BaseAIProvider(ABC):
    """Abstract base class for AI Providers (Gemini, Ollama, Offline Fallback)"""

    @abstractmethod
    def parse_intent(self, prompt: str, context_summary: str = "") -> Dict:
        pass

    @abstractmethod
    def generate_commands(self, intent: Dict, prompt: str) -> List[str]:
        pass

    @abstractmethod
    def diagnose_error(self, error_context: Dict) -> Dict:
        pass

class GeminiProvider(BaseAIProvider):
    """Gemini API Provider using google-genai SDK"""

    def __init__(self):
        from backend.app.ai.gemini_client import gemini_client
        self.client = gemini_client

    def parse_intent(self, prompt: str, context_summary: str = "") -> Dict:
        drives_str = "C:\\, D:\\"
        try:
            from backend.app.services.drive_service import drive_service
            drives = drive_service.list_drives()
            drives_str = ", ".join([f"{d['drive_letter']}:\\" for d in drives])
        except Exception:
            pass

        full_prompt = f"""
        Context: {context_summary}
        Analyze this terminal user request and return JSON matching one of these formats:
        Format 1 (For package/venv installation): {{"type": "install", "venv_name": "venv", "packages": {{"main": ["numpy"]}}}}
        Format 2 (For specific shell commands or system-wide requests): {{"type": "command", "commands": ["dir"]}}
        Format 3 (For ambiguous file search/copy/delete without drive/folder target): {{"type": "clarification_needed", "question": "Which drive or folder would you like to target? (Available drives: {drives_str})"}}

        Request: {prompt}
        """
        try:
            res_text = self.client.generate_content(full_prompt)
            if '{' in res_text and '}' in res_text:
                json_str = res_text[res_text.find('{'):res_text.rfind('}')+1]
                return json.loads(json_str)
        except Exception as e:
            logging.warning(f"GeminiProvider parse error: {str(e)}")
        return {"type": "command", "commands": [prompt]}

    def generate_commands(self, intent: Dict, prompt: str) -> List[str]:
        if intent.get("commands"):
            return intent["commands"]
        try:
            cmd = self.client.translate_command(prompt)
            return [cmd] if cmd else []
        except Exception:
            return [prompt]

    def diagnose_error(self, error_context: Dict) -> Dict:
        try:
            from backend.app.ai.error_diagnosis import error_diagnoser
            return error_diagnoser.diagnose(
                user_prompt=error_context.get("prompt", ""),
                command=error_context.get("command", ""),
                stdout=error_context.get("stdout", ""),
                stderr=error_context.get("stderr", ""),
                exit_code=error_context.get("exit_code", 1)
            )
        except Exception as e:
            return {"category": "unknown", "explanation": str(e), "proposed_recovery": None}

class OfflineDeterministicProvider(BaseAIProvider):
    """Fallback offline deterministic provider when no AI API key is available"""

    def parse_intent(self, prompt: str, context_summary: str = "") -> Dict:
        p_lower = prompt.lower()
        if any(kw in p_lower for kw in ["install", "pip install"]):
            pkgs = p_lower.replace("install", "").replace("pip", "").strip().split()
            return {"type": "install", "venv_name": "venv", "packages": {"main": pkgs}}
        return {"type": "command", "commands": [prompt]}

    def generate_commands(self, intent: Dict, prompt: str) -> List[str]:
        if intent.get("type") == "install":
            pkgs = " ".join(intent.get("packages", {}).get("main", []))
            return ["python -m venv venv", f"venv\\Scripts\\pip install {pkgs}"]
        return [prompt]

    def diagnose_error(self, error_context: Dict) -> Dict:
        stderr = error_context.get("stderr", "")
        if "File Not Found" in stderr or "cannot find the path" in stderr.lower():
            return {
                "category": "path_not_found",
                "explanation": "Target file or directory path does not exist.",
                "proposed_recovery": {"action": "check_path", "command": "dir"}
            }
        return {
            "category": "command_failed",
            "explanation": f"Command exited with code {error_context.get('exit_code', 1)}.",
            "proposed_recovery": None
        }

class AIProviderFactory:
    """Factory for selecting and instantiating AI providers with graceful fallback"""

    @staticmethod
    def get_provider() -> BaseAIProvider:
        provider_name = settings.AI_PROVIDER.lower()
        if provider_name == "gemini" and settings.GEMINI_API_KEY:
            try:
                return GeminiProvider()
            except Exception as e:
                logging.warning(f"Failed to load GeminiProvider ({str(e)}). Falling back to OfflineProvider.")
        
        return OfflineDeterministicProvider()

ai_provider_factory = AIProviderFactory()
