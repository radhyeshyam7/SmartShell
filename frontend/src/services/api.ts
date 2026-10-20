import axios from 'axios';
import {
  Task, SystemMetrics, ProcessItem, FileItem, DriveItem, DuplicateGroup, Workflow, AppSettings,
  CPUSchedulerResult, MemoryContiguousResult, MemoryPageReplacementResult, BankersResult, DiskSchedulerResult
} from '../types';

const API_BASE = '/api';

export const api = {
  // Health
  getHealth: async () => (await axios.get(`${API_BASE}/health`)).data,

  // AI & Plan Generator
  generatePlan: async (prompt: string, workingDirectory: string = '.') => {
    return (await axios.post(`${API_BASE}/ai/plan`, { prompt, working_directory: workingDirectory })).data;
  },

  // Task Engine
  getTask: async (taskId: string): Promise<Task> => {
    return (await axios.get(`${API_BASE}/tasks/${taskId}`)).data;
  },
  approveTask: async (taskId: string) => {
    return (await axios.post(`${API_BASE}/tasks/${taskId}/approve`)).data;
  },
  rejectTask: async (taskId: string) => {
    return (await axios.post(`${API_BASE}/tasks/${taskId}/reject`)).data;
  },
  executeTask: async (taskId: string) => {
    return (await axios.post(`${API_BASE}/tasks/${taskId}/execute`)).data;
  },

  // Multi-Drive Discovery & Search
  getDrives: async (): Promise<{ drives: DriveItem[] }> => {
    return (await axios.get(`${API_BASE}/drives`)).data;
  },
  searchDrives: async (query: string, startPath: string = '.', maxResults: number = 100, minSizeMb: number = 0) => {
    return (await axios.post(`${API_BASE}/drives/search`, {
      query,
      start_path: startPath,
      max_results: maxResults,
      min_size_mb: minSizeMb
    })).data;
  },
  findDuplicates: async (path: string = '.'): Promise<{ path: string; duplicate_groups: DuplicateGroup[]; count: number }> => {
    return (await axios.get(`${API_BASE}/drives/duplicates`, { params: { path } })).data;
  },

  // System & Process Monitoring
  getMetrics: async (): Promise<SystemMetrics> => {
    return (await axios.get(`${API_BASE}/system/metrics`)).data;
  },
  getProcesses: async (limit: number = 50): Promise<ProcessItem[]> => {
    return (await axios.get(`${API_BASE}/system/processes`, { params: { limit } })).data.processes;
  },
  terminateProcess: async (pid: number) => {
    return (await axios.post(`${API_BASE}/system/processes/${pid}/terminate`)).data;
  },

  // File Explorer CRUD
  listFiles: async (path: string = '.'): Promise<{ path: string; items: FileItem[] }> => {
    return (await axios.get(`${API_BASE}/files/list`, { params: { path } })).data;
  },
  readFile: async (path: string): Promise<{ path: string; content: string }> => {
    return (await axios.get(`${API_BASE}/files/read`, { params: { path } })).data;
  },
  createFile: async (path: string, content: string = '') => {
    return (await axios.post(`${API_BASE}/files/create`, { path, content })).data;
  },
  makeDirectory: async (path: string) => {
    return (await axios.post(`${API_BASE}/files/mkdir`, { path })).data;
  },
  deleteItem: async (path: string) => {
    return (await axios.delete(`${API_BASE}/files/delete`, { data: { path } })).data;
  },

  // OS Academic Simulators
  simulateCPUScheduling: async (payload: {
    algorithm: string;
    processes: any[];
    time_quantum?: number;
    is_preemptive?: boolean;
  }): Promise<CPUSchedulerResult> => {
    return (await axios.post(`${API_BASE}/simulators/cpu-scheduling`, payload)).data;
  },

  simulateContiguousMemory: async (payload: {
    strategy: string;
    total_memory: number;
    blocks: number[];
    processes: any[];
  }): Promise<MemoryContiguousResult> => {
    return (await axios.post(`${API_BASE}/simulators/memory/contiguous`, payload)).data;
  },

  simulatePageReplacement: async (payload: {
    algorithm: string;
    num_frames: number;
    pages: number[];
  }): Promise<MemoryPageReplacementResult> => {
    return (await axios.post(`${API_BASE}/simulators/memory/page-replacement`, payload)).data;
  },

  simulateBankersAlgorithm: async (payload: {
    processes: string[];
    resource_types: string[];
    available: number[];
    max_matrix: number[][];
    allocation_matrix: number[][];
  }): Promise<BankersResult> => {
    return (await axios.post(`${API_BASE}/simulators/deadlock/bankers`, payload)).data;
  },

  simulateDiskScheduling: async (payload: {
    algorithm: string;
    requests: number[];
    initial_head: number;
    disk_size?: number;
    direction?: string;
  }): Promise<DiskSchedulerResult> => {
    return (await axios.post(`${API_BASE}/simulators/disk-scheduling`, payload)).data;
  },

  // History & Workflows
  getHistory: async (search?: string, status?: string, limit: number = 50) => {
    return (await axios.get(`${API_BASE}/history`, { params: { search, status, limit } })).data.history;
  },
  getWorkflows: async (): Promise<Workflow[]> => {
    return (await axios.get(`${API_BASE}/workflows`)).data.workflows;
  },
  createWorkflow: async (workflow: Omit<Workflow, 'id'>) => {
    return (await axios.post(`${API_BASE}/workflows`, workflow)).data;
  },

  // Settings
  getSettings: async (): Promise<AppSettings> => (await axios.get(`${API_BASE}/settings`)).data,
  updateSettings: async (settingsData: any): Promise<AppSettings> => (await axios.put(`${API_BASE}/settings`, settingsData)).data,
  testApiKey: async (apiKey?: string) => (await axios.post(`${API_BASE}/settings/test-key`, { api_key: apiKey })).data,

  // SmartShell OS Digital Twin
  getDigitalTwinState: async () => (await axios.get(`${API_BASE}/digital-twin/state`)).data,
  resetDigitalTwin: async () => (await axios.post(`${API_BASE}/digital-twin/reset`)).data,
  executeDigitalTwin: async (instruction: string) => (await axios.post(`${API_BASE}/digital-twin/execute`, { instruction })).data,
  createDigitalTwinProcess: async (payload: any) => (await axios.post(`${API_BASE}/digital-twin/process/create`, payload)).data,
  terminateDigitalTwinProcess: async (pid: string) => (await axios.post(`${API_BASE}/digital-twin/process/terminate`, { pid })).data,
  runDigitalTwinScheduler: async (payload: any) => (await axios.post(`${API_BASE}/digital-twin/schedule/run`, payload)).data,
  allocateDigitalTwinMemory: async (payload: any) => (await axios.post(`${API_BASE}/digital-twin/memory/allocate`, payload)).data,
  deallocateDigitalTwinMemory: async (pid: string) => (await axios.post(`${API_BASE}/digital-twin/memory/deallocate`, { pid })).data,
  createDigitalTwinFile: async (payload: any) => (await axios.post(`${API_BASE}/digital-twin/disk/file`, payload)).data,
  deleteDigitalTwinFile: async (path: string) => (await axios.delete(`${API_BASE}/digital-twin/disk/file`, { data: { path } })).data,
  scheduleDigitalTwinDisk: async (payload: any) => (await axios.post(`${API_BASE}/digital-twin/disk/schedule`, payload)).data,
  requestDigitalTwinResource: async (payload: any) => (await axios.post(`${API_BASE}/digital-twin/resources/request`, payload)).data,
  releaseDigitalTwinResource: async (payload: any) => (await axios.post(`${API_BASE}/digital-twin/resources/release`, payload)).data,
  checkDigitalTwinDeadlock: async () => (await axios.get(`${API_BASE}/digital-twin/deadlock/check`)).data,
  requestDigitalTwinIO: async (payload: any) => (await axios.post(`${API_BASE}/digital-twin/io/request`, payload)).data,
  tickDigitalTwinIO: async (ticks: number = 1) => (await axios.post(`${API_BASE}/digital-twin/io/tick`, { ticks })).data,
  listDigitalTwinSnapshots: async () => (await axios.get(`${API_BASE}/digital-twin/snapshots`)).data,
  createDigitalTwinSnapshot: async (label: string) => (await axios.post(`${API_BASE}/digital-twin/snapshots/create`, { label })).data,
  restoreDigitalTwinSnapshot: async (snapshot_id: string) => (await axios.post(`${API_BASE}/digital-twin/snapshots/restore`, { snapshot_id })).data,
  compareDigitalTwinAlgorithms: async (payload: any = {}) => (await axios.post(`${API_BASE}/digital-twin/compare`, payload)).data,
  verifyDigitalTwinInvariants: async () => (await axios.get(`${API_BASE}/digital-twin/verify`)).data
};

// Real-time WebSocket Event Subscriber
export const createWebSocketClient = (onEvent: (event: any) => void) => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/ws/events`;
  
  const ws = new WebSocket(wsUrl);
  
  ws.onmessage = (message) => {
    try {
      const data = JSON.parse(message.data);
      onEvent(data);
    } catch (e) {
      console.error("WS Parse error", e);
    }
  };

  return ws;
};
