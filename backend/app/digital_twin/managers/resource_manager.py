from typing import Dict, List, Optional, Any, Tuple
from backend.app.digital_twin.models import VirtualResource, ProcessState
from backend.app.digital_twin.state import simulation_state

class ResourceManager:
    """Manages virtual system resources, allocation, claims, and wait queues."""

    def __init__(self, state=None):
        self.state = state or simulation_state

    def register_resource(self, name: str, total_instances: int) -> Dict[str, Any]:
        with self.state._lock:
            name = name.upper().strip()
            self.state.resources[name] = VirtualResource(
                name=name,
                total_instances=total_instances,
                available_instances=total_instances
            )
            msg = f"Registered resource {name} with {total_instances} total instances."
            self.state.add_event("RESOURCE", msg, {"resource": name, "total": total_instances})
            return {"success": True, "message": msg}

    def request_resource(self, pid: str, resource_name: str, amount: int = 1) -> Dict[str, Any]:
        """Process requests instances of a resource. Blocks if not enough instances."""
        with self.state._lock:
            pid = pid.upper().strip()
            res_name = resource_name.upper().strip()

            if pid not in self.state.processes:
                return {"success": False, "error": f"Process {pid} not found."}
            if res_name not in self.state.resources:
                return {"success": False, "error": f"Resource {res_name} not found."}

            proc = self.state.processes[pid]
            res = self.state.resources[res_name]

            if res.available_instances >= amount:
                # Grant immediately
                res.available_instances -= amount
                proc.allocated_resources[res_name] = proc.allocated_resources.get(res_name, 0) + amount
                if res_name in proc.requested_resources:
                    del proc.requested_resources[res_name]

                msg = f"Granted {amount} instance(s) of {res_name} to Process {pid}. (Available remaining: {res.available_instances})."
                self.state.add_event("RESOURCE", msg, {"pid": pid, "resource": res_name, "amount": amount, "granted": True})
                return {"success": True, "granted": True, "message": msg}
            else:
                # Block process
                proc.requested_resources[res_name] = amount
                old_state = proc.state
                proc.state = ProcessState.WAITING
                if pid in self.state.ready_queue:
                    self.state.ready_queue.remove(pid)
                if self.state.running_pid == pid:
                    self.state.running_pid = None
                if pid not in self.state.waiting_queue:
                    self.state.waiting_queue.append(pid)

                msg = f"Process {pid} BLOCKED requesting {amount} of {res_name}. Only {res.available_instances} available. State: {old_state} -> WAITING."
                self.state.add_event("RESOURCE", msg, {"pid": pid, "resource": res_name, "amount": amount, "granted": False})
                return {"success": True, "granted": False, "blocked": True, "message": msg}

    def release_resource(self, pid: str, resource_name: str, amount: int = 1) -> Dict[str, Any]:
        """Process releases instances of a resource and potentially wakes waiting processes."""
        with self.state._lock:
            pid = pid.upper().strip()
            res_name = resource_name.upper().strip()

            if pid not in self.state.processes:
                return {"success": False, "error": f"Process {pid} not found."}
            if res_name not in self.state.resources:
                return {"success": False, "error": f"Resource {res_name} not found."}

            proc = self.state.processes[pid]
            res = self.state.resources[res_name]
            currently_held = proc.allocated_resources.get(res_name, 0)

            if currently_held < amount:
                return {"success": False, "error": f"Process {pid} holds only {currently_held} of {res_name}, cannot release {amount}."}

            proc.allocated_resources[res_name] -= amount
            if proc.allocated_resources[res_name] == 0:
                del proc.allocated_resources[res_name]

            res.available_instances += amount

            msg = f"Process {pid} released {amount} of {res_name}. Available now: {res.available_instances}."
            self.state.add_event("RESOURCE", msg, {"pid": pid, "resource": res_name, "amount": amount})

            # Check if any waiting process can be unblocked
            unblocked = []
            for wait_pid in list(self.state.waiting_queue):
                wait_proc = self.state.processes.get(wait_pid)
                if not wait_proc or not wait_proc.requested_resources:
                    continue

                can_satisfy_all = True
                for req_res, req_amt in wait_proc.requested_resources.items():
                    if self.state.resources.get(req_res, VirtualResource(name=req_res, total_instances=0, available_instances=0)).available_instances < req_amt:
                        can_satisfy_all = False
                        break

                if can_satisfy_all:
                    for req_res, req_amt in list(wait_proc.requested_resources.items()):
                        self.state.resources[req_res].available_instances -= req_amt
                        wait_proc.allocated_resources[req_res] = wait_proc.allocated_resources.get(req_res, 0) + req_amt
                    wait_proc.requested_resources = {}
                    wait_proc.state = ProcessState.READY
                    self.state.waiting_queue.remove(wait_pid)
                    self.state.ready_queue.append(wait_pid)
                    unblocked.append(wait_pid)
                    self.state.add_event("RESOURCE", f"Process {wait_pid} unblocked and moved to READY.", {"pid": wait_pid})

            return {"success": True, "message": msg, "unblocked_processes": unblocked}

    def get_matrices(self) -> Dict[str, Any]:
        """Generates Available, Max Claim, Allocation, and Need matrices for Deadlock/Banker analysis."""
        with self.state._lock:
            resource_keys = sorted(list(self.state.resources.keys()))
            available = [self.state.resources[r].available_instances for r in resource_keys]

            active_pids = sorted([pid for pid, p in self.state.processes.items() if p.state != ProcessState.TERMINATED])
            max_matrix = []
            alloc_matrix = []
            need_matrix = []

            for pid in active_pids:
                p = self.state.processes[pid]
                row_max = [p.max_claim_resources.get(r, 0) for r in resource_keys]
                row_alloc = [p.allocated_resources.get(r, 0) for r in resource_keys]
                row_need = [max(0, row_max[i] - row_alloc[i]) for i in range(len(resource_keys))]

                max_matrix.append(row_max)
                alloc_matrix.append(row_alloc)
                need_matrix.append(row_need)

            return {
                "resource_names": resource_keys,
                "process_names": active_pids,
                "available": available,
                "max_matrix": max_matrix,
                "allocation_matrix": alloc_matrix,
                "need_matrix": need_matrix
            }
