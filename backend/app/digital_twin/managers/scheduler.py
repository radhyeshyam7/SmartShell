from typing import Dict, List, Optional, Any
from backend.app.digital_twin.models import ProcessState
from backend.app.digital_twin.state import simulation_state
from backend.app.services.simulators import CPUScheduler as LegacyCPUScheduler

class VirtualScheduler:
    """Manages CPU process scheduling algorithms and timeline generation in the Digital Twin."""

    def __init__(self, state=None):
        self.state = state or simulation_state

    def schedule(
        self,
        algorithm: str = "ROUND_ROBIN",
        time_quantum: int = 2,
        is_preemptive: bool = False,
        custom_processes: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Runs scheduling simulation and synchronizes process metrics and Gantt chart in state."""
        with self.state._lock:
            alg = algorithm.upper().strip()

            if custom_processes is not None:
                procs_to_run = custom_processes
            else:
                # Use active/ready processes from the shared state
                procs_to_run = []
                for pid in self.state.ready_queue:
                    if pid in self.state.processes:
                        p = self.state.processes[pid]
                        procs_to_run.append({
                            "pid": p.pid,
                            "arrival_time": p.arrival_time,
                            "burst_time": p.remaining_burst if p.remaining_burst > 0 else p.burst_time,
                            "priority": p.priority
                        })

                # If ready queue is empty, fallback to all non-terminated processes
                if not procs_to_run:
                    for pid, p in self.state.processes.items():
                        if p.state != ProcessState.TERMINATED:
                            procs_to_run.append({
                                "pid": p.pid,
                                "arrival_time": p.arrival_time,
                                "burst_time": p.remaining_burst if p.remaining_burst > 0 else p.burst_time,
                                "priority": p.priority
                            })

            if not procs_to_run:
                return {
                    "success": False,
                    "error": "No runnable processes available for CPU scheduling."
                }

            # Run scheduler simulation
            res = LegacyCPUScheduler.simulate(
                algorithm=alg,
                processes=procs_to_run,
                time_quantum=time_quantum,
                is_preemptive=is_preemptive
            )

            # Update shared state with result
            self.state.gantt_chart = res.get("gantt_chart", [])
            for p_res in res.get("processes", []):
                pid = p_res.get("pid")
                if pid in self.state.processes:
                    proc = self.state.processes[pid]
                    proc.completion_time = p_res.get("completion_time")
                    proc.turnaround_time = p_res.get("turnaround_time", 0)
                    proc.waiting_time = p_res.get("waiting_time", 0)

            # Advance logical clock to end of last scheduled item
            if self.state.gantt_chart:
                last_end = max(item["end_time"] for item in self.state.gantt_chart)
                self.state.tick = max(self.state.tick, last_end)

            msg = f"Executed {alg} CPU Scheduling on {len(procs_to_run)} process(es). Avg TAT: {res['metrics']['avg_turnaround_time']} ms, Avg WT: {res['metrics']['avg_waiting_time']} ms."
            self.state.add_event("SCHEDULER", msg, {
                "algorithm": alg, "quantum": time_quantum, "metrics": res["metrics"]
            })

            res["success"] = True
            res["message"] = msg
            return res
