import re
from typing import Dict, List, Optional, Any
from backend.app.digital_twin.state import simulation_state, SimulationState
from backend.app.digital_twin.managers.process_manager import ProcessManager
from backend.app.digital_twin.managers.memory_manager import MemoryManager
from backend.app.digital_twin.managers.disk_manager import DiskManager
from backend.app.digital_twin.managers.resource_manager import ResourceManager
from backend.app.digital_twin.managers.scheduler import VirtualScheduler
from backend.app.digital_twin.managers.io_manager import IOManager
from backend.app.digital_twin.managers.deadlock_manager import DeadlockManager
from backend.app.digital_twin.services.scenario_service import ScenarioService
from backend.app.digital_twin.services.verification_service import VerificationService

class DigitalTwinEngine:
    """Unified coordinating engine for the SmartShell OS Digital Twin."""

    def __init__(self, state: Optional[SimulationState] = None):
        self.state = state or simulation_state
        self.process_manager = ProcessManager(self.state)
        self.memory_manager = MemoryManager(self.state)
        self.disk_manager = DiskManager(self.state)
        self.resource_manager = ResourceManager(self.state)
        self.scheduler = VirtualScheduler(self.state)
        self.io_manager = IOManager(self.state)
        self.deadlock_manager = DeadlockManager(self.state)
        self.scenario_service = ScenarioService(self.state)
        self.verification_service = VerificationService(self.state)

    def get_full_state(self) -> Dict[str, Any]:
        """Returns deep snapshot of the complete virtual operating-system state."""
        return self.state.to_dict()

    def reset_state(self) -> Dict[str, Any]:
        """Resets the Digital Twin to initial baseline workload."""
        self.state.reset_to_default()
        return {"success": True, "message": "SmartShell OS Digital Twin reset to initial baseline state."}

    def execute_command_or_nl(self, text: str) -> Dict[str, Any]:
        """
        Parses and executes an OS instruction on the Digital Twin.
        Works deterministically without external LLM dependencies,
        and accepts natural language phrases as well as 'dt <command>' syntax.
        """
        raw = text.strip()
        lower = raw.lower()

        # Remove optional command prefixes
        cmd_text = re.sub(r'^(dt|digital[-_ ]?twin)\s+', '', raw, flags=re.IGNORECASE).strip()
        cmd_lower = cmd_text.lower()

        # -------------------------------------------------------------
        # 1. State Status / Summary
        # -------------------------------------------------------------
        if cmd_lower in ["status", "state", "show", "info", "overview", "show os state", "show virtual os state", "inspect"]:
            st = self.state.to_dict()
            inv = self.verification_service.verify_invariants()
            return {
                "success": True,
                "action": "status",
                "tick": st["tick"],
                "process_count": len(st["processes"]),
                "ready_queue": st["ready_queue"],
                "waiting_queue": st["waiting_queue"],
                "running_pid": st["running_pid"],
                "memory_used_kb": st["metrics"]["used_memory_kb"],
                "memory_total_kb": st["metrics"]["total_memory_kb"],
                "virtual_files_count": len(st["virtual_files"]),
                "invariants_valid": inv.is_valid,
                "message": f"Digital Twin active at tick {st['tick']}. {len(st['processes'])} processes, {st['metrics']['used_memory_kb']}/{st['metrics']['total_memory_kb']} KB RAM used. Invariants: {'VALID ✅' if inv.is_valid else 'VIOLATIONS ❌'}."
            }

        # -------------------------------------------------------------
        # 2. Reset
        # -------------------------------------------------------------
        if cmd_lower in ["reset", "restart", "reboot", "clean", "reset virtual os"]:
            return self.reset_state()

        # -------------------------------------------------------------
        # 3. Invariant Verification
        # -------------------------------------------------------------
        if "verify" in cmd_lower or "invariant" in cmd_lower or "check integrity" in cmd_lower:
            report = self.verification_service.verify_invariants()
            return {
                "success": True,
                "action": "verify",
                "is_valid": report.is_valid,
                "checks_run": report.checks_run,
                "violations": report.violations,
                "message": f"Verification completed ({report.checks_run} checks): {'ALL INVARIANTS PASSED ✅' if report.is_valid else f'{len(report.violations)} VIOLATIONS FOUND ❌'}."
            }

        # -------------------------------------------------------------
        # 4. Deadlock & Banker's Algorithm
        # -------------------------------------------------------------
        if any(k in cmd_lower for k in ["deadlock", "banker", "rag", "safe state", "safe sequence"]):
            banker_res = self.deadlock_manager.check_bankers_safety()
            rag_res = self.deadlock_manager.detect_rag_cycles()
            return {
                "success": True,
                "action": "deadlock_check",
                "is_safe": banker_res.get("is_safe", False),
                "safe_sequence": banker_res.get("safe_sequence", []),
                "need_matrix": banker_res.get("need_matrix", []),
                "has_deadlock_cycle": rag_res.get("has_deadlock_cycle", False),
                "deadlocked_processes": rag_res.get("deadlocked_processes", []),
                "message": f"{banker_res['message']} {rag_res['message']}"
            }

        # -------------------------------------------------------------
        # 5. Side-by-Side Algorithm Comparison
        # -------------------------------------------------------------
        if "compare" in cmd_lower or "benchmark" in cmd_lower:
            # Check for optional quantum
            tq_match = re.search(r'quantum\s*(\d+)', cmd_lower)
            tq = int(tq_match.group(1)) if tq_match else 2
            return self.scenario_service.compare_scheduling_algorithms(time_quantum=tq)

        # -------------------------------------------------------------
        # 6. Snapshots
        # -------------------------------------------------------------
        if "snapshot" in cmd_lower:
            if "restore" in cmd_lower or "load" in cmd_lower:
                match = re.search(r'(?:restore|load)\s+([a-zA-Z0-9_\-]+)', cmd_text)
                if match:
                    return self.scenario_service.restore_snapshot(match.group(1))
                else:
                    snaps = self.scenario_service.list_snapshots()
                    if snaps:
                        return self.scenario_service.restore_snapshot(snaps[-1]["snapshot_id"])
                    return {"success": False, "error": "No snapshot ID specified and no snapshots exist."}
            elif "list" in cmd_lower:
                return {"success": True, "snapshots": self.scenario_service.list_snapshots()}
            else:
                # Create snapshot
                label_match = re.search(r'(?:create|take|save)?\s*(?:label|named|as)?\s*([a-zA-Z0-9_\- ]+)?', cmd_text)
                label = label_match.group(1).strip() if label_match and label_match.group(1) else "Manual Snapshot"
                return self.scenario_service.create_snapshot(label=label)

        # -------------------------------------------------------------
        # 7. Process Creation
        # -------------------------------------------------------------
        # Matches: create process P6 burst 5 memory 200 priority 2
        if ("process" in cmd_lower and ("create" in cmd_lower or "spawn" in cmd_lower or "add" in cmd_lower)) or cmd_lower.startswith("create virtual process"):
            pid_match = re.search(r'\b([P|p]\d+)\b', cmd_text)
            if not pid_match:
                pid_match = re.search(r'(?:create|spawn|add)\s+(?:process\s+|proc\s+)?([A-Za-z0-9_]+)', cmd_text, re.IGNORECASE)
            raw_pid = pid_match.group(1).upper() if pid_match else ""
            if raw_pid.lower() in ["create", "spawn", "add", "process", "proc", "virtual"]:
                pid = f"P{len(self.state.processes) + 1}"
            elif raw_pid:
                pid = raw_pid
            else:
                pid = f"P{len(self.state.processes) + 1}"
            
            burst_match = re.search(r'burst\s*(\d+)', cmd_lower)
            burst = int(burst_match.group(1)) if burst_match else 4
            
            mem_match = re.search(r'(?:memory|mem|size)\s*(\d+)', cmd_lower)
            mem = int(mem_match.group(1)) if mem_match else 128
            
            pri_match = re.search(r'priority\s*(\d+)', cmd_lower)
            pri = int(pri_match.group(1)) if pri_match else 1

            return self.process_manager.create_process(
                pid=pid,
                burst_time=burst,
                memory_required=mem,
                priority=pri
            )

        # -------------------------------------------------------------
        # 8. Process Termination
        # -------------------------------------------------------------
        if any(k in cmd_lower for k in ["terminate", "kill", "stop process", "exit process"]):
            pid_match = re.search(r'\b([P|p]\d+)\b', cmd_text)
            if not pid_match:
                pid_match = re.search(r'(?:terminate|kill|stop)\s+(?:process\s+|proc\s+)?([A-Za-z0-9_]+)', cmd_text, re.IGNORECASE)
            if pid_match and pid_match.group(1).lower() not in ["process", "proc", "terminate", "kill", "stop"]:
                return self.process_manager.terminate_process(pid_match.group(1).upper())
            return {"success": False, "error": "Could not identify target PID to terminate."}

        # -------------------------------------------------------------
        # 9. CPU Scheduling Execution
        # -------------------------------------------------------------
        # Matches: schedule round robin quantum 3 / run scheduler sjf
        if "disk" not in cmd_lower and any(k in cmd_lower for k in ["schedule", "run scheduler", "cpu schedule"]):
            alg = "ROUND_ROBIN"
            if "fcfs" in cmd_lower:
                alg = "FCFS"
            elif "srtf" in cmd_lower:
                alg = "SRTF"
            elif "sjf" in cmd_lower:
                alg = "SJF"
            elif "priority" in cmd_lower:
                alg = "PRIORITY"
            elif "round robin" in cmd_lower or "rr" in cmd_lower:
                alg = "ROUND_ROBIN"

            tq_match = re.search(r'quantum\s*(\d+)', cmd_lower)
            tq = int(tq_match.group(1)) if tq_match else 2

            return self.scheduler.schedule(algorithm=alg, time_quantum=tq)

        # -------------------------------------------------------------
        # 10. Memory Allocation & Paging
        # -------------------------------------------------------------
        if "memory" in cmd_lower:
            if "allocate" in cmd_lower or "alloc" in cmd_lower:
                pid_match = re.search(r'\b([P|p]\d+)\b', cmd_text)
                if not pid_match:
                    pid_match = re.search(r'(?:allocate|alloc)\s+(?:for\s+)?([A-Za-z0-9_]+)', cmd_text, re.IGNORECASE)
                pid = pid_match.group(1).upper() if pid_match and pid_match.group(1).lower() not in ["memory", "allocate", "alloc", "for"] else "P1"
                
                size_match = re.search(r'(\d+)\s*(?:kb|mb)?', cmd_lower)
                size = int(size_match.group(1)) if size_match else 100

                strat = "FIRST_FIT"
                if "best" in cmd_lower:
                    strat = "BEST_FIT"
                elif "worst" in cmd_lower:
                    strat = "WORST_FIT"

                return self.memory_manager.allocate(pid=pid, size_kb=size, strategy=strat)
            elif "deallocate" in cmd_lower or "free" in cmd_lower:
                pid_match = re.search(r'\b([P|p]\d+)\b', cmd_text)
                if not pid_match:
                    pid_match = re.search(r'(?:deallocate|free)\s+([A-Za-z0-9_]+)', cmd_text, re.IGNORECASE)
                pid = pid_match.group(1).upper() if pid_match and pid_match.group(1).lower() not in ["memory", "deallocate", "free"] else "P1"
                return self.memory_manager.deallocate(pid=pid)
            elif "page" in cmd_lower:
                alg = "FIFO"
                if "lru" in cmd_lower:
                    alg = "LRU"
                elif "optimal" in cmd_lower:
                    alg = "OPTIMAL"
                return self.memory_manager.simulate_page_replacement(algorithm=alg, reference_pages=[7, 0, 1, 2, 0, 3, 0, 4, 2, 3])

        # -------------------------------------------------------------
        # 11. Virtual Disk & Files
        # -------------------------------------------------------------
        if "disk" in cmd_lower or "virtual file" in cmd_lower:
            if "create" in cmd_lower or "write" in cmd_lower or "touch" in cmd_lower:
                path_match = re.search(r'(?:file|path)?\s*(/[a-zA-Z0-9_\-\./]+)', cmd_text)
                path = path_match.group(1) if path_match else "/home/user/newfile.txt"
                size_match = re.search(r'size\s*(\d+)', cmd_lower)
                size = int(size_match.group(1)) if size_match else 2
                return self.disk_manager.create_file(path=path, size_kb=size)
            elif "delete" in cmd_lower or "rm" in cmd_lower:
                path_match = re.search(r'(?:file|path)?\s*(/[a-zA-Z0-9_\-\./]+)', cmd_text)
                path = path_match.group(1) if path_match else ""
                return self.disk_manager.delete_file(path=path)
            elif "schedule" in cmd_lower or "scan" in cmd_lower or "sstf" in cmd_lower or "look" in cmd_lower:
                alg = "C-SCAN"
                if "sstf" in cmd_lower:
                    alg = "SSTF"
                elif "c-look" in cmd_lower or "clook" in cmd_lower:
                    alg = "C-LOOK"
                elif "look" in cmd_lower:
                    alg = "LOOK"
                elif "c-scan" in cmd_lower or "cscan" in cmd_lower:
                    alg = "C-SCAN"
                elif "scan" in cmd_lower:
                    alg = "SCAN"
                elif "fcfs" in cmd_lower:
                    alg = "FCFS"
                res = self.disk_manager.simulate_disk_scheduling(algorithm=alg)
                res["success"] = True
                res["message"] = f"Simulated {alg} Disk Scheduling. Total seek distance: {res.get('total_seek_distance')} cylinders."
                return res

        # -------------------------------------------------------------
        # 12. Resource Request / Release
        # -------------------------------------------------------------
        if "resource" in cmd_lower:
            pid_match = re.search(r'(?:for|proc|process|by)?\s*([P|p]\d+)', cmd_text, re.IGNORECASE)
            pid = pid_match.group(1).upper() if pid_match else "P1"
            
            res_match = re.search(r'(R\d+|[A-C])', cmd_text)
            r_name = res_match.group(1).upper() if res_match else "R1"
            
            amt_match = re.search(r'(\d+)\s*(?:instance|unit)?', cmd_lower)
            amt = int(amt_match.group(1)) if amt_match else 1

            if "release" in cmd_lower or "free" in cmd_lower or "return" in cmd_lower:
                return self.resource_manager.release_resource(pid=pid, resource_name=r_name, amount=amt)
            else:
                return self.resource_manager.request_resource(pid=pid, resource_name=r_name, amount=amt)

        # -------------------------------------------------------------
        # 13. Virtual I/O Requests & Ticking
        # -------------------------------------------------------------
        if "io" in cmd_lower or "i/o" in cmd_lower:
            if "tick" in cmd_lower or "advance" in cmd_lower:
                ticks_match = re.search(r'(\d+)', cmd_lower)
                ticks = int(ticks_match.group(1)) if ticks_match else 1
                return self.io_manager.tick(ticks=ticks)
            else:
                pid_match = re.search(r'([P|p]\d+)', cmd_text, re.IGNORECASE)
                pid = pid_match.group(1).upper() if pid_match else "P1"
                dur_match = re.search(r'(?:duration|ticks|time)?\s*(\d+)', cmd_lower)
                dur = int(dur_match.group(1)) if dur_match else 3
                return self.io_manager.request_io(pid=pid, device="DISK_IO", duration=dur)

        # Fallback explanation
        return {
            "success": False,
            "error": f"Could not match instruction: '{text}'. Try 'dt status', 'dt process create P6', 'dt schedule round robin', 'dt deadlock check', 'dt compare', or 'dt verify'."
        }

# Global engine singleton
digital_twin_engine = DigitalTwinEngine()
