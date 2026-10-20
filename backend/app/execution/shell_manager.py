import os
import subprocess
from typing import Tuple

class ShellManager:
    """Cross-platform shell abstraction layer for Windows (CMD/PowerShell) and POSIX (Bash/Zsh)"""
    
    def __init__(self):
        self.is_windows = os.name == 'nt'
        self.default_shell = "powershell" if self.is_windows else "bash"

    def prepare_command(self, command: str, requested_shell: str = "auto") -> Tuple[str, bool]:
        """
        Wraps and formats command for appropriate host OS shell execution.
        Returns (executable_command_str, use_shell_bool)
        """
        cmd_str = command.strip()
        
        if not self.is_windows:
            # POSIX Bash execution
            return cmd_str, True

        # Windows Execution
        import re
        cmd_str = re.sub(r'\bWin_LogicalDisk\b', 'Win32_LogicalDisk', cmd_str, flags=re.IGNORECASE)
        
        ps_keywords = ['get-', 'new-', 'set-', 'remove-', 'select-string', 'where-object', 'out-file', 'test-path', 'start-process', 'stop-process']
        is_ps_cmdlet = any(kw in cmd_str.lower() for kw in ps_keywords)
        
        if is_ps_cmdlet or requested_shell.lower() == "powershell":
            if not cmd_str.lower().startswith('powershell'):
                formatted_arg = subprocess.list2cmdline([cmd_str])
                return f'powershell -NoProfile -ExecutionPolicy Bypass -Command {formatted_arg}', True

        return cmd_str, True

shell_manager = ShellManager()
