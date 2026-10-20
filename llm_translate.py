# LLM translation/explanation layer using Google Gemini via google-genai
# Demonstrates high-level interaction with an external language model API (network I/O).
import logging
from typing import Optional, Dict, List, Tuple
import json
import os
import time

from google import genai
from config import GEMINI_API_KEY, GEMINI_MODEL

class LLMTranslator:
    """Translate natural language to shell commands and explain executions using Gemini.
    This layer demonstrates a user-space interface to an external LLM (no local model downloads).
    """
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment (.env).")
        # Initialize client with the API key
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.model_name = GEMINI_MODEL or 'gemini-3.5-flash-lite'
        self.last_error = None

    def _generate_content_with_retry(self, prompt: str) -> Optional[object]:
        """Generate content with automatic retry and model fallback for 503/429 errors"""
        models_to_try = [self.model_name]
        for fallback in ['gemini-3.5-flash-lite', 'gemini-3.5-flash', 'gemini-3.8-flash']:
            if fallback not in models_to_try:
                models_to_try.append(fallback)

        last_exception = None
        for model_id in models_to_try:
            for attempt in range(2):
                try:
                    response = self.client.models.generate_content(
                        model=model_id,
                        contents=prompt
                    )
                    return response
                except Exception as e:
                    last_exception = e
                    err_str = str(e)
                    if "503" in err_str or "UNAVAILABLE" in err_str or "429" in err_str:
                        logging.warning(f"Model {model_id} returned transient error ({err_str}). Retrying...")
                        time.sleep(1)
                        continue
                    else:
                        break

        if last_exception:
            raise last_exception
        return None

    def translate_command(self, natural_command: str) -> str:
        """Translate natural language to shell command"""
        self.last_error = None
        try:
            import re
            os_info = "Windows PowerShell/CMD" if os.name == 'nt' else "Linux/macOS Bash"
            prompt = (
                f"Convert this natural language command to a single shell command for {os_info} "
                "(return ONLY the raw executable command text, no markdown, no explanation). "
                "CRITICAL WINDOWS RULE: If querying disk drives via WMI/CIM, always use Win32_LogicalDisk (never Win_LogicalDisk) "
                "or (Get-PSDrive -PSProvider FileSystem). "
                f"Command request: {natural_command}"
            )
            response = self._generate_content_with_retry(prompt)
            
            if not response or not response.text:
                logging.warning(f"Empty response from Gemini for input: {natural_command}")
                return ""
                
            cmd = response.text.strip()
            if cmd.startswith("```"):
                lines = [l for l in cmd.split('\n') if not l.startswith("```")]
                cmd = " ".join(lines).strip()

            # Auto-correct common LLM WMI class typos
            cmd = re.sub(r'\bWin_LogicalDisk\b', 'Win32_LogicalDisk', cmd, flags=re.IGNORECASE)
            return cmd
            
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"Gemini API error: {str(e)}")
            return ""

    def explain_execution(self, command: str, output: Optional[str]) -> str:
        """Explain what happened during command execution"""
        self.last_error = None
        try:
            prompt = f"Explain what this shell command did at the OS level:\nCommand: {command}\nOutput: {output or '<no output>'}"
            response = self._generate_content_with_retry(prompt)
            
            if not response or not response.text:
                return "Explanation unavailable."
                
            return response.text.strip()
            
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"Gemini explain error: {str(e)}")
            return "Explanation unavailable (API error)."

    def _parse_structured_response(self, text: str) -> Dict:
        """Parse LLM response into structured format"""
        try:
            # Try to extract JSON-like structure
            if '{' in text and '}' in text:
                json_str = text[text.find('{'):text.rfind('}')+1]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback parsing for key-value format
        result = {}
        for line in text.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                result[key.strip('- ').strip()] = value.strip()
        return result

    def parse_command_intent(self, user_input: str) -> Dict:
        """Enhanced command parsing with support for package installation, general shell commands, and clarification follow-ups"""
        self.last_error = None
        os_info = "Windows PowerShell/CMD" if os.name == 'nt' else "Linux/macOS Bash"

        drives_str = "C:\\, D:\\"
        try:
            from backend.app.services.drive_service import drive_service
            drives = drive_service.list_drives()
            drives_str = ", ".join([f"{d['drive_letter']}:\\" for d in drives])
        except Exception:
            pass

        prompt = f"""
        Analyze this terminal user request on {os_info} and return JSON matching one of these formats:

        Format 1 (For package/venv installation):
        {{
            "type": "install",
            "venv_name": "venv",
            "packages": {{
                "main": ["numpy", "pandas"],
                "dependencies": []
            }}
        }}

        Format 2 (For specific shell commands where target path/drive is clear or when requested across all drives / system-wide):
        {{
            "type": "command",
            "commands": ["dir"]
        }}

        Format 3 (For file search/copy/move/delete requests where target drive or directory is NOT specified or ambiguous):
        {{
            "type": "clarification_needed",
            "question": "Which drive or folder would you like to target? (Available drives: {drives_str})"
        }}

        Format 4 (For academic OS concept simulator requests like CPU scheduling, Memory allocation, Page replacement, Banker's algorithm, Disk scheduling):
        {{
            "type": "simulator",
            "simulator_category": "cpu_scheduling",
            "algorithm": "ROUND_ROBIN"
        }}

        Format 5 (For SmartShell OS Digital Twin virtual environment operations: inspecting virtual OS state, creating/killing virtual processes, allocating virtual memory, checking deadlock/Banker in virtual OS, comparing scheduling algorithms, snapshots, invariant verification):
        {{
            "type": "digital_twin",
            "instruction": "dt status"
        }}

        CRITICAL CLARIFICATION RULE:
        - If the request explicitly mentions "digital twin", "virtual os", "virtual process", "virtual memory", "virtual disk", "virtual file", "compare scheduling", "snapshot", "invariant", or starts with "dt", use Format 5 with type "digital_twin".
        - If the request asks to simulate an OS concept without digital twin state context (CPU scheduling, Round Robin, FCFS, SJF, Memory allocation, First-Fit, Best-Fit, Worst-Fit, Page replacement, FIFO, LRU, Optimal, Banker's algorithm, Deadlock, Disk scheduling, SSTF, SCAN, C-SCAN, LOOK, C-LOOK), use Format 4 with type "simulator". Set simulator_category to one of ["cpu_scheduling", "memory_allocation", "page_replacement", "bankers_algorithm", "disk_scheduling"]. DO NOT ask for drive clarification.
        - If the user explicitly mentions "all drives", "whole system", "system wide", "everywhere", or specifies a drive (like C:, D:) or folder, use Format 2.
        - Only if the target drive or folder is completely unspecified for a file/folder request, use Format 3 so SmartShell prompts the user to specify the target drive or folder.

        Mounted Drives on System: {drives_str}

        Request: {user_input}
        """

        try:
            response = self._generate_content_with_retry(prompt)
            result = self._parse_structured_response(response.text)
            logging.info(f"Parsed intent: {result}")
            return result
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"Parse error: {str(e)}")
            return {}

    def explain_package_installation(self, output: str) -> str:
        """Generate concise installation explanation"""
        self.last_error = None
        prompt = """
        Analyze this package installation output and explain briefly:
        1. What was installed/attempted (package names and versions)
        2. Any installation errors and their causes
        3. Version compatibility issues (if any)
        4. Required vs optional dependencies
        Keep the explanation short and focused on installation details only.

        Installation output:
        {output}
        """
        
        try:
            response = self._generate_content_with_retry(prompt.format(output=output))
            return response.text.strip()
        except Exception as e:
            self.last_error = str(e)
            logging.error(f"Explanation error: {str(e)}")
            return "Could not generate installation explanation."

    def generate_command_sequence(self, intent: Dict, user_input: str = "") -> List[str]:
        """Generate command sequence for venv, package installation, or general shell commands"""
        commands = []
        
        try:
            intent_type = intent.get('type')
            if intent_type == 'install':
                venv_name = intent.get('venv_name', 'venv')
                packages = intent.get('packages', {}).get('main', [])
                
                if packages:
                    commands.append(f"python -m venv {venv_name}")
                    if os.name == 'nt':
                        commands.append(f"{venv_name}\\Scripts\\activate.bat")
                    else:
                        commands.append(f"source {venv_name}/bin/activate")
                    
                    packages = [pkg for pkg in packages if pkg.lower() != 'python']
                    if packages:
                        commands.append(f"pip install {' '.join(packages)}")
            elif intent.get('commands'):
                cmds = intent['commands']
                if isinstance(cmds, list):
                    commands.extend(cmds)
                else:
                    commands.append(str(cmds))
            elif intent.get('command'):
                commands.append(str(intent['command']))
                
            # Fallback to direct translation if no command resolved
            if not commands and user_input:
                cmd = self.translate_command(user_input)
                if cmd:
                    commands.append(cmd)

            logging.info(f"Generated commands: {commands}")
            return commands
            
        except Exception as e:
            logging.error(f"Command generation error: {str(e)}")
            return []

    def generate_file_modification_script(self, filename: str, changes: str) -> str:
        """Generate a safer Python script to modify a file"""
        script_content = f"""
import os

def modify_file():
    filename = "{filename}"
    
    # Check permissions first
    if not os.path.exists(filename):
        print(f"Error: File {{filename}} does not exist")
        return False
        
    if not os.access(filename, os.R_OK | os.W_OK):
        print(f"Error: Permission denied for {{filename}}")
        return False
        
    try:
        with open(filename, 'r') as f:
            content = f.read()
            
        # Apply changes: {changes}
        # Modify content here based on changes
        
        with open(filename, 'w') as f:
            f.write(content)
            
        print(f"Successfully modified {{filename}}")
        return True
        
    except Exception as e:
        print(f"Error modifying file: {{str(e)}}")
        return False

if __name__ == '__main__':
    modify_file()
"""
        script_name = "temp_modifier.py"
        try:
            with open(script_name, 'w') as f:
                f.write(script_content)
            return script_name
        except Exception as e:
            logging.error(f"Error creating modifier script: {str(e)}")
            return ""

    def is_safe_operation(self, path: str, operation: str) -> bool:
        """Enhanced safety check for both file and directory operations"""
        unsafe_paths = [
            '/etc', '/sys', '/boot', '/root', 
            'C:\\Windows', 'C:\\Program Files'
        ]
        
        if any(unsafe in path for unsafe in unsafe_paths):
            return False
            
        try:
            if operation == 'directory':
                if os.path.exists(path):
                    return os.access(path, os.W_OK)
                return os.access(os.path.dirname(path) or '.', os.W_OK)
            else:
                return self.is_safe_file_operation(path)
        except (IOError, PermissionError):
            return False

    def is_safe_file_operation(self, filepath: str) -> bool:
        """Enhanced safety check for file operations"""
        # Check unsafe paths
        unsafe_paths = [
            '/etc', '/sys', '/boot', '/root', 
            'C:\\Windows', 'C:\\Program Files'
        ]
        if any(unsafe in filepath for unsafe in unsafe_paths):
            return False
            
        # Check if file exists and we have permission
        try:
            if os.path.exists(filepath):
                # Test read permission
                with open(filepath, 'r'):
                    pass
                # Test write permission
                with open(filepath, 'a'):
                    pass
                return True
            else:
                # For new files, check directory permission
                directory = os.path.dirname(filepath) or '.'
                return os.access(directory, os.W_OK)
        except (IOError, PermissionError):
            return False

    def explain_package(self, package_name: str) -> str:
        """Get concise package purpose and version info"""
        prompt = f"""
        Explain briefly:
        1. What is {package_name} used for (1-2 sentences)
        2. Latest stable version
        3. Key dependencies needed
        Keep it very short and installation-focused.
        """
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception:
            return f"Could not fetch info for {package_name}"
