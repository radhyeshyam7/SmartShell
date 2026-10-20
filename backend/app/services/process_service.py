import psutil
import os
import sys
from typing import List, Dict

class ProcessService:
    """System Metrics and Process Monitoring Service via psutil"""
    
    def get_system_metrics(self) -> Dict:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            "os": os.name,
            "platform": sys.platform,
            "python_version": sys.version.split()[0],
            "cpu_percent": cpu_percent,
            "memory": {
                "total_mb": round(mem.total / (1024 * 1024), 2),
                "available_mb": round(mem.available / (1024 * 1024), 2),
                "used_mb": round(mem.used / (1024 * 1024), 2),
                "percent": mem.percent
            },
            "disk": {
                "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
                "free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
                "percent": disk.percent
            }
        }

    def list_processes(self, limit: int = 50) -> List[Dict]:
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
            try:
                info = proc.info
                mem_mb = round(info['memory_info'].rss / (1024 * 1024), 2) if info['memory_info'] else 0.0
                processes.append({
                    "pid": info['pid'],
                    "name": info['name'],
                    "cpu_percent": info['cpu_percent'] or 0.0,
                    "memory_mb": mem_mb,
                    "status": info['status']
                })
            except Exception:
                continue

        processes.sort(key=lambda x: x['memory_mb'], reverse=True)
        return processes[:limit]

    def terminate_process(self, pid: int) -> bool:
        if psutil.pid_exists(pid):
            proc = psutil.Process(pid)
            proc.terminate()
            return True
        return False

process_service = ProcessService()
