export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';
export type TaskStatus = 'pending' | 'approved' | 'rejected' | 'running' | 'completed' | 'failed' | 'cancelled';
export type StepStatus = 'pending' | 'running' | 'completed' | 'failed' | 'skipped';

export interface Step {
  id: string;
  step_index: number;
  description: string;
  command: string;
  shell: string;
  working_directory: string;
  depends_on: string[];
  risk_level: RiskLevel;
  requires_approval: boolean;
  status: StepStatus;
  exit_code?: number;
  stdout?: string;
  stderr?: string;
  duration_seconds?: number;
}

export interface Task {
  id: string;
  task_name: string;
  user_prompt: string;
  summary: string;
  status: TaskStatus;
  working_directory: string;
  created_at: string;
  steps: Step[];
}

export interface SystemMetrics {
  os: string;
  platform: string;
  python_version: string;
  cpu_percent: number;
  memory: {
    total_mb: number;
    available_mb: number;
    used_mb: number;
    percent: number;
  };
  disk: {
    total_gb: number;
    free_gb: number;
    percent: number;
  };
}

export interface ProcessItem {
  pid: number;
  name: string;
  cpu_percent: number;
  memory_mb: number;
  status: string;
}

export interface FileItem {
  name: string;
  path: string;
  is_dir: boolean;
  size_bytes: number;
  modified_at: number;
}

export interface DriveItem {
  device: string;
  mountpoint: string;
  drive_letter: string;
  fstype: string;
  opts: string;
  is_readable: boolean;
  total_bytes: number;
  used_bytes: number;
  free_bytes: number;
  used_percent: number;
  drive_type: string;
}

export interface DuplicateGroup {
  hash: string;
  size_bytes: number;
  count: number;
  files: { name: string; path: string }[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  category: string;
  template_json: any;
  created_at?: string;
}

export interface AppSettings {
  gemini_api_key_configured: boolean;
  gemini_api_key?: string;
  model_name: string;
  execution_timeout: number;
  auto_approve_low_risk: boolean;
  allow_all_directories?: boolean;
  ai_provider?: string;
  local_model_url?: string;
}

// OS Simulator Types
export interface ProcessInput {
  pid: string;
  arrival_time: number;
  burst_time: number;
  priority?: number;
}

export interface GanttSegment {
  pid: string;
  start_time: number;
  end_time: number;
}

export interface CPUSchedulerResult {
  processes: any[];
  gantt_chart: GanttSegment[];
  metrics: {
    avg_turnaround_time: number;
    avg_waiting_time: number;
    avg_response_time: number;
    cpu_utilization_percent: number;
    total_execution_time: number;
  };
}

export interface MemoryContiguousResult {
  strategy: string;
  blocks: any[];
  allocations: any[];
  metrics: {
    internal_fragmentation_bytes: number;
    external_fragmentation_bytes: number;
    total_memory: number;
  };
}

export interface MemoryPageReplacementResult {
  algorithm: string;
  num_frames: number;
  total_requests: number;
  page_hits: number;
  page_faults: number;
  hit_ratio_percent: number;
  fault_ratio_percent: number;
  timeline: { step: number; page: number; status: string; frames: number[] }[];
}

export interface BankersResult {
  is_safe: boolean;
  safe_sequence: string[];
  processes: string[];
  resource_types: string[];
  available: number[];
  allocation_matrix: number[][];
  max_matrix: number[][];
  need_matrix: number[][];
  explanation: string;
}

export interface DiskSchedulerResult {
  algorithm: string;
  initial_head: number;
  sequence: number[];
  moves?: { from: number; to: number; seek: number }[];
  total_seek_distance: number;
  avg_seek_distance: number;
}
