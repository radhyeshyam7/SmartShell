import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Google Gemini configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.5-flash-lite')

# If you still need to support Hugging Face in future, keep HUGGINGFACE_TOKEN optional
HUGGINGFACE_TOKEN = os.getenv('HUGGINGFACE_TOKEN', None)

# Command Settings
SAFE_COMMANDS = {
    'ls', 'dir', 'pwd', 'cd', 'mkdir', 'rmdir', 'pip', 'python',
    'echo', 'cat', 'type', 'grep', 'findstr', 'ps', 'whoami'
}

DANGEROUS_COMMANDS = {
    'rm -rf', 'sudo', 'format', 'del', 'shutdown', 'poweroff',
    'mkfs', 'dd', ':(){:|:&};:', '> /dev/sda'
}

# File System Settings
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'smartshell.log')

# Process Settings
MAX_BACKGROUND_PROCESSES = 5
DEFAULT_PRIORITY = 0  # Normal priority

# Shell Settings
SHELL_PROMPT = "SmartShell> "
CONFIRMATION_REQUIRED = True
