import time
from typing import Dict, List, Optional, Any
from backend.app.digital_twin.models import VirtualFile
from backend.app.digital_twin.state import simulation_state
from backend.app.services.simulators import DiskScheduler as LegacyDiskSimulator

class DiskManager:
    """Manages virtual files, virtual disk tree, and disk head scheduling (strictly isolated from host OS)."""

    def __init__(self, state=None):
        self.state = state or simulation_state
        self.head_position = 50

    def create_file(
        self,
        path: str,
        content: str = "",
        size_kb: int = 1,
        is_directory: bool = False,
        owner_pid: Optional[str] = None
    ) -> Dict[str, Any]:
        """Creates a virtual file or directory in the isolated virtual filesystem."""
        with self.state._lock:
            # Clean path
            path = "/" + path.strip().strip("/").replace("\\", "/")
            if path in self.state.virtual_files:
                return {"success": False, "error": f"Virtual path '{path}' already exists."}

            # Check capacity
            current_used = sum(f.size_kb for f in self.state.virtual_files.values())
            if current_used + size_kb > self.state.total_disk_capacity:
                return {"success": False, "error": f"Virtual disk full: needed {size_kb} KB, but only {self.state.total_disk_capacity - current_used} KB available."}

            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            name = path.split("/")[-1] or "root"

            vfile = VirtualFile(
                path=path,
                name=name,
                is_directory=is_directory,
                size_kb=size_kb if not is_directory else 4,
                content=content if not is_directory else "",
                created_at=now_str,
                modified_at=now_str,
                owner_pid=owner_pid
            )
            self.state.virtual_files[path] = vfile

            msg = f"Created virtual {'directory' if is_directory else 'file'} '{path}' ({vfile.size_kb} KB)."
            self.state.add_event("DISK", msg, {"path": path, "size_kb": vfile.size_kb, "owner": owner_pid})
            return {"success": True, "file": vfile.model_dump(), "message": msg}

    def delete_file(self, path: str) -> Dict[str, Any]:
        """Deletes a virtual file or directory."""
        with self.state._lock:
            path = "/" + path.strip().strip("/").replace("\\", "/")
            if path == "/":
                return {"success": False, "error": "Cannot delete virtual root directory '/'."}

            if path not in self.state.virtual_files:
                return {"success": False, "error": f"Virtual file '{path}' not found."}

            # Check if directory has children
            children = [p for p in self.state.virtual_files.keys() if p != path and p.startswith(path + "/")]
            for child in children:
                del self.state.virtual_files[child]

            deleted_file = self.state.virtual_files.pop(path)
            msg = f"Deleted virtual file/directory '{path}' and {len(children)} children."
            self.state.add_event("DISK", msg, {"path": path, "deleted_count": len(children) + 1})
            return {"success": True, "message": msg}

    def read_file(self, path: str) -> Dict[str, Any]:
        """Reads content of a virtual file."""
        with self.state._lock:
            path = "/" + path.strip().strip("/").replace("\\", "/")
            if path not in self.state.virtual_files:
                return {"success": False, "error": f"Virtual file '{path}' not found."}
            f = self.state.virtual_files[path]
            if f.is_directory:
                return {"success": False, "error": f"'{path}' is a directory, not a file."}
            return {"success": True, "path": path, "content": f.content, "size_kb": f.size_kb}

    def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """Writes content into an existing virtual file or creates it."""
        with self.state._lock:
            path = "/" + path.strip().strip("/").replace("\\", "/")
            calc_size = max(1, len(content.encode("utf-8")) // 1024 + 1)
            if path in self.state.virtual_files:
                f = self.state.virtual_files[path]
                if f.is_directory:
                    return {"success": False, "error": f"'{path}' is a directory."}
                f.content = content
                f.size_kb = calc_size
                f.modified_at = time.strftime("%Y-%m-%d %H:%M:%S")
                msg = f"Updated virtual file '{path}' (New size: {calc_size} KB)."
                self.state.add_event("DISK", msg, {"path": path, "size_kb": calc_size})
                return {"success": True, "file": f.model_dump(), "message": msg}
            else:
                return self.create_file(path, content=content, size_kb=calc_size)

    def list_files(self, directory: str = "/") -> List[Dict[str, Any]]:
        """Lists files in the virtual filesystem."""
        with self.state._lock:
            directory = "/" + directory.strip().strip("/").replace("\\", "/")
            results = []
            for path, f in self.state.virtual_files.items():
                if directory == "/":
                    if path.count("/") == 1 or path == "/":
                        results.append(f.model_dump())
                else:
                    if path.startswith(directory + "/") and path[len(directory)+1:].count("/") == 0:
                        results.append(f.model_dump())
            return results

    def simulate_disk_scheduling(
        self,
        algorithm: str = "C-SCAN",
        track_requests: Optional[List[int]] = None,
        initial_head: Optional[int] = None,
        direction: str = "right"
    ) -> Dict[str, Any]:
        """Simulates disk arm head scheduling."""
        with self.state._lock:
            head = initial_head if initial_head is not None else self.head_position
            reqs = track_requests or [98, 183, 37, 122, 14, 124, 65, 67]
            res = LegacyDiskSimulator.simulate(algorithm, reqs, initial_head=head, direction=direction)

            # Update arm position to final track
            if res.get("sequence"):
                self.head_position = res["sequence"][-1]

            msg = f"Simulated {algorithm} Disk Scheduling: Head {head} -> {res['total_seek_distance']} total cylinders traversed."
            self.state.add_event("DISK", msg, res)
            return res
