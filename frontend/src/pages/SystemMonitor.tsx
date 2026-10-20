import React, { useState, useEffect } from 'react';
import { Cpu, HardDrive, RefreshCw, XCircle, Search } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { api } from '../services/api';
import { SystemMetrics, ProcessItem } from '../types';

export const SystemMonitor: React.FC = () => {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [processes, setProcesses] = useState<ProcessItem[]>([]);
  const [chartData, setChartData] = useState<any[]>([]);
  const [search, setSearch] = useState<string>('');

  const loadData = () => {
    api.getMetrics().then((m) => {
      setMetrics(m);
      setChartData((prev) => [
        ...prev.slice(-15),
        { time: new Date().toLocaleTimeString(), cpu: m.cpu_percent, memory: m.memory.percent }
      ]);
    }).catch(console.error);

    api.getProcesses(50).then(setProcesses).catch(console.error);
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleTerminate = async (pid: number, name: string) => {
    if (!confirm(`Are you sure you want to terminate process '${name}' (PID: ${pid})?`)) return;
    try {
      await api.terminateProcess(pid);
      loadData();
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Failed to terminate process');
    }
  };

  const filteredProcesses = processes.filter(p => p.name.toLowerCase().includes(search.toLowerCase()));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <Cpu className="w-6 h-6 text-purple-400" />
            <span>Real-Time System & Process Monitor</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">Monitor real-time system metrics (psutil) and manage running processes.</p>
        </div>
        <button onClick={loadData} className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 rounded-lg text-xs font-medium border border-slate-700 flex items-center space-x-2">
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Refresh Now</span>
        </button>
      </div>

      {/* Real-time CPU & RAM Usage Chart */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <h3 className="text-sm font-bold text-white uppercase tracking-wider">Live System Resource Utilization</h3>
        <div className="h-64 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <XAxis dataKey="time" stroke="#64748B" fontSize={10} />
              <YAxis domain={[0, 100]} stroke="#64748B" fontSize={10} />
              <Tooltip contentStyle={{ backgroundColor: '#0F172A', borderColor: '#1E293B', fontSize: '12px' }} />
              <Area type="monotone" dataKey="cpu" stroke="#3B82F6" fillOpacity={0.2} fill="#3B82F6" name="CPU %" />
              <Area type="monotone" dataKey="memory" stroke="#8B5CF6" fillOpacity={0.2} fill="#8B5CF6" name="RAM %" />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Active Process List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <h3 className="text-sm font-bold text-white uppercase tracking-wider">Running Processes ({processes.length})</h3>
          <div className="relative w-72">
            <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search process name..."
              className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
            />
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm text-slate-300">
            <thead className="bg-slate-950 text-xs font-semibold text-slate-400 border-b border-slate-800 uppercase tracking-wider">
              <tr>
                <th className="px-6 py-3">PID</th>
                <th className="px-6 py-3">Process Name</th>
                <th className="px-6 py-3">CPU %</th>
                <th className="px-6 py-3">Memory (MB)</th>
                <th className="px-6 py-3">Status</th>
                <th className="px-6 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono text-xs">
              {filteredProcesses.map((p) => (
                <tr key={p.pid} className="hover:bg-slate-800/40 transition-colors">
                  <td className="px-6 py-3 text-slate-400">{p.pid}</td>
                  <td className="px-6 py-3 text-white font-semibold">{p.name}</td>
                  <td className="px-6 py-3 text-blue-400">{p.cpu_percent}%</td>
                  <td className="px-6 py-3 text-purple-400">{p.memory_mb} MB</td>
                  <td className="px-6 py-3 text-emerald-400">{p.status}</td>
                  <td className="px-6 py-3 text-right">
                    <button
                      onClick={() => handleTerminate(p.pid, p.name)}
                      className="px-2.5 py-1 bg-red-950/40 hover:bg-red-900/60 text-red-400 border border-red-800/40 rounded text-xs transition-colors"
                    >
                      Terminate
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
