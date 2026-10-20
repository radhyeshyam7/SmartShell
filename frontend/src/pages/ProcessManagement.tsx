import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { ProcessItem } from '../types';
import { Activity, RefreshCw, Trash2, Search, AlertTriangle } from 'lucide-react';

export const ProcessManagement: React.FC = () => {
  const [processes, setProcesses] = useState<ProcessItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProcesses();
    const interval = setInterval(fetchProcesses, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchProcesses = async () => {
    try {
      const procs = await api.getProcesses(100);
      setProcesses(procs);
    } catch (err: any) {
      setError('Failed to refresh system processes.');
    } finally {
      setLoading(false);
    }
  };

  const handleTerminate = async (pid: number, name: string) => {
    if (!window.confirm(`Are you sure you want to terminate process ${name} (PID: ${pid})?`)) return;
    try {
      await api.terminateProcess(pid);
      fetchProcesses();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to terminate process');
    }
  };

  const filtered = processes.filter(
    (p) => p.name.toLowerCase().includes(search.toLowerCase()) || p.pid.toString().includes(search)
  );

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Activity className="text-cyan-400" size={28} />
            OS Process Management
          </h1>
          <p className="text-slate-400 text-sm">
            Inspect running processes, monitor CPU and memory consumption, and safely terminate eligible processes.
          </p>
        </div>
        <button
          onClick={fetchProcesses}
          disabled={loading}
          className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-sm flex items-center gap-2 transition"
        >
          <RefreshCw className={loading ? 'animate-spin' : ''} size={16} /> Refresh
        </button>
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex items-center gap-4">
        <Search className="text-slate-500" size={18} />
        <input
          type="text"
          placeholder="Filter by process name or PID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="bg-transparent text-slate-200 text-sm focus:outline-none w-full"
        />
      </div>

      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950 text-slate-400 uppercase text-xs">
            <tr>
              <th className="px-4 py-3">PID</th>
              <th className="px-4 py-3">Process Name</th>
              <th className="px-4 py-3">CPU Usage</th>
              <th className="px-4 py-3">Memory (MB)</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3 text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {filtered.map((proc) => (
              <tr key={proc.pid} className="hover:bg-slate-850/50">
                <td className="px-4 py-2.5 font-mono text-cyan-400">{proc.pid}</td>
                <td className="px-4 py-2.5 font-semibold text-slate-200">{proc.name}</td>
                <td className="px-4 py-2.5 font-mono text-xs text-slate-300">{proc.cpu_percent}%</td>
                <td className="px-4 py-2.5 font-mono text-xs text-slate-300">{proc.memory_mb.toFixed(1)} MB</td>
                <td className="px-4 py-2.5 text-xs">
                  <span className="px-2 py-0.5 rounded bg-slate-950 text-emerald-400 border border-slate-800 uppercase font-bold text-[10px]">
                    {proc.status}
                  </span>
                </td>
                <td className="px-4 py-2.5 text-right">
                  <button
                    onClick={() => handleTerminate(proc.pid, proc.name)}
                    className="text-slate-400 hover:text-rose-400 p-1"
                    title="Terminate Process"
                  >
                    <Trash2 size={16} />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
