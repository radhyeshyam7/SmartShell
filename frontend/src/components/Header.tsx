import React, { useEffect, useState } from 'react';
import { Search, Folder, ShieldCheck, AlertCircle } from 'lucide-react';
import { api } from '../services/api';

export const Header: React.FC = () => {
  const [healthy, setHealthy] = useState<boolean | null>(null);
  const [geminiConfigured, setGeminiConfigured] = useState<boolean>(false);

  useEffect(() => {
    api.getHealth()
      .then((res) => {
        setHealthy(true);
        setGeminiConfigured(res.gemini_configured);
      })
      .catch(() => setHealthy(false));
  }, []);

  return (
    <header className="h-16 bg-[#0F172A] border-b border-slate-800 px-6 flex items-center justify-between select-none">
      {/* Search Input */}
      <div className="relative w-96">
        <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          placeholder="Search commands, history, workflows..."
          className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-4 py-2 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
        />
      </div>
    </header>
  );
};
