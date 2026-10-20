from typing import List, Dict, Any
from backend.app.digital_twin.models import InvariantReport, ProcessState
from backend.app.digital_twin.state import simulation_state

class VerificationService:
    """Rigorous state invariant and safety validation engine for the Digital Twin."""

    def __init__(self, state=None):
        self.state = state or simulation_state

    def verify_invariants(self) -> InvariantReport:
        """Evaluates all system invariants across memory, processes, resources, and disk."""
        with self.state._lock:
            violations: List[str] = []
            checks_run = 0

            # ---------------------------------------------------------
            # 1. Memory Invariants
            # ---------------------------------------------------------
            checks_run += 1
            total_partition_size = sum(b.size for b in self.state.memory_blocks)
            if total_partition_size != self.state.total_memory_capacity:
                violations.append(
                    f"Memory size mismatch: sum of partitions ({total_partition_size} KB) != total memory capacity ({self.state.total_memory_capacity} KB)."
                )

            checks_run += 1
            # Check partition overlaps
            sorted_blocks = sorted(self.state.memory_blocks, key=lambda b: b.start_address)
            for i in range(len(sorted_blocks) - 1):
                cur = sorted_blocks[i]
                nxt = sorted_blocks[i+1]
                if cur.start_address + cur.size > nxt.start_address:
                    violations.append(
                        f"Memory partition overlap detected between Block {cur.block_id} and Block {nxt.block_id}."
                    )

            checks_run += 1
            for b in self.state.memory_blocks:
                if b.is_allocated and b.internal_fragmentation > b.size:
                    violations.append(
                        f"Block {b.block_id} internal fragmentation ({b.internal_fragmentation} KB) exceeds block size ({b.size} KB)."
                    )

            # ---------------------------------------------------------
            # 2. Process & Memory Cross-Consistency
            # ---------------------------------------------------------
            checks_run += 1
            for b in self.state.memory_blocks:
                if b.is_allocated:
                    if not b.allocated_pid:
                        violations.append(f"Block {b.block_id} is marked allocated but has no allocated_pid.")
                    elif b.allocated_pid not in self.state.processes:
                        violations.append(f"Block {b.block_id} references non-existent process {b.allocated_pid}.")

            checks_run += 1
            for pid, p in self.state.processes.items():
                if p.state == ProcessState.TERMINATED:
                    if p.allocated_memory_blocks:
                        violations.append(f"Terminated process {pid} still holds memory blocks {p.allocated_memory_blocks}.")
                    if p.allocated_resources:
                        violations.append(f"Terminated process {pid} still holds resource instances {p.allocated_resources}.")

            # ---------------------------------------------------------
            # 3. Resource Invariants
            # ---------------------------------------------------------
            checks_run += 1
            for r_name, res in self.state.resources.items():
                allocated_sum = sum(
                    p.allocated_resources.get(r_name, 0)
                    for p in self.state.processes.values()
                    if p.state != ProcessState.TERMINATED
                )
                if res.available_instances + allocated_sum != res.total_instances:
                    violations.append(
                        f"Resource count mismatch for {r_name}: Available ({res.available_instances}) + Allocated ({allocated_sum}) != Total ({res.total_instances})."
                    )

            checks_run += 1
            for pid, p in self.state.processes.items():
                for r_name, count in p.allocated_resources.items():
                    max_c = p.max_claim_resources.get(r_name, float("inf"))
                    if count > max_c:
                        violations.append(
                            f"Process {pid} holds {count} of {r_name}, which exceeds its declared maximum claim of {max_c}."
                        )

            # ---------------------------------------------------------
            # 4. Process State & Queue Invariants
            # ---------------------------------------------------------
            checks_run += 1
            overlap_queues = set(self.state.ready_queue).intersection(set(self.state.waiting_queue))
            if overlap_queues:
                violations.append(f"Processes {overlap_queues} are simultaneously in ready_queue and waiting_queue.")

            checks_run += 1
            if self.state.running_pid:
                run_p = self.state.processes.get(self.state.running_pid)
                if not run_p or run_p.state != ProcessState.RUNNING:
                    violations.append(f"running_pid is set to {self.state.running_pid}, but process state is {run_p.state if run_p else 'None'}.")

            # ---------------------------------------------------------
            # 5. Virtual Disk Invariants
            # ---------------------------------------------------------
            checks_run += 1
            total_disk_used = sum(f.size_kb for f in self.state.virtual_files.values())
            if total_disk_used > self.state.total_disk_capacity:
                violations.append(
                    f"Virtual disk over-allocated: Used ({total_disk_used} KB) exceeds total disk capacity ({self.state.total_disk_capacity} KB)."
                )

            is_valid = len(violations) == 0
            report = InvariantReport(
                is_valid=is_valid,
                checks_run=checks_run,
                violations=violations
            )

            msg = f"Invariant verification: {'VALID ✅ (0 violations)' if is_valid else f'VIOLATIONS FOUND ❌ ({len(violations)} issues)'} across {checks_run} invariant checks."
            self.state.add_event("SYSTEM", msg, {"is_valid": is_valid, "violations_count": len(violations)})

            return report
