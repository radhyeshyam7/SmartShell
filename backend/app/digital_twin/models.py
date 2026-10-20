from enum import Enum
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
import time

class ProcessState(str, Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"

class VirtualProcess(BaseModel):
    pid: str
    name: str
    state: ProcessState = ProcessState.NEW
    priority: int = 1
    arrival_time: int = 0
    burst_time: int = 4
    remaining_burst: int = 4
    memory_required: int = 128  # in KB
    allocated_memory_blocks: List[int] = Field(default_factory=list)
    allocated_resources: Dict[str, int] = Field(default_factory=dict)
    requested_resources: Dict[str, int] = Field(default_factory=dict)
    max_claim_resources: Dict[str, int] = Field(default_factory=dict)
    io_device: Optional[str] = None
    io_remaining: int = 0
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    waiting_time: int = 0
    turnaround_time: int = 0
    exit_code: int = 0

class MemoryBlock(BaseModel):
    block_id: int
    start_address: int
    size: int  # in KB
    is_allocated: bool = False
    allocated_pid: Optional[str] = None
    internal_fragmentation: int = 0

class PageFrame(BaseModel):
    frame_id: int
    page_number: Optional[int] = None
    pid: Optional[str] = None
    last_accessed: int = 0
    load_time: int = 0

class VirtualFile(BaseModel):
    path: str
    name: str
    is_directory: bool = False
    size_kb: int = 1
    content: str = ""
    created_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    modified_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    owner_pid: Optional[str] = None

class VirtualResource(BaseModel):
    name: str
    total_instances: int
    available_instances: int

class SimulationEvent(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    tick: int = 0
    category: str  # PROCESS, MEMORY, DISK, RESOURCE, SCHEDULER, IO, DEADLOCK
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class SimulationMetrics(BaseModel):
    cpu_utilization_percent: float = 0.0
    avg_waiting_time: float = 0.0
    avg_turnaround_time: float = 0.0
    throughput: float = 0.0
    total_memory_kb: int = 1024
    used_memory_kb: int = 0
    free_memory_kb: int = 1024
    external_fragmentation_kb: int = 0
    internal_fragmentation_kb: int = 0
    total_disk_kb: int = 10240
    used_disk_kb: int = 0
    free_disk_kb: int = 10240
    disk_seek_distance: int = 0

class Snapshot(BaseModel):
    snapshot_id: str
    label: str
    created_at: str
    state_dump: Dict[str, Any]

class InvariantReport(BaseModel):
    is_valid: bool
    checks_run: int
    violations: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
