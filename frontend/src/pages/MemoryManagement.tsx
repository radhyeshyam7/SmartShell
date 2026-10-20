import React, { useState } from 'react';
import { api } from '../services/api';
import { MemoryContiguousResult, MemoryPageReplacementResult } from '../types';
import { HardDrive, Play, Layers, Activity } from 'lucide-react';

export const MemoryManagement: React.FC = () => {
  const [tab, setTab] = useState<'contiguous' | 'paging'>('contiguous');
  
  // Contiguous State
  const [strategy, setStrategy] = useState<string>('FIRST_FIT');
  const [totalMemory, setTotalMemory] = useState<number>(1000);
  const [blocks, setBlocks] = useState<string>('100, 500, 200, 300, 600');
  const [procInput, setProcInput] = useState<string>('P1:212, P2:417, P3:112, P4:426');
  const [contResult, setContResult] = useState<MemoryContiguousResult | null>(null);

  // Paging State
  const [pageAlg, setPageAlg] = useState<string>('FIFO');
  const [numFrames, setNumFrames] = useState<number>(3);
  const [pageSequence, setPageSequence] = useState<string>('7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1');
  const [pageResult, setPageResult] = useState<MemoryPageReplacementResult | null>(null);

  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSimulateContiguous = async () => {
    try {
      setLoading(true);
      setError(null);
      const parsedBlocks = blocks.split(',').map((b) => parseInt(b.trim()) || 100);
      const parsedProcs = procInput.split(',').map((item) => {
        const [pid, sz] = item.split(':');
        return { pid: pid?.trim() || 'P', size: parseInt(sz?.trim() || '100') };
      });

      const res = await api.simulateContiguousMemory({
        strategy,
        total_memory: totalMemory,
        blocks: parsedBlocks,
        processes: parsedProcs,
      });
      setContResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Contiguous Memory Simulation Failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleSimulatePaging = async () => {
    try {
      setLoading(true);
      setError(null);
      const parsedPages = pageSequence.split(',').map((p) => parseInt(p.trim()) || 0);

      const res = await api.simulatePageReplacement({
        algorithm: pageAlg,
        num_frames: numFrames,
        pages: parsedPages,
      });
      setPageResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Page Replacement Simulation Failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <HardDrive className="text-cyan-400" size={28} />
            Memory Management Simulator
          </h1>
          <p className="text-slate-400 text-sm">
            Simulate contiguous allocation strategies (First Fit, Best Fit, Worst Fit) and Page Replacement (FIFO, LRU, Optimal).
          </p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-800 pb-2">
        <button
          onClick={() => setTab('contiguous')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
            tab === 'contiguous' ? 'bg-cyan-600 text-white' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
          }`}
        >
          <Layers size={16} /> Contiguous Memory Allocation
        </button>
        <button
          onClick={() => setTab('paging')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition flex items-center gap-2 ${
            tab === 'paging' ? 'bg-cyan-600 text-white' : 'bg-slate-900 text-slate-400 hover:bg-slate-800'
          }`}
        >
          <Activity size={16} /> Page Replacement Algorithms
        </button>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/50 border border-rose-500/50 rounded-lg text-rose-300 text-sm">
          {error}
        </div>
      )}

      {tab === 'contiguous' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Strategy</label>
                <select
                  value={strategy}
                  onChange={(e) => setStrategy(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
                >
                  <option value="FIRST_FIT">First Fit</option>
                  <option value="BEST_FIT">Best Fit</option>
                  <option value="WORST_FIT">Worst Fit</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Total Memory Size (KB)</label>
                <input
                  type="number"
                  value={totalMemory}
                  onChange={(e) => setTotalMemory(parseInt(e.target.value) || 1000)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Memory Blocks (Comma-separated sizes)</label>
              <input
                type="text"
                value={blocks}
                onChange={(e) => setBlocks(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Process Requests (Format: PID:Size)</label>
              <input
                type="text"
                value={procInput}
                onChange={(e) => setProcInput(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
              />
            </div>

            <button
              onClick={handleSimulateContiguous}
              disabled={loading}
              className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg shadow-lg flex items-center gap-2 transition"
            >
              <Play size={16} /> Simulate Allocation
            </button>
          </div>

          {contResult && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5">
              <h2 className="text-slate-200 font-semibold text-base">Memory Layout Visualization</h2>
              <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
                {contResult.blocks.map((b, i) => (
                  <div
                    key={i}
                    className={`p-4 rounded-xl border flex flex-col justify-between ${
                      b.process_id ? 'bg-cyan-950/40 border-cyan-500/50' : 'bg-slate-950 border-slate-800'
                    }`}
                  >
                    <span className="text-xs font-mono text-slate-400">Block {b.id} ({b.size} KB)</span>
                    <span className="text-base font-bold text-slate-200 mt-2">
                      {b.process_id ? `${b.process_id} (${b.allocated_size} KB)` : 'FREE'}
                    </span>
                    {b.process_id && (
                      <span className="text-[10px] text-amber-400 mt-1">Frag: {b.size - b.allocated_size} KB</span>
                    )}
                  </div>
                ))}
              </div>

              <div className="grid grid-cols-2 gap-4 pt-4 border-t border-slate-800 text-sm">
                <div>
                  <span className="text-slate-400 block text-xs">Total Internal Fragmentation</span>
                  <span className="text-lg font-bold text-amber-400">{contResult.metrics.internal_fragmentation_bytes} KB</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-xs">External Fragmentation (Free Unused Memory)</span>
                  <span className="text-lg font-bold text-emerald-400">{contResult.metrics.external_fragmentation_bytes} KB</span>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {tab === 'paging' && (
        <div className="space-y-6">
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Page Replacement Algorithm</label>
                <select
                  value={pageAlg}
                  onChange={(e) => setPageAlg(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
                >
                  <option value="FIFO">First In First Out (FIFO)</option>
                  <option value="LRU">Least Recently Used (LRU)</option>
                  <option value="OPTIMAL">Optimal Page Replacement</option>
                </select>
              </div>
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Number of Frames</label>
                <input
                  type="number"
                  min="1"
                  max="10"
                  value={numFrames}
                  onChange={(e) => setNumFrames(parseInt(e.target.value) || 3)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Page Reference Sequence (Comma-separated)</label>
              <input
                type="text"
                value={pageSequence}
                onChange={(e) => setPageSequence(e.target.value)}
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
              />
            </div>

            <button
              onClick={handleSimulatePaging}
              disabled={loading}
              className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg shadow-lg flex items-center gap-2 transition"
            >
              <Play size={16} /> Simulate Paging
            </button>
          </div>

          {pageResult && (
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-5">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <span className="text-xs text-slate-400 block">Total Page Requests</span>
                  <span className="text-xl font-bold text-slate-200">{pageResult.total_requests}</span>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <span className="text-xs text-slate-400 block">Page Faults</span>
                  <span className="text-xl font-bold text-rose-400">{pageResult.page_faults}</span>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <span className="text-xs text-slate-400 block">Page Hits</span>
                  <span className="text-xl font-bold text-emerald-400">{pageResult.page_hits}</span>
                </div>
                <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
                  <span className="text-xs text-slate-400 block">Hit Ratio</span>
                  <span className="text-xl font-bold text-cyan-400">{pageResult.hit_ratio_percent}%</span>
                </div>
              </div>

              {/* Timeline */}
              <div className="overflow-x-auto">
                <table className="w-full text-center text-xs text-slate-300">
                  <thead className="bg-slate-950 text-slate-400 uppercase">
                    <tr>
                      <th className="p-2">Step</th>
                      <th className="p-2">Page</th>
                      <th className="p-2">Status</th>
                      <th className="p-2">Frame State</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800">
                    {pageResult.timeline.map((step, idx) => (
                      <tr key={idx} className="hover:bg-slate-850/50">
                        <td className="p-2 text-slate-400 font-mono">{step.step}</td>
                        <td className="p-2 font-bold text-cyan-400">{step.page}</td>
                        <td className="p-2">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                              step.status === 'HIT' ? 'bg-emerald-950 text-emerald-300 border border-emerald-500/40' : 'bg-rose-950 text-rose-300 border border-rose-500/40'
                            }`}
                          >
                            {step.status}
                          </span>
                        </td>
                        <td className="p-2 font-mono text-slate-300">
                          [{step.frames.map((f) => (f === -1 ? '-' : f)).join(', ')}]
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
