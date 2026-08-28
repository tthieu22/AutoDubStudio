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
    "mode": "MODE_DUBBING",
    "created_at": new Date().toISOString(),
    "updated_at": new Date().toISOString(),
    "source": { "path": "source/input.mp4", "language": "en" },
    "target": { "language": "vi" },
    "settings": {
      "whisper_model": "small",
      "whisper_compute_type": "int8",
      "translation_model": "qwen3:4b",
      "translation_batch_size": 3,
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
  },
  "story-webnovel-mang-theo-sieu-thi": {
    "version": 1,
    "project_id": "mock-uuid-story-002",
    "name": "story-webnovel-mang-theo-sieu-thi",
    "mode": "MODE_STORY",
    "created_at": new Date().toISOString(),
    "updated_at": new Date().toISOString(),
    "source": { "path": "source/chapters/001.txt", "language": "vi" },
    "target": { "language": "vi" },
    "settings": {
      "translation_model": "qwen2.5:7b-instruct",
      "translation_style": "meme",
      "tts_engine": "piper"
    },
    "pipeline": {}
  },
  "podcast-radio-ai-dubbing": {
    "version": 1,
    "project_id": "mock-uuid-audio-003",
    "name": "podcast-radio-ai-dubbing",
    "mode": "MODE_AUDIO",
    "created_at": new Date().toISOString(),
    "updated_at": new Date().toISOString(),
    "source": { "path": "source/podcast.mp3", "language": "en" },
    "target": { "language": "vi" },
    "settings": {
      "translation_style": "general",
      "tts_engine": "piper"
    },
    "pipeline": {}
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

  static async createProject(
    name: string,
    sourceVideoPath: string,
    translationStyle: string = "general",
    customTranslationStyle?: string
  ): Promise<string> {
    if (!isTauri()) {
      const sanitizedName = name.replace(/\s+/g, '-');
      const projectPath = `projects/${sanitizedName}`;
      mockProjects[projectPath] = {
        version: 1,
        project_id: Math.random().toString(36).substring(7),
        name: name,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        source: { path: sourceVideoPath, language: "zh" },
        target: { language: "vi" },
        settings: {
          whisper_model: "small",
          whisper_compute_type: "int8",
          translation_model: "qwen3:4b",
          translation_style: translationStyle,
          custom_translation_style: customTranslationStyle || null,
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
    return invoke<string>('create_project', {
      name,
      sourceVideoPath,
      translationStyle,
      customTranslationStyle: customTranslationStyle || null
    });
  }

  static async deleteProject(name: string): Promise<void> {
    const folderName = name.split('/').pop()?.split('\\').pop() || name;
    if (!isTauri()) {
      delete mockProjects[folderName];
      Object.keys(mockProjects).forEach(key => {
        if (key === folderName || key.endsWith('/' + folderName) || key.endsWith('\\' + folderName) || key.includes(folderName)) {
          delete mockProjects[key];
        }
      });
      return;
    }
    return invoke<void>('delete_project', { name: folderName });
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

  static async synthesizeSegmentVoice(projectDir: string, segmentId: number | string, text: string, voice?: string): Promise<{ success: boolean; duration?: number; audioPath?: string }> {
    if (!isTauri()) {
      return { success: true, duration: 4.0, audioPath: `audio/segments/seg_${segmentId}.wav` };
    }
    return invoke<any>('synthesize_segment_voice', { projectDir, segmentId: String(segmentId), text, voice });
  }

  static async renderFinalComposition(projectDir: string, composition: any): Promise<{ success: boolean; outputPath?: string }> {
    if (!isTauri()) {
      return { success: true, outputPath: `${projectDir}/output/final_dubbed.mp4` };
    }
    return invoke<any>('render_final_composition', { projectDir, composition });
  }

  static async readComposition(projectDir: string): Promise<any> {
    if (!isTauri()) {
      return {
        version: 1,
        width: 1920,
        height: 1080,
        fps: 30.0,
        duration: 120.0,
        layers: [
          { id: "layer-title-1", type: "title", text: "AUTO DUB STUDIO", start: 0, duration: 5, x: 700, y: 80, z_index: 2, style: { font_size: 44, color: "#facc15", border_width: 2, border_color: "#000000" }, visible: true, locked: false },
          { id: "layer-logo-1", type: "logo", text: "LOGO WATERMARK", start: 0, duration: 120, x: 1650, y: 60, z_index: 3, style: { font_size: 24, color: "#38bdf8", border_width: 1, border_color: "#000000" }, visible: true, locked: false }
        ]
      };
    }
    return invoke<any>('read_composition', { projectDir });
  }

  static async writeComposition(projectDir: string, data: any): Promise<void> {
    if (!isTauri()) {
      return;
    }
    return invoke<void>('write_composition', { projectDir, data });
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

  static async startPipeline(projectDir: string, force: boolean = false, stopAt?: string): Promise<void> {
    if (!isTauri()) {
      this.simulateMockPipeline(projectDir, stopAt);
      return;
    }
    return invoke<void>('start_pipeline', { projectDir, force, stopAt });
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

  static async resumePipeline(projectDir: string, stopAt?: string): Promise<void> {
    if (!isTauri()) {
      this.simulateMockPipeline(projectDir, stopAt);
      return;
    }
    return invoke<void>('resume_pipeline', { projectDir, stopAt });
  }

  static async retryPipeline(projectDir: string, stage: string, force: boolean = false): Promise<void> {
    if (!isTauri()) {
      this.simulateMockPipeline(projectDir);
      return;
    }
    return invoke<void>('retry_pipeline', { projectDir, stage, force });
  }

  static async discoverStoryUrl(url: string, projectDir?: string): Promise<any> {
    if (!isTauri()) {
      // Mock simulation mode for web browser sandbox
      return {
        storyUrl: url,
        pattern: `${url}/chuong-{number}`,
        patternStatus: 'VALIDATED',
        confidence: 'HIGH',
        highestChapter: 1294,
        lowestChapter: 1,
        totalCandidates: 1294,
        validatedCount: 1292,
        invalidCount: 0,
        pendingCount: 0,
        missingChapters: [4, 27],
        discoveryMethods: ['HTML_LINK', 'LOAD_MORE', 'URL_PATTERN'],
        chapters: Array.from({ length: 50 }, (_, i) => ({
          number: i + 1,
          title: `Chương ${i + 1}`,
          url: `${url}/chuong-${i + 1}`,
          discoveredBy: ['HTML_LINK', 'PATTERN'],
          status: (i + 1 === 4 || i + 1 === 27) ? 'MISSING' : 'VALID'
        }))
      };
    }
    return invoke<any>('discover_story_url', { url, projectDir: projectDir || null });
  }

  static async startStoryImport(projectDir: string, chapters: any[]): Promise<any> {
    if (!isTauri()) {
      return { status: "SUCCESS", importedCount: chapters.length };
    }
    return invoke<any>('start_story_import', { projectDir, chaptersJson: JSON.stringify(chapters) });
  }

  static subscribeDiscoveryProgress(callback: (event: any) => void) {
    if (!isTauri()) {
      return () => {};
    }
    return listen<any>('discovery://progress', (event: Event<any>) => {
      callback(event.payload);
    });
  }

  static async getOllamaModels(): Promise<string[]> {
    if (isTauri()) {
      try {
        const models = await invoke<string[]>('list_local_llm_models');
        if (models && Array.isArray(models) && models.length > 0) {
          return models;
        }
      } catch (e) {
        console.error('Failed to scan models/llm directory via Tauri IPC:', e);
      }
    }
    return ['qwen2.5-3b-instruct-q4_k_m.gguf'];
  }

  static subscribeChapterImportProgress(callback: (event: any) => void) {
    if (!isTauri()) {
      return () => {};
    }
    return listen<any>('chapter://import_progress', (event: Event<any>) => {
      callback(event.payload);
    });
  }

  // ── AI Novel Engine APIs ─────────────────────────────────────────
  static async initializeNovel(projectDir: string, storyIdea: any): Promise<any> {
    if (!isTauri()) {
      return {
        premise: `Bộ truyện ${storyIdea.title || 'Tu Tiên Vô Địch'}`,
        cultivation_system: [
          { rank: 1, name: "Luyện Khí", description: "Tích tụ linh khí" },
          { rank: 2, name: "Trúc Cơ", description: "Đúc kết Linh Đài" },
          { rank: 3, name: "Kim Đan", description: "Ngưng tụ Kim Đan" },
          { rank: 4, name: "Nguyên Anh", description: "Phá Đan thành Anh" },
          { rank: 5, name: "Hóa Thần", description: "Thần thức xuất khiếu" }
        ],
        characters: [
          { id: "char_001", name: storyIdea.protagonist?.name || "Lâm Phàm", realm: "Luyện Khí Tầng 1", location: "Thanh Vân Tông" }
        ],
        rules: ["Cảnh giới cố định", "Nhân vật không biết trước tương lai"]
      };
    }
    return invoke<any>('initialize_novel', { projectDir, storyIdeaJson: JSON.stringify(storyIdea) });
  }

  static async generateNovelMasterPlan(projectDir: string): Promise<any[]> {
    if (!isTauri()) {
      return [
        { arc_num: 1, title: "Arc 01 — Xuyên Không & Thanh Vân Tông", start_chapter: 1, end_chapter: 40, goal: "Gia nhập宗 môn", conflict: "Đối thủ ghen ghét", status: "PLANNED" },
        { arc_num: 2, title: "Arc 02 — Bí Cảnh Tinh Hà & Đột Phá Trúc Cơ", start_chapter: 41, end_chapter: 80, goal: "Đoạt Tinh Hà Quả", conflict: "Ma Tông vây phục", status: "PLANNED" },
        { arc_num: 3, title: "Arc 03 — Đại Chiến Tu Tiên Giới", start_chapter: 81, end_chapter: 150, goal: "Quyết chiến Ma Tông", conflict: "Tông môn tồn vong", status: "PLANNED" }
      ];
    }
    return invoke<any[]>('generate_novel_master_plan', { projectDir });
  }

  static async startNovelAutoWrite(projectDir: string, startChapter: number = 1, endChapter: number = 1000): Promise<void> {
    if (!isTauri()) {
      console.log(`[Web Simulation] Auto writing novel from chapter ${startChapter} to ${endChapter}`);
      return;
    }
    return invoke<void>('start_novel_auto_write', { projectDir, startChapter, endChapter });
  }

  static async getCanonFacts(projectDir: string, limit: number = 30): Promise<any[]> {
    if (!isTauri()) {
      return [
        { id: 1, chapter_num: 1, category: "realm_change", fact_text: "Lâm Phàm xuyên không đến Thanh Vân Tông, cảnh giới Luyện Khí Tầng 1", confidence: 1.0 },
        { id: 2, chapter_num: 10, category: "reveal", fact_text: "Phát hiện Thanh Vân Quả có chứa tinh linh khí cổ đại", confidence: 0.95 }
      ];
    }
    return invoke<any[]>('get_novel_canon_facts', { projectDir, limit });
  }

  static async getPlotThreads(projectDir: string): Promise<any[]> {
    if (!isTauri()) {
      return [
        { id: "thread_1", title: "Sư phụ Lý Thanh Vân mất tích", status: "OPEN", since_chapter: 5, description: "Sư phụ đi tìm linh dược bí cảnh chưa trở về" },
        { id: "thread_2", title: "Nguồn gốc thật của Hệ Thống", status: "PARTIAL", since_chapter: 15, description: "Hệ thống phát phát tín hiệu Tiên Giới" }
      ];
    }
    return invoke<any[]>('get_novel_plot_threads', { projectDir });
  }

  static async readTextFile(filePath: string): Promise<string> {
    if (!isTauri()) {
      return "";
    }
    try {
      return await invoke<string>('read_text_file', { filePath });
    } catch {
      return "";
    }
  }

  static subscribeNovelProgress(callback: (event: any) => void) {
    if (!isTauri()) {
      return () => {};
    }
    return listen<any>('novel://progress', (event: Event<any>) => {
      callback(event.payload);
    });
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

  private static async simulateMockPipeline(projectDir: string, stopAt?: string) {
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

    const completedStagesList: string[] = [];

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
      completedStagesList.push(st);
      await sleep(200);

      if (stopAt && st.toLowerCase() === stopAt.toLowerCase()) {
        break;
      }
    }

    if (!this.isPipelineSimulating) return;
    
    // Save completion state in mock storage for executed stages only
    const proj = mockProjects[projectDir] || mockProjects["vietnam-tourism-dubbed"];
    if (proj && proj.pipeline) {
      completedStagesList.forEach(st => {
        const key = st.toLowerCase();
        if (proj.pipeline[key]) {
          proj.pipeline[key].status = 'COMPLETED';
          proj.pipeline[key].progress = 100;
        }
      });
    }

    if (this.progressCallback) {
      this.progressCallback({ event: 'pipeline_complete', stage: 'PIPELINE' });
    }
    if (this.logCallback) {
      this.logCallback('[INFO] Pipeline phase completed successfully!');
    }
    if (this.terminatedCallback) {
      this.terminatedCallback(0);
    }
  }
}
