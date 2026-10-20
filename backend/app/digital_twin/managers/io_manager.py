from typing import Dict, List, Optional, Any
from backend.app.digital_twin.models import ProcessState
from backend.app.digital_twin.state import simulation_state

class IOManager:
    """Manages virtual I/O devices (DISK_IO, NETWORK_IO, CONSOLE_IO) and blocked I/O queues."""

    def __init__(self, state=None):
        self.state = state or simulation_state
        self.devices = ["DISK_IO", "NETWORK_IO", "CONSOLE_IO"]

    def request_io(self, pid: str, device: str = "DISK_IO", duration: int = 3) -> Dict[str, Any]:
        """Process issues an I/O request and blocks into the WAITING queue."""
        with self.state._lock:
            pid = pid.upper().strip()
            dev = device.upper().strip()

            if pid not in self.state.processes:
                return {"success": False, "error": f"Process {pid} not found."}

            proc = self.state.processes[pid]
            old_state = proc.state

            # Move to WAITING
            proc.state = ProcessState.WAITING
            proc.io_device = dev
            proc.io_remaining = duration

            if pid in self.state.ready_queue:
                self.state.ready_queue.remove(pid)
            if self.state.running_pid == pid:
                self.state.running_pid = None
            if pid not in self.state.waiting_queue:
                self.state.waiting_queue.append(pid)

            msg = f"Process {pid} requested {dev} I/O for {duration} ticks. Blocked: {old_state} -> WAITING."
            self.state.add_event("IO", msg, {"pid": pid, "device": dev, "duration": duration})
            return {"success": True, "pid": pid, "device": dev, "duration": duration, "message": msg}

    def tick(self, ticks: int = 1) -> Dict[str, Any]:
        """Advances I/O clock by specified ticks and wakes up processes upon I/O completion."""
        with self.state._lock:
            self.state.tick += ticks
            completed = []

            for pid in list(self.state.waiting_queue):
                proc = self.state.processes.get(pid)
                if not proc or not proc.io_device:
                    continue

                proc.io_remaining -= ticks
                if proc.io_remaining <= 0:
                    dev = proc.io_device
                    proc.io_device = None
                    proc.io_remaining = 0
                    proc.state = ProcessState.READY

                    self.state.waiting_queue.remove(pid)
                    if pid not in self.state.ready_queue:
                        self.state.ready_queue.append(pid)

                    completed.append({"pid": pid, "device": dev})
                    self.state.add_event("IO", f"Process {pid} completed {dev} I/O and returned to READY queue.", {"pid": pid, "device": dev})

            return {
                "success": True,
                "current_tick": self.state.tick,
                "completed_io_processes": completed,
                "waiting_queue_count": len(self.state.waiting_queue)
            }

    def get_io_queues(self) -> Dict[str, List[Dict[str, Any]]]:
        """Returns processes currently blocked waiting for each I/O device."""
        with self.state._lock:
            queues = {d: [] for d in self.devices}
            for pid in self.state.waiting_queue:
                p = self.state.processes.get(pid)
                if p and p.io_device:
                    queues.setdefault(p.io_device, []).append({
                        "pid": p.pid,
                        "remaining": p.io_remaining
                    })
            return queues
