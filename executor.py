import subprocess
import os
import psutil
import time
from typing import Tuple, Dict, List
import logging
from config import SAFE_COMMANDS, DANGEROUS_COMMANDS

class CommandExecutor:
    def __init__(self):
        self.running_processes: Dict[int, psutil.Process] = {}
        self.current_venv = None
        self.package_tracker = {}
        self.is_windows = os.name == 'nt'

    def is_safe_command(self, command: str) -> bool:
        """Check if command is safe to execute"""
        command_base = command.split()[0].lower()
        
        if any(dangerous in command.lower() for dangerous in DANGEROUS_COMMANDS):
            return False
            
        return command_base in SAFE_COMMANDS

    def setup_venv(self, name: str) -> bool:
        """Create and activate virtual environment"""
        try:
            venv_path = os.path.join(os.getcwd(), name)
            venv.create(venv_path, with_pip=True)
            self.current_venv = venv_path
            return True
        except Exception as e:
            logging.error(f"Venv creation error: {str(e)}")
            return False

    def execute_command(self, command: str, background: bool = False) -> Tuple[int, str, str]:
        """Execute a command and return its output"""
        try:
            import re
            cmd_to_run = command
            if self.is_windows:
                # Auto-correct common LLM WMI class typos
                cmd_to_run = re.sub(r'\bWin_LogicalDisk\b', 'Win32_LogicalDisk', cmd_to_run, flags=re.IGNORECASE)
                
                ps_keywords = ['get-', 'new-', 'set-', 'remove-', 'select-string', 'where-object', 'out-file', 'test-path', 'start-process', 'stop-process']
                if any(kw in cmd_to_run.lower() for kw in ps_keywords) and not cmd_to_run.lower().startswith('powershell'):
                    formatted_arg = subprocess.list2cmdline([cmd_to_run])
                    cmd_to_run = f'powershell -NoProfile -ExecutionPolicy Bypass -Command {formatted_arg}'

            use_shell = 'activate' in cmd_to_run or self.is_windows
            
            process = subprocess.Popen(
                cmd_to_run,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate()
            return process.pid, stdout, stderr
            
        except Exception as e:
            logging.error(f"Command execution error: {str(e)}")
            return -1, "", str(e)

    def execute_command_sequence(self, commands: List[str]) -> List[Tuple[int, str, str]]:
        """Execute a sequence of commands in order"""
        results = []
        for cmd in commands:
            if self.current_venv and 'pip install' in cmd:
                # Track installed packages
                packages = cmd.split('install ')[1].split()
                for pkg in packages:
                    self.package_tracker[pkg] = True
            
            pid, out, err = self.execute_command(cmd)
            results.append((pid, out, err))
        return results

    def get_process_info(self, pid: int) -> Dict:
        """Get information about a running process"""
        if pid in self.running_processes:
            proc = self.running_processes[pid]
            return {
                'pid': pid,
                'cpu_percent': proc.cpu_percent(),
                'memory_mb': proc.memory_info().rss / 1024 / 1024,
                'status': proc.status()
            }
        return {}
