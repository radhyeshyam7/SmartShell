import React, { useState } from 'react';
import { api } from '../services/api';
import { DiskSchedulerResult } from '../types';
import { Disc, Play, ArrowRight } from 'lucide-react';

export const DiskScheduling: React.FC = () => {
  const [algorithm, setAlgorithm] = useState<string>('FCFS');
  const [initialHead, setInitialHead] = useState<number>(53);
  const [diskSize, setDiskSize] = useState<number>(200);
  const [direction, setDirection] = useState<string>('right');
  const [requestQueue, setRequestQueue] = useState<string>('98, 183, 37, 122, 14, 124, 65, 67');

  const [result, setResult] = useState<DiskSchedulerResult | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  const handleSimulate = async () => {
    try {
      setLoading(true);
      setError(null);
      const reqs = requestQueue.split(',').map((x) => parseInt(x.trim()) || 0);

      const res = await api.simulateDiskScheduling({
        algorithm,
        requests: reqs,
        initial_head: initialHead,
        disk_size: diskSize,
        direction,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Disk Scheduling Simulation Failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Disc className="text-cyan-400" size={28} />
            Disk Scheduling Simulator
          </h1>
          <p className="text-slate-400 text-sm">
            Simulate FCFS, SSTF, SCAN, C-SCAN, LOOK, and C-LOOK disk track arm movement algorithms.
          </p>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-950/50 border border-rose-500/50 rounded-lg text-rose-300 text-sm">
          {error}
        </div>
      )}

      {/* Inputs */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Algorithm</label>
            <select
              value={algorithm}
              onChange={(e) => setAlgorithm(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
            >
              <option value="FCFS">FCFS (First Come First Served)</option>
              <option value="SSTF">SSTF (Shortest Seek Time First)</option>
              <option value="SCAN">SCAN (Elevator)</option>
              <option value="C-SCAN">C-SCAN (Circular SCAN)</option>
              <option value="LOOK">LOOK</option>
              <option value="C-LOOK">C-LOOK</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Initial Head Position</label>
            <input
              type="number"
              min="0"
              value={initialHead}
              onChange={(e) => setInitialHead(parseInt(e.target.value) || 0)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Disk Track Capacity</label>
            <input
              type="number"
              min="10"
              value={diskSize}
              onChange={(e) => setDiskSize(parseInt(e.target.value) || 200)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Head Direction</label>
            <select
              value={direction}
              onChange={(e) => setDirection(e.target.value)}
              className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm"
            >
              <option value="right">Right (Increasing Tracks)</option>
              <option value="left">Left (Decreasing Tracks)</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-300 uppercase mb-1">Track Request Queue (Comma-separated numbers)</label>
          <input
            type="text"
            value={requestQueue}
            onChange={(e) => setRequestQueue(e.target.value)}
            className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-slate-200 text-sm font-mono"
          />
        </div>

        <button
          onClick={handleSimulate}
          disabled={loading}
          className="px-5 py-2.5 bg-cyan-600 hover:bg-cyan-500 text-white font-medium rounded-lg shadow-lg flex items-center gap-2 transition"
        >
          <Play size={16} /> Simulate Seek Sequence
        </button>
      </div>

      {/* Results */}
      {result && (
        <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block">Total Seek Distance</span>
              <span className="text-2xl font-bold text-cyan-400">{result.total_seek_distance} tracks</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block">Average Seek Distance</span>
              <span className="text-2xl font-bold text-emerald-400">{result.avg_seek_distance} tracks</span>
            </div>
            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
              <span className="text-xs text-slate-400 block">Head Movements Count</span>
              <span className="text-2xl font-bold text-indigo-400">{result.sequence.length - 1} moves</span>
            </div>
          </div>

          <div>
            <h3 className="text-slate-200 font-semibold text-sm mb-3">Head Seek Order Sequence</h3>
            <div className="flex flex-wrap items-center gap-2 bg-slate-950 p-4 rounded-xl border border-slate-800">
              {result.sequence.map((track, i) => (
                <React.Fragment key={i}>
                  <div
                    className={`px-3 py-1.5 rounded-lg font-mono text-xs font-bold ${
                      i === 0 ? 'bg-cyan-950 text-cyan-300 border border-cyan-500/50' : 'bg-slate-800 text-slate-200'
                    }`}
                  >
                    {track}
                  </div>
                  {i < result.sequence.length - 1 && <ArrowRight size={14} className="text-slate-500" />}
                </React.Fragment>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
