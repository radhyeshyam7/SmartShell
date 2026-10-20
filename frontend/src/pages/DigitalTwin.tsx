import React, { useState, useEffect } from 'react';
import { 
  Sparkles, Activity, Cpu, HardDrive, Disc, AlertOctagon, RefreshCw, 
  Play, Plus, Trash2, ShieldCheck, ShieldAlert, ArrowRight, Save, Clock
} from 'lucide-react';
import { api } from '../services/api';

export const DigitalTwin: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'overview' | 'scheduler' | 'memory' | 'disk' | 'deadlock' | 'what-if'>('overview');
  const [state, setState] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [promptInput, setPromptInput] = useState<string>('');
  const [promptLoading, setPromptLoading] = useState<boolean>(false);
  const [actionMessage, setActionMessage] = useState<string>('');
  
  // Modals & form states
  const [newProc, setNewProc] = useState({ pid: 'P6', name: 'worker_task', burst: 5, mem: 150, priority: 2 });
  const [schedForm, setSchedForm] = useState({ algorithm: 'ROUND_ROBIN', quantum: 2 });
  const [memForm, setMemForm] = useState({ pid: 'P1', size: 100, strategy: 'FIRST_FIT' });
  const [resForm, setResForm] = useState({ pid: 'P1', resource: 'R1', amount: 1 });
  const [fileForm, setFileForm] = useState({ path: '/home/user/test.txt', size: 4, content: 'Virtual file data' });
  const [deadlockData, setDeadlockData] = useState<any>(null);
  const [compareData, setCompareData] = useState<any>(null);
  const [invariantReport, setInvariantReport] = useState<any>(null);
  const [snapshots, setSnapshots] = useState<any[]>([]);

  const fetchState = async () => {
    try {
      setLoading(true);
      const data = await api.getDigitalTwinState();
      setState(data);
      const inv = await api.verifyDigitalTwinInvariants();
      setInvariantReport(inv);
      const snaps = await api.listDigitalTwinSnapshots();
      setSnapshots(snaps);
    } catch (err: any) {
      console.error("Failed to load digital twin state", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchState();
  }, []);

  const handleReset = async () => {
    if (!window.confirm("Reset Digital Twin back to default baseline state?")) return;
    try {
      await api.resetDigitalTwin();
      setActionMessage("SmartShell OS Digital Twin reset to initial baseline.");
      await fetchState();
    } catch (err: any) {
      alert("Reset failed: " + err.message);
    }
  };

  const handlePromptSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!promptInput.trim()) return;
    try {
      setPromptLoading(true);
      const res = await api.executeDigitalTwin(promptInput);
      setActionMessage(res.message || "Instruction executed.");
      setPromptInput('');
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message || "Failed to execute instruction");
    } finally {
      setPromptLoading(false);
    }
  };

  const handleCreateProcess = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.createDigitalTwinProcess({
        pid: newProc.pid,
        name: newProc.name,
        burst_time: Number(newProc.burst),
        memory_required: Number(newProc.mem),
        priority: Number(newProc.priority)
      });
      setActionMessage(res.message);
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const handleTerminateProcess = async (pid: string) => {
    try {
      const res = await api.terminateDigitalTwinProcess(pid);
      setActionMessage(res.message);
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const handleRunScheduler = async () => {
    try {
      const res = await api.runDigitalTwinScheduler({
        algorithm: schedForm.algorithm,
        time_quantum: Number(schedForm.quantum)
      });
      setActionMessage(res.message);
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const handleAllocateMemory = async () => {
    try {
      const res = await api.allocateDigitalTwinMemory({
        pid: memForm.pid,
        size_kb: Number(memForm.size),
        strategy: memForm.strategy
      });
      setActionMessage(res.message);
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const handleCheckDeadlock = async () => {
    try {
      const res = await api.checkDigitalTwinDeadlock();
      setDeadlockData(res);
      setActionMessage("Deadlock safety evaluation completed.");
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const handleResourceRequest = async (isRelease: boolean) => {
    try {
      const payload = {
        pid: resForm.pid,
        resource_name: resForm.resource,
        amount: Number(resForm.amount)
      };
      const res = isRelease
        ? await api.releaseDigitalTwinResource(payload)
        : await api.requestDigitalTwinResource(payload);
      setActionMessage(res.message);
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const handleCreateFile = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await api.createDigitalTwinFile({
        path: fileForm.path,
        size_kb: Number(fileForm.size),
        content: fileForm.content
      });
      setActionMessage(res.message);
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const handleDeleteFile = async (path: string) => {
    try {
      const res = await api.deleteDigitalTwinFile(path);
      setActionMessage(res.message);
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const handleRunComparison = async () => {
    try {
      const res = await api.compareDigitalTwinAlgorithms({
        algorithms: ['FCFS', 'SJF', 'ROUND_ROBIN', 'PRIORITY'],
        time_quantum: 2
      });
      setCompareData(res);
      setActionMessage(res.recommendation);
      await fetchState();
    } catch (err: any) {
      alert(err.response?.data?.detail || err.message);
    }
  };

  const handleCreateSnapshot = async () => {
    const label = prompt("Enter snapshot label:", `Checkpoint at tick ${state?.tick || 0}`);
    if (!label) return;
    try {
      const res = await api.createDigitalTwinSnapshot(label);
      setActionMessage(`Snapshot created: ${res.snapshot_id}`);
      await fetchState();
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleRestoreSnapshot = async (id: string) => {
    if (!window.confirm(`Restore state to snapshot '${id}'?`)) return;
    try {
      const res = await api.restoreDigitalTwinSnapshot(id);
      setActionMessage(res.message);
      await fetchState();
    } catch (err: any) {
      alert(err.message);
    }
  };

  if (loading && !state) {
    return (
      <div className="flex h-96 items-center justify-center">
        <RefreshCw className="w-8 h-8 text-cyan-400 animate-spin" />
        <span className="ml-3 text-slate-300 font-medium">Synchronizing SmartShell OS Digital Twin...</span>
      </div>
    );
  }

  const processes = state ? Object.values(state.processes) : [];
  const metrics = state?.metrics || {};

  return (
    <div className="space-y-6">
      {/* Top Header & Digital Twin Info */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 shadow-xl relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-4">
            <div className="p-3 bg-gradient-to-tr from-cyan-600 to-indigo-600 rounded-xl shadow-lg shadow-cyan-500/20">
              <Sparkles className="w-7 h-7 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-3">
                <h1 className="text-2xl font-bold text-white tracking-wide">SmartShell OS Digital Twin</h1>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                  Logical Clock: Tick {state?.tick || 0}
                </span>
                {invariantReport && (
                  <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold flex items-center space-x-1 ${
                    invariantReport.is_valid 
                      ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' 
                      : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
                  }`}>
                    {invariantReport.is_valid ? <ShieldCheck className="w-3.5 h-3.5 inline mr-1" /> : <ShieldAlert className="w-3.5 h-3.5 inline mr-1" />}
                    {invariantReport.is_valid ? 'Invariants Valid' : `${invariantReport.violations.length} Violation(s)`}
                  </span>
                )}
              </div>
              <p className="text-slate-400 text-xs mt-1">
                Unified virtual operating-system simulation environment with shared process, memory, disk, and deadlock states.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={handleCreateSnapshot}
              className="flex items-center space-x-2 px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 transition"
            >
              <Save className="w-4 h-4 text-cyan-400" />
              <span>Snapshot</span>
            </button>
            <button
              onClick={handleReset}
              className="flex items-center space-x-2 px-3 py-2 bg-rose-950/40 hover:bg-rose-900/50 text-rose-300 rounded-lg text-xs font-medium border border-rose-800/40 transition"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reset State</span>
            </button>
            <button
              onClick={fetchState}
              className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs border border-slate-700 transition"
              title="Refresh State"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Quick Command Prompt */}
        <form onSubmit={handlePromptSubmit} className="mt-5 flex gap-2">
          <input
            type="text"
            value={promptInput}
            onChange={(e) => setPromptInput(e.target.value)}
            placeholder="Type Digital Twin command or NL (e.g. 'dt schedule round robin quantum 2', 'create virtual process P6', 'check deadlock')..."
            className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500 font-mono"
          />
          <button
            type="submit"
            disabled={promptLoading}
            className="px-5 py-2.5 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition shadow-lg shadow-cyan-600/20 disabled:opacity-50"
          >
            {promptLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4 fill-white" />}
            <span>Execute</span>
          </button>
        </form>

        {actionMessage && (
          <div className="mt-3 p-2.5 bg-cyan-950/30 border border-cyan-800/40 rounded-lg text-xs text-cyan-300 font-mono">
            {actionMessage}
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-slate-800 space-x-2 overflow-x-auto pb-1">
        {[
          { id: 'overview', label: 'Process Table & State', icon: Activity },
          { id: 'scheduler', label: 'CPU Scheduler & Gantt', icon: Cpu },
          { id: 'memory', label: 'Virtual Memory (RAM)', icon: HardDrive },
          { id: 'disk', label: 'Virtual Disk & Files', icon: Disc },
          { id: 'deadlock', label: 'Deadlock & Banker RAG', icon: AlertOctagon },
          { id: 'what-if', label: 'What-If & Benchmarking', icon: Clock },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2.5 rounded-t-lg text-xs font-medium transition ${
                isActive
                  ? 'bg-slate-800 text-cyan-400 border-b-2 border-cyan-400 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/40'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview & Process Table */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-sm font-semibold text-white flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-cyan-400" />
                  <span>Virtual Process Table (PCB)</span>
                </h3>
                <span className="text-xs text-slate-400 font-mono">{processes.length} Processes</span>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full text-left text-xs">
                  <thead className="bg-slate-950 text-slate-400 font-mono border-b border-slate-800">
                    <tr>
                      <th className="py-2.5 px-3">PID</th>
                      <th className="py-2.5 px-3">Name</th>
                      <th className="py-2.5 px-3">State</th>
                      <th className="py-2.5 px-3">Burst</th>
                      <th className="py-2.5 px-3">Priority</th>
                      <th className="py-2.5 px-3">Memory</th>
                      <th className="py-2.5 px-3">Resources</th>
                      <th className="py-2.5 px-3 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60 font-mono text-slate-300">
                    {processes.map((p: any) => {
                      const stateColor = 
                        p.state === 'READY' ? 'text-emerald-400 bg-emerald-500/10 border-emerald-500/20' :
                        p.state === 'RUNNING' ? 'text-amber-400 bg-amber-500/10 border-amber-500/20' :
                        p.state === 'WAITING' ? 'text-purple-400 bg-purple-500/10 border-purple-500/20' :
                        'text-rose-400 bg-rose-500/10 border-rose-500/20';
                      return (
                        <tr key={p.pid} className="hover:bg-slate-800/30 transition">
                          <td className="py-2.5 px-3 font-bold text-cyan-300">{p.pid}</td>
                          <td className="py-2.5 px-3 text-slate-200">{p.name}</td>
                          <td className="py-2.5 px-3">
                            <span className={`px-2 py-0.5 rounded border text-[10px] font-semibold ${stateColor}`}>
                              {p.state}
                            </span>
                          </td>
                          <td className="py-2.5 px-3">{p.remaining_burst}/{p.burst_time}</td>
                          <td className="py-2.5 px-3">{p.priority}</td>
                          <td className="py-2.5 px-3">{p.memory_required} KB</td>
                          <td className="py-2.5 px-3 text-slate-400">
                            {Object.entries(p.allocated_resources || {}).map(([r, c]) => `${r}:${c}`).join(', ') || '-'}
                          </td>
                          <td className="py-2.5 px-3 text-right">
                            {p.state !== 'TERMINATED' && (
                              <button
                                onClick={() => handleTerminateProcess(p.pid)}
                                className="px-2 py-1 bg-rose-950/40 hover:bg-rose-900/60 text-rose-300 border border-rose-800/40 rounded text-[11px] transition"
                              >
                                Terminate
                              </button>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Recent Simulation Events */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
              <h3 className="text-sm font-semibold text-white mb-3 flex items-center space-x-2">
                <Clock className="w-4 h-4 text-cyan-400" />
                <span>Simulation Event Audit Stream</span>
              </h3>
              <div className="space-y-2 max-h-56 overflow-y-auto font-mono text-xs">
                {(state?.history_events || []).slice(-10).reverse().map((ev: any, idx: number) => (
                  <div key={idx} className="p-2 bg-slate-950 border border-slate-800/80 rounded flex items-start space-x-3">
                    <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-cyan-400 font-bold">
                      {ev.category}
                    </span>
                    <span className="text-slate-300 flex-1">{ev.message}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Create Process Form & Metrics Column */}
          <div className="space-y-6">
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
              <h3 className="text-sm font-semibold text-white mb-4 flex items-center space-x-2">
                <Plus className="w-4 h-4 text-cyan-400" />
                <span>Create Virtual Process</span>
              </h3>
              <form onSubmit={handleCreateProcess} className="space-y-3 text-xs">
                <div>
                  <label className="text-slate-400 block mb-1">Process ID (PID)</label>
                  <input
                    type="text"
                    value={newProc.pid}
                    onChange={(e) => setNewProc({ ...newProc, pid: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-slate-200"
                  />
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Name</label>
                  <input
                    type="text"
                    value={newProc.name}
                    onChange={(e) => setNewProc({ ...newProc, name: e.target.value })}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-slate-200"
                  />
                </div>
                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <label className="text-slate-400 block mb-1">CPU Burst (ticks)</label>
                    <input
                      type="number"
                      value={newProc.burst}
                      onChange={(e) => setNewProc({ ...newProc, burst: Number(e.target.value) })}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-slate-200"
                    />
                  </div>
                  <div>
                    <label className="text-slate-400 block mb-1">Memory (KB)</label>
                    <input
                      type="number"
                      value={newProc.mem}
                      onChange={(e) => setNewProc({ ...newProc, mem: Number(e.target.value) })}
                      className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-slate-200"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-slate-400 block mb-1">Priority (1 = Highest)</label>
                  <input
                    type="number"
                    value={newProc.priority}
                    onChange={(e) => setNewProc({ ...newProc, priority: Number(e.target.value) })}
                    className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-slate-200"
                  />
                </div>
                <button
                  type="submit"
                  className="w-full mt-2 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-medium text-xs transition"
                >
                  Spawn Process
                </button>
              </form>
            </div>

            {/* Quick Metrics */}
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg space-y-3">
              <h3 className="text-sm font-semibold text-white mb-2">Digital Twin Resources</h3>
              <div className="flex justify-between text-xs py-1 border-b border-slate-800">
                <span className="text-slate-400">Total Virtual RAM</span>
                <span className="font-mono text-cyan-300">{metrics.total_memory_kb} KB</span>
              </div>
              <div className="flex justify-between text-xs py-1 border-b border-slate-800">
                <span className="text-slate-400">RAM Allocated</span>
                <span className="font-mono text-emerald-400">{metrics.used_memory_kb} KB</span>
              </div>
              <div className="flex justify-between text-xs py-1 border-b border-slate-800">
                <span className="text-slate-400">Internal Frag</span>
                <span className="font-mono text-amber-400">{metrics.internal_fragmentation_kb} KB</span>
              </div>
              <div className="flex justify-between text-xs py-1">
                <span className="text-slate-400">Virtual Disk Capacity</span>
                <span className="font-mono text-cyan-300">{metrics.total_disk_kb} KB</span>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: CPU Scheduler & Gantt Chart */}
      {activeTab === 'scheduler' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-6">
              <div>
                <h3 className="text-base font-semibold text-white">CPU Scheduling Simulation Engine</h3>
                <p className="text-slate-400 text-xs">Simulates execution scheduling on all currently ready virtual processes.</p>
              </div>

              <div className="flex items-center space-x-3">
                <select
                  value={schedForm.algorithm}
                  onChange={(e) => setSchedForm({ ...schedForm, algorithm: e.target.value })}
                  className="bg-slate-950 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200"
                >
                  <option value="ROUND_ROBIN">Round Robin (RR)</option>
                  <option value="FCFS">First-Come, First-Served (FCFS)</option>
                  <option value="SJF">Shortest Job First (SJF)</option>
                  <option value="SRTF">Shortest Remaining Time First (SRTF)</option>
                  <option value="PRIORITY">Priority Scheduling</option>
                </select>

                {schedForm.algorithm === 'ROUND_ROBIN' && (
                  <div className="flex items-center space-x-1">
                    <span className="text-xs text-slate-400">Quantum:</span>
                    <input
                      type="number"
                      value={schedForm.quantum}
                      onChange={(e) => setSchedForm({ ...schedForm, quantum: Number(e.target.value) })}
                      className="w-16 bg-slate-950 border border-slate-800 rounded px-2 py-1.5 text-xs text-slate-200"
                    />
                  </div>
                )}

                <button
                  onClick={handleRunScheduler}
                  className="px-4 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1 transition"
                >
                  <Play className="w-3.5 h-3.5 fill-white" />
                  <span>Run Simulation</span>
                </button>
              </div>
            </div>

            {/* Visual Gantt Chart Timeline */}
            <div className="mt-4 p-4 bg-slate-950 border border-slate-800 rounded-xl">
              <h4 className="text-xs font-semibold text-slate-300 mb-3 flex items-center space-x-1">
                <span>Gantt Chart Execution Timeline</span>
              </h4>
              {state?.gantt_chart?.length > 0 ? (
                <div className="space-y-2">
                  <div className="flex w-full overflow-x-auto py-2">
                    {state.gantt_chart.map((item: any, idx: number) => (
                      <div
                        key={idx}
                        className="flex-1 min-w-[70px] border border-cyan-500/30 bg-cyan-950/40 p-2 text-center rounded mx-0.5 relative group hover:bg-cyan-900/60 transition"
                      >
                        <span className="font-bold text-xs text-cyan-300 block">{item.pid}</span>
                        <span className="text-[10px] text-slate-400 font-mono">{item.start_time} - {item.end_time}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500 font-mono">No scheduler timeline generated yet. Click 'Run Simulation' above.</p>
              )}
            </div>

            {/* Metrics cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6">
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                <span className="text-slate-400 text-xs">Average Turnaround Time</span>
                <p className="text-xl font-bold text-cyan-400 font-mono mt-1">{metrics.avg_turnaround_time} ms</p>
              </div>
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                <span className="text-slate-400 text-xs">Average Waiting Time</span>
                <p className="text-xl font-bold text-emerald-400 font-mono mt-1">{metrics.avg_waiting_time} ms</p>
              </div>
              <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl">
                <span className="text-slate-400 text-xs">CPU Utilization</span>
                <p className="text-xl font-bold text-indigo-400 font-mono mt-1">{metrics.cpu_utilization_percent}%</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Virtual Memory Management */}
      {activeTab === 'memory' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <h3 className="text-base font-semibold text-white mb-2">Virtual Physical RAM Allocation Map</h3>
            <p className="text-slate-400 text-xs mb-5">
              Contiguous memory allocation with First-Fit, Best-Fit, and Worst-Fit strategies across fixed/dynamic partitions.
            </p>

            {/* Visual RAM Blocks Bar */}
            <div className="flex w-full h-12 rounded-lg overflow-hidden border border-slate-800 bg-slate-950 p-1 gap-1">
              {(state?.memory_blocks || []).map((b: any) => {
                const isAlloc = b.is_allocated;
                const pct = Math.max(10, Math.round((b.size / (state.total_memory_capacity || 1700)) * 100));
                return (
                  <div
                    key={b.block_id}
                    style={{ flex: b.size }}
                    className={`h-full rounded flex flex-col justify-center items-center text-[10px] font-mono px-1 transition ${
                      isAlloc
                        ? 'bg-cyan-600/30 border border-cyan-500/40 text-cyan-200'
                        : 'bg-slate-800/40 border border-slate-700/30 text-slate-400'
                    }`}
                  >
                    <span className="font-bold">{isAlloc ? b.allocated_pid : 'FREE'}</span>
                    <span className="text-[9px] text-slate-400">{b.size} KB</span>
                  </div>
                );
              })}
            </div>

            {/* Partitions Table */}
            <div className="mt-6 overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2.5 px-3">Block ID</th>
                    <th className="py-2.5 px-3">Start Address</th>
                    <th className="py-2.5 px-3">Partition Size</th>
                    <th className="py-2.5 px-3">Status</th>
                    <th className="py-2.5 px-3">Allocated PID</th>
                    <th className="py-2.5 px-3">Internal Frag</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {(state?.memory_blocks || []).map((b: any) => (
                    <tr key={b.block_id} className="hover:bg-slate-800/30">
                      <td className="py-2.5 px-3 font-bold text-cyan-300">Block {b.block_id}</td>
                      <td className="py-2.5 px-3">{b.start_address}</td>
                      <td className="py-2.5 px-3">{b.size} KB</td>
                      <td className="py-2.5 px-3">
                        <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${b.is_allocated ? 'bg-cyan-500/20 text-cyan-300' : 'bg-slate-800 text-slate-400'}`}>
                          {b.is_allocated ? 'ALLOCATED' : 'FREE'}
                        </span>
                      </td>
                      <td className="py-2.5 px-3">{b.allocated_pid || '-'}</td>
                      <td className="py-2.5 px-3 text-amber-400">{b.internal_fragmentation} KB</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Allocate Memory Form */}
            <div className="mt-6 p-4 bg-slate-950 border border-slate-800 rounded-xl flex flex-wrap items-center gap-3">
              <span className="text-xs text-white font-semibold">Allocate Partition:</span>
              <select
                value={memForm.pid}
                onChange={(e) => setMemForm({ ...memForm, pid: e.target.value })}
                className="bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                {processes.map((p: any) => (
                  <option key={p.pid} value={p.pid}>{p.pid} ({p.name})</option>
                ))}
              </select>

              <input
                type="number"
                value={memForm.size}
                onChange={(e) => setMemForm({ ...memForm, size: Number(e.target.value) })}
                placeholder="Size KB"
                className="w-24 bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              />

              <select
                value={memForm.strategy}
                onChange={(e) => setMemForm({ ...memForm, strategy: e.target.value })}
                className="bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                <option value="FIRST_FIT">First-Fit</option>
                <option value="BEST_FIT">Best-Fit</option>
                <option value="WORST_FIT">Worst-Fit</option>
              </select>

              <button
                onClick={handleAllocateMemory}
                className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-semibold transition"
              >
                Allocate Block
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 4: Virtual Disk & Filesystem */}
      {activeTab === 'disk' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <h3 className="text-base font-semibold text-white mb-2">Isolated Virtual Filesystem Tree</h3>
            <p className="text-slate-400 text-xs mb-4">
              Pure virtual filesystem simulated in RAM. Completely isolated from the Windows host OS.
            </p>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                  <tr>
                    <th className="py-2 px-3">Path</th>
                    <th className="py-2 px-3">Type</th>
                    <th className="py-2 px-3">Size (KB)</th>
                    <th className="py-2 px-3">Owner</th>
                    <th className="py-2 px-3 text-right">Action</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {Object.values(state?.virtual_files || {}).map((f: any) => (
                    <tr key={f.path} className="hover:bg-slate-800/30">
                      <td className="py-2 px-3 font-bold text-cyan-300">{f.path}</td>
                      <td className="py-2 px-3 text-slate-400">{f.is_directory ? 'DIR' : 'FILE'}</td>
                      <td className="py-2 px-3">{f.size_kb}</td>
                      <td className="py-2 px-3 text-slate-400">{f.owner_pid || 'sys'}</td>
                      <td className="py-2 px-3 text-right">
                        {f.path !== '/' && (
                          <button
                            onClick={() => handleDeleteFile(f.path)}
                            className="p-1 hover:text-rose-400 transition"
                            title="Delete virtual file"
                          >
                            <Trash2 className="w-3.5 h-3.5 inline" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <h3 className="text-sm font-semibold text-white mb-3">Create Virtual File</h3>
            <form onSubmit={handleCreateFile} className="space-y-3 text-xs">
              <div>
                <label className="text-slate-400 block mb-1">Path</label>
                <input
                  type="text"
                  value={fileForm.path}
                  onChange={(e) => setFileForm({ ...fileForm, path: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-slate-200 font-mono"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Size (KB)</label>
                <input
                  type="number"
                  value={fileForm.size}
                  onChange={(e) => setFileForm({ ...fileForm, size: Number(e.target.value) })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-slate-200"
                />
              </div>
              <div>
                <label className="text-slate-400 block mb-1">Content</label>
                <textarea
                  rows={3}
                  value={fileForm.content}
                  onChange={(e) => setFileForm({ ...fileForm, content: e.target.value })}
                  className="w-full bg-slate-950 border border-slate-800 rounded px-3 py-1.5 text-slate-200 font-mono"
                />
              </div>
              <button
                type="submit"
                className="w-full py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded font-medium text-xs transition"
              >
                Write Virtual File
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Tab 5: Deadlock, Banker & Resource Management */}
      {activeTab === 'deadlock' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-white">Deadlock Avoidance & Resource Allocation Graph</h3>
                <p className="text-slate-400 text-xs">Evaluates safe state sequence with Banker's Algorithm and RAG cycle detection.</p>
              </div>
              <button
                onClick={handleCheckDeadlock}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-1 transition"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>Evaluate Safety</span>
              </button>
            </div>

            {deadlockData && (
              <div className="mb-6 p-4 bg-slate-950 border border-slate-800 rounded-xl">
                <div className="flex items-center space-x-3">
                  <span className={`px-2.5 py-1 rounded text-xs font-bold ${
                    deadlockData.banker?.is_safe ? 'bg-emerald-500/20 text-emerald-400' : 'bg-rose-500/20 text-rose-400'
                  }`}>
                    {deadlockData.banker?.is_safe ? 'SAFE STATE ✅' : 'DEADLOCKED / UNSAFE ❌'}
                  </span>
                  {deadlockData.banker?.safe_sequence && (
                    <span className="text-xs text-slate-300 font-mono">
                      Safe Execution Order: {deadlockData.banker.safe_sequence.join(' -> ')}
                    </span>
                  )}
                </div>
              </div>
            )}

            {/* Resources Vector */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {Object.values(state?.resources || {}).map((r: any) => (
                <div key={r.name} className="p-4 bg-slate-950 border border-slate-800 rounded-xl font-mono">
                  <span className="text-cyan-400 font-bold text-sm">{r.name} Instances</span>
                  <div className="flex justify-between items-center mt-2 text-xs">
                    <span className="text-slate-400">Available: <b className="text-emerald-400">{r.available_instances}</b></span>
                    <span className="text-slate-400">Total: <b className="text-slate-200">{r.total_instances}</b></span>
                  </div>
                </div>
              ))}
            </div>

            {/* Resource Request / Release Form */}
            <div className="p-4 bg-slate-950 border border-slate-800 rounded-xl flex flex-wrap items-center gap-3">
              <span className="text-xs text-white font-semibold">Process Action:</span>
              <select
                value={resForm.pid}
                onChange={(e) => setResForm({ ...resForm, pid: e.target.value })}
                className="bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                {processes.map((p: any) => (
                  <option key={p.pid} value={p.pid}>{p.pid}</option>
                ))}
              </select>

              <select
                value={resForm.resource}
                onChange={(e) => setResForm({ ...resForm, resource: e.target.value })}
                className="bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              >
                {Object.keys(state?.resources || {}).map((r) => (
                  <option key={r} value={r}>{r}</option>
                ))}
              </select>

              <input
                type="number"
                value={resForm.amount}
                onChange={(e) => setResForm({ ...resForm, amount: Number(e.target.value) })}
                className="w-16 bg-slate-900 border border-slate-800 rounded px-2.5 py-1.5 text-xs text-slate-200"
              />

              <button
                onClick={() => handleResourceRequest(false)}
                className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-white rounded text-xs font-semibold transition"
              >
                Request
              </button>
              <button
                onClick={() => handleResourceRequest(true)}
                className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded text-xs font-semibold transition"
              >
                Release
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Tab 6: What-If & Benchmarking */}
      {activeTab === 'what-if' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-semibold text-white">Side-by-Side Algorithm Comparison Benchmark</h3>
                <p className="text-slate-400 text-xs">Simulates FCFS, SJF, Round Robin, and Priority on the exact same process workload.</p>
              </div>
              <button
                onClick={handleRunComparison}
                className="px-4 py-2 bg-gradient-to-r from-cyan-600 to-indigo-600 hover:from-cyan-500 hover:to-indigo-500 text-white rounded-lg text-xs font-semibold flex items-center space-x-2 transition"
              >
                <Play className="w-4 h-4 fill-white" />
                <span>Run Benchmark</span>
              </button>
            </div>

            {compareData && (
              <div className="space-y-4">
                <div className="p-3 bg-emerald-950/30 border border-emerald-800/40 rounded-lg text-xs text-emerald-300 font-mono">
                  💡 {compareData.recommendation}
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-mono">
                    <thead className="bg-slate-950 text-slate-400 border-b border-slate-800">
                      <tr>
                        <th className="py-2.5 px-3">Algorithm</th>
                        <th className="py-2.5 px-3">Avg Turnaround Time</th>
                        <th className="py-2.5 px-3">Avg Waiting Time</th>
                        <th className="py-2.5 px-3">CPU Utilization</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60 text-slate-300">
                      {(compareData.comparisons || []).map((c: any) => (
                        <tr key={c.algorithm} className="hover:bg-slate-800/30">
                          <td className="py-2.5 px-3 font-bold text-cyan-300">{c.algorithm}</td>
                          <td className="py-2.5 px-3">{c.avg_turnaround_time} ms</td>
                          <td className="py-2.5 px-3">{c.avg_waiting_time} ms</td>
                          <td className="py-2.5 px-3">{c.cpu_utilization_percent}%</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>

          {/* Snapshots Checkpoint Manager */}
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 shadow-lg">
            <h3 className="text-base font-semibold text-white mb-2">Checkpoints & Snapshots</h3>
            <p className="text-slate-400 text-xs mb-4">Restore or compare historical virtual OS state checkpoints.</p>

            <div className="space-y-2">
              {snapshots.length > 0 ? (
                snapshots.map((s) => (
                  <div key={s.snapshot_id} className="p-3 bg-slate-950 border border-slate-800 rounded-lg flex items-center justify-between text-xs font-mono">
                    <div>
                      <span className="font-bold text-cyan-300">{s.label}</span>
                      <span className="text-slate-500 ml-2">({s.snapshot_id})</span>
                      <span className="text-slate-400 block text-[11px] mt-0.5">Created at: {s.created_at} | Tick {s.tick}</span>
                    </div>
                    <button
                      onClick={() => handleRestoreSnapshot(s.snapshot_id)}
                      className="px-3 py-1 bg-cyan-950 hover:bg-cyan-900 text-cyan-300 border border-cyan-800/40 rounded transition"
                    >
                      Restore
                    </button>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-500 font-mono">No checkpoints recorded yet. Click 'Snapshot' at the top to save one.</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
