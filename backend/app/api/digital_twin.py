from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from backend.app.digital_twin.engine import digital_twin_engine

router = APIRouter(prefix="/digital-twin", tags=["Digital Twin"])

class ExecuteRequest(BaseModel):
    instruction: str

class CreateProcessRequest(BaseModel):
    pid: str
    name: Optional[str] = ""
    burst_time: int = 4
    memory_required: int = 128
    priority: int = 1
    arrival_time: int = 0
    max_claim_resources: Optional[Dict[str, int]] = None

class TerminateProcessRequest(BaseModel):
    pid: str
    exit_code: int = 0

class TransitionProcessRequest(BaseModel):
    pid: str
    target_state: str

class ScheduleRunRequest(BaseModel):
    algorithm: str = "ROUND_ROBIN"
    time_quantum: int = 2
    is_preemptive: bool = False
    custom_processes: Optional[List[Dict[str, Any]]] = None

class MemoryAllocateRequest(BaseModel):
    pid: str
    size_kb: int
    strategy: str = "FIRST_FIT"

class MemoryDeallocateRequest(BaseModel):
    pid: str

class PageReplacementRequest(BaseModel):
    algorithm: str = "FIFO"
    reference_pages: List[int]
    num_frames: int = 4

class CreateFileRequest(BaseModel):
    path: str
    content: str = ""
    size_kb: int = 1
    is_directory: bool = False
    owner_pid: Optional[str] = None

class DeleteFileRequest(BaseModel):
    path: str

class DiskScheduleRequest(BaseModel):
    algorithm: str = "C-SCAN"
    track_requests: Optional[List[int]] = None
    initial_head: Optional[int] = None
    direction: str = "right"

class ResourceRequestModel(BaseModel):
    pid: str
    resource_name: str
    amount: int = 1

class IORequestModel(BaseModel):
    pid: str
    device: str = "DISK_IO"
    duration: int = 3

class IOTickModel(BaseModel):
    ticks: int = 1

class SnapshotCreateRequest(BaseModel):
    label: Optional[str] = "Manual Checkpoint"

class SnapshotRestoreRequest(BaseModel):
    snapshot_id: str

class CompareRequest(BaseModel):
    algorithms: Optional[List[str]] = None
    custom_workload: Optional[List[Dict[str, Any]]] = None
    time_quantum: int = 2

# -------------------------------------------------------------
# Endpoints
# -------------------------------------------------------------

@router.get("/state")
def get_state():
    """Retrieve full live snapshot of the digital twin state."""
    return digital_twin_engine.get_full_state()

@router.post("/reset")
def reset_state():
    """Reset the digital twin back to baseline academic state."""
    return digital_twin_engine.reset_state()

@router.post("/execute")
def execute_instruction(req: ExecuteRequest):
    """Execute natural language or 'dt <cmd>' instruction on digital twin."""
    res = digital_twin_engine.execute_command_or_nl(req.instruction)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error", "Execution failed."))
    return res

@router.post("/process/create")
def create_process(req: CreateProcessRequest):
    res = digital_twin_engine.process_manager.create_process(
        pid=req.pid,
        name=req.name or "",
        burst_time=req.burst_time,
        memory_required=req.memory_required,
        priority=req.priority,
        arrival_time=req.arrival_time,
        max_claim_resources=req.max_claim_resources
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/process/terminate")
def terminate_process(req: TerminateProcessRequest):
    res = digital_twin_engine.process_manager.terminate_process(pid=req.pid, exit_code=req.exit_code)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/process/transition")
def transition_process(req: TransitionProcessRequest):
    res = digital_twin_engine.process_manager.transition_state(pid=req.pid, target_state=req.target_state)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/schedule/run")
def run_scheduler(req: ScheduleRunRequest):
    res = digital_twin_engine.scheduler.schedule(
        algorithm=req.algorithm,
        time_quantum=req.time_quantum,
        is_preemptive=req.is_preemptive,
        custom_processes=req.custom_processes
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/memory/allocate")
def allocate_memory(req: MemoryAllocateRequest):
    res = digital_twin_engine.memory_manager.allocate(
        pid=req.pid,
        size_kb=req.size_kb,
        strategy=req.strategy
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/memory/deallocate")
def deallocate_memory(req: MemoryDeallocateRequest):
    return digital_twin_engine.memory_manager.deallocate(pid=req.pid)

@router.post("/memory/page-replacement")
def page_replacement(req: PageReplacementRequest):
    return digital_twin_engine.memory_manager.simulate_page_replacement(
        algorithm=req.algorithm,
        reference_pages=req.reference_pages,
        num_frames=req.num_frames
    )

@router.post("/disk/file")
def create_file(req: CreateFileRequest):
    res = digital_twin_engine.disk_manager.create_file(
        path=req.path,
        content=req.content,
        size_kb=req.size_kb,
        is_directory=req.is_directory,
        owner_pid=req.owner_pid
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.delete("/disk/file")
def delete_file(req: DeleteFileRequest):
    res = digital_twin_engine.disk_manager.delete_file(path=req.path)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/disk/schedule")
def schedule_disk(req: DiskScheduleRequest):
    return digital_twin_engine.disk_manager.simulate_disk_scheduling(
        algorithm=req.algorithm,
        track_requests=req.track_requests,
        initial_head=req.initial_head,
        direction=req.direction
    )

@router.post("/resources/request")
def request_resource(req: ResourceRequestModel):
    res = digital_twin_engine.resource_manager.request_resource(
        pid=req.pid,
        resource_name=req.resource_name,
        amount=req.amount
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/resources/release")
def release_resource(req: ResourceRequestModel):
    res = digital_twin_engine.resource_manager.release_resource(
        pid=req.pid,
        resource_name=req.resource_name,
        amount=req.amount
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.get("/resources/matrices")
def get_resource_matrices():
    return digital_twin_engine.resource_manager.get_matrices()

@router.get("/deadlock/check")
def check_deadlock():
    banker = digital_twin_engine.deadlock_manager.check_bankers_safety()
    rag = digital_twin_engine.deadlock_manager.detect_rag_cycles()
    return {
        "banker": banker,
        "rag": rag
    }

@router.post("/io/request")
def request_io(req: IORequestModel):
    res = digital_twin_engine.io_manager.request_io(
        pid=req.pid,
        device=req.device,
        duration=req.duration
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/io/tick")
def tick_io(req: IOTickModel):
    return digital_twin_engine.io_manager.tick(ticks=req.ticks)

@router.get("/snapshots")
def list_snapshots():
    return digital_twin_engine.scenario_service.list_snapshots()

@router.post("/snapshots/create")
def create_snapshot(req: SnapshotCreateRequest):
    return digital_twin_engine.scenario_service.create_snapshot(label=req.label or "Manual Checkpoint")

@router.post("/snapshots/restore")
def restore_snapshot(req: SnapshotRestoreRequest):
    res = digital_twin_engine.scenario_service.restore_snapshot(snapshot_id=req.snapshot_id)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("error"))
    return res

@router.post("/compare")
def compare_algorithms(req: CompareRequest):
    return digital_twin_engine.scenario_service.compare_scheduling_algorithms(
        algorithms=req.algorithms,
        custom_workload=req.custom_workload,
        time_quantum=req.time_quantum
    )

@router.get("/verify")
def verify_invariants():
    report = digital_twin_engine.verification_service.verify_invariants()
    return report.model_dump()
