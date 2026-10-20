import os
import psutil
from typing import List, Dict, Optional
from backend.app.config import settings

class DriveService:
    """Service to discover and query Windows drives and volume metadata"""

    @staticmethod
    def list_drives() -> List[Dict]:
        """Discover all mounted drives and retrieve capacity/metadata"""
        drives = []
        try:
            partitions = psutil.disk_partitions(all=True)
            for part in partitions:
                mount = part.mountpoint
                drive_letter = mount.split(':')[0].upper() if ':' in mount else mount
                
                drive_info = {
                    "device": part.device,
                    "mountpoint": mount,
                    "drive_letter": drive_letter,
                    "fstype": part.fstype or "NTFS",
                    "opts": part.opts,
                    "is_readable": False,
                    "total_bytes": 0,
                    "used_bytes": 0,
                    "free_bytes": 0,
                    "used_percent": 0.0,
                    "drive_type": DriveService._get_drive_type(part.opts, part.device)
                }

                try:
                    usage = psutil.disk_usage(mount)
                    drive_info.update({
                        "is_readable": True,
                        "total_bytes": usage.total,
                        "used_bytes": usage.used,
                        "free_bytes": usage.free,
                        "used_percent": round(usage.percent, 1)
                    })
                except Exception:
                    drive_info["is_readable"] = False

                drives.append(drive_info)
        except Exception:
            if os.name == 'nt':
                import string
                for letter in string.ascii_uppercase:
                    drive_path = f"{letter}:\\"
                    if os.path.exists(drive_path):
                        drives.append({
                            "device": f"{letter}:",
                            "mountpoint": drive_path,
                            "drive_letter": letter,
                            "fstype": "NTFS",
                            "opts": "rw",
                            "is_readable": os.access(drive_path, os.R_OK),
                            "total_bytes": 0,
                            "used_bytes": 0,
                            "free_bytes": 0,
                            "used_percent": 0.0,
                            "drive_type": "Fixed"
                        })

        return drives

    @staticmethod
    def _get_drive_type(opts: str, device: str) -> str:
        opts_lower = opts.lower()
        if "cdrom" in opts_lower:
            return "Optical"
        elif "removable" in opts_lower:
            return "Removable"
        elif "network" in opts_lower or "remote" in opts_lower:
            return "Network"
        else:
            return "Fixed"

drive_service = DriveService()
