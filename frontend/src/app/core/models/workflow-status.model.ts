export interface WorkflowStatusInfo {
  workflow_id: number;
  status: string;
  isTerminal: boolean;
  started_at?: string;
  finished_at?: string;
  error?: string;
  last_heartbeat_at?: string;
  heartbeat_stale: boolean;
  message: string;
  connectionType?: string;
}

export interface WorkflowResponse {
  id: number;
  name: string;
  jira_story_id: string;
  jira_story_title: string;
  jira_story_description: string;
  status: string;
  created_at: string;
  updated_at: string;
  repository_url: string;
  target_branch: string;
  conversations: any[];
  code_files: any[];
  
  // Additional fields that may exist
  agents?: string[];
  executions?: any[];
  
  // Enhanced status fields
  isTerminal: boolean;
  started_at?: string;
  finished_at?: string;
  error?: string;
  last_heartbeat_at?: string;
  heartbeat_stale: boolean;
}

export interface WorkflowStatusUpdate {
  type: 'status_update' | 'heartbeat' | 'terminal' | 'error';
  data: WorkflowStatusInfo;
  timestamp: string;
}

export enum WorkflowStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
  ERROR = 'error'
}

export enum ConnectionType {
  WEBSOCKET = 'websocket',
  SSE = 'sse',
  POLLING = 'polling'
}

export interface StatusChannelConfig {
  workflowId: number;
  connectionType: ConnectionType;
  retryCount: number;
  maxRetries: number;
  backoffMs: number;
  maxBackoffMs: number;
}
