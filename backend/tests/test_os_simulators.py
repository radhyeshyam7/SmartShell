import pytest
from backend.app.services.drive_service import drive_service
from backend.app.services.simulators import CPUScheduler, MemoryManager, DeadlockSimulator, DiskScheduler

def test_drive_discovery():
    drives = drive_service.list_drives()
    assert isinstance(drives, list)
    assert len(drives) > 0
    assert "drive_letter" in drives[0]

def test_cpu_fcfs_scheduling():
    procs = [
        {"pid": "P1", "arrival_time": 0, "burst_time": 4, "priority": 1},
        {"pid": "P2", "arrival_time": 1, "burst_time": 3, "priority": 2}
    ]
    res = CPUScheduler.simulate("FCFS", procs)
    assert "gantt_chart" in res
    assert res["metrics"]["avg_turnaround_time"] > 0

def test_cpu_sjf_scheduling():
    procs = [
        {"pid": "P1", "arrival_time": 0, "burst_time": 8, "priority": 1},
        {"pid": "P2", "arrival_time": 1, "burst_time": 4, "priority": 2}
    ]
    res = CPUScheduler.simulate("SJF", procs)
    assert res["processes"][1]["pid"] == "P2" or res["processes"][0]["pid"] == "P1"

def test_memory_contiguous_allocation():
    blocks = [100, 500, 200, 300, 600]
    procs = [{"pid": "P1", "size": 212}, {"pid": "P2", "size": 417}]
    res = MemoryManager.contiguous_allocation("FIRST_FIT", 1700, blocks, procs)
    assert len(res["allocations"]) == 2

def test_memory_page_replacement():
    pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
    res = MemoryManager.page_replacement("FIFO", 3, pages)
    assert res["page_faults"] > 0
    assert res["hit_ratio_percent"] >= 0

def test_bankers_algorithm_safe_state():
    processes = ["P0", "P1", "P2", "P3", "P4"]
    resource_types = ["A", "B", "C"]
    available = [3, 3, 2]
    max_matrix = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
    alloc_matrix = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
    
    res = DeadlockSimulator.bankers_algorithm(processes, resource_types, available, max_matrix, alloc_matrix)
    assert res["is_safe"] is True
    assert len(res["safe_sequence"]) == 5

def test_disk_fcfs_scheduling():
    reqs = [98, 183, 37, 122, 14, 124, 65, 67]
    res = DiskScheduler.simulate("FCFS", reqs, initial_head=53)
    assert res["total_seek_distance"] == 640
