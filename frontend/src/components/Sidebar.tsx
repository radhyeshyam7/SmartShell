import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  Activity, 
  Cpu, 
  HardDrive, 
  Lock, 
  AlertOctagon, 
  Disc, 
  FolderGit2, 
  History, 
  Settings,
  Sparkles
} from 'lucide-react';

export const Sidebar: React.FC = () => {
  const navItems = [
    { path: '/', label: 'Dashboard', icon: LayoutDashboard },
    { path: '/digital-twin', label: 'OS Digital Twin', icon: Sparkles },
    { path: '/processes', label: 'Processes', icon: Activity },
    { path: '/cpu-scheduling', label: 'CPU Scheduling', icon: Cpu },
    { path: '/memory-management', label: 'Memory Mgmt', icon: HardDrive },
    { path: '/concurrency', label: 'Concurrency', icon: Lock },
    { path: '/deadlock-ipc', label: 'Deadlock & IPC', icon: AlertOctagon },
    { path: '/disk-scheduling', label: 'Disk Scheduling', icon: Disc },
    { path: '/files', label: 'Multi-Drive Files', icon: FolderGit2 },
    { path: '/system', label: 'System Monitor', icon: Activity },
    { path: '/history', label: 'Command History', icon: History },
    { path: '/settings', label: 'Settings', icon: Settings },
  ];

  return (
    <aside className="w-64 bg-[#0F172A] border-r border-slate-800 flex flex-col justify-between select-none h-screen">
      <div className="flex flex-col h-full overflow-hidden">
        {/* Brand Header */}
        <div className="h-16 flex items-center px-6 border-b border-slate-800 flex-shrink-0">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-gradient-to-tr from-cyan-600 to-indigo-600 rounded-lg shadow-lg shadow-cyan-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-base text-white tracking-wider">SmartShell</h1>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
                2.0 OS Dashboard
              </span>
            </div>
          </div>
        </div>

        {/* Nav Links */}
        <nav className="p-3 space-y-1 overflow-y-auto flex-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) =>
                  `flex items-center space-x-3 px-3.5 py-2.5 rounded-lg font-medium text-xs transition-all duration-150 ${
                    isActive
                      ? 'bg-cyan-600 text-white shadow-lg shadow-cyan-600/30 font-semibold'
                      : 'text-slate-400 hover:text-white hover:bg-slate-800/60'
                  }`
                }
              >
                <Icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </NavLink>
            );
          })}
        </nav>

        {/* Footer Status */}
        <div className="p-3 border-t border-slate-800 flex-shrink-0">
          <div className="p-2.5 bg-slate-900/80 rounded-lg border border-slate-800 text-[11px] text-slate-400">
            <div className="flex items-center justify-between mb-1">
              <span>System Status</span>
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
            </div>
            <p className="text-slate-300 font-mono text-[10px]">CLI Active | v2.0.0</p>
          </div>
        </div>
      </div>
    </aside>
  );
};
