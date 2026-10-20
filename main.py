import sys
import time
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
import os
import logging
from typing import Dict, List
from rich.console import Console
from rich.table import Table

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from llm_translate import LLMTranslator
from executor import CommandExecutor
from file_monitor import FileMonitor
from process_manager import ProcessManager
from utils import setup_logging
from config import SHELL_PROMPT

from backend.app.ai.context_manager import context_manager
from backend.app.ai.personalization import personalization_manager
from backend.app.ai.local_rag import local_rag
from backend.app.execution.risk_analyzer import risk_analyzer
from backend.app.execution.anomaly_detector import anomaly_detector
from backend.app.execution.audit_logger import audit_logger
from backend.app.digital_twin.engine import digital_twin_engine

class SmartShell:
    def __init__(self):
        self.console = Console()
        self.session = PromptSession(history=FileHistory('.shell_history'))
        self.llm = LLMTranslator()
        self.executor = CommandExecutor()
        self.process_manager = ProcessManager()
        self.file_monitor = FileMonitor(self.llm)
        
        setup_logging()
        self.file_monitor.start()

    def run(self):
        """Main shell loop"""
        self.console.print("[bold green]Welcome to SmartShell 2.0! (Type commands in plain English)[/bold green]")
        self.console.print("[dim]Type 'exit' to quit. AI Assistant + Multi-Drive Shell + Risk Classifier Active.[/dim]\n")
        
        while True:
            try:
                # Get user input
                raw_input = self.session.prompt(SHELL_PROMPT)
                if not raw_input.strip():
                    continue

                if raw_input.lower() in ['exit', 'quit']:
                    break

                # Resolve Context & Follow-Up References (e.g. 'them', 'that folder', 'undo')
                user_input = context_manager.resolve_follow_up_reference(raw_input)
                
                # Check User Preferences
                prefs = personalization_manager.get_applicable_preferences(user_input)
                if prefs:
                    for p in prefs:
                        self.console.print(f"[dim cyan]Applied User Preference: {p['key']} -> {p['value']}[/dim cyan]")

                # Audit Log: Request Received
                audit_logger.record_event("request_received", {"raw": raw_input, "resolved": user_input})

                # Check if this is a SmartShell OS Digital Twin direct command or NL request
                if self.is_digital_twin_request(user_input):
                    self.handle_digital_twin_cli(user_input)
                    continue

                # Parse user intent
                intent = self.llm.parse_command_intent(user_input)
                if not intent:
                    if getattr(self.llm, 'last_error', None):
                        self.console.print(f"[red]Gemini API Error: {self.llm.last_error}[/red]")
                    else:
                        self.console.print("[red]Could not understand command. Please try rephrasing.[/red]")
                    continue

                # Handle Digital Twin intent recognized by LLM
                if intent.get('type') == 'digital_twin':
                    inst = intent.get('instruction') or user_input
                    self.handle_digital_twin_cli(inst)
                    continue

                # Handle Follow-Up Clarification Questions for ambiguous/underspecified inputs
                if intent.get('type') == 'clarification_needed':
                    question = intent.get('question', 'Which drive or folder would you like to target?')
                    self.console.print(f"\n[bold yellow]Clarification Needed:[/bold yellow] {question}")
                    audit_logger.record_event("clarification_requested", {"question": question})
                    
                    answer = self.console.input("[cyan]Target Drive / Folder (press Enter for system-wide / default): [/cyan]").strip()
                    if answer and answer.lower() not in ['all', 'whole system', 'system wide', 'system-wide', 'default', 'skip', 'everywhere']:
                        user_input = f"{user_input} in {answer}"
                        intent = self.llm.parse_command_intent(user_input)
                        audit_logger.record_event("clarification_answered", {"answer": answer})
                    else:
                        self.console.print("[dim yellow]No specific target specified. Executing system-wide command across all available drives...[/dim yellow]")
                        system_input = f"{user_input} across all drives"
                        cmd = self.llm.translate_command(system_input)
                        if cmd:
                            intent = {"type": "command", "commands": [cmd]}
                        else:
                            intent = self.llm.parse_command_intent(system_input)
                        audit_logger.record_event("clarification_fallback", {"mode": "system_wide"})

                # Handle Academic OS Simulator requests directly
                if intent.get('type') == 'simulator':
                    cat = intent.get('simulator_category', '').lower()
                    alg = intent.get('algorithm', 'ROUND_ROBIN').upper()
                    
                    # ---------------------------------------------------------
                    # Category 1: Banker's Algorithm & Deadlock Simulator
                    # ---------------------------------------------------------
                    if alg in ["BANKERS", "BANKER", "DEADLOCK", "RAG"] or cat == "bankers_algorithm":
                        self.console.print("\n[bold green]📊 Academic OS Deadlock & Banker's Algorithm Simulator[/bold green]")
                        from backend.app.services.simulators import DeadlockSimulator
                        
                        avail_inp = self.console.input("[cyan]Enter Available Resources vector (e.g. 3, 3, 2) [default: 3, 3, 2]: [/cyan]").strip()
                        if avail_inp:
                            try:
                                avail = [int(x.strip()) for x in avail_inp.split(",")]
                            except Exception:
                                avail = [3, 3, 2]
                        else:
                            avail = [3, 3, 2]
                            
                        procs = ["P0", "P1", "P2", "P3", "P4"]
                        res_types = ["A", "B", "C"]
                        max_matrix = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
                        alloc_matrix = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
                        
                        res = DeadlockSimulator.bankers_algorithm(procs, res_types, avail, max_matrix, alloc_matrix)
                        
                        self.console.print("\n[bold cyan]Need Matrix (Max - Allocation):[/bold cyan]")
                        for idx, row in enumerate(res['need_matrix']):
                            self.console.print(f"  - Process {procs[idx]}: Need = {row}")
                            
                        if res['is_safe']:
                            seq_str = " -> ".join(res['safe_sequence'])
                            self.console.print(f"\n[bold green]System State: SAFE ✅[/bold green]")
                            self.console.print(f"[bold green]Safe Execution Sequence:[/bold green] [yellow]{seq_str}[/yellow]\n")
                        else:
                            self.console.print(f"\n[bold red]System State: DEADLOCKED / UNSAFE ❌[/bold red]\n")
                            
                        self.record_history(user_input, "Banker's Algorithm Check", f"Safe: {res['is_safe']}, Seq: {res['safe_sequence']}", "", 0.1)
                        continue

                    # ---------------------------------------------------------
                    # Category 2: Disk Scheduling Simulator (SSTF, SCAN, C-SCAN, LOOK, C-LOOK, FCFS)
                    # ---------------------------------------------------------
                    elif alg in ["SSTF", "SCAN", "C-SCAN", "CSCAN", "LOOK", "C-LOOK", "CLOOK"] or cat == "disk_scheduling":
                        self.console.print(f"\n[bold green]📊 Academic OS Disk Scheduling Simulation ({alg}):[/bold green]")
                        from backend.app.services.simulators import DiskScheduler
                        
                        head_inp = self.console.input("[cyan]Enter Initial Disk Head Position [default: 50]: [/cyan]").strip()
                        head = int(head_inp) if head_inp.isdigit() else 50
                        
                        req_inp = self.console.input("[cyan]Enter Track Requests (comma separated) [default: 98, 183, 37, 122, 14, 124, 65, 67]: [/cyan]").strip()
                        if req_inp:
                            try:
                                track_reqs = [int(x.strip()) for x in req_inp.split(",")]
                            except Exception:
                                track_reqs = [98, 183, 37, 122, 14, 124, 65, 67]
                        else:
                            track_reqs = [98, 183, 37, 122, 14, 124, 65, 67]
                            
                        dir_inp = self.console.input("[cyan]Enter Head Direction (right/left) [default: right]: [/cyan]").strip()
                        direction = dir_inp.lower() if dir_inp.lower() in ["left", "right"] else "right"
                        
                        res = DiskScheduler.simulate(alg, track_reqs, initial_head=head, direction=direction)
                        
                        self.console.print("\n[bold cyan]Disk Head Seek Traversal Sequence:[/bold cyan]")
                        seq_str = " -> ".join(str(x) for x in res['sequence'])
                        self.console.print(f"[yellow]{seq_str}[/yellow]\n")
                        
                        self.console.print(f"[bold green]Total Seek Head Movements:[/bold green] {res['total_seek_distance']} cylinders")
                        self.console.print(f"[bold green]Average Seek Distance:[/bold green] {res['avg_seek_distance']} cylinders/request\n")
                        
                        self.record_history(user_input, f"Simulate {alg} Disk Scheduling", f"Total Seek: {res['total_seek_distance']}", "", 0.1)
                        continue

                    # ---------------------------------------------------------
                    # Category 3: Memory Management & Page Replacement
                    # ---------------------------------------------------------
                    elif alg in ["FIRST_FIT", "BEST_FIT", "WORST_FIT", "FIFO", "LRU", "OPTIMAL"] or cat in ["memory_allocation", "page_replacement"]:
                        from backend.app.services.simulators import MemoryManager
                        
                        if alg in ["FIFO", "LRU", "OPTIMAL"] or cat == "page_replacement":
                            self.console.print(f"\n[bold green]📊 Academic OS Page Replacement Simulation ({alg}):[/bold green]")
                            frames_inp = self.console.input("[cyan]Enter Number of Memory Frames [default: 3]: [/cyan]").strip()
                            num_frames = int(frames_inp) if frames_inp.isdigit() else 3
                            
                            pages_inp = self.console.input("[cyan]Enter Page Reference Sequence (comma separated) [default: 7, 0, 1, 2, 0, 3, 0, 4, 2, 3]: [/cyan]").strip()
                            if pages_inp:
                                try:
                                    pages = [int(x.strip()) for x in pages_inp.split(",")]
                                except Exception:
                                    pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
                            else:
                                pages = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]
                                
                            res = MemoryManager.page_replacement(alg, num_frames, pages)
                            
                            self.console.print(f"\n[bold green]Page Hits:[/bold green] {res['page_hits']} ({res['hit_ratio_percent']}%)")
                            self.console.print(f"[bold red]Page Faults:[/bold red] {res['page_faults']} ({res['fault_ratio_percent']}%)\n")
                            
                            self.record_history(user_input, f"Simulate {alg} Page Replacement", f"Hits: {res['page_hits']}, Faults: {res['page_faults']}", "", 0.1)
                            continue
                        else:
                            self.console.print(f"\n[bold green]📊 Academic OS Contiguous Memory Allocation ({alg}):[/bold green]")
                            blocks_inp = self.console.input("[cyan]Enter Memory Block Sizes in KB (comma separated) [default: 100, 500, 200, 300, 600]: [/cyan]").strip()
                            blocks = [int(x.strip()) for x in blocks_inp.split(",")] if blocks_inp else [100, 500, 200, 300, 600]
                            
                            procs_inp = self.console.input("[cyan]Enter Process Requested Sizes in KB (comma separated) [default: 212, 417, 112, 426]: [/cyan]").strip()
                            sizes = [int(x.strip()) for x in procs_inp.split(",")] if procs_inp else [212, 417, 112, 426]
                            
                            procs = [{"pid": f"P{idx+1}", "size": s} for idx, s in enumerate(sizes)]
                            res = MemoryManager.contiguous_allocation(alg, sum(blocks), blocks, procs)
                            
                            self.console.print("\n[bold cyan]Memory Allocation Results:[/bold cyan]")
                            for a in res['allocations']:
                                status_color = "green" if a['block_id'] is not None else "red"
                                self.console.print(f"  - Process {a['pid']} ({a['size']} KB): [{status_color}]{a['status']}[/{status_color}] (Block ID: {a['block_id']}, Frag: {a['internal_fragmentation']} KB)")
                                
                            m = res['metrics']
                            self.console.print(f"\n[bold yellow]Internal Fragmentation:[/bold yellow] {m['internal_fragmentation_bytes']} KB")
                            self.console.print(f"[bold yellow]External Fragmentation:[/bold yellow] {m['external_fragmentation_bytes']} KB\n")
                            
                            self.record_history(user_input, f"Simulate {alg} Memory Allocation", f"Int Frag: {m['internal_fragmentation_bytes']} KB", "", 0.1)
                            continue

                    # ---------------------------------------------------------
                    # Category 4: CPU Scheduling Simulator (Default Fallback)
                    # ---------------------------------------------------------
                    else:
                        self.console.print(f"\n[bold green]📊 Academic OS CPU Scheduling Simulation ({alg}):[/bold green]")
                        from backend.app.services.simulators import CPUScheduler
                        
                        bt_inp = self.console.input("[cyan]Enter Process Burst Times (comma separated) [default: 5, 3, 8, 6]: [/cyan]").strip()
                        bursts = [int(x.strip()) for x in bt_inp.split(",")] if bt_inp else [5, 3, 8, 6]
                        
                        at_inp = self.console.input("[cyan]Enter Process Arrival Times (comma separated) [default: 0, 1, 2, 3]: [/cyan]").strip()
                        arrivals = [int(x.strip()) for x in at_inp.split(",")] if at_inp else [0, 1, 2, 3]
                        
                        tq = 2
                        if alg in ["ROUND_ROBIN", "RR"]:
                            tq_inp = self.console.input("[cyan]Enter Time Quantum (integer) [default: 2]: [/cyan]").strip()
                            tq = int(tq_inp) if tq_inp.isdigit() else 2
                            
                        procs = [{"pid": f"P{i+1}", "arrival_time": arrivals[i] if i < len(arrivals) else 0, "burst_time": bursts[i], "priority": i+1} for i in range(len(bursts))]
                        
                        res = CPUScheduler.simulate(alg, procs, time_quantum=tq)
                        
                        self.console.print("\n[bold cyan]Gantt Chart Execution Timeline:[/bold cyan]")
                        gantt_str = " | ".join([f"{g['pid']} ({g['start_time']} -> {g['end_time']})" for g in res['gantt_chart']])
                        self.console.print(f"[yellow]| {gantt_str} |[/yellow]\n")
                        
                        self.console.print("[bold cyan]Process Metrics Summary:[/bold cyan]")
                        for p in res['processes']:
                            self.console.print(f"  - Process {p['pid']}: Arrival={p['arrival_time']}, Burst={p['burst_time']} -> Completion={p['completion_time']}, TAT={p['turnaround_time']}, WT={p['waiting_time']}")
                        
                        m = res['metrics']
                        self.console.print(f"\n[bold green]Average Turnaround Time:[/bold green] {m['avg_turnaround_time']} ms")
                        self.console.print(f"[bold green]Average Waiting Time:[/bold green] {m['avg_waiting_time']} ms")
                        self.console.print(f"[bold green]CPU Utilization:[/bold green] {m['cpu_utilization_percent']}%\n")
                        
                        self.record_history(user_input, f"Simulate {alg} CPU Scheduling", f"Avg TAT: {m['avg_turnaround_time']} ms, Avg WT: {m['avg_waiting_time']} ms", "", 0.1)
                        continue

                # Display understood command details
                self.console.print(f"\n[blue]Understood command:[/blue]")
                self.console.print(f"Type: {intent.get('type', 'unknown')}")
                
                # Generate and display commands
                commands = self.llm.generate_command_sequence(intent, user_input)
                if not commands:
                    self.console.print("[red]Could not generate commands for this request.[/red]")
                    continue

                # Assess Risk Level for generated commands
                max_risk = "low"
                self.console.print(f"\n[yellow]Will execute:[/yellow]")
                for cmd in commands:
                    risk_level, req_approval, reason = risk_analyzer.analyze_command(cmd)
                    risk_color = "green" if risk_level == "low" else "yellow" if risk_level == "medium" else "orange3" if risk_level == "high" else "red"
                    self.console.print(f"  - {cmd} [{risk_color}][Risk: {risk_level.upper()}][/{risk_color}] ({reason})")
                    if risk_level in ["high", "critical"]:
                        max_risk = risk_level

                # Execute after confirmation
                prompt_msg = "\nProceed? (y/n): " if max_risk != "critical" else "\n[bold red]CRITICAL ACTION REQUIRED. Confirm execution? (y/n): [/bold red]"
                if self.console.input(prompt_msg).lower().startswith('y'):
                    audit_logger.record_event("user_approved", {"commands": commands, "risk": max_risk})
                    
                    for cmd in commands:
                        try:
                            start_t = time.time()
                            pid, output, error = self.executor.execute_command(cmd)
                            duration = round(time.time() - start_t, 2)

                            status = "completed" if not error else "failed"
                            exit_code = 0 if not error else 1

                            # Monitor for behavioral anomalies
                            anomaly_detector.record_event(cmd, status, exit_code, max_risk)
                            anom_status = anomaly_detector.analyze_behavior()
                            if anom_status.get("anomaly_detected"):
                                self.console.print(f"\n[bold red]⚠️ Security Alert:[/bold red] {anom_status['reasons'][0]}")

                            if output and output.strip():
                                self.console.print(output.strip())
                            elif not error:
                                self.console.print("[dim text-yellow-400]No matching files/items found (output was empty).[/dim text-yellow-400]")
                            
                            if error and error.strip():
                                self.console.print(f"[red]Error:[/red] {error.strip()}")
                                # Local RAG Technical Troubleshooting Citation Grounding
                                exp, citations = local_rag.get_grounded_answer(error)
                                if citations:
                                    self.console.print(f"\n[cyan]📖 Grounded Diagnosis ({citations[0]}):[/cyan]")
                                    self.console.print(f"[dim]{exp[:300]}...[/dim]")

                            # Update Context Manager
                            context_manager.add_turn(
                                prompt=raw_input,
                                summary=output[:100] if output else (error[:100] if error else "Success"),
                                command=cmd
                            )

                            # Record CLI command history to DB / API for frontend sync
                            self.record_history(user_input, cmd, output, error, duration)
                            audit_logger.record_event("command_executed", {"command": cmd, "exit_code": exit_code, "duration": duration})

                        except Exception as e:
                            self.console.print(f"[red]Error executing command:[/red] {str(e)}")
                            audit_logger.record_event("execution_error", {"command": cmd, "error": str(e)})

            except Exception as e:
                logging.error(f"Error: {str(e)}")
                self.console.print(f"[red]Error:[/red] {str(e)}")

    def is_digital_twin_request(self, text: str) -> bool:
        """Determines if the request is targeted at the SmartShell OS Digital Twin."""
        low = text.lower().strip()
        if low.startswith(('dt ', 'dt', 'digital-twin', 'digital_twin')):
            return True
        keywords = [
            'digital twin', 'virtual os', 'virtual process', 'virtual memory',
            'virtual disk', 'virtual file', 'compare scheduling', 'banker safe',
            'verify invariants', 'os invariants'
        ]
        return any(k in low for k in keywords)

    def handle_digital_twin_cli(self, text: str):
        """Processes, executes, and renders SmartShell OS Digital Twin commands with rich visual UI."""
        start_t = time.time()
        res = digital_twin_engine.execute_command_or_nl(text)
        duration = round(time.time() - start_t, 2)

        action = res.get("action")
        if not res.get("success"):
            self.console.print(f"[bold red]Digital Twin Error:[/bold red] {res.get('error', 'Execution failed.')}\n")
            self.record_history(text, "Digital Twin Error", "", res.get('error', ''), duration)
            return

        # 1. State / Status Overview
        if action == "status":
            self.console.print(f"\n[bold green]🌐 SmartShell OS Digital Twin Status (Tick: {res['tick']})[/bold green]")
            self.console.print(f"[cyan]Memory Used:[/cyan] {res['memory_used_kb']} / {res['memory_total_kb']} KB | [cyan]Files:[/cyan] {res['virtual_files_count']} | [cyan]Active Running PID:[/cyan] {res['running_pid'] or 'None (CPU Idle)'}")

            st = digital_twin_engine.get_full_state()
            p_table = Table(title="Virtual Process Table (PCB)", title_style="bold cyan")
            p_table.add_column("PID", style="bold yellow")
            p_table.add_column("Name", style="white")
            p_table.add_column("State", style="bold")
            p_table.add_column("Burst", justify="right")
            p_table.add_column("Memory (KB)", justify="right")
            p_table.add_column("Priority", justify="right")
            p_table.add_column("Allocated Resources", style="cyan")

            for pid, p in st["processes"].items():
                state_color = "green" if p["state"] == "READY" else "yellow" if p["state"] == "RUNNING" else "magenta" if p["state"] == "WAITING" else "red"
                res_str = ", ".join([f"{k}:{v}" for k, v in p["allocated_resources"].items() if v > 0]) or "None"
                p_table.add_row(
                    p["pid"],
                    p["name"],
                    f"[{state_color}]{p['state']}[/{state_color}]",
                    str(p["burst_time"]),
                    str(p["memory_required"]),
                    str(p["priority"]),
                    res_str
                )
            self.console.print(p_table)

            m_table = Table(title="Virtual Physical Memory Partitions", title_style="bold cyan")
            m_table.add_column("Block ID", justify="center")
            m_table.add_column("Start Addr", justify="right")
            m_table.add_column("Size (KB)", justify="right")
            m_table.add_column("Status", justify="center")
            m_table.add_column("Allocated PID", justify="center")
            m_table.add_column("Internal Frag (KB)", justify="right")

            for b in st["memory_blocks"]:
                status_str = "[bold green]ALLOCATED[/bold green]" if b["is_allocated"] else "[bold blue]FREE[/bold blue]"
                m_table.add_row(
                    str(b["block_id"]),
                    str(b["start_address"]),
                    str(b["size"]),
                    status_str,
                    b["allocated_pid"] or "-",
                    str(b["internal_fragmentation"])
                )
            self.console.print(m_table)

            inv_color = "green" if res["invariants_valid"] else "red"
            self.console.print(f"[bold {inv_color}]State Invariant Status: {'VALID ✅ (0 violations)' if res['invariants_valid'] else 'VIOLATIONS DETECTED ❌'}[/bold {inv_color}]\n")

        # 2. Scheduling Result
        elif "gantt_chart" in res:
            self.console.print(f"\n[bold green]📊 Digital Twin CPU Scheduling Result ({res.get('algorithm', '')}):[/bold green]")
            gantt_str = " | ".join([f"{g['pid']} ({g['start_time']} -> {g['end_time']})" for g in res['gantt_chart']])
            self.console.print(f"[yellow]| {gantt_str} |[/yellow]\n")

            m = res.get("metrics", {})
            self.console.print(f"[bold green]Average Turnaround Time:[/bold green] {m.get('avg_turnaround_time', 0)} ms")
            self.console.print(f"[bold green]Average Waiting Time:[/bold green] {m.get('avg_waiting_time', 0)} ms")
            self.console.print(f"[bold green]CPU Utilization:[/bold green] {m.get('cpu_utilization_percent', 0)}%\n")

        # 3. Deadlock Result
        elif action == "deadlock_check":
            self.console.print("\n[bold green]🛡️ Digital Twin Deadlock & Safety Analysis:[/bold green]")
            if res.get("is_safe"):
                seq_str = " -> ".join(res.get("safe_sequence", []))
                self.console.print(f"[bold green]Banker's Algorithm State: SAFE ✅[/bold green]")
                self.console.print(f"[bold green]Safe Execution Sequence:[/bold green] [yellow]{seq_str}[/yellow]")
            else:
                self.console.print("[bold red]Banker's Algorithm State: DEADLOCKED / UNSAFE ❌[/bold red]")

            if res.get("has_deadlock_cycle"):
                self.console.print(f"[bold red]RAG Cycle Detected ⚠️ Deadlocked Processes:[/bold red] {res.get('deadlocked_processes', [])}\n")
            else:
                self.console.print("[bold green]Resource Allocation Graph: NO CYCLES (Clean) ✅[/bold green]\n")

        # 4. Algorithm Comparison
        elif "comparisons" in res:
            self.console.print(f"\n[bold green]📈 Side-by-Side Scheduling Algorithm Benchmark ({res.get('workload_process_count', 0)} Processes):[/bold green]")
            cmp_table = Table(title="Algorithm Comparison Matrix", title_style="bold cyan")
            cmp_table.add_column("Algorithm", style="bold yellow")
            cmp_table.add_column("Avg Turnaround Time", justify="right")
            cmp_table.add_column("Avg Waiting Time", justify="right")
            cmp_table.add_column("CPU Utilization", justify="right")

            for c in res["comparisons"]:
                cmp_table.add_row(
                    c["algorithm"],
                    f"{c.get('avg_turnaround_time', 0)} ms",
                    f"{c.get('avg_waiting_time', 0)} ms",
                    f"{c.get('cpu_utilization_percent', 0)}%"
                )
            self.console.print(cmp_table)
            self.console.print(f"[bold green]💡 AI Recommendation:[/bold green] {res.get('recommendation', '')}\n")

        # 5. Invariant Verification
        elif action == "verify":
            self.console.print("\n[bold green]🔍 Digital Twin Invariant Verification Report:[/bold green]")
            self.console.print(f"Total Invariant Rules Checked: [bold]{res.get('checks_run', 0)}[/bold]")
            if res.get("is_valid"):
                self.console.print("[bold green]Result: ALL INVARIANTS SATISFIED ✅ (Memory bounds, process states, resources balanced)[/bold green]\n")
            else:
                self.console.print(f"[bold red]Result: {len(res.get('violations', []))} VIOLATION(S) DETECTED ❌[/bold red]")
                for v in res.get("violations", []):
                    self.console.print(f"  - [red]{v}[/red]")
                self.console.print()

        # 6. General / Process / Memory / Disk / Snapshot Success
        else:
            self.console.print(f"\n[bold green]✅ Digital Twin Action Completed:[/bold green] {res.get('message', 'Success')}\n")

        self.record_history(text, f"Digital Twin {action or 'Action'}", res.get('message', 'Completed'), "", duration)

    def record_history(self, user_prompt: str, cmd: str, output: str, error: str, duration: float):
        """Record CLI executions to history DB/API for real-time frontend sync"""
        try:
            import requests
            requests.post("http://127.0.0.1:8000/api/history", json={
                "user_prompt": user_prompt,
                "command": cmd,
                "task_name": "CLI Execution",
                "working_directory": os.getcwd(),
                "risk_level": "low",
                "status": "completed" if not error else "failed",
                "exit_code": 0 if not error else 1,
                "stdout": output or "",
                "stderr": error or "",
                "duration_seconds": duration
            }, timeout=1)
        except Exception:
            try:
                import uuid
                from datetime import datetime
                from backend.app.database.database import get_db
                from backend.app.database.models import CommandHistoryModel
                db = next(get_db())
                record = CommandHistoryModel(
                    id=f"cmd-{uuid.uuid4().hex[:8]}",
                    user_prompt=user_prompt,
                    command=cmd,
                    task_name="CLI Execution",
                    working_directory=os.getcwd(),
                    risk_level="low",
                    status="completed" if not error else "failed",
                    exit_code=0 if not error else 1,
                    stdout=output or "",
                    stderr=error or "",
                    duration_seconds=duration,
                    created_at=datetime.utcnow()
                )
                db.add(record)
                db.commit()
            except Exception:
                pass

    def cleanup(self):
        """Cleanup resources"""
        self.file_monitor.stop()

if __name__ == "__main__":
    shell = SmartShell()
    try:
        shell.run()
    finally:
        shell.cleanup()
