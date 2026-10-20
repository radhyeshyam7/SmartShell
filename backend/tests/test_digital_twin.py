import pytest
from starlette.testclient import TestClient
from backend.app.main import app
from backend.app.digital_twin.engine import digital_twin_engine
from backend.app.digital_twin.models import ProcessState

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_twin():
    """Ensure every test runs on a fresh baseline Digital Twin state."""
    digital_twin_engine.reset_state()
    yield
    digital_twin_engine.reset_state()

def test_initial_digital_twin_state():
    state = digital_twin_engine.get_full_state()
    assert len(state["processes"]) == 5
    assert "P1" in state["processes"]
    assert len(state["memory_blocks"]) == 5
    assert len(state["resources"]) == 3
    assert state["total_memory_capacity"] == 1700
    assert len(state["virtual_files"]) >= 5

def test_process_lifecycle_and_memory_reclaim():
    pm = digital_twin_engine.process_manager
    # Create P6
    res = pm.create_process("P6", name="test_p6", burst_time=5, memory_required=150, priority=2)
    assert res["success"] is True
    assert "P6" in digital_twin_engine.state.processes
    p6 = digital_twin_engine.state.processes["P6"]
    assert p6.state == ProcessState.READY
    assert len(p6.allocated_memory_blocks) > 0

    # Terminate P6 and verify memory is freed
    term_res = pm.terminate_process("P6")
    assert term_res["success"] is True
    assert p6.state == ProcessState.TERMINATED
    assert len(p6.allocated_memory_blocks) == 0

def test_illegal_state_transition_blocked():
    pm = digital_twin_engine.process_manager
    # NEW process cannot transition directly to RUNNING without READY
    res = pm.create_process("P_TEST", memory_required=9999) # Won't fit memory -> stays NEW
    p = digital_twin_engine.state.processes["P_TEST"]
    assert p.state == ProcessState.NEW
    
    trans_res = pm.transition_state("P_TEST", "RUNNING")
    assert trans_res["success"] is False
    assert "Illegal" in trans_res["error"]

def test_memory_allocation_strategies():
    mm = digital_twin_engine.memory_manager
    # Free existing blocks for a clean allocation test
    for b in digital_twin_engine.state.memory_blocks:
        b.is_allocated = False
        b.allocated_pid = None
        b.internal_fragmentation = 0

    # Best-Fit: sizes are [100, 500, 200, 300, 600]. For 180 KB, best block is 200 KB (Block 3)
    res_best = mm.allocate("P1", size_kb=180, strategy="BEST_FIT")
    assert res_best["success"] is True
    assert res_best["block_id"] == 3
    assert res_best["internal_fragmentation"] == 20

def test_virtual_disk_isolation():
    dm = digital_twin_engine.disk_manager
    res = dm.create_file("/sandbox/test.log", content="test data isolation", size_kb=2)
    assert res["success"] is True
    assert "/sandbox/test.log" in digital_twin_engine.state.virtual_files

    read_res = dm.read_file("/sandbox/test.log")
    assert read_res["success"] is True
    assert read_res["content"] == "test data isolation"

    del_res = dm.delete_file("/sandbox/test.log")
    assert del_res["success"] is True
    assert "/sandbox/test.log" not in digital_twin_engine.state.virtual_files

def test_banker_safety_and_rag():
    dm = digital_twin_engine.deadlock_manager
    banker = dm.check_bankers_safety()
    assert banker["is_safe"] is True
    assert len(banker["safe_sequence"]) > 0

    rag = dm.detect_rag_cycles()
    assert rag["has_deadlock_cycle"] is False

def test_scheduler_and_side_by_side_comparison():
    sc = digital_twin_engine.scheduler
    sched_res = sc.schedule("ROUND_ROBIN", time_quantum=2)
    assert sched_res["success"] is True
    assert len(sched_res["gantt_chart"]) > 0
    assert sched_res["metrics"]["avg_turnaround_time"] > 0

    # Side-by-side comparison
    service = digital_twin_engine.scenario_service
    cmp_res = service.compare_scheduling_algorithms(algorithms=["FCFS", "SJF", "ROUND_ROBIN"])
    assert cmp_res["success"] is True
    assert len(cmp_res["comparisons"]) == 3
    assert cmp_res["best_turnaround_algorithm"] is not None

def test_snapshot_and_restoration():
    service = digital_twin_engine.scenario_service
    # Take snapshot
    snap = service.create_snapshot("Baseline Snap")
    snap_id = snap["snapshot_id"]

    # Mutate state (terminate P1)
    digital_twin_engine.process_manager.terminate_process("P1")
    assert digital_twin_engine.state.processes["P1"].state == ProcessState.TERMINATED

    # Restore snapshot
    rest = service.restore_snapshot(snap_id)
    assert rest["success"] is True
    assert digital_twin_engine.state.processes["P1"].state == ProcessState.READY

def test_state_invariant_verification():
    vs = digital_twin_engine.verification_service
    report = vs.verify_invariants()
    assert report.is_valid is True
    assert len(report.violations) == 0

def test_digital_twin_api_endpoints():
    # 1. State endpoint
    r = client.get("/api/digital-twin/state")
    assert r.status_code == 200
    data = r.json()
    assert "processes" in data
    assert "metrics" in data

    # 2. Banker safety endpoint
    r2 = client.get("/api/digital-twin/deadlock/check")
    assert r2.status_code == 200
    assert r2.json()["banker"]["is_safe"] is True

    # 3. Side-by-side compare endpoint
    r3 = client.post("/api/digital-twin/compare", json={"algorithms": ["FCFS", "SJF", "ROUND_ROBIN"]})
    assert r3.status_code == 200
    assert len(r3.json()["comparisons"]) == 3

    # 4. Verify invariants endpoint
    r4 = client.get("/api/digital-twin/verify")
    assert r4.status_code == 200
    assert r4.json()["is_valid"] is True
