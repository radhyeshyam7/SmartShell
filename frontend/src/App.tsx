import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { MainLayout } from './layouts/MainLayout';
import { Dashboard } from './pages/Dashboard';
import { ProcessManagement } from './pages/ProcessManagement';
import { CPUScheduling } from './pages/CPUScheduling';
import { MemoryManagement } from './pages/MemoryManagement';
import { ConcurrencySync } from './pages/ConcurrencySync';
import { DeadlockIPC } from './pages/DeadlockIPC';
import { DiskScheduling } from './pages/DiskScheduling';
import { FileExplorer } from './pages/FileExplorer';
import { SystemMonitor } from './pages/SystemMonitor';
import { CommandHistory } from './pages/CommandHistory';
import { Settings } from './pages/Settings';
import { DigitalTwin } from './pages/DigitalTwin';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<MainLayout />}>
          <Route index element={<Dashboard />} />
          <Route path="digital-twin" element={<DigitalTwin />} />
          <Route path="processes" element={<ProcessManagement />} />
          <Route path="cpu-scheduling" element={<CPUScheduling />} />
          <Route path="memory-management" element={<MemoryManagement />} />
          <Route path="concurrency" element={<ConcurrencySync />} />
          <Route path="deadlock-ipc" element={<DeadlockIPC />} />
          <Route path="disk-scheduling" element={<DiskScheduling />} />
          <Route path="files" element={<FileExplorer />} />
          <Route path="system" element={<SystemMonitor />} />
          <Route path="history" element={<CommandHistory />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
};

export default App;
