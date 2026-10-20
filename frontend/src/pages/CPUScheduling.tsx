import React, { useState } from 'react';
import { api } from '../services/api';
import { ProcessInput, CPUSchedulerResult } from '../types';
import { Cpu, Play, Plus, Trash2, Clock, CheckCircle, BarChart2 } from 'lucide-react';

export const CPUScheduling: React.FC = () => {
  const [algorithm, setAlgorithm] = useState<string>('FCFS');
  const [timeQuantum, setTimeQuantum] = useState<number>(2);
  const [isPreemptive, setIsPreemptive] = useState<boolean>(false);
  const [processes, setProcesses] = useState<ProcessInput[]>([
    { pid: 'P1', arrival_time: 0, burst_time: 5, priority: 1 },
    { pid: 'P2', arrival_time: 1, burst_time: 3, priority: 2 },
    { pid: 'P3', arrival_time: 2, burst_time: 8, priority: 1 },
    { pid: 'P4', arrival_time: 3, burst_time: 6, priority: 3 },
  ]);
  const [result, setResult] = useState<CPUSchedulerResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleAddProcess = () => {
    const nextNum = processes.length + 1;
    setProcesses([
      ...processes,
      { pid: `P${nextNum}`, arrival_time: 0, burst_time: 4, priority: 1 },
    ]);
  };

  const handleRemoveProcess = (index: number) => {
    setProcesses(processes.filter((_, i) => i !== index));
  };

  const handleProcessChange = (index: number, field: keyof ProcessInput, value: any) => {
    const updated = [...processes];
    updated[index] = { ...updated[index], [field]: value };
    setProcesses(updated);
  };

  const handleRunSimulation = async () => {
    if (processes.length === 0) {
      setError('Please add at least one process.');
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const res = await api.simulateCPUScheduling({
        algorithm,
        processes,
        time_quantum: timeQuantum,
        is_preemptive: isPreemptive,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Simulation failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Cpu className="text-cyan-400" size={28} />
            CPU Scheduling Simulator
          </h1>
          <p className="text-slate-400 text-sm">
            Simulate FCFS, SJF, SRTF, Priority, and Round Robin scheduling algorithms with Gantt charts.
          </p>
        </div>
        <button
          onClick={handleRunSimulation}
          disabled={loading}
          className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg shadow-lg flex items-center gap-2 transition disabled:opacity-50"
        >
          <Play size={18} />
          {loading ? 'Simulating...' : 'Run Simulation'}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/50 border border-rose-500/50 rounded-lg text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Algorithm Config */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Algorithm</label>
          <select
            value={algorithm}
            onChange={(e) => setAlgorithm(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
          >
            <option value="FCFS">First Come First Served (FCFS)</option>
            <option value="SJF">Shortest Job First (SJF - Non-Preemptive)</option>
            <option value="SRTF">Shortest Remaining Time First (SRTF - Preemptive)</option>
            <option value="PRIORITY">Priority Scheduling</option>
            <option value="ROUND_ROBIN">Round Robin (RR)</option>
          </select>
        </div>

        {algorithm === 'ROUND_ROBIN' && (
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Time Quantum</label>
            <input
              type="number"
              min="1"
              value={timeQuantum}
              onChange={(e) => setTimeQuantum(parseInt(e.target.value) || 1)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm focus:outline-none focus:border-cyan-500"
            />
          </div>
        )}

        {algorithm === 'PRIORITY' && (
          <div className="flex items-center pt-6">
            <label className="flex items-center gap-2 text-sm text-slate-300 cursor-pointer">
              <input
                type="checkbox"
                checked={isPreemptive}
                onChange={(e) => setIsPreemptive(e.target.checked)}
                className="rounded border-slate-700 text-cyan-600 focus:ring-cyan-500"
              />
              Preemptive Mode
            </label>
          </div>
        )}
      </div>

      {/* Process Table Input */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5">
        <div className="flex items-center justify-between border-b border-slate-800 pb-3 mb-4">
          <h2 className="text-slate-200 font-semibold text-base flex items-center gap-2">
            <Clock size={18} className="text-cyan-400" />
            Process Queue Configuration
          </h2>
          <button
            onClick={handleAddProcess}
            className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium flex items-center gap-1 transition"
          >
            <Plus size={14} /> Add Process
          </button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-slate-400 uppercase text-xs">
              <tr>
                <th className="px-4 py-2">Process ID</th>
                <th className="px-4 py-2">Arrival Time</th>
                <th className="px-4 py-2">Burst Time</th>
                <th className="px-4 py-2">Priority (Lower = Higher)</th>
                <th className="px-4 py-2 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {processes.map((proc, idx) => (
                <tr key={idx} className="hover:bg-slate-850/50">
                  <td className="px-4 py-2 font-mono text-cyan-400">{proc.pid}</td>
                  <td className="px-4 py-2">
                    <input
                      type="number"
                      min="0"
                      value={proc.arrival_time}
                      onChange={(e) => handleProcessChange(idx, 'arrival_time', parseInt(e.target.value) || 0)}
                      className="w-24 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <input
                      type="number"
                      min="1"
                      value={proc.burst_time}
                      onChange={(e) => handleProcessChange(idx, 'burst_time', parseInt(e.target.value) || 1)}
                      className="w-24 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs"
                    />
                  </td>
                  <td className="px-4 py-2">
                    <input
                      type="number"
                      min="0"
                      value={proc.priority || 0}
                      onChange={(e) => handleProcessChange(idx, 'priority', parseInt(e.target.value) || 0)}
                      className="w-24 bg-slate-950 border border-slate-700 rounded px-2 py-1 text-slate-200 text-xs"
                    />
                  </td>
                  <td className="px-4 py-2 text-right">
                    <button
                      onClick={() => handleRemoveProcess(idx)}
                      className="text-slate-400 hover:text-rose-400 p-1"
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

      {/* Gantt Chart & Performance Results */}
      {result && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-6">
          <div>
            <h2 className="text-slate-200 font-semibold text-base mb-3 flex items-center gap-2">
              <BarChart2 className="text-cyan-400" size={18} />
              Gantt Chart Timeline
            </h2>
            <div className="flex overflow-x-auto p-3 bg-slate-950 rounded-xl border border-slate-800 gap-1">
              {result.gantt_chart.map((g, i) => (
                <div key={i} className="flex flex-col items-center min-w-[70px] flex-1">
                  <div
                    className={`w-full h-12 rounded-lg flex items-center justify-center font-bold text-xs shadow ${
                      g.pid === 'IDLE' ? 'bg-slate-800 text-slate-500' : 'bg-cyan-600 text-white'
                    }`}
                  >
                    {g.pid}
                  </div>
                  <div className="flex justify-between w-full text-[10px] text-slate-400 mt-1 font-mono">
                    <span>{g.start_time}</span>
                    <span>{g.end_time}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Performance Metrics Table */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block">Avg Turnaround Time</span>
              <span className="text-xl font-bold text-cyan-400">{result.metrics.avg_turnaround_time} ms</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block">Avg Waiting Time</span>
              <span className="text-xl font-bold text-emerald-400">{result.metrics.avg_waiting_time} ms</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block">Avg Response Time</span>
              <span className="text-xl font-bold text-amber-400">{result.metrics.avg_response_time} ms</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block">CPU Utilization</span>
              <span className="text-xl font-bold text-indigo-400">{result.metrics.cpu_utilization_percent}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
