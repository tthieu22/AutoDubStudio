export type PipelineMode = 'DUBBING' | 'STORY';

export type PipelineStatus =
  | 'IDLE'
  | 'STARTING'
  | 'RUNNING'
  | 'PAUSED'
  | 'REVIEW_REQUIRED'
  | 'CANCELLING'
  | 'CANCELLED'
  | 'COMPLETED'
  | 'FAILED'
  | 'RESUMING';

export type StageName =
  | 'COLLECT'
  | 'CLEAN'
  | 'ANALYZE'
  | 'MEMORY'
  | 'SCENE'
  | 'IMAGE'
  | 'EXTRACT'
  | 'TRANSCRIBE'
  | 'TRANSLATE'
  | 'TTS'
  | 'SUBTITLE'
  | 'TIMELINE'
  | 'SYNC'
  | 'RENDER'
  | 'QA'
  | 'PUBLISH';

export type StageStatus =
  | 'PENDING'
  | 'RUNNING'
  | 'REVIEW_REQUIRED'
  | 'APPROVED'
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

export interface HardwareTelemetry {
  gpu_util_percent: number;
  vram_used_gb: number;
  vram_total_gb: number;
  vram_percent: number;
  ram_used_gb: number;
  ram_total_gb: number;
  ram_percent: number;
  cpu_percent: number;
  temp_c: number;
  gpu_name: string;
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

