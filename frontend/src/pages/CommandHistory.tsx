import React, { useState, useEffect } from 'react';
import { History, Search, Download, Eye, X } from 'lucide-react';
import { api } from '../services/api';
import { Task } from '../types';

export const CommandHistory: React.FC = () => {
  const [history, setHistory] = useState<any[]>([]);
  const [search, setSearch] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  const loadHistory = () => {
    api.getHistory(search, statusFilter, 50).then(setHistory).catch(console.error);
  };

  useEffect(() => {
    loadHistory();
  }, [search, statusFilter]);

  const exportJSON = () => {
    const jsonStr = JSON.stringify(history, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `smartshell_history_${Date.now()}.json`;
    a.click();
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white flex items-center space-x-2">
            <History className="w-6 h-6 text-blue-400" />
            <span>SQLite Command History & Audit Logs</span>
          </h1>
          <p className="text-slate-400 text-sm mt-1">Search past executions, review stdout/stderr outputs, and export reports.</p>
        </div>

        <button
          onClick={exportJSON}
          className="inline-flex items-center space-x-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 rounded-lg text-xs font-medium transition-colors"
        >
          <Download className="w-4 h-4" />
          <span>Export History JSON</span>
        </button>
      </div>

      {/* Filter Bar */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="relative w-80">
          <Search className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search prompt or task..."
            className="w-full bg-slate-950 border border-slate-800 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500"
          />
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-xs text-slate-400 font-medium">Filter Status:</span>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="bg-slate-950 border border-slate-800 text-xs text-slate-200 rounded-lg p-1.5 focus:outline-none"
          >
            <option value="">All Statuses</option>
            <option value="completed">Completed</option>
            <option value="failed">Failed</option>
            <option value="pending">Pending</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>
      </div>

      {/* History Table */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <table className="w-full text-left text-sm text-slate-300">
          <thead className="bg-slate-950 text-xs font-semibold text-slate-400 border-b border-slate-800 uppercase tracking-wider">
            <tr>
              <th className="px-6 py-3">Task Name</th>
              <th className="px-6 py-3">User Prompt</th>
              <th className="px-6 py-3">Status</th>
              <th className="px-6 py-3">Timestamp</th>
              <th className="px-6 py-3 text-right">Details</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/60">
            {history.map((item) => (
              <tr key={item.id} className="hover:bg-slate-800/40 transition-colors">
                <td className="px-6 py-3 font-semibold text-white">{item.task_name}</td>
                <td className="px-6 py-3 text-xs font-mono text-slate-300">{item.user_prompt}</td>
                <td className="px-6 py-3 text-xs">
                  <span className={`px-2.5 py-0.5 rounded font-semibold ${
                    item.status === 'completed' ? 'bg-emerald-950 text-emerald-400 border border-emerald-800' :
                    item.status === 'failed' ? 'bg-red-950 text-red-400 border border-red-800' :
                    'bg-amber-950 text-amber-400 border border-amber-800'
                  }`}>
                    {item.status.toUpperCase()}
                  </span>
                </td>
                <td className="px-6 py-3 text-xs font-mono text-slate-400">
                  {(() => {
                    if (!item.created_at) return 'N/A';
                    const dateStr = item.created_at;
                    const isoStr = (!dateStr.endsWith('Z') && !dateStr.includes('+')) ? `${dateStr}Z` : dateStr;
                    const d = new Date(isoStr);
                    return isNaN(d.getTime()) ? dateStr : d.toLocaleString();
                  })()}
                </td>
                <td className="px-6 py-3 text-right">
                  <button
                    onClick={() => api.getTask(item.id).then(setSelectedTask).catch(console.error)}
                    className="p-1.5 rounded bg-slate-800 hover:bg-slate-700 text-slate-300 transition-colors"
                  >
                    <Eye className="w-4 h-4" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Task Details Inspection Modal */}
      {selectedTask && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center p-6 z-50">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl w-full max-w-4xl max-h-[85vh] overflow-y-auto shadow-2xl p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div>
                <h3 className="font-bold text-white text-lg">{selectedTask.task_name}</h3>
                <p className="text-xs text-slate-400">{selectedTask.user_prompt}</p>
              </div>
              <button onClick={() => setSelectedTask(null)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-3">
              {selectedTask.steps.map((s) => (
                <div key={s.id} className="p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-bold text-blue-400 font-mono">Step {s.step_index}: {s.description}</span>
                    <span className="text-xs font-semibold px-2 py-0.5 rounded bg-slate-800 text-slate-300">{s.status}</span>
                  </div>
                  <p className="text-xs font-mono text-slate-300 bg-slate-900 p-2 rounded">$ {s.command}</p>
                  {s.stdout && <pre className="text-xs font-mono text-slate-300 bg-slate-900 p-2 rounded overflow-x-auto">{s.stdout}</pre>}
                  {s.stderr && <pre className="text-xs font-mono text-red-400 bg-slate-900 p-2 rounded overflow-x-auto">{s.stderr}</pre>}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
