from fastapi import APIRouter, HTTPException
from typing import List, Dict, Optional
from pydantic import BaseModel
from backend.app.services.simulators import CPUScheduler, MemoryManager, DeadlockSimulator, DiskScheduler

router = APIRouter(prefix="/simulators", tags=["OS Simulators"])

# 1. CPU Scheduling Schema
class ProcessInput(BaseModel):
    pid: str
    arrival_time: int
    burst_time: int
    priority: Optional[int] = 0

class CPUSchedulingRequest(BaseModel):
    algorithm: str  # FCFS, SJF, SRTF, Priority, Round_Robin
    processes: List[ProcessInput]
    time_quantum: Optional[int] = 2
    is_preemptive: Optional[bool] = False

# 2. Memory Management Schema
class ContiguousAllocRequest(BaseModel):
    strategy: str  # First_Fit, Best_Fit, Worst_Fit
    total_memory: int
    blocks: List[int]
    processes: List[Dict]

class PageReplacementRequest(BaseModel):
    algorithm: str  # FIFO, LRU, Optimal
    num_frames: int
    pages: List[int]

# 3. Deadlock Banker's Schema
class BankersRequest(BaseModel):
    processes: List[str]
    resource_types: List[str]
    available: List[int]
    max_matrix: List[List[int]]
    allocation_matrix: List[List[int]]

# 4. Disk Scheduling Schema
class DiskSchedulingRequest(BaseModel):
    algorithm: str  # FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK
    requests: List[int]
    initial_head: int
    disk_size: Optional[int] = 200
    direction: Optional[str] = "right"


@router.post("/cpu-scheduling")
def simulate_cpu_scheduling(req: CPUSchedulingRequest):
    try:
        proc_list = [p.dict() for p in req.processes]
        res = CPUScheduler.simulate(
            algorithm=req.algorithm,
            processes=proc_list,
            time_quantum=req.time_quantum or 2,
            is_preemptive=req.is_preemptive or False
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/memory/contiguous")
def simulate_contiguous_memory(req: ContiguousAllocRequest):
    try:
        return MemoryManager.contiguous_allocation(
            strategy=req.strategy,
            total_memory=req.total_memory,
            blocks=req.blocks,
            processes=req.processes
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/memory/page-replacement")
def simulate_page_replacement(req: PageReplacementRequest):
    try:
        return MemoryManager.page_replacement(
            algorithm=req.algorithm,
            num_frames=req.num_frames,
            pages=req.pages
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/deadlock/bankers")
def simulate_bankers_algorithm(req: BankersRequest):
    try:
        return DeadlockSimulator.bankers_algorithm(
            processes=req.processes,
            resource_types=req.resource_types,
            available=req.available,
            max_matrix=req.max_matrix,
            allocation_matrix=req.allocation_matrix
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/disk-scheduling")
def simulate_disk_scheduling(req: DiskSchedulingRequest):
    try:
        return DiskScheduler.simulate(
            algorithm=req.algorithm,
            requests=req.requests,
            initial_head=req.initial_head,
            disk_size=req.disk_size or 200,
            direction=req.direction or "right"
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
