import React, { useState } from 'react';
import { ShieldCheck, Play, Lock, Users, RefreshCw } from 'lucide-react';

export const ConcurrencySync: React.FC = () => {
  const [problem, setProblem] = useState<'producer_consumer' | 'readers_writers' | 'dining_philosophers'>('producer_consumer');
  const [step, setStep] = useState<number>(0);
  const [isSimulating, setIsSimulating] = useState<boolean>(false);

  // Producer-Consumer state
  const [buffer, setBuffer] = useState<number[]>([]);
  const bufferCapacity = 5;

  // Readers-Writers state
  const [activeReaders, setActiveReaders] = useState<number>(0);
  const [isWriting, setIsWriting] = useState<boolean>(false);

  // Dining Philosophers state
  const [philosophers, setPhilosophers] = useState<string[]>(['Thinking', 'Thinking', 'Thinking', 'Thinking', 'Thinking']);

  const handleStepNext = () => {
    setStep((prev) => prev + 1);

    if (problem === 'producer_consumer') {
      if (buffer.length < bufferCapacity) {
        setBuffer((prev) => [...prev, prev.length + 1]);
      } else {
        setBuffer((prev) => prev.slice(1));
      }
    } else if (problem === 'readers_writers') {
      if (!isWriting && activeReaders < 3) {
        setActiveReaders((prev) => prev + 1);
      } else if (activeReaders > 0) {
        setActiveReaders((prev) => prev - 1);
        setIsWriting(true);
      } else {
        setIsWriting(false);
      }
    } else if (problem === 'dining_philosophers') {
      const nextStates = [...philosophers];
      const idx = step % 5;
      nextStates[idx] = nextStates[idx] === 'Thinking' ? 'Eating' : 'Thinking';
      setPhilosophers(nextStates);
    }
  };

  const handleReset = () => {
    setStep(0);
    setBuffer([]);
    setActiveReaders(0);
    setIsWriting(false);
    setPhilosophers(['Thinking', 'Thinking', 'Thinking', 'Thinking', 'Thinking']);
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 flex items-center gap-2">
            <Lock className="text-cyan-400" size={28} />
            Concurrency & Synchronization Simulator
          </h1>
          <p className="text-slate-400 text-sm">
            Educational visualizer for race conditions, critical sections, mutex locks, semaphores, and classic OS synchronization problems.
          </p>
        </div>
      </div>

      {/* Select Problem */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <button
          onClick={() => { setProblem('producer_consumer'); handleReset(); }}
          className={`p-4 rounded-xl border text-left transition ${
            problem === 'producer_consumer' ? 'bg-cyan-950/40 border-cyan-500' : 'bg-slate-900 border-slate-800 hover:bg-slate-850'
          }`}
        >
          <div className="font-semibold text-slate-200">Producer-Consumer</div>
          <div className="text-xs text-slate-400 mt-1">Bounded buffer synchronization using Semaphores</div>
        </button>

        <button
          onClick={() => { setProblem('readers_writers'); handleReset(); }}
          className={`p-4 rounded-xl border text-left transition ${
            problem === 'readers_writers' ? 'bg-cyan-950/40 border-cyan-500' : 'bg-slate-900 border-slate-800 hover:bg-slate-850'
          }`}
        >
          <div className="font-semibold text-slate-200">Readers-Writers</div>
          <div className="text-xs text-slate-400 mt-1">Shared resource access with Reader-preference / Writer-exclusion</div>
        </button>

        <button
          onClick={() => { setProblem('dining_philosophers'); handleReset(); }}
          className={`p-4 rounded-xl border text-left transition ${
            problem === 'dining_philosophers' ? 'bg-cyan-950/40 border-cyan-500' : 'bg-slate-900 border-slate-800 hover:bg-slate-850'
          }`}
        >
          <div className="font-semibold text-slate-200">Dining Philosophers</div>
          <div className="text-xs text-slate-400 mt-1">Resource allocation, deadlock avoidance & chopstick lock state</div>
        </button>
      </div>

      {/* Interactive Controls */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-5 flex items-center justify-between">
        <div className="text-sm font-medium text-slate-300">
          Simulation Step: <span className="text-cyan-400 font-mono text-base">{step}</span>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleReset}
            className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm flex items-center gap-1"
          >
            <RefreshCw size={16} /> Reset
          </button>
          <button
            onClick={handleStepNext}
            className="px-5 py-2 bg-cyan-600 hover:bg-cyan-500 text-white rounded-lg text-sm font-medium flex items-center gap-1 shadow-lg"
          >
            <Play size={16} /> Advance Step
          </button>
        </div>
      </div>

      {/* Visualization Canvas */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 min-h-[300px] flex items-center justify-center">
        {problem === 'producer_consumer' && (
          <div className="w-full space-y-6 text-center">
            <h3 className="text-slate-200 font-semibold text-base">Bounded Buffer (Capacity: 5)</h3>
            <div className="flex justify-center gap-3">
              {[0, 1, 2, 3, 4].map((idx) => (
                <div
                  key={idx}
                  className={`w-16 h-16 rounded-xl border flex items-center justify-center font-bold text-base transition-all ${
                    idx < buffer.length
                      ? 'bg-emerald-950/60 border-emerald-500 text-emerald-300 scale-105 shadow-lg shadow-emerald-950/50'
                      : 'bg-slate-950 border-slate-800 text-slate-600'
                  }`}
                >
                  {idx < buffer.length ? `Item ${buffer[idx]}` : 'Empty'}
                </div>
              ))}
            </div>
            <div className="text-xs text-slate-400">
              {buffer.length === bufferCapacity ? 'Buffer FULL (Producer Blocked)' : buffer.length === 0 ? 'Buffer EMPTY (Consumer Blocked)' : 'Buffer Active'}
            </div>
          </div>
        )}

        {problem === 'readers_writers' && (
          <div className="w-full space-y-6 text-center">
            <h3 className="text-slate-200 font-semibold text-base">Shared Resource State</h3>
            <div className="flex justify-center items-center gap-8">
              <div className={`p-4 rounded-xl border w-40 text-center ${activeReaders > 0 ? 'bg-cyan-950/50 border-cyan-500 text-cyan-300' : 'bg-slate-950 border-slate-800 text-slate-600'}`}>
                <div className="text-xs font-semibold">Active Readers</div>
                <div className="text-2xl font-bold mt-1">{activeReaders}</div>
              </div>
              <div className={`p-4 rounded-xl border w-40 text-center ${isWriting ? 'bg-rose-950/50 border-rose-500 text-rose-300' : 'bg-slate-950 border-slate-800 text-slate-600'}`}>
                <div className="text-xs font-semibold">Writer Status</div>
                <div className="text-base font-bold mt-1">{isWriting ? 'WRITING (Exclusive Lock)' : 'IDLE'}</div>
              </div>
            </div>
          </div>
        )}

        {problem === 'dining_philosophers' && (
          <div className="w-full space-y-6 text-center">
            <h3 className="text-slate-200 font-semibold text-base">5 Philosophers Table</h3>
            <div className="flex justify-center gap-4">
              {philosophers.map((state, idx) => (
                <div
                  key={idx}
                  className={`p-4 rounded-xl border min-w-[100px] flex flex-col items-center transition-all ${
                    state === 'Eating' ? 'bg-amber-950/50 border-amber-500 text-amber-300 scale-105' : 'bg-slate-950 border-slate-800 text-slate-400'
                  }`}
                >
                  <Users size={24} className="mb-2" />
                  <span className="text-xs font-bold">Philosopher {idx + 1}</span>
                  <span className="text-[10px] mt-1 uppercase font-semibold">{state}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
