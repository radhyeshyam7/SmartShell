import copy
import time
import uuid
from typing import Dict, List, Optional, Any, Callable
from backend.app.digital_twin.models import Snapshot, ProcessState
from backend.app.digital_twin.state import simulation_state, SimulationState
from backend.app.services.simulators import CPUScheduler as LegacyCPUScheduler

class ScenarioService:
    """Provides Snapshots, What-If Branching, and Side-by-Side Algorithm Comparison."""

    def __init__(self, state=None):
        self.state = state or simulation_state

    def create_snapshot(self, label: str = "") -> Dict[str, Any]:
        """Creates a persistent checkpoint snapshot of current simulation state."""
        with self.state._lock:
            snap_id = f"snap_{int(time.time())}_{uuid.uuid4().hex[:6]}"
            label = label or f"Checkpoint at tick {self.state.tick}"
            dump = self.state.to_dict()

            snapshot = Snapshot(
                snapshot_id=snap_id,
                label=label,
                created_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                state_dump=dump
            )
            self.state.snapshots[snap_id] = snapshot

            msg = f"Created snapshot '{snap_id}' ({label})."
            self.state.add_event("SYSTEM", msg, {"snapshot_id": snap_id, "label": label})
            return {"success": True, "snapshot_id": snap_id, "label": label, "created_at": snapshot.created_at}

    def restore_snapshot(self, snapshot_id: str) -> Dict[str, Any]:
        """Restores simulation state back to a previous snapshot."""
        with self.state._lock:
            if snapshot_id not in self.state.snapshots:
                return {"success": False, "error": f"Snapshot '{snapshot_id}' not found."}

            snap = self.state.snapshots[snapshot_id]
            self.state.load_dict(snap.state_dump)

            msg = f"Restored simulation state to snapshot '{snapshot_id}' ({snap.label})."
            self.state.add_event("SYSTEM", msg, {"snapshot_id": snapshot_id})
            return {"success": True, "snapshot_id": snapshot_id, "label": snap.label, "message": msg}

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """Returns metadata for all available snapshots."""
        with self.state._lock:
            return [
                {
                    "snapshot_id": s.snapshot_id,
                    "label": s.label,
                    "created_at": s.created_at,
                    "tick": s.state_dump.get("tick", 0),
                    "process_count": len(s.state_dump.get("processes", {}))
                }
                for s in self.state.snapshots.values()
            ]

    def branch_what_if(self, snapshot_id: str, modification_fn: Optional[Callable[[SimulationState], None]] = None) -> Dict[str, Any]:
        """Runs a sandbox simulation branch without modifying the live state."""
        with self.state._lock:
            if snapshot_id not in self.state.snapshots:
                return {"success": False, "error": f"Snapshot '{snapshot_id}' not found."}

            # Create isolated sandbox state
            snap = self.state.snapshots[snapshot_id]
            sandbox = SimulationState()
            sandbox.load_dict(snap.state_dump)

            # Apply modification if provided
            if modification_fn:
                modification_fn(sandbox)

            result_state = sandbox.to_dict()
            return {
                "success": True,
                "sandbox_state": result_state,
                "message": f"Successfully simulated what-if branch from snapshot {snapshot_id}."
            }

    def compare_scheduling_algorithms(
        self,
        algorithms: Optional[List[str]] = None,
        custom_workload: Optional[List[Dict[str, Any]]] = None,
        time_quantum: int = 2
    ) -> Dict[str, Any]:
        """Runs multiple scheduling algorithms on the exact same workload for side-by-side comparison."""
        with self.state._lock:
            algs = algorithms or ["FCFS", "SJF", "ROUND_ROBIN", "PRIORITY"]
            
            # Prepare identical workload
            if custom_workload:
                workload = copy.deepcopy(custom_workload)
            else:
                workload = []
                for pid, p in sorted(self.state.processes.items()):
                    if p.state != ProcessState.TERMINATED:
                        workload.append({
                            "pid": p.pid,
                            "arrival_time": p.arrival_time,
                            "burst_time": p.burst_time,
                            "priority": p.priority
                        })
                if not workload:
                    # Fallback academic workload
                    workload = [
                        {"pid": "P1", "arrival_time": 0, "burst_time": 6, "priority": 3},
                        {"pid": "P2", "arrival_time": 1, "burst_time": 4, "priority": 1},
                        {"pid": "P3", "arrival_time": 2, "burst_time": 8, "priority": 4},
                        {"pid": "P4", "arrival_time": 3, "burst_time": 3, "priority": 2},
                        {"pid": "P5", "arrival_time": 4, "burst_time": 5, "priority": 5},
                    ]

            comparisons = []
            best_tat_alg = None
            min_avg_tat = float("inf")
            best_wt_alg = None
            min_avg_wt = float("inf")

            for alg in algs:
                try:
                    res = LegacyCPUScheduler.simulate(
                        algorithm=alg,
                        processes=copy.deepcopy(workload),
                        time_quantum=time_quantum,
                        is_preemptive=False
                    )
                    metrics = res.get("metrics", {})
                    avg_tat = metrics.get("avg_turnaround_time", 0.0)
                    avg_wt = metrics.get("avg_waiting_time", 0.0)

                    if avg_tat < min_avg_tat:
                        min_avg_tat = avg_tat
                        best_tat_alg = alg
                    if avg_wt < min_avg_wt:
                        min_avg_wt = avg_wt
                        best_wt_alg = alg

                    comparisons.append({
                        "algorithm": alg,
                        "avg_turnaround_time": avg_tat,
                        "avg_waiting_time": avg_wt,
                        "cpu_utilization_percent": metrics.get("cpu_utilization_percent", 0.0),
                        "gantt_chart": res.get("gantt_chart", [])
                    })
                except Exception as e:
                    comparisons.append({
                        "algorithm": alg,
                        "error": str(e)
                    })

            recommendation = (
                f"For this workload, {best_wt_alg} produced the lowest average waiting time ({min_avg_wt} ms), "
                f"while {best_tat_alg} achieved the lowest turnaround time ({min_avg_tat} ms)."
            )

            msg = f"Compared {len(algs)} scheduling algorithms on {len(workload)} processes. Recommendation: {best_wt_alg}."
            self.state.add_event("SCHEDULER", msg, {"algorithms": algs, "recommendation": recommendation})

            return {
                "success": True,
                "workload_process_count": len(workload),
                "workload": workload,
                "comparisons": comparisons,
                "best_turnaround_algorithm": best_tat_alg,
                "best_waiting_algorithm": best_wt_alg,
                "recommendation": recommendation,
                "message": msg
            }
