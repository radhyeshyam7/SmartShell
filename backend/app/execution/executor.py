import os
import subprocess
import time
import logging
from pathlib import Path
from typing import Tuple, Optional, Callable
from backend.app.execution.shell_manager import shell_manager
from backend.app.utils.sanitization import sanitize_text
from backend.app.config import settings

class CommandExecutor:
    """Subprocess command execution engine with working directory state & UTF-8 encoding handling"""
    
    def resolve_venv_command(self, command: str, working_dir: str) -> str:
        """
        Resolves python/pip commands to target virtual environment binaries if a venv exists in working_dir.
        Fixes global pip installation leakage issues.
        """
        cmd_parts = command.strip().split()
        if not cmd_parts:
            return command
            
        base_binary = cmd_parts[0].lower()
        if base_binary not in ['python', 'pip', 'python3', 'pip3']:
            return command

        # Search for virtualenv folders in working_dir or parent directories
        target_dir = Path(working_dir).resolve()
        possible_venvs = ['venv', 'env', 'dev_env', 'ml_env', 'data_env', '.venv']
        
        # Check if user specified a venv in the command or working dir contains one
        for venv_name in possible_venvs:
            venv_path = target_dir / venv_name
            if venv_path.exists() and venv_path.is_dir():
                if os.name == 'nt':
                    py_bin = venv_path / "Scripts" / "python.exe"
                    pip_bin = venv_path / "Scripts" / "pip.exe"
                else:
                    py_bin = venv_path / "bin" / "python"
                    pip_bin = venv_path / "bin" / "pip"

                if base_binary in ['python', 'python3'] and py_bin.exists():
                    cmd_parts[0] = str(py_bin)
                    return " ".join(cmd_parts)
                elif base_binary in ['pip', 'pip3'] and pip_bin.exists():
                    cmd_parts[0] = str(pip_bin)
                    return " ".join(cmd_parts)
                    
        return command

    def execute_command(
        self, 
        command: str, 
        working_dir: str = ".",
        shell: str = "auto",
        timeout: int = 300,
        output_callback: Optional[Callable[[str, str], None]] = None
    ) -> Tuple[int, str, str, float]:
        """
        Executes command with UTF-8 decoding fallback, timeout handling, and secret redaction.
        Returns (exit_code, stdout, stderr, duration_seconds)
        """
        start_time = time.time()
        
        # Resolve venv python/pip if applicable
        resolved_cmd = self.resolve_venv_command(command, working_dir)
        prepared_cmd, use_shell = shell_manager.prepare_command(resolved_cmd, shell)
        
        abs_cwd = str(Path(working_dir).resolve())
        if not os.path.exists(abs_cwd):
            os.makedirs(abs_cwd, exist_ok=True)

        try:
            process = subprocess.Popen(
                prepared_cmd,
                cwd=abs_cwd,
                shell=use_shell,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=False  # Read bytes first for safe UTF-8 decoding fallback
            )

            try:
                stdout_bytes, stderr_bytes = process.communicate(timeout=timeout)
            except subprocess.TimeoutExpired:
                process.kill()
                stdout_bytes, stderr_bytes = process.communicate()
                duration = time.time() - start_time
                return -1, "", f"Execution timed out after {timeout} seconds.", duration

            duration = time.time() - start_time
            
            # Safe UTF-8 decoding with fallback replacement (Fixes UnicodeDecodeError on Windows)
            stdout = stdout_bytes.decode('utf-8', errors='replace') if stdout_bytes else ""
            stderr = stderr_bytes.decode('utf-8', errors='replace') if stderr_bytes else ""

            # Truncate if exceeds max length
            if len(stdout) > settings.MAX_OUTPUT_LENGTH:
                stdout = stdout[:settings.MAX_OUTPUT_LENGTH] + "\n...[Output Truncated]"
            if len(stderr) > settings.MAX_OUTPUT_LENGTH:
                stderr = stderr[:settings.MAX_OUTPUT_LENGTH] + "\n...[Output Truncated]"

            # Sanitize secrets from output
            clean_stdout = sanitize_text(stdout)
            clean_stderr = sanitize_text(stderr)

            if output_callback:
                if clean_stdout: output_callback("stdout", clean_stdout)
                if clean_stderr: output_callback("stderr", clean_stderr)

            return process.returncode, clean_stdout, clean_stderr, round(duration, 3)

        except Exception as e:
            duration = time.time() - start_time
            err_msg = sanitize_text(f"Execution Error: {str(e)}")
            logging.error(err_msg)
            return -1, "", err_msg, round(duration, 3)

executor = CommandExecutor()
