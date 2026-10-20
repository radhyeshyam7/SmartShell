from rich.console import Console
from rich.table import Table
import logging
import os
from datetime import datetime

console = Console()

def setup_logging():
    """Configure logging for the application"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    logging.basicConfig(
        filename=f'logs/smartshell_{datetime.now().strftime("%Y%m%d")}.log',
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

def display_process_table(processes):
    """Display process information in a formatted table"""
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("PID")
    table.add_column("Name")
    table.add_column("Status")
    table.add_column("CPU %")
    table.add_column("Memory %")
    table.add_column("Priority")

    for proc in processes:
        table.add_row(
            str(proc['pid']),
            proc['name'],
            proc['status'],
            f"{proc['cpu_percent']:.1f}",
            f"{proc['memory_percent']:.1f}",
            str(proc['priority'])
        )

    console.print(table)

def format_command_output(output: str, error: str) -> str:
    """Format command output for display"""
    if error:
        return f"[red]Error:[/red]\n{error}"
    return output
