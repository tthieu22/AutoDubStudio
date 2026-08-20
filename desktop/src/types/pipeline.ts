export type PipelineStatus =
  | 'IDLE'
  | 'STARTING'
  | 'RUNNING'
  | 'CANCELLING'
  | 'CANCELLED'
  | 'COMPLETED'
  | 'FAILED'
  | 'RESUMING';

export type StageName =
  | 'EXTRACT'
  | 'TRANSCRIBE'
  | 'TRANSLATE'
  | 'TTS'
  | 'SYNC'
  | 'RENDER';

export type StageStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'COMPLETED'
  | 'SKIPPED'
  | 'FAILED'
  | 'CANCELLED';

export interface StageProgressInfo {
  status: StageStatus;
  progress: number;
  current: number;
  total: number;
  error: string | null;
}

export interface PipelineProgressEvent {
  event: string;
  stage: string;
  percent?: number;
  current?: number;
  total?: number;
  message?: string;
  error?: string;
  chunk?: number;
  total_chunks?: number;
  segment_id?: number;
  elapsed?: number;
}
