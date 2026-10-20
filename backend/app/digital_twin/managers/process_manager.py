from typing import Dict, List, Optional, Tuple, Any
from backend.app.digital_twin.models import VirtualProcess, ProcessState
from backend.app.digital_twin.state import simulation_state

class ProcessManager:
    """Manages virtual process lifecycles, states, and process control blocks (PCBs)."""

    def __init__(self, state=None):
        self.state = state or simulation_state

    def create_process(
        self,
        pid: str,
        name: str = "",
        burst_time: int = 4,
        memory_required: int = 128,
        priority: int = 1,
        arrival_time: int = 0,
        max_claim_resources: Optional[Dict[str, int]] = None
    ) -> Dict[str, Any]:
        """Creates a new virtual process in NEW state and attempts memory allocation."""
        with self.state._lock:
            pid = pid.upper().strip()
            if pid in self.state.processes:
                return {"success": False, "error": f"Process {pid} already exists."}

            if not name:
                name = f"proc_{pid.lower()}"

            proc = VirtualProcess(
                pid=pid,
                name=name,
                state=ProcessState.NEW,
                priority=priority,
                arrival_time=arrival_time,
                burst_time=burst_time,
                remaining_burst=burst_time,
                memory_required=memory_required,
                max_claim_resources=max_claim_resources or {"R1": 1, "R2": 1, "R3": 1}
            )
            self.state.processes[pid] = proc

            # Attempt initial contiguous memory allocation (First-Fit)
            allocated = False
            for block in self.state.memory_blocks:
                if not block.is_allocated and block.size >= memory_required:
                    block.is_allocated = True
                    block.allocated_pid = pid
                    block.internal_fragmentation = block.size - memory_required
                    proc.allocated_memory_blocks.append(block.block_id)
                    allocated = True
                    break

            if allocated:
                proc.state = ProcessState.READY
                if pid not in self.state.ready_queue:
                    self.state.ready_queue.append(pid)
                msg = f"Process {pid} ({name}) created and admitted to READY queue (Allocated Block {proc.allocated_memory_blocks[0]})."
            else:
                msg = f"Process {pid} ({name}) created in NEW state (Waiting for free memory partition)."

            self.state.add_event("PROCESS", msg, {"pid": pid, "allocated": allocated})
            return {"success": True, "process": proc.model_dump(), "message": msg}

    def terminate_process(self, pid: str, exit_code: int = 0) -> Dict[str, Any]:
        """Terminates process, deallocates memory, and returns held resources."""
        with self.state._lock:
            pid = pid.upper().strip()
            if pid not in self.state.processes:
                return {"success": False, "error": f"Process {pid} not found."}

            proc = self.state.processes[pid]
            old_state = proc.state
            proc.state = ProcessState.TERMINATED
            proc.exit_code = exit_code

            # 1. Clean from active queues
            if pid in self.state.ready_queue:
                self.state.ready_queue.remove(pid)
            if pid in self.state.waiting_queue:
                self.state.waiting_queue.remove(pid)
            if self.state.running_pid == pid:
                self.state.running_pid = None
            if pid not in self.state.terminated_list:
                self.state.terminated_list.append(pid)

            # 2. Free Memory Blocks
            freed_memory_blocks = []
            for block in self.state.memory_blocks:
                if block.allocated_pid == pid:
                    block.is_allocated = False
                    block.allocated_pid = None
                    block.internal_fragmentation = 0
                    freed_memory_blocks.append(block.block_id)
            proc.allocated_memory_blocks = []

            # 3. Return Allocated Resources to System Pool
            freed_resources = {}
            for res_name, count in proc.allocated_resources.items():
                if res_name in self.state.resources:
                    self.state.resources[res_name].available_instances += count
                    freed_resources[res_name] = count
            proc.allocated_resources = {}
            proc.requested_resources = {}

            msg = f"Process {pid} TERMINATED (from {old_state}). Freed {len(freed_memory_blocks)} memory blocks and resources {freed_resources}."
            self.state.add_event("PROCESS", msg, {"pid": pid, "freed_memory": freed_memory_blocks, "freed_resources": freed_resources})

            # 4. Check if any NEW process can now be admitted to READY
            for other_pid, other_proc in self.state.processes.items():
                if other_proc.state == ProcessState.NEW:
                    for block in self.state.memory_blocks:
                        if not block.is_allocated and block.size >= other_proc.memory_required:
                            block.is_allocated = True
                            block.allocated_pid = other_pid
                            block.internal_fragmentation = block.size - other_proc.memory_required
                            other_proc.allocated_memory_blocks.append(block.block_id)
                            other_proc.state = ProcessState.READY
                            self.state.ready_queue.append(other_pid)
                            self.state.add_event("MEMORY", f"Process {other_pid} admitted to READY after deallocation.")
                            break

            return {"success": True, "pid": pid, "freed_blocks": freed_memory_blocks, "freed_resources": freed_resources, "message": msg}

    def transition_state(self, pid: str, target_state: str) -> Dict[str, Any]:
        """Performs a verified operating-system state transition."""
        with self.state._lock:
            pid = pid.upper().strip()
            target = target_state.upper().strip()

            if pid not in self.state.processes:
                return {"success": False, "error": f"Process {pid} not found."}

            try:
                tgt_enum = ProcessState(target)
            except ValueError:
                return {"success": False, "error": f"Invalid state: {target_state}. Must be one of {[s.value for s in ProcessState]}"}

            proc = self.state.processes[pid]
            current = proc.state

            if current == tgt_enum:
                return {"success": True, "message": f"Process {pid} is already in state {target}."}

            # Verify legal transition
            legal_transitions = {
                ProcessState.NEW: [ProcessState.READY, ProcessState.TERMINATED],
                ProcessState.READY: [ProcessState.RUNNING, ProcessState.WAITING, ProcessState.TERMINATED],
                ProcessState.RUNNING: [ProcessState.READY, ProcessState.WAITING, ProcessState.TERMINATED],
                ProcessState.WAITING: [ProcessState.READY, ProcessState.TERMINATED],
                ProcessState.TERMINATED: []
            }

            if tgt_enum not in legal_transitions.get(current, []):
                return {
                    "success": False,
                    "error": f"Illegal state transition from {current} to {target}."
                }

            if tgt_enum == ProcessState.TERMINATED:
                return self.terminate_process(pid)

            # Update queues
            if current == ProcessState.READY and pid in self.state.ready_queue:
                self.state.ready_queue.remove(pid)
            elif current == ProcessState.WAITING and pid in self.state.waiting_queue:
                self.state.waiting_queue.remove(pid)
            elif current == ProcessState.RUNNING and self.state.running_pid == pid:
                self.state.running_pid = None

            proc.state = tgt_enum

            if tgt_enum == ProcessState.RUNNING:
                if self.state.running_pid and self.state.running_pid != pid:
                    # Preempt existing running process back to READY
                    old_run = self.state.running_pid
                    if old_run in self.state.processes:
                        self.state.processes[old_run].state = ProcessState.READY
                        self.state.ready_queue.append(old_run)
                self.state.running_pid = pid
            elif tgt_enum == ProcessState.READY:
                if pid not in self.state.ready_queue:
                    self.state.ready_queue.append(pid)
            elif tgt_enum == ProcessState.WAITING:
                if pid not in self.state.waiting_queue:
                    self.state.waiting_queue.append(pid)

            msg = f"Process {pid} transitioned from {current} to {target}."
            self.state.add_event("PROCESS", msg, {"pid": pid, "from": str(current), "to": target})
            return {"success": True, "pid": pid, "state": target, "message": msg}

    def list_processes(self) -> List[Dict[str, Any]]:
        with self.state._lock:
            return [p.model_dump() for p in self.state.processes.values()]

    def get_process(self, pid: str) -> Optional[Dict[str, Any]]:
        with self.state._lock:
            p = self.state.processes.get(pid.upper().strip())
            return p.model_dump() if p else None
