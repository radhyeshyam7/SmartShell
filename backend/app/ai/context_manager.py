from typing import List, Dict, Optional
import os

class ContextManager:
    """Session conversation memory for follow-up prompt resolution, entity tracking, and pronoun resolution"""
    
    def __init__(self):
        self.history: List[Dict[str, str]] = []
        self.current_working_dir: str = os.getcwd()
        self.active_drive: str = os.path.splitdrive(os.getcwd())[0] or "C:"
        self.last_venv: str = ""
        self.recent_files: List[str] = []
        self.recent_directories: List[str] = []
        self.recent_commands: List[str] = []

    def add_turn(self, prompt: str, summary: str, working_dir: str = "", venv: str = "", files: Optional[List[str]] = None, dirs: Optional[List[str]] = None, command: str = ""):
        if working_dir:
            self.current_working_dir = working_dir
            drive = os.path.splitdrive(working_dir)[0]
            if drive:
                self.active_drive = drive
        if venv:
            self.last_venv = venv
        if files:
            for f in files:
                if f not in self.recent_files:
                    self.recent_files.append(f)
            self.recent_files = self.recent_files[-15:]
        if dirs:
            for d in dirs:
                if d not in self.recent_directories:
                    self.recent_directories.append(d)
            self.recent_directories = self.recent_directories[-10:]
        if command:
            self.recent_commands.append(command)
            self.recent_commands = self.recent_commands[-10:]

        self.history.append({
            "prompt": prompt,
            "summary": summary,
            "working_dir": self.current_working_dir,
            "active_drive": self.active_drive,
            "venv": self.last_venv,
            "command": command
        })
        if len(self.history) > 15:
            self.history.pop(0)

    def resolve_follow_up_reference(self, prompt: str) -> str:
        """Resolve pronouns like 'them', 'that folder', 'same location', 'undo' to recent context"""
        lower_p = prompt.lower()
        
        # Check for undo request
        if lower_p in ["undo", "undo last operation", "undo that"]:
            if self.recent_commands:
                last_cmd = self.recent_commands[-1]
                return f"Undo action for last command: {last_cmd}"

        # Resolve 'them' or 'those files'
        if any(ref in lower_p for ref in ["them", "those files", "the files found", "these files"]):
            if self.recent_files:
                files_str = ", ".join(self.recent_files[:5])
                return f"{prompt} (targeting previously referenced files: {files_str})"

        # Resolve 'that folder', 'same location', 'that directory'
        if any(ref in lower_p for ref in ["that folder", "same location", "that directory", "the same folder"]):
            if self.recent_directories:
                target_dir = self.recent_directories[-1]
                return f"{prompt} in folder {target_dir}"
            elif self.current_working_dir:
                return f"{prompt} in folder {self.current_working_dir}"

        return prompt

    def get_context_summary(self) -> str:
        if not self.history and not self.recent_files:
            return f"Current Working Dir: {self.current_working_dir} | Active Drive: {self.active_drive}"
            
        lines = [
            f"Current Working Dir: {self.current_working_dir}",
            f"Active Drive: {self.active_drive}"
        ]
        if self.last_venv:
            lines.append(f"Active Virtual Environment: {self.last_venv}")
        if self.recent_files:
            lines.append(f"Recent Referenced Files: {', '.join(self.recent_files[-5:])}")
        if self.recent_directories:
            lines.append(f"Recent Referenced Directories: {', '.join(self.recent_directories[-3:])}")
            
        lines.append("Recent Interaction History:")
        for turn in self.history[-3:]:
            lines.append(f"- User: {turn['prompt']} | Result: {turn['summary']}")
            
        return "\n".join(lines)

    def clear(self):
        self.history.clear()
        self.recent_files.clear()
        self.recent_directories.clear()
        self.recent_commands.clear()
        self.current_working_dir = os.getcwd()
        self.active_drive = os.path.splitdrive(self.current_working_dir)[0] or "C:"
        self.last_venv = ""

context_manager = ContextManager()
