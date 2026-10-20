from typing import Dict, List, Optional, Any, Tuple
from backend.app.digital_twin.models import MemoryBlock, PageFrame, ProcessState
from backend.app.digital_twin.state import simulation_state
from backend.app.services.simulators import MemoryManager as LegacyMemorySimulator

class MemoryManager:
    """Manages virtual physical memory, contiguous partitions, and paging."""

    def __init__(self, state=None):
        self.state = state or simulation_state

    def allocate(self, pid: str, size_kb: int, strategy: str = "FIRST_FIT") -> Dict[str, Any]:
        """Contiguous partition allocation using FIRST_FIT, BEST_FIT, or WORST_FIT."""
        with self.state._lock:
            pid = pid.upper().strip()
            strat = strategy.upper().strip()

            if pid not in self.state.processes:
                return {"success": False, "error": f"Process {pid} not found."}

            proc = self.state.processes[pid]
            free_blocks = [b for b in self.state.memory_blocks if not b.is_allocated]

            if not free_blocks:
                return {
                    "success": False,
                    "error": f"Out of Memory: No free memory blocks available for {size_kb} KB."
                }

            chosen_block: Optional[MemoryBlock] = None

            if strat == "FIRST_FIT":
                for b in free_blocks:
                    if b.size >= size_kb:
                        chosen_block = b
                        break

            elif strat == "BEST_FIT":
                suitable = [b for b in free_blocks if b.size >= size_kb]
                if suitable:
                    chosen_block = min(suitable, key=lambda b: b.size - size_kb)

            elif strat == "WORST_FIT":
                suitable = [b for b in free_blocks if b.size >= size_kb]
                if suitable:
                    chosen_block = max(suitable, key=lambda b: b.size - size_kb)

            else:
                return {"success": False, "error": f"Unknown allocation strategy: {strategy}. Use FIRST_FIT, BEST_FIT, or WORST_FIT."}

            if not chosen_block:
                total_free = sum(b.size for b in free_blocks)
                return {
                    "success": False,
                    "error": f"External Fragmentation: {total_free} KB total free across {len(free_blocks)} blocks, but no single contiguous block fits {size_kb} KB."
                }

            # Allocate block
            chosen_block.is_allocated = True
            chosen_block.allocated_pid = pid
            chosen_block.internal_fragmentation = chosen_block.size - size_kb
            if chosen_block.block_id not in proc.allocated_memory_blocks:
                proc.allocated_memory_blocks.append(chosen_block.block_id)

            if proc.state == ProcessState.NEW:
                proc.state = ProcessState.READY
                if pid not in self.state.ready_queue:
                    self.state.ready_queue.append(pid)

            msg = f"Allocated Block {chosen_block.block_id} ({chosen_block.size} KB) to {pid} using {strat} (Internal Frag: {chosen_block.internal_fragmentation} KB)."
            self.state.add_event("MEMORY", msg, {
                "pid": pid, "block_id": chosen_block.block_id, "size": size_kb, "strategy": strat, "internal_frag": chosen_block.internal_fragmentation
            })

            return {
                "success": True,
                "block_id": chosen_block.block_id,
                "start_address": chosen_block.start_address,
                "allocated_size": chosen_block.size,
                "requested_size": size_kb,
                "internal_fragmentation": chosen_block.internal_fragmentation,
                "strategy": strat,
                "message": msg
            }

    def deallocate(self, pid: str) -> Dict[str, Any]:
        """Deallocates all memory blocks reserved by the process."""
        with self.state._lock:
            pid = pid.upper().strip()
            freed = []
            for b in self.state.memory_blocks:
                if b.allocated_pid == pid:
                    b.is_allocated = False
                    b.allocated_pid = None
                    b.internal_fragmentation = 0
                    freed.append(b.block_id)

            if pid in self.state.processes:
                self.state.processes[pid].allocated_memory_blocks = []

            msg = f"Deallocated {len(freed)} memory block(s) for Process {pid} (Blocks: {freed})."
            self.state.add_event("MEMORY", msg, {"pid": pid, "freed_blocks": freed})
            return {"success": True, "pid": pid, "freed_blocks": freed, "message": msg}

    def get_fragmentation_metrics(self) -> Dict[str, Any]:
        with self.state._lock:
            total_cap = self.state.total_memory_capacity
            allocated_blocks = [b for b in self.state.memory_blocks if b.is_allocated]
            free_blocks = [b for b in self.state.memory_blocks if not b.is_allocated]

            int_frag = sum(b.internal_fragmentation for b in allocated_blocks)
            ext_frag = sum(b.size for b in free_blocks)
            used_mem = sum(b.size for b in allocated_blocks)

            return {
                "total_capacity_kb": total_cap,
                "used_capacity_kb": used_mem,
                "free_capacity_kb": ext_frag,
                "internal_fragmentation_kb": int_frag,
                "external_fragmentation_kb": ext_frag,
                "allocated_block_count": len(allocated_blocks),
                "free_block_count": len(free_blocks)
            }

    def simulate_page_replacement(self, algorithm: str, reference_pages: List[int], num_frames: int = 4) -> Dict[str, Any]:
        """Runs page replacement simulation and records performance metrics."""
        with self.state._lock:
            res = LegacyMemorySimulator.page_replacement(algorithm, num_frames, reference_pages)
            self.state.page_hits += res.get("page_hits", 0)
            self.state.page_faults += res.get("page_faults", 0)

            # Update state page frames based on final frame status
            final_frames = res.get("frames", [])
            self.state.page_frames = [
                PageFrame(frame_id=idx + 1, page_number=p if p != -1 else None, last_accessed=self.state.tick)
                for idx, p in enumerate(final_frames)
            ]

            msg = f"Simulated {algorithm} Page Replacement ({len(reference_pages)} pages, {num_frames} frames): Hits={res['page_hits']}, Faults={res['page_faults']}."
            self.state.add_event("MEMORY", msg, res)
            return res
