from typing import Dict, List, Optional, Any, Tuple
from backend.app.digital_twin.models import ProcessState
from backend.app.digital_twin.state import simulation_state
from backend.app.services.simulators import DeadlockSimulator as LegacyDeadlockSimulator

class DeadlockManager:
    """Manages Deadlock avoidance (Banker's Algorithm) and detection (Resource Allocation Graph / RAG cycles)."""

    def __init__(self, state=None):
        self.state = state or simulation_state

    def check_bankers_safety(self) -> Dict[str, Any]:
        """Evaluates live system state using Banker's Algorithm."""
        with self.state._lock:
            from backend.app.digital_twin.managers.resource_manager import ResourceManager
            rm = ResourceManager(self.state)
            matrices = rm.get_matrices()

            pids = matrices["process_names"]
            res_names = matrices["resource_names"]
            available = matrices["available"]
            max_m = matrices["max_matrix"]
            alloc_m = matrices["allocation_matrix"]

            if not pids or not res_names:
                return {
                    "is_safe": True,
                    "safe_sequence": [],
                    "need_matrix": [],
                    "message": "No active processes or resources to evaluate."
                }

            result = LegacyDeadlockSimulator.bankers_algorithm(
                processes=pids,
                resource_types=res_names,
                available=available,
                max_matrix=max_m,
                allocation_matrix=alloc_m
            )

            msg = f"Banker's Algorithm evaluation: System is {'SAFE ✅' if result['is_safe'] else 'DEADLOCKED/UNSAFE ❌'}. Safe Sequence: {' -> '.join(result['safe_sequence']) if result['is_safe'] else 'None'}."
            self.state.add_event("DEADLOCK", msg, result)
            result["message"] = msg
            return result

    def detect_rag_cycles(self) -> Dict[str, Any]:
        """Builds the Resource Allocation Graph (RAG) and performs cycle detection."""
        with self.state._lock:
            # Build graph adjacency list
            # Nodes: processes (e.g. "P1"), resources (e.g. "R1")
            adj: Dict[str, List[str]] = {}
            all_nodes = set()

            for r_name in self.state.resources.keys():
                adj[r_name] = []
                all_nodes.add(r_name)

            for pid, p in self.state.processes.items():
                if p.state == ProcessState.TERMINATED:
                    continue
                adj[pid] = []
                all_nodes.add(pid)

                # Allocation edges: Resource -> Process
                for r_name, count in p.allocated_resources.items():
                    if count > 0 and r_name in adj:
                        adj[r_name].append(pid)

                # Request edges: Process -> Resource
                for r_name, count in p.requested_resources.items():
                    if count > 0 and pid in adj:
                        adj[pid].append(r_name)

            # DFS Cycle Detection
            visited = set()
            rec_stack = set()
            cycles = []

            def dfs(node: str, path: List[str]):
                visited.add(node)
                rec_stack.add(node)
                path.append(node)

                for neighbor in adj.get(node, []):
                    if neighbor not in visited:
                        dfs(neighbor, path)
                    elif neighbor in rec_stack:
                        # Cycle found!
                        cycle_start_idx = path.index(neighbor)
                        cycle_path = path[cycle_start_idx:] + [neighbor]
                        cycles.append(cycle_path)

                path.pop()
                rec_stack.remove(node)

            for node in sorted(list(all_nodes)):
                if node not in visited:
                    dfs(node, [])

            has_cycle = len(cycles) > 0
            involved_pids = set()
            for c in cycles:
                for node in c:
                    if node.startswith("P"):
                        involved_pids.add(node)

            msg = f"RAG Cycle Detection: {'CYCLE DETECTED ⚠️ Potential Deadlock' if has_cycle else 'NO CYCLES FOUND ✅ System Clean'}."
            res = {
                "has_deadlock_cycle": has_cycle,
                "cycles": cycles,
                "deadlocked_processes": sorted(list(involved_pids)),
                "adjacency_list": adj,
                "message": msg
            }
            self.state.add_event("DEADLOCK", msg, res)
            return res
