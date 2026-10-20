import React, { useState } from 'react';
import { api } from '../services/api';
import { BankersResult } from '../types';
import { AlertOctagon, Play, CheckCircle2, AlertTriangle, Shield } from 'lucide-react';

export const DeadlockIPC: React.FC = () => {
  const [tab, setTab] = useState<'bankers' | 'ipc'>('bankers');
  
  // Banker's Algorithm input state
  const [available, setAvailable] = useState<string>('3, 3, 2');
  const [maxMatrixStr, setMaxMatrixStr] = useState<string>('7,5,3\n3,2,2\n9,0,2\n2,2,2\n4,3,3');
  const [allocMatrixStr, setAllocMatrixStr] = useState<string>('0,1,0\n2,0,0\n3,0,2\n2,1,1\n0,0,2');

  const [bankersResult, setBankersResult] = useState<BankersResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleRunBankers = async () => {
    try {
      setLoading(true);
      setError(null);

      const availParsed = available.split(',').map((x) => parseInt(x.trim()) || 0);
      const parseMatrix = (str: string) =>
        str
          .trim()
          .split('\n')
          .map((line) => line.split(',').map((x) => parseInt(x.trim()) || 0));

      const maxM = parseMatrix(maxMatrixStr);
      const allocM = parseMatrix(allocMatrixStr);

      const procs = maxM.map((_, i) => `P${i}`);
      const resTypes = ['A', 'B', 'C'].slice(0, availParsed.length);

      const res = await api.simulateBankersAlgorithm({
        processes: procs,
        resource_types: resTypes,
        available: availParsed,
        max_matrix: maxM,
        allocation_matrix: allocM,
      });

      setBankersResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || "Banker's Algorithm computation failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <AlertOctagon className="text-cyan-400" size={28} />
            Deadlock & IPC Simulator
          </h1>
          <p className="text-slate-400 text-sm">
            Simulate Banker's Algorithm for deadlock avoidance, Resource Allocation Graphs (RAG), and Inter-Process Communication (IPC).
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setTab('bankers')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
            tab === 'bankers' ? 'bg-cyan-600 text-white' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
          }`}
        >
          <Shield size={16} /> Banker's Algorithm Solver
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/50 border border-rose-500/50 rounded-lg text-rose-300 text-sm">
          {error}
        </div>
      )}

      {tab === 'bankers' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Available Resources (Vector)</label>
              <input
                type="text"
                value={available}
                onChange={(e) => setAvailable(e.target.value)}
                placeholder="e.g. 3, 3, 2"
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm font-mono"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Max Matrix (Rows: P0..Pn)</label>
                <textarea
                  rows={5}
                  value={maxMatrixStr}
                  onChange={(e) => setMaxMatrixStr(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-slate-200 text-xs font-mono"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Allocation Matrix (Rows: P0..Pn)</label>
                <textarea
                  rows={5}
                  value={allocMatrixStr}
                  onChange={(e) => setAllocMatrixStr(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg p-3 text-slate-200 text-xs font-mono"
                />
              </div>
            </div>

            <button
              onClick={handleRunBankers}
              disabled={loading}
              className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg shadow-lg flex items-center gap-2 transition"
            >
              <Play size={16} /> Run Banker's Algorithm
            </button>
          </div>

          {bankersResult && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
              <div
                className={`p-4 rounded-xl flex items-center gap-3 border ${
                  bankersResult.is_safe
                    ? 'bg-emerald-950/40 border-emerald-500/50 text-emerald-300'
                    : 'bg-rose-950/40 border-rose-500/50 text-rose-300'
                }`}
              >
                {bankersResult.is_safe ? <CheckCircle2 size={24} /> : <AlertTriangle size={24} />}
                <div>
                  <h3 className="font-bold text-base">
                    System State: {bankersResult.is_safe ? 'SAFE STATE' : 'DEADLOCKED / UNSAFE STATE'}
                  </h3>
                  <p className="text-xs mt-0.5">{bankersResult.explanation}</p>
                </div>
              </div>

              {/* Matrix Display */}
              <div>
                <h3 className="text-slate-200 font-semibold text-sm mb-3">Calculated Need Matrix</h3>
                <div className="overflow-x-auto">
                  <table className="w-full text-center text-xs text-slate-300 font-mono">
                    <thead className="bg-slate-950 text-slate-400">
                      <tr>
                        <th className="p-2">Process</th>
                        {bankersResult.resource_types.map((r, i) => (
                          <th key={i} className="p-2">Resource {r}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                      {bankersResult.need_matrix.map((row, i) => (
                        <tr key={i} className="hover:bg-slate-850/50">
                          <td className="p-2 font-bold text-cyan-400">{bankersResult.processes[i]}</td>
                          {row.map((val, j) => (
                            <td key={j} className="p-2">{val}</td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
