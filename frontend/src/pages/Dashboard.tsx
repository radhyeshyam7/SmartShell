import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { SystemMetrics, DriveItem } from '../types';
import { Cpu, HardDrive, Layers, Activity, Clock, ShieldCheck, ArrowRight, Disc, AlertOctagon } from 'lucide-react';
import { Link } from 'react-router-dom';

export const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [drives, setDrives] = useState<DriveItem[]>([]);
  const [history, setHistory] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [mRes, dRes, hRes] = await Promise.all([
        api.getMetrics().catch(() => null),
        api.getDrives().catch(() => ({ drives: [] })),
        api.getHistory(undefined, undefined, 5).catch(() => []),
      ]);
      setMetrics(mRes);
      setDrives(dRes.drives);
      setHistory(hRes);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-900 to-cyan-950 border border-slate-800 rounded-xl p-6 flex justify-between items-center">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Activity className="text-cyan-400" size={28} />
            SmartShell OS Dashboard
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Real-time operating system metrics, multi-drive monitoring, and interactive OS course simulators.
          </p>
        </div>
        <div className="hidden md:flex gap-3">
          <Link
            to="/cpu-scheduling"
            className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold transition"
          >
            Launch Simulators
          </Link>
        </div>
      </div>

      {/* Metrics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-medium block">CPU Usage</span>
            <span className="text-2xl font-bold text-cyan-400 mt-1 block">
              {metrics ? `${metrics.cpu_percent}%` : '--'}
            </span>
          </div>
          <Cpu className="text-cyan-400/50" size={32} />
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-medium block">RAM Memory</span>
            <span className="text-2xl font-bold text-emerald-400 mt-1 block">
              {metrics ? `${metrics.memory.percent}%` : '--'}
            </span>
          </div>
          <Layers className="text-emerald-400/50" size={32} />
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-medium block">Primary Disk</span>
            <span className="text-2xl font-bold text-amber-400 mt-1 block">
              {metrics ? `${metrics.disk.percent}%` : '--'}
            </span>
          </div>
          <HardDrive className="text-amber-400/50" size={32} />
        </div>

        <div className="bg-slate-900 border border-slate-800 p-4 rounded-xl flex items-center justify-between">
          <div>
            <span className="text-xs text-slate-400 font-medium block">Mounted Drives</span>
            <span className="text-2xl font-bold text-indigo-400 mt-1 block">
              {drives.length} Drives
            </span>
          </div>
          <HardDrive className="text-indigo-400/50" size={32} />
        </div>
      </div>

      {/* Mounted Drives Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-slate-200 font-semibold text-base flex items-center gap-2">
            <HardDrive className="text-cyan-400" size={20} />
            Connected Windows Storage Drives
          </h2>
          <Link to="/files" className="text-xs text-cyan-400 hover:underline flex items-center gap-1">
            Open File Explorer <ArrowRight size={14} />
          </Link>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {drives.map((d, i) => (
            <div key={i} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2">
              <div className="flex items-center justify-between font-bold text-slate-200">
                <span>Drive {d.drive_letter}:</span>
                <span className="text-xs text-slate-400 font-mono">{d.fstype}</span>
              </div>
              <div className="w-full bg-slate-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-cyan-500 h-full rounded-full"
                  style={{ width: `${d.used_percent}%` }}
                />
              </div>
              <div className="flex justify-between text-[11px] text-slate-400">
                <span>{d.used_percent}% used</span>
                <span>{(d.free_bytes / (1024 * 1024 * 1024)).toFixed(1)} GB free</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* OS Simulators Quick Access Grid */}
      <div>
        <h2 className="text-slate-200 font-semibold text-base mb-4 flex items-center gap-2">
          <Layers className="text-cyan-400" size={20} />
          OS Course Academic Simulators
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            to="/cpu-scheduling"
            className="bg-slate-900 border border-slate-800 hover:border-cyan-500/50 p-5 rounded-xl transition space-y-2 group"
          >
            <Cpu className="text-cyan-400 group-hover:scale-110 transition" size={24} />
            <div className="font-bold text-slate-200 text-sm">CPU Scheduling Simulator</div>
            <div className="text-xs text-slate-400">FCFS, SJF, SRTF, Priority, and Round Robin Gantt charts.</div>
          </Link>

          <Link
            to="/memory-management"
            className="bg-slate-900 border border-slate-800 hover:border-cyan-500/50 p-5 rounded-xl transition space-y-2 group"
          >
            <HardDrive className="text-emerald-400 group-hover:scale-110 transition" size={24} />
            <div className="font-bold text-slate-200 text-sm">Memory Management</div>
            <div className="text-xs text-slate-400">Contiguous Allocation (Fit strategies) & Page Replacement (FIFO, LRU).</div>
          </Link>

          <Link
            to="/deadlock-ipc"
            className="bg-slate-900 border border-slate-800 hover:border-cyan-500/50 p-5 rounded-xl transition space-y-2 group"
          >
            <AlertOctagon className="text-amber-400 group-hover:scale-110 transition" size={24} />
            <div className="font-bold text-slate-200 text-sm">Deadlock & Banker's Algorithm</div>
            <div className="text-xs text-slate-400">Resource Allocation Graphs, Safe State checking & Matrix solvers.</div>
          </Link>
        </div>
      </div>
    </div>
  );
};
