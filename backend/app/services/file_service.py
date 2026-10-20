import os
from pathlib import Path
from typing import List, Dict, Optional
from backend.app.config import settings

class FileService:
    """Safe File Explorer Service with Path Traversal Protection"""
    
    def validate_path(self, requested_path: str) -> Path:
        resolved = Path(requested_path).resolve()
        
        if settings.ALLOW_ALL_DIRECTORIES:
            return resolved
            
        for auth_root in settings.AUTHORIZED_ROOTS:
            auth_resolved = Path(auth_root).resolve()
            if resolved == auth_resolved or auth_resolved in resolved.parents:
                return resolved

        raise PermissionError(f"Access denied: Path '{requested_path}' is outside authorized directory boundaries.")

    def list_files(self, path: str = ".") -> List[Dict]:
        target = self.validate_path(path)
        if not target.exists() or not target.is_dir():
            raise FileNotFoundError(f"Directory '{path}' does not exist.")

        results = []
        for entry in os.scandir(target):
            try:
                stat = entry.stat()
                results.append({
                    "name": entry.name,
                    "path": entry.path,
                    "is_dir": entry.is_dir(),
                    "size_bytes": stat.st_size if not entry.is_dir() else 0,
                    "modified_at": stat.st_mtime
                })
            except Exception:
                continue

        results.sort(key=lambda x: (not x["is_dir"], x["name"].lower()))
        return results

    def read_file(self, path: str, max_bytes: int = 500000) -> str:
        target = self.validate_path(path)
        if not target.exists() or not target.is_file():
            raise FileNotFoundError(f"File '{path}' does not exist.")

        with open(target, 'rb') as f:
            content = f.read(max_bytes)
            return content.decode('utf-8', errors='replace')

    def create_file(self, path: str, content: str = "") -> bool:
        target = self.validate_path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

    def create_directory(self, path: str) -> bool:
        target = self.validate_path(path)
        target.mkdir(parents=True, exist_ok=True)
        return True

    def delete_item(self, path: str) -> bool:
        target = self.validate_path(path)
        if target.is_file():
            target.unlink()
        elif target.is_dir():
            import shutil
            shutil.rmtree(target)
        return True

file_service = FileService()
