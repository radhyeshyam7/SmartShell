import os
from pathlib import Path
from typing import List, Set
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    PROJECT_NAME: str = "SmartShell 2.0 — Intelligent OS Assistant"
    VERSION: str = "2.0.0"
    API_PREFIX: str = "/api"
    
    # Gemini & Local AI Configuration
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    AI_PROVIDER: str = os.getenv("AI_PROVIDER", "gemini")  # 'gemini' or 'ollama'
    LOCAL_MODEL_URL: str = os.getenv("LOCAL_MODEL_URL", "http://localhost:11434")
    LOCAL_MODEL_NAME: str = os.getenv("LOCAL_MODEL_NAME", "llama3")

    # Database
    DATABASE_URL: str = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/smartshell.db")
    
    # Security & Filesystem Boundaries
    AUTHORIZED_ROOTS: List[str] = [str(BASE_DIR)]
    ALLOW_ALL_DIRECTORIES: bool = os.getenv("ALLOW_ALL_DIRECTORIES", "true").lower() in ("true", "1", "yes")
    
    SAFE_COMMANDS: Set[str] = {
        'ls', 'dir', 'pwd', 'cd', 'mkdir', 'rmdir', 'pip', 'python',
        'echo', 'cat', 'type', 'grep', 'findstr', 'ps', 'whoami',
        'get-childitem', 'get-process', 'new-item', 'select-string',
        'git', 'node', 'npm', 'npx', 'cargo', 'go'
    }
    
    DANGEROUS_COMMANDS: Set[str] = {
        'rm -rf /', 'sudo rm -rf', 'format c:', 'del /f /s /q c:\\windows',
        'shutdown', 'poweroff', 'mkfs', 'dd if=', ':(){:|:&};:', '> /dev/sda',
        'diskpart', 'reg delete'
    }

    # Features & Safety Controls
    ENABLE_RAG: bool = True
    ENABLE_ML_RISK: bool = True
    ANOMALY_THRESHOLD_ZSCORE: float = 2.5
    AUTO_APPROVE_LOW_RISK: bool = False
    EXECUTION_TIMEOUT: int = 300  # seconds
    MAX_OUTPUT_LENGTH: int = 100000  # characters
    MAX_STEPS_PER_TASK: int = 15

    class Config:
        extra = "ignore"

settings = Settings()
