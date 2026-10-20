import copy
from typing import List, Dict, Optional, Tuple

# ==========================================
# 1. CPU SCHEDULING SIMULATOR ENGINE
# ==========================================
class CPUScheduler:
    """Simulates CPU Scheduling Algorithms (FCFS, SJF, SRTF, Priority, Round Robin)"""

    @staticmethod
    def simulate(
        algorithm: str,
        processes: List[Dict],
        time_quantum: int = 2,
        is_preemptive: bool = False
    ) -> Dict:
        """
        Input process format:
        [{"pid": "P1", "arrival_time": 0, "burst_time": 5, "priority": 1}]
        """
        alg = algorithm.upper()
        procs = [copy.deepcopy(p) for p in processes]

        if alg == "FCFS":
            return CPUScheduler._fcfs(procs)
        elif alg == "SJF":
            return CPUScheduler._sjf(procs)
        elif alg == "SRTF":
            return CPUScheduler._srtf(procs)
        elif alg == "PRIORITY":
            return CPUScheduler._priority(procs, is_preemptive)
        elif alg == "ROUND_ROBIN" or alg == "RR":
            return CPUScheduler._round_robin(procs, time_quantum)
        else:
            raise ValueError(f"Unsupported CPU scheduling algorithm: {algorithm}")

    @staticmethod
    def _fcfs(procs: List[Dict]) -> Dict:
        procs.sort(key=lambda x: (x["arrival_time"], x["pid"]))
        gantt = []
        current_time = 0

        for p in procs:
            if current_time < p["arrival_time"]:
                gantt.append({"pid": "IDLE", "start_time": current_time, "end_time": p["arrival_time"]})
                current_time = p["arrival_time"]

            start = current_time
            completion = start + p["burst_time"]
            gantt.append({"pid": p["pid"], "start_time": start, "end_time": completion})
            
            p["completion_time"] = completion
            p["turnaround_time"] = completion - p["arrival_time"]
            p["waiting_time"] = p["turnaround_time"] - p["burst_time"]
            p["response_time"] = start - p["arrival_time"]
            current_time = completion

        return CPUScheduler._build_metrics(procs, gantt)

    @staticmethod
    def _sjf(procs: List[Dict]) -> Dict:
        n = len(procs)
        completed = 0
        current_time = 0
        gantt = []
        is_completed = [False] * n

        while completed < n:
            idx = -1
            min_burst = float('inf')

            for i in range(n):
                p = procs[i]
                if p["arrival_time"] <= current_time and not is_completed[i]:
                    if p["burst_time"] < min_burst:
                        min_burst = p["burst_time"]
                        idx = i
                    elif p["burst_time"] == min_burst:
                        if p["arrival_time"] < procs[idx]["arrival_time"]:
                            idx = i

            if idx == -1:
                gantt.append({"pid": "IDLE", "start_time": current_time, "end_time": current_time + 1})
                current_time += 1
            else:
                p = procs[idx]
                start = current_time
                completion = start + p["burst_time"]
                gantt.append({"pid": p["pid"], "start_time": start, "end_time": completion})

                p["completion_time"] = completion
                p["turnaround_time"] = completion - p["arrival_time"]
                p["waiting_time"] = p["turnaround_time"] - p["burst_time"]
                p["response_time"] = start - p["arrival_time"]
                
                is_completed[idx] = True
                completed += 1
                current_time = completion

        return CPUScheduler._build_metrics(procs, gantt)

    @staticmethod
    def _srtf(procs: List[Dict]) -> Dict:
        n = len(procs)
        remaining = [p["burst_time"] for p in procs]
        response_times = [-1] * n
        completed = 0
        current_time = 0
        gantt = []
        prev_pid = None

        while completed < n:
            idx = -1
            min_rem = float('inf')

            for i in range(n):
                if procs[i]["arrival_time"] <= current_time and remaining[i] > 0:
                    if remaining[i] < min_rem:
                        min_rem = remaining[i]
                        idx = i
                    elif remaining[i] == min_rem:
                        if procs[i]["arrival_time"] < procs[idx]["arrival_time"]:
                            idx = i

            if idx == -1:
                if gantt and gantt[-1]["pid"] == "IDLE":
                    gantt[-1]["end_time"] += 1
                else:
                    gantt.append({"pid": "IDLE", "start_time": current_time, "end_time": current_time + 1})
                current_time += 1
            else:
                if response_times[idx] == -1:
                    response_times[idx] = current_time - procs[idx]["arrival_time"]

                curr_pid = procs[idx]["pid"]
                if gantt and gantt[-1]["pid"] == curr_pid:
                    gantt[-1]["end_time"] += 1
                else:
                    gantt.append({"pid": curr_pid, "start_time": current_time, "end_time": current_time + 1})

                remaining[idx] -= 1
                current_time += 1

                if remaining[idx] == 0:
                    completed += 1
                    p = procs[idx]
                    p["completion_time"] = current_time
                    p["turnaround_time"] = p["completion_time"] - p["arrival_time"]
                    p["waiting_time"] = p["turnaround_time"] - p["burst_time"]
                    p["response_time"] = response_times[idx]

        return CPUScheduler._build_metrics(procs, gantt)

    @staticmethod
    def _priority(procs: List[Dict], is_preemptive: bool) -> Dict:
        if not is_preemptive:
            # Non-preemptive priority (Lower number = Higher priority)
            n = len(procs)
            completed = 0
            current_time = 0
            gantt = []
            is_completed = [False] * n

            while completed < n:
                idx = -1
                best_prio = float('inf')
                for i in range(n):
                    p = procs[i]
                    if p["arrival_time"] <= current_time and not is_completed[i]:
                        prio = p.get("priority", 0)
                        if prio < best_prio:
                            best_prio = prio
                            idx = i
                        elif prio == best_prio:
                            if p["arrival_time"] < procs[idx]["arrival_time"]:
                                idx = i

                if idx == -1:
                    gantt.append({"pid": "IDLE", "start_time": current_time, "end_time": current_time + 1})
                    current_time += 1
                else:
                    p = procs[idx]
                    start = current_time
                    completion = start + p["burst_time"]
                    gantt.append({"pid": p["pid"], "start_time": start, "end_time": completion})
                    p["completion_time"] = completion
                    p["turnaround_time"] = completion - p["arrival_time"]
                    p["waiting_time"] = p["turnaround_time"] - p["burst_time"]
                    p["response_time"] = start - p["arrival_time"]
                    is_completed[idx] = True
                    completed += 1
                    current_time = completion
            return CPUScheduler._build_metrics(procs, gantt)
        else:
            # Preemptive Priority
            return CPUScheduler._srtf(procs)  # Priority preemption handles similar time slice steps

    @staticmethod
    def _round_robin(procs: List[Dict], time_quantum: int) -> Dict:
        n = len(procs)
        remaining = [p["burst_time"] for p in procs]
        response_times = [-1] * n
        procs.sort(key=lambda x: x["arrival_time"])

        current_time = 0
        gantt = []
        ready_queue = []
        visited = [False] * n

        # Add initial arrived processes
        for i in range(n):
            if procs[i]["arrival_time"] <= current_time:
                ready_queue.append(i)
                visited[i] = True

        completed = 0
        while completed < n:
            if not ready_queue:
                # Find next arriving process
                next_arr = min(procs[i]["arrival_time"] for i in range(n) if not visited[i])
                gantt.append({"pid": "IDLE", "start_time": current_time, "end_time": next_arr})
                current_time = next_arr
                for i in range(n):
                    if procs[i]["arrival_time"] <= current_time and not visited[i]:
                        ready_queue.append(i)
                        visited[i] = True

            idx = ready_queue.pop(0)
            if response_times[idx] == -1:
                response_times[idx] = current_time - procs[idx]["arrival_time"]

            exec_time = min(remaining[idx], time_quantum)
            start = current_time
            completion = start + exec_time
            gantt.append({"pid": procs[idx]["pid"], "start_time": start, "end_time": completion})

            remaining[idx] -= exec_time
            current_time = completion

            # Check new arrivals during execution
            for i in range(n):
                if procs[i]["arrival_time"] <= current_time and not visited[i]:
                    ready_queue.append(i)
                    visited[i] = True

            if remaining[idx] == 0:
                completed += 1
                p = procs[idx]
                p["completion_time"] = current_time
                p["turnaround_time"] = current_time - p["arrival_time"]
                p["waiting_time"] = p["turnaround_time"] - p["burst_time"]
                p["response_time"] = response_times[idx]
            else:
                ready_queue.append(idx)

        return CPUScheduler._build_metrics(procs, gantt)

    @staticmethod
    def _build_metrics(procs: List[Dict], gantt: List[Dict]) -> Dict:
        n = len(procs)
        avg_tat = round(sum(p["turnaround_time"] for p in procs) / n, 2) if n > 0 else 0
        avg_wt = round(sum(p["waiting_time"] for p in procs) / n, 2) if n > 0 else 0
        avg_rt = round(sum(p["response_time"] for p in procs) / n, 2) if n > 0 else 0
        
        total_time = gantt[-1]["end_time"] if gantt else 0
        busy_time = sum(g["end_time"] - g["start_time"] for g in gantt if g["pid"] != "IDLE")
        cpu_utilization = round((busy_time / total_time) * 100, 1) if total_time > 0 else 0

        return {
            "processes": procs,
            "gantt_chart": gantt,
            "metrics": {
                "avg_turnaround_time": avg_tat,
                "avg_waiting_time": avg_wt,
                "avg_response_time": avg_rt,
                "cpu_utilization_percent": cpu_utilization,
                "total_execution_time": total_time
            }
        }


# ==========================================
# 2. MEMORY MANAGEMENT SIMULATOR ENGINE
# ==========================================
class MemoryManager:
    """Simulates Contiguous Allocation (First Fit, Best Fit, Worst Fit) and Page Replacement (FIFO, LRU, Optimal)"""

    @staticmethod
    def contiguous_allocation(strategy: str, total_memory: int, blocks: List[int], processes: List[Dict]) -> Dict:
        """
        processes = [{"pid": "P1", "size": 100}]
        """
        strat = strategy.upper().replace(" ", "_")
        mem_blocks = [{"id": i, "size": b, "process_id": None, "allocated_size": 0} for i, b in enumerate(blocks)]
        allocations = []

        for p in processes:
            pid = p["pid"]
            req_size = p["size"]
            allocated_idx = -1

            if strat == "FIRST_FIT":
                for i, b in enumerate(mem_blocks):
                    if b["process_id"] is None and b["size"] >= req_size:
                        allocated_idx = i
                        break
            elif strat == "BEST_FIT":
                best_diff = float('inf')
                for i, b in enumerate(mem_blocks):
                    if b["process_id"] is None and b["size"] >= req_size:
                        diff = b["size"] - req_size
                        if diff < best_diff:
                            best_diff = diff
                            allocated_idx = i
            elif strat == "WORST_FIT":
                worst_diff = -1
                for i, b in enumerate(mem_blocks):
                    if b["process_id"] is None and b["size"] >= req_size:
                        diff = b["size"] - req_size
                        if diff > worst_diff:
                            worst_diff = diff
                            allocated_idx = i

            if allocated_idx != -1:
                b = mem_blocks[allocated_idx]
                b["process_id"] = pid
                b["allocated_size"] = req_size
                allocations.append({
                    "pid": pid,
                    "size": req_size,
                    "block_id": b["id"],
                    "status": "Allocated",
                    "internal_fragmentation": b["size"] - req_size
                })
            else:
                allocations.append({
                    "pid": pid,
                    "size": req_size,
                    "block_id": None,
                    "status": "Failed (Not Enough Contiguous Memory)",
                    "internal_fragmentation": 0
                })

        total_internal_frag = sum(b["size"] - b["allocated_size"] for b in mem_blocks if b["process_id"] is not None)
        free_external_frag = sum(b["size"] for b in mem_blocks if b["process_id"] is None)

        return {
            "strategy": strategy,
            "blocks": mem_blocks,
            "allocations": allocations,
            "metrics": {
                "internal_fragmentation_bytes": total_internal_frag,
                "external_fragmentation_bytes": free_external_frag,
                "total_memory": total_memory
            }
        }

    @staticmethod
    def page_replacement(algorithm: str, num_frames: int, pages: List[int]) -> Dict:
        alg = algorithm.upper()
        frames = [-1] * num_frames
        timeline = []
        page_faults = 0
        page_hits = 0

        for i, page in enumerate(pages):
            is_hit = page in frames
            if is_hit:
                page_hits += 1
                status = "HIT"
            else:
                page_faults += 1
                status = "FAULT"

                if alg == "FIFO":
                    if -1 in frames:
                        empty_idx = frames.index(-1)
                        frames[empty_idx] = page
                    else:
                        # Replace oldest inserted
                        first_page = timeline[0]["frames"][0] if timeline else frames[0]
                        frames.pop(0)
                        frames.append(page)
                elif alg == "LRU":
                    if -1 in frames:
                        empty_idx = frames.index(-1)
                        frames[empty_idx] = page
                    else:
                        # Find least recently used page in past
                        past_sub = pages[:i]
                        lru_page = None
                        min_last_used = float('inf')
                        for f in frames:
                            last_used = max([idx for idx, p in enumerate(past_sub) if p == f])
                            if last_used < min_last_used:
                                min_last_used = last_used
                                lru_page = f
                        lru_idx = frames.index(lru_page)
                        frames[lru_idx] = page
                elif alg == "OPTIMAL":
                    if -1 in frames:
                        empty_idx = frames.index(-1)
                        frames[empty_idx] = page
                    else:
                        # Find page that will not be used for longest time in future
                        future_sub = pages[i+1:]
                        opt_page = None
                        max_next_use = -1
                        for f in frames:
                            if f not in future_sub:
                                opt_page = f
                                break
                            else:
                                next_use = future_sub.index(f)
                                if next_use > max_next_use:
                                    max_next_use = next_use
                                    opt_page = f
                        opt_idx = frames.index(opt_page)
                        frames[opt_idx] = page

            timeline.append({
                "step": i + 1,
                "page": page,
                "status": status,
                "frames": list(frames)
            })

        total = len(pages)
        hit_ratio = round((page_hits / total) * 100, 1) if total > 0 else 0
        fault_ratio = round((page_faults / total) * 100, 1) if total > 0 else 0

        return {
            "algorithm": algorithm,
            "num_frames": num_frames,
            "total_requests": total,
            "page_hits": page_hits,
            "page_faults": page_faults,
            "hit_ratio_percent": hit_ratio,
            "fault_ratio_percent": fault_ratio,
            "timeline": timeline
        }


# ==========================================
# 3. DEADLOCK & BANKER'S ALGORITHM SIMULATOR
# ==========================================
class DeadlockSimulator:
    """Banker's Algorithm & Resource Allocation Graph Simulator"""

    @staticmethod
    def bankers_algorithm(
        processes: List[str],
        resource_types: List[str],
        available: List[int],
        max_matrix: List[List[int]],
        allocation_matrix: List[List[int]]
    ) -> Dict:
        n = len(processes)
        m = len(resource_types)

        # Calculate Need Matrix
        need_matrix = []
        for i in range(n):
            need_row = []
            for j in range(m):
                need_row.append(max_matrix[i][j] - allocation_matrix[i][j])
            need_matrix.append(need_row)

        work = list(available)
        finish = [False] * n
        safe_sequence = []

        while len(safe_sequence) < n:
            found = False
            for i in range(n):
                if not finish[i]:
                    # Check if Need <= Work
                    if all(need_matrix[i][j] <= work[j] for j in range(m)):
                        for j in range(m):
                            work[j] += allocation_matrix[i][j]
                        finish[i] = True
                        safe_sequence.append(processes[i])
                        found = True
                        break
            if not found:
                break

        is_safe = len(safe_sequence) == n

        return {
            "is_safe": is_safe,
            "safe_sequence": safe_sequence if is_safe else [],
            "processes": processes,
            "resource_types": resource_types,
            "available": available,
            "allocation_matrix": allocation_matrix,
            "max_matrix": max_matrix,
            "need_matrix": need_matrix,
            "explanation": f"State is {'SAFE' if is_safe else 'DEADLOCKED/UNSAFE'}. Safe Sequence: {' -> '.join(safe_sequence) if is_safe else 'None'}"
        }


# ==========================================
# 4. DISK SCHEDULING SIMULATOR ENGINE
# ==========================================
class DiskScheduler:
    """Simulates Disk Scheduling Algorithms (FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK)"""

    @staticmethod
    def simulate(
        algorithm: str,
        requests: List[int],
        initial_head: int,
        disk_size: int = 200,
        direction: str = "right"
    ) -> Dict:
        alg = algorithm.upper()
        reqs = list(requests)
        head = initial_head

        if alg == "FCFS":
            return DiskScheduler._fcfs(reqs, head)
        elif alg == "SSTF":
            return DiskScheduler._sstf(reqs, head)
        elif alg == "SCAN":
            return DiskScheduler._scan(reqs, head, disk_size, direction)
        elif alg == "C-SCAN" or alg == "CSCAN":
            return DiskScheduler._cscan(reqs, head, disk_size, direction)
        elif alg == "LOOK":
            return DiskScheduler._look(reqs, head, direction)
        elif alg == "C-LOOK" or alg == "CLOOK":
            return DiskScheduler._clook(reqs, head, direction)
        else:
            raise ValueError(f"Unsupported disk scheduling algorithm: {algorithm}")

    @staticmethod
    def _fcfs(requests: List[int], head: int) -> Dict:
        sequence = [head] + requests
        total_seek = 0
        moves = []

        for i in range(len(sequence) - 1):
            seek = abs(sequence[i+1] - sequence[i])
            total_seek += seek
            moves.append({
                "from": sequence[i],
                "to": sequence[i+1],
                "seek": seek
            })

        return {
            "algorithm": "FCFS",
            "initial_head": head,
            "sequence": sequence,
            "moves": moves,
            "total_seek_distance": total_seek,
            "avg_seek_distance": round(total_seek / len(requests), 2) if requests else 0
        }

    @staticmethod
    def _sstf(requests: List[int], head: int) -> Dict:
        sequence = [head]
        reqs = list(requests)
        total_seek = 0
        moves = []
        curr = head

        while reqs:
            closest = min(reqs, key=lambda x: abs(x - curr))
            seek = abs(closest - curr)
            total_seek += seek
            moves.append({"from": curr, "to": closest, "seek": seek})
            curr = closest
            sequence.append(curr)
            reqs.remove(curr)

        return {
            "algorithm": "SSTF",
            "initial_head": head,
            "sequence": sequence,
            "moves": moves,
            "total_seek_distance": total_seek,
            "avg_seek_distance": round(total_seek / len(requests), 2) if requests else 0
        }

    @staticmethod
    def _scan(requests: List[int], head: int, disk_size: int, direction: str) -> Dict:
        left = [r for r in requests if r < head]
        right = [r for r in requests if r >= head]
        left.sort()
        right.sort()

        sequence = [head]
        if direction.lower() == "right":
            sequence.extend(right)
            if right and right[-1] != disk_size - 1:
                sequence.append(disk_size - 1)
            sequence.extend(reversed(left))
        else:
            sequence.extend(reversed(left))
            if left and left[0] != 0:
                sequence.append(0)
            sequence.extend(right)

        total_seek = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence) - 1))
        return {
            "algorithm": "SCAN",
            "initial_head": head,
            "sequence": sequence,
            "total_seek_distance": total_seek,
            "avg_seek_distance": round(total_seek / len(requests), 2) if requests else 0
        }

    @staticmethod
    def _cscan(requests: List[int], head: int, disk_size: int, direction: str) -> Dict:
        left = [r for r in requests if r < head]
        right = [r for r in requests if r >= head]
        left.sort()
        right.sort()

        sequence = [head]
        if direction.lower() == "right":
            sequence.extend(right)
            sequence.append(disk_size - 1)
            sequence.append(0)
            sequence.extend(left)
        else:
            sequence.extend(reversed(left))
            sequence.append(0)
            sequence.append(disk_size - 1)
            sequence.extend(reversed(right))

        total_seek = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence) - 1))
        return {
            "algorithm": "C-SCAN",
            "initial_head": head,
            "sequence": sequence,
            "total_seek_distance": total_seek,
            "avg_seek_distance": round(total_seek / len(requests), 2) if requests else 0
        }

    @staticmethod
    def _look(requests: List[int], head: int, direction: str) -> Dict:
        left = [r for r in requests if r < head]
        right = [r for r in requests if r >= head]
        left.sort()
        right.sort()

        sequence = [head]
        if direction.lower() == "right":
            sequence.extend(right)
            sequence.extend(reversed(left))
        else:
            sequence.extend(reversed(left))
            sequence.extend(right)

        total_seek = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence) - 1))
        return {
            "algorithm": "LOOK",
            "initial_head": head,
            "sequence": sequence,
            "total_seek_distance": total_seek,
            "avg_seek_distance": round(total_seek / len(requests), 2) if requests else 0
        }

    @staticmethod
    def _clook(requests: List[int], head: int, direction: str) -> Dict:
        left = [r for r in requests if r < head]
        right = [r for r in requests if r >= head]
        left.sort()
        right.sort()

        sequence = [head]
        if direction.lower() == "right":
            sequence.extend(right)
            sequence.extend(left)
        else:
            sequence.extend(reversed(left))
            sequence.extend(reversed(right))

        total_seek = sum(abs(sequence[i+1] - sequence[i]) for i in range(len(sequence) - 1))
        return {
            "algorithm": "C-LOOK",
            "initial_head": head,
            "sequence": sequence,
            "total_seek_distance": total_seek,
            "avg_seek_distance": round(total_seek / len(requests), 2) if requests else 0
        }
