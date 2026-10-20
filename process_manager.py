import psutil
import os
import signal
from typing import Dict, List
from config import MAX_BACKGROUND_PROCESSES, DEFAULT_PRIORITY

class ProcessManager:
    def __init__(self):
        self.background_processes: Dict[int, psutil.Process] = {}
        
    def add_background_process(self, pid: int) -> bool:
        """Add a process to background monitoring"""
        if len(self.background_processes) >= MAX_BACKGROUND_PROCESSES:
            return False
            
        try:
            process = psutil.Process(pid)
            self.background_processes[pid] = process
            return True
        except psutil.NoSuchProcess:
            return False

    def set_priority(self, pid: int, priority: int) -> bool:
        """Change process priority (nice value)"""
        try:
            process = psutil.Process(pid)
            process.nice(priority)
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def suspend_process(self, pid: int) -> bool:
        """Suspend a process (SIGSTOP)"""
        try:
            process = psutil.Process(pid)
            process.suspend()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def resume_process(self, pid: int) -> bool:
        """Resume a suspended process (SIGCONT)"""
        try:
            process = psutil.Process(pid)
            process.resume()
            return True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False

    def list_processes(self) -> List[Dict]:
        """List all managed processes and their status"""
        processes = []
        for pid, process in self.background_processes.items():
            try:
                processes.append({
                    'pid': pid,
                    'name': process.name(),
                    'status': process.status(),
                    'cpu_percent': process.cpu_percent(),
                    'memory_percent': process.memory_percent(),
                    'priority': process.nice()
                })
            except psutil.NoSuchProcess:
                self.background_processes.pop(pid)
        return processes
