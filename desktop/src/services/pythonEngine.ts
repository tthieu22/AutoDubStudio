import { invoke } from '@tauri-apps/api/tauri';
import { listen, Event } from '@tauri-apps/api/event';
import { PipelineProgressEvent } from '../types/pipeline';

export interface PreflightResult {
  ffmpeg: boolean;
  ffprobe: boolean;
  python: boolean;
  source_video: boolean;
  disk_space: boolean;
  message: string;
}

const isTauri = () => typeof (window as any).__TAURI_IPC__ === 'function';

// Local storage mocks for web mode
const mockProjects: Record<string, any> = {
  "vietnam-tourism-dubbed": {
    "version": 1,
    "project_id": "mock-uuid-001",
    "name": "vietnam-tourism-dubbed",
    "created_at": new Date().toISOString(),
    "updated_at": new Date().toISOString(),
    "source": { "path": "source/input.mp4", "language": "en" },
    "target": { "language": "vi" },
    "settings": {
      "whisper_model": "small",
      "whisper_compute_type": "int8",
      "translation_model": "qwen2.5:3b",
      "tts_engine": "piper",
      "chunk_duration": 600
    },
    "pipeline": {
      "extract": { "status": "PENDING", "progress": 0, "current": 0, "total": 0, "error": null },
      "transcribe": { "status": "PENDING", "progress": 0, "current": 0, "total": 0, "error": null },
      "translate": { "status": "PENDING", "progress": 0, "current": 0, "total": 0, "error": null },
      "tts": { "status": "PENDING", "progress": 0, "current": 0, "total": 0, "error": null },
      "sync": { "status": "PENDING", "progress": 0, "current": 0, "total": 0, "error": null },
      "render": { "status": "PENDING", "progress": 0, "current": 0, "total": 0, "error": null }
    }
  }
};

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export class PythonEngineService {
  private static progressCallback: ((evt: PipelineProgressEvent) => void) | null = null;
  private static logCallback: ((line: string) => void) | null = null;
  private static terminatedCallback: ((code: number) => void) | null = null;
  private static isPipelineSimulating = false;

  static async runPreflight(projectDir: string): Promise<PreflightResult> {
    if (!isTauri()) {
      return {
        ffmpeg: true,
        ffprobe: true,
        python: true,
        source_video: true,
        disk_space: true,
        message: "Ready to run (Web Browser Sandbox Mode)"
      };
    }
    return invoke<PreflightResult>('run_preflight_check', { projectDir });
  }

  static async getSystemMetrics(): Promise<{ ram_usage: string; vram_usage: string }> {
    if (isTauri()) {
      try {
        return await invoke<{ ram_usage: string; vram_usage: string }>('get_system_hardware_metrics');
      } catch (e) {
        console.error(e);
      }
    }
    let heapUsedMb = "29.9 MB";
    if (typeof (performance as any)?.memory?.usedJSHeapSize === 'number') {
      heapUsedMb = (((performance as any).memory.usedJSHeapSize) / (1024 * 1024)).toFixed(1) + " MB";
    }
    return {
      ram_usage: `10.1 GB / 15.8 GB (${heapUsedMb} active)`,
      vram_usage: `0.28 GB / 4.00 GB (GeForce GTX 1650 Ti)`
    };
  }

  static async listProjects(): Promise<string[]> {
    if (!isTauri()) {
      return Object.keys(mockProjects);
    }
    return invoke<string[]>('list_projects');
  }

  static async listJobsQueue(status?: string): Promise<any[]> {
    if (!isTauri()) {
      return [];
    }
    return invoke<any[]>('list_jobs_queue', { status: status || null });
  }

  static async pauseJobQueue(jobId: string): Promise<void> {
    if (!isTauri()) {
      return;
    }
    return invoke<void>('pause_job_queue', { jobId });
  }

  static async openOutputFolder(projectDir: string): Promise<void> {
    if (!isTauri()) {
      alert(`[Mock Alert] Opening output directory at: ${projectDir}/output`);
      return;
    }
    return invoke<void>('open_output_folder', { projectDir });
  }

  static async createProject(name: string, sourceVideoPath: string): Promise<string> {
    if (!isTauri()) {
      const sanitizedName = name.replace(/\s+/g, '-');
      const projectPath = `projects/${sanitizedName}`;
      mockProjects[projectPath] = {
        version: 1,
        project_id: Math.random().toString(36).substring(7),
        name: name,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        source: { path: sourceVideoPath, language: "en" },
        target: { language: "vi" },
        settings: {
          whisper_model: "small",
          whisper_compute_type: "int8",
          translation_model: "qwen2.5:3b",
          tts_engine: "piper",
          chunk_duration: 600
        },
        pipeline: {
          extract: { status: "PENDING", progress: 0, current: 0, total: 0, error: null },
          transcribe: { status: "PENDING", progress: 0, current: 0, total: 0, error: null },
          translate: { status: "PENDING", progress: 0, current: 0, total: 0, error: null },
          tts: { status: "PENDING", progress: 0, current: 0, total: 0, error: null },
          sync: { status: "PENDING", progress: 0, current: 0, total: 0, error: null },
          render: { status: "PENDING", progress: 0, current: 0, total: 0, error: null }
        }
      };
      return projectPath;
    }
    return invoke<string>('create_project', { name, sourceVideoPath });
  }

  static async readProjectJson(projectDir: string): Promise<any> {
    if (!isTauri()) {
      return mockProjects[projectDir] || mockProjects["vietnam-tourism-dubbed"];
    }
    return invoke<any>('read_project_json', { projectDir });
  }

  static async writeProjectJson(projectDir: string, data: any): Promise<void> {
    if (!isTauri()) {
      mockProjects[projectDir] = data;
      return;
    }
    return invoke<void>('write_project_json', { projectDir, data });
  }

  static async readSubtitles(projectDir: string): Promise<any[]> {
    if (!isTauri()) {
      return [
        { id: 1, start: 0.0, end: 4.96, text: "Welcome everyone to our travel documentary.", translated_text: "Xin chào mọi người đến với thước phim tài liệu du lịch của chúng tôi.", speaker: "Speaker 1", voice: "vi_VN-vais1000-medium", speed: 1.0 },
        { id: 2, start: 6.12, end: 9.16, text: "Today we will explore the breathtaking mountains of Da Lat.", translated_text: "Hôm nay chúng ta sẽ cùng khám phá vùng núi tuyệt đẹp của Đà Lạt.", speaker: "Speaker 1", voice: "vi_VN-vais1000-medium", speed: 1.0 },
        { id: 3, start: 10.0, end: 14.2, text: "The weather is cool and refreshing all year round.", translated_text: "Thời tiết tại đây quanh năm luôn mát mẻ và trong lành.", speaker: "Speaker 2", voice: "vi_VN-vnu-medium", speed: 1.0 }
      ];
    }
    return invoke<any[]>('read_subtitles', { projectDir });
  }

  static async writeSubtitles(projectDir: string, data: any[]): Promise<void> {
    if (!isTauri()) {
      return;
    }
    return invoke<void>('write_subtitles', { projectDir, data });
  }

  static async runQcCheck(projectDir: string): Promise<any> {
    if (!isTauri()) {
      return {
        valid: true,
        total_segments: 3,
        error_count: 0,
        warning_count: 1,
        issues: [
          { severity: 'WARNING', segment_id: 2, type: 'SPEECH_EXCEEDS_WINDOW', message: 'Segment #2 TTS audio exceeds window by +0.22s', action: 'Auto Fit' }
        ],
        stats: { avg_tts_duration_ratio: 1.04, max_duration_exceeded_sec: 0.22, missing_audio_segments: 0 }
      };
    }
    return invoke<any>('run_qc_check', { projectDir });
  }

  static async applyAutofitQc(projectDir: string): Promise<any> {
    if (!isTauri()) {
      return { success: true, modified: true, total_segments: 3 };
    }
    return invoke<any>('apply_autofit_qc', { projectDir });
  }

  static async previewTtsVoice(text: string, voice: string, gender: string): Promise<any> {
    if (!isTauri()) {
      return { success: true, audio_b64: "" };
    }
    return invoke<any>('preview_tts_voice', { text, voice, gender });
  }

  static async readPipelineLog(projectDir: string, limit: number = 100): Promise<string[]> {
    if (!isTauri()) {
      return [
        "[INFO] AutoDubStudio Web Simulation Mode log sequence",
        `[INFO] Target project directory: ${projectDir}`
      ];
    }
    return invoke<string[]>('read_pipeline_log', { projectDir, limit });
  }

  static async startPipeline(projectDir: string, force: boolean = false): Promise<void> {
    if (!isTauri()) {
      this.simulateMockPipeline(projectDir);
      return;
    }
    return invoke<void>('start_pipeline', { projectDir, force });
  }

  static async cancelPipeline(): Promise<void> {
    if (!isTauri()) {
      this.isPipelineSimulating = false;
      if (this.progressCallback) {
        this.progressCallback({ event: 'pipeline_cancelled', stage: 'PIPELINE' });
      }
      if (this.logCallback) {
        this.logCallback('[WARNING] Simulation cancelled by user.');
      }
      if (this.terminatedCallback) {
        this.terminatedCallback(5);
      }
      return;
    }
    return invoke<void>('cancel_pipeline');
  }

  static async resumePipeline(projectDir: string): Promise<void> {
    if (!isTauri()) {
      this.simulateMockPipeline(projectDir);
      return;
    }
    return invoke<void>('resume_pipeline', { projectDir });
  }

  static async retryPipeline(projectDir: string, stage: string, force: boolean = false): Promise<void> {
    if (!isTauri()) {
      this.simulateMockPipeline(projectDir);
      return;
    }
    return invoke<void>('retry_pipeline', { projectDir, stage, force });
  }

  // Event listener helpers
  static subscribeProgress(callback: (event: PipelineProgressEvent) => void) {
    if (!isTauri()) {
      this.progressCallback = callback;
      return () => { this.progressCallback = null; };
    }
    return listen<PipelineProgressEvent>('pipeline://progress', (event: Event<PipelineProgressEvent>) => {
      callback(event.payload);
    });
  }

  static subscribeLog(callback: (logLine: string) => void) {
    if (!isTauri()) {
      this.logCallback = callback;
      return () => { this.logCallback = null; };
    }
    return listen<string>('pipeline://log', (event: Event<string>) => {
      callback(event.payload);
    });
  }

  static subscribeTerminated(callback: (exitCode: number) => void) {
    if (!isTauri()) {
      this.terminatedCallback = callback;
      return () => { this.terminatedCallback = null; };
    }
    return listen<number>('pipeline://terminated', (event: Event<number>) => {
      callback(event.payload);
    });
  }

  private static async simulateMockPipeline(projectDir: string) {
    this.isPipelineSimulating = true;
    
    if (this.progressCallback) {
      this.progressCallback({ event: 'pipeline_start', stage: 'PIPELINE' });
    }
    if (this.logCallback) {
      this.logCallback('[INFO] Starting video dubbing pipeline simulation...');
    }

    const stages: Array<'EXTRACT' | 'TRANSCRIBE' | 'TRANSLATE' | 'TTS' | 'SYNC' | 'RENDER'> = [
      'EXTRACT', 'TRANSCRIBE', 'TRANSLATE', 'TTS', 'SYNC', 'RENDER'
    ];

    for (const st of stages) {
      if (!this.isPipelineSimulating) return;

      if (this.progressCallback) {
        this.progressCallback({ event: 'stage_start', stage: st });
      }
      if (this.logCallback) {
        this.logCallback(`[INFO] Starting stage: ${st}`);
      }
      await sleep(400);

      for (let p = 10; p <= 100; p += 20) {
        if (!this.isPipelineSimulating) return;
        if (this.progressCallback) {
          this.progressCallback({ event: 'progress', stage: st, percent: p });
        }
        if (this.logCallback) {
          this.logCallback(`[INFO] Running ${st}: ${p}% completed...`);
        }
        await sleep(300);
      }

      if (this.progressCallback) {
        this.progressCallback({ event: 'stage_complete', stage: st });
      }
      if (this.logCallback) {
        this.logCallback(`[INFO] Completed stage: ${st}`);
      }
      await sleep(200);
    }

    if (!this.isPipelineSimulating) return;
    
    // Save completion state in mock storage
    const proj = mockProjects[projectDir] || mockProjects["vietnam-tourism-dubbed"];
    if (proj && proj.pipeline) {
      Object.keys(proj.pipeline).forEach(key => {
        proj.pipeline[key].status = 'COMPLETED';
        proj.pipeline[key].progress = 100;
      });
    }

    if (this.progressCallback) {
      this.progressCallback({ event: 'pipeline_complete', stage: 'PIPELINE' });
    }
    if (this.logCallback) {
      this.logCallback('[INFO] Translation and rendering completed successfully!');
    }
    if (this.terminatedCallback) {
      this.terminatedCallback(0);
    }
  }
}
