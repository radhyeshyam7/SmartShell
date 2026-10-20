import copy
import threading
import time
from typing import Dict, List, Optional, Any
from backend.app.digital_twin.models import (
    VirtualProcess, ProcessState, MemoryBlock, PageFrame,
    VirtualFile, VirtualResource, SimulationEvent, SimulationMetrics, Snapshot
)

class SimulationState:
    """Thread-safe centralized shared state store for the SmartShell OS Digital Twin."""

    def __init__(self):
        self._lock = threading.RLock()
        self.reset_to_default()

    def reset_to_default(self):
        """Initializes state with a clean, realistic academic virtual OS scenario."""
        with self._lock:
            self.tick = 0
            self.running_pid: Optional[str] = None
            self.ready_queue: List[str] = []
            self.waiting_queue: List[str] = []
            self.terminated_list: List[str] = []
            self.gantt_chart: List[Dict[str, Any]] = []
            self.page_hits = 0
            self.page_faults = 0
            self.total_memory_capacity = 1700  # sum of initial partitions in KB
            self.total_disk_capacity = 10240   # 10 MB in KB
            self.snapshots: Dict[str, Snapshot] = {}
            self.history_events: List[SimulationEvent] = []

            # 1. Initialize Memory Partitions
            partition_sizes = [100, 500, 200, 300, 600]
            self.memory_blocks: List[MemoryBlock] = []
            curr_addr = 0
            for idx, sz in enumerate(partition_sizes):
                self.memory_blocks.append(MemoryBlock(
                    block_id=idx + 1,
                    start_address=curr_addr,
                    size=sz,
                    is_allocated=False,
                    allocated_pid=None,
                    internal_fragmentation=0
                ))
                curr_addr += sz

            # 2. Page Frames (for virtual memory paging)
            self.page_frames = [
                PageFrame(frame_id=i) for i in range(4)
            ]

            # 3. Resources (Standard Banker's Algorithm scenario: R1/A, R2/B, R3/C)
            # Total instances: A=10, B=5, C=7
            self.resources: Dict[str, VirtualResource] = {
                "R1": VirtualResource(name="R1", total_instances=10, available_instances=3),
                "R2": VirtualResource(name="R2", total_instances=5, available_instances=3),
                "R3": VirtualResource(name="R3", total_instances=7, available_instances=2),
            }

            # 4. Standard Process Table (P1 through P5)
            # Standard Banker's configuration:
            # Allocations: P1=[0,1,0], P2=[2,0,0], P3=[3,0,2], P4=[2,1,1], P5=[0,0,2]
            # Max claims:   P1=[7,5,3], P2=[3,2,2], P3=[9,0,2], P4=[2,2,2], P5=[4,3,3]
            sample_processes = [
                VirtualProcess(
                    pid="P1", name="virtual_init", state=ProcessState.READY, priority=3,
                    arrival_time=0, burst_time=6, remaining_burst=6, memory_required=212,
                    allocated_resources={"R1": 0, "R2": 1, "R3": 0},
                    max_claim_resources={"R1": 7, "R2": 5, "R3": 3}
                ),
                VirtualProcess(
                    pid="P2", name="virtual_calc", state=ProcessState.READY, priority=1,
                    arrival_time=1, burst_time=4, remaining_burst=4, memory_required=417,
                    allocated_resources={"R1": 2, "R2": 0, "R3": 0},
                    max_claim_resources={"R1": 3, "R2": 2, "R3": 2}
                ),
                VirtualProcess(
                    pid="P3", name="virtual_netd", state=ProcessState.READY, priority=4,
                    arrival_time=2, burst_time=8, remaining_burst=8, memory_required=112,
                    allocated_resources={"R1": 3, "R2": 0, "R3": 2},
                    max_claim_resources={"R1": 9, "R2": 0, "R3": 2}
                ),
                VirtualProcess(
                    pid="P4", name="virtual_logger", state=ProcessState.READY, priority=2,
                    arrival_time=3, burst_time=3, remaining_burst=3, memory_required=250,
                    allocated_resources={"R1": 2, "R2": 1, "R3": 1},
                    max_claim_resources={"R1": 2, "R2": 2, "R3": 2}
                ),
                VirtualProcess(
                    pid="P5", name="virtual_backup", state=ProcessState.READY, priority=5,
                    arrival_time=4, burst_time=5, remaining_burst=5, memory_required=426,
                    allocated_resources={"R1": 0, "R2": 0, "R3": 2},
                    max_claim_resources={"R1": 4, "R2": 3, "R3": 3}
                ),
            ]

            self.processes: Dict[str, VirtualProcess] = {}
            for p in sample_processes:
                self.processes[p.pid] = p
                self.ready_queue.append(p.pid)

            # Assign memory to P1, P2, P3 in available partitions
            # Block 2 (500 KB) -> P1 (212 KB) -> internal frag 288
            self.memory_blocks[1].is_allocated = True
            self.memory_blocks[1].allocated_pid = "P1"
            self.memory_blocks[1].internal_fragmentation = 500 - 212
            self.processes["P1"].allocated_memory_blocks = [2]

            # Block 5 (600 KB) -> P2 (417 KB) -> internal frag 183
            self.memory_blocks[4].is_allocated = True
            self.memory_blocks[4].allocated_pid = "P2"
            self.memory_blocks[4].internal_fragmentation = 600 - 417
            self.processes["P2"].allocated_memory_blocks = [5]

            # Block 3 (200 KB) -> P3 (112 KB) -> internal frag 88
            self.memory_blocks[2].is_allocated = True
            self.memory_blocks[2].allocated_pid = "P3"
            self.memory_blocks[2].internal_fragmentation = 200 - 112
            self.processes["P3"].allocated_memory_blocks = [3]

            # 5. Virtual File System (Hierarchical tree, pure virtual memory)
            now_str = time.strftime("%Y-%m-%d %H:%M:%S")
            self.virtual_files: Dict[str, VirtualFile] = {
                "/": VirtualFile(path="/", name="root", is_directory=True, size_kb=4, created_at=now_str, modified_at=now_str),
                "/sys": VirtualFile(path="/sys", name="sys", is_directory=True, size_kb=4, created_at=now_str, modified_at=now_str),
                "/sys/kernel.sys": VirtualFile(path="/sys/kernel.sys", name="kernel.sys", is_directory=False, size_kb=256, content="SMARTSHELL_VIRTUAL_KERNEL_V1", created_at=now_str, modified_at=now_str),
                "/etc": VirtualFile(path="/etc", name="etc", is_directory=True, size_kb=4, created_at=now_str, modified_at=now_str),
                "/etc/twin_config.json": VirtualFile(path="/etc/twin_config.json", name="twin_config.json", is_directory=False, size_kb=16, content="{\"twin_version\": \"2.0\", \"scheduler\": \"ROUND_ROBIN\"}", created_at=now_str, modified_at=now_str),
                "/home": VirtualFile(path="/home", name="home", is_directory=True, size_kb=4, created_at=now_str, modified_at=now_str),
                "/home/user": VirtualFile(path="/home/user", name="user", is_directory=True, size_kb=4, created_at=now_str, modified_at=now_str),
                "/home/user/notes.txt": VirtualFile(path="/home/user/notes.txt", name="notes.txt", is_directory=False, size_kb=8, content="Welcome to SmartShell OS Digital Twin!", created_at=now_str, modified_at=now_str, owner_pid="P1"),
            }

            self.add_event("SYSTEM", "SmartShell OS Digital Twin initialized to default baseline state.")

    def add_event(self, category: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Append an event to audit history."""
        with self._lock:
            evt = SimulationEvent(
                timestamp=time.time(),
                tick=self.tick,
                category=category,
                message=message,
                details=details or {}
            )
            self.history_events.append(evt)
            if len(self.history_events) > 300:
                self.history_events.pop(0)

    def to_dict(self) -> Dict[str, Any]:
        """Deep serializes the entire simulation state to a dictionary."""
        with self._lock:
            used_mem = sum(b.size for b in self.memory_blocks if b.is_allocated)
            free_mem = self.total_memory_capacity - used_mem
            int_frag = sum(b.internal_fragmentation for b in self.memory_blocks if b.is_allocated)
            ext_frag = sum(b.size for b in self.memory_blocks if not b.is_allocated)
            used_disk = sum(f.size_kb for f in self.virtual_files.values())
            free_disk = max(0, self.total_disk_capacity - used_disk)

            metrics = SimulationMetrics(
                cpu_utilization_percent=round((sum(p.burst_time for p in self.processes.values()) / max(1, self.tick + sum(p.burst_time for p in self.processes.values()))) * 100, 1) if self.processes else 0.0,
                avg_waiting_time=round(sum(p.waiting_time for p in self.processes.values()) / max(1, len(self.processes)), 2) if self.processes else 0.0,
                avg_turnaround_time=round(sum(p.turnaround_time for p in self.processes.values()) / max(1, len(self.processes)), 2) if self.processes else 0.0,
                throughput=round(len(self.terminated_list) / max(1, self.tick), 3),
                total_memory_kb=self.total_memory_capacity,
                used_memory_kb=used_mem,
                free_memory_kb=free_mem,
                internal_fragmentation_kb=int_frag,
                external_fragmentation_kb=ext_frag,
                total_disk_kb=self.total_disk_capacity,
                used_disk_kb=used_disk,
                free_disk_kb=free_disk,
                disk_seek_distance=0
            )

            return {
                "tick": self.tick,
                "running_pid": self.running_pid,
                "ready_queue": copy.deepcopy(self.ready_queue),
                "waiting_queue": copy.deepcopy(self.waiting_queue),
                "terminated_list": copy.deepcopy(self.terminated_list),
                "processes": {pid: p.model_dump() for pid, p in self.processes.items()},
                "memory_blocks": [b.model_dump() for b in self.memory_blocks],
                "total_memory_capacity": self.total_memory_capacity,
                "page_frames": [f.model_dump() for f in self.page_frames],
                "page_hits": self.page_hits,
                "page_faults": self.page_faults,
                "virtual_files": {p: f.model_dump() for p, f in self.virtual_files.items()},
                "total_disk_capacity": self.total_disk_capacity,
                "resources": {k: r.model_dump() for k, r in self.resources.items()},
                "gantt_chart": copy.deepcopy(self.gantt_chart),
                "metrics": metrics.model_dump(),
                "history_events": [e.model_dump() for e in self.history_events[-50:]],
                "snapshots": list(self.snapshots.keys())
            }

    def load_dict(self, data: Dict[str, Any]):
        """Restores state from a serialized dictionary."""
        with self._lock:
            self.tick = data.get("tick", 0)
            self.running_pid = data.get("running_pid")
            self.ready_queue = copy.deepcopy(data.get("ready_queue", []))
            self.waiting_queue = copy.deepcopy(data.get("waiting_queue", []))
            self.terminated_list = copy.deepcopy(data.get("terminated_list", []))
            self.total_memory_capacity = data.get("total_memory_capacity", 1700)
            self.total_disk_capacity = data.get("total_disk_capacity", 10240)
            self.page_hits = data.get("page_hits", 0)
            self.page_faults = data.get("page_faults", 0)
            self.gantt_chart = copy.deepcopy(data.get("gantt_chart", []))

            self.processes = {
                pid: VirtualProcess(**p_data) for pid, p_data in data.get("processes", {}).items()
            }
            self.memory_blocks = [
                MemoryBlock(**b_data) for b_data in data.get("memory_blocks", [])
            ]
            self.page_frames = [
                PageFrame(**f_data) for f_data in data.get("page_frames", [])
            ]
            self.virtual_files = {
                path: VirtualFile(**f_data) for path, f_data in data.get("virtual_files", {}).items()
            }
            self.resources = {
                k: VirtualResource(**r_data) for k, r_data in data.get("resources", {}).items()
            }

# Shared singleton instance
simulation_state = SimulationState()
