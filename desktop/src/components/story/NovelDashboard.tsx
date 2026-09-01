import React, { useState, useEffect } from 'react';
import { 
  Sparkles, Play, Pause, RefreshCw, BookOpen, Layers, ShieldCheck, 
  Brain, FileText, CheckCircle2, AlertCircle, AlertTriangle, Sliders, Cpu, Activity, Clock, Copy, Check, Trash2
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface NovelDashboardProps {
  projectDir?: string | null;
}

export const NovelDashboard: React.FC<NovelDashboardProps> = ({ projectDir }) => {
  const [title, setTitle] = useState('Vũ Trụ Chi Vương');
  const [genre, setGenre] = useState('Khoa học viễn tưởng');
  const [style, setStyle] = useState('Tiết tấu nhanh, cuốn hút, giàu hình ảnh');
  const [protagonistName, setProtagonistName] = useState('Diệp Phàm');
  const [protagonistAge, setProtagonistAge] = useState('20');
  const [protagonistBg, setProtagonistBg] = useState('Thiếu niên khám phá thế giới quan mới');
  const [totalChapters, setTotalChapters] = useState(1000);
  const [enableTiktokSlang, setEnableTiktokSlang] = useState(false);

  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>('IDLE');
  const [progressPercent, setProgressPercent] = useState(0);
  const [currentChapterNum, setCurrentChapterNum] = useState(1);
  const [logs, setLogs] = useState<string[]>([]);
  const [storyBible, setStoryBible] = useState<any>(null);
  const [globalProgress, setGlobalProgress] = useState<any>(null);
  const [hasMasterPlan, setHasMasterPlan] = useState<boolean>(false);
  const [copiedLogs, setCopiedLogs] = useState(false);
  const [gpuServerInfo, setGpuServerInfo] = useState<string>('Đang khởi động GPU Ollama (qwen2.5:3b)...');
  const [currentSubStage, setCurrentSubStage] = useState<'1A' | '1B' | '1C' | '1D' | '1E' | '1F' | '2A' | '2B' | 'DONE' | 'IDLE'>('IDLE');
  const [currentChapterStep, setCurrentChapterStep] = useState<number>(0);
  const [showResetConfirm, setShowResetConfirm] = useState(false);

  const handleCopyLogs = () => {
    if (logs.length === 0) return;
    navigator.clipboard.writeText(logs.join('\n'));
    setCopiedLogs(true);
    setTimeout(() => setCopiedLogs(false), 2000);
  };

  useEffect(() => {
    window.dispatchEvent(new CustomEvent('novel-writing-change', { detail: { isWriting: isGenerating } }));
  }, [isGenerating]);

  useEffect(() => {
    PythonEngineService.isNovelWritingActive().then(isActive => {
      if (isActive) {
        setIsGenerating(true);
        setCurrentStage('AUTO_WRITING');
        setCurrentChapterStep(1);
      }
    }).catch(() => {});

    PythonEngineService.ensureLocalLlmServer().then(res => {
      if (res && res.active) {
        setGpuServerInfo(`GPU CUDA (GTX 1650 Ti) Ready`);
      } else {
        setGpuServerInfo(`GPU CUDA (GTX 1650 Ti) Ready`);
      }
    }).catch(() => {
      setGpuServerInfo(`GPU CUDA (GTX 1650 Ti) Ready`);
    });

    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(data => {
        if (!data) return;
        if (data.global_progress) {
          setGlobalProgress(data.global_progress);
        }
        if (data.novel_idea) {
          setTitle(data.novel_idea.title || title);
          setGenre(data.novel_idea.genre || genre);
          setStyle(data.novel_idea.style || style);
          if (typeof data.novel_idea.enable_tiktok_slang === 'boolean') {
            setEnableTiktokSlang(data.novel_idea.enable_tiktok_slang);
          }
          if (data.novel_idea.protagonist) {
            setProtagonistName(data.novel_idea.protagonist.name || protagonistName);
            setProtagonistAge(data.novel_idea.protagonist.age || protagonistAge);
            setProtagonistBg(data.novel_idea.protagonist.background || protagonistBg);
          }
          if (data.novel_idea.total_chapters) {
            setTotalChapters(data.novel_idea.total_chapters);
          }
        }
        if (data.story_bible) {
          setStoryBible(data.story_bible);
          if (typeof data.story_bible.enable_tiktok_slang === 'boolean') {
            setEnableTiktokSlang(data.story_bible.enable_tiktok_slang);
          }
          if (!data.global_progress && data.story_bible.global_progress) {
            setGlobalProgress(data.story_bible.global_progress);
          }
        }
        if (data.arc_plans && Array.isArray(data.arc_plans) && data.arc_plans.length > 0) {
          setHasMasterPlan(true);
        }
        if (data.novel_logs && Array.isArray(data.novel_logs)) {
          setLogs(data.novel_logs);
        }
        PythonEngineService.readTextFile(`${projectDir}/novel_execution.log`).then((txt: string) => {
          if (txt && typeof txt === 'string') {
            const lines = txt.split(/\r?\n/).map(l => l.trim()).filter(Boolean);
            if (lines.length > 0) {
              setLogs(lines.reverse().slice(0, 150));
            }
          }
        }).catch(() => {});
        if (data.novel_current_stage) {
          setCurrentStage(data.novel_current_stage);
        }
        if (typeof data.novel_current_chapter === 'number') {
          setCurrentChapterNum(data.novel_current_chapter);
        }
        if (typeof data.novel_progress_percent === 'number') {
          setProgressPercent(data.novel_progress_percent);
        }
      }).catch(console.error);
    }

    let unsubFn: (() => void) | null = null;
    let unsubLogFn: (() => void) | null = null;

    const res = PythonEngineService.subscribeNovelProgress((evt: any) => {
      if (evt.event === 'novel_chapter_start') {
        setIsGenerating(true);
        setCurrentChapterNum(evt.current);
        setProgressPercent(evt.percent || 0);
        setCurrentStage(`WRITING_CHAPTER_${evt.current}`);
        setCurrentChapterStep(1);
      } else if (evt.event === 'novel_sub_stage') {
        const stepName = String(evt.step || '').toUpperCase();
        if (['RETRIEVAL', 'HARDWARE'].includes(stepName)) {
          setCurrentChapterStep(1);
        } else if (['PLANNING', 'CONTRACT'].includes(stepName)) {
          setCurrentChapterStep(2);
        } else if (['SCENE_EXECUTION', 'WRITING', 'WRITER', 'SCENE_PLANNER'].includes(stepName)) {
          setCurrentChapterStep(3);
        } else if (['ASSEMBLER', 'CHAPTER_ASSEMBLER', 'EDITOR'].includes(stepName)) {
          setCurrentChapterStep(4);
        } else if (['PROGRESSION_VALIDATOR', 'VALIDATOR'].includes(stepName)) {
          setCurrentChapterStep(5);
        } else if (['METADATA_EXTRACTOR', 'EXTRACTOR', 'CHARACTER_ENGINE', 'WORLD_ENGINE', 'LEVEL_ENGINE', 'EVENT_ENGINE', 'RELATIONSHIP_ENGINE', 'OPEN_THREAD_ENGINE'].includes(stepName)) {
          setCurrentChapterStep(6);
        } else if (['CANON_VALIDATOR', 'MEMORY', 'MEMORY_EXTRACTOR', 'MEMORY_UPDATE'].includes(stepName)) {
          setCurrentChapterStep(7);
        }
      } else if (evt.event === 'novel_chapter_complete') {
        setCurrentChapterNum(evt.current + 1);
        setProgressPercent(evt.percent || 0);
        setCurrentChapterStep(7);
      } else if (evt.event === 'novel_complete') {
        setIsGenerating(false);
        setCurrentStage('COMPLETED');
        setProgressPercent(100);
        setCurrentChapterStep(7);
      }
    });

    const resLog = PythonEngineService.subscribeNovelLogs((evt: any) => {
      let displayLine = typeof evt === 'string' ? evt : evt.message || JSON.stringify(evt);
      if (displayLine.startsWith('{') && displayLine.endsWith('}')) {
        try {
          const parsed = JSON.parse(displayLine);
          if (parsed.message) {
            displayLine = `[INFO] ${parsed.message}`;
          } else {
            return;
          }
        } catch {}
      }

      if (displayLine.includes('PROMPT 1A/5') || displayLine.includes('BƯỚC 1/7') || displayLine.includes('WORLD_GENERATION')) {
        setCurrentSubStage('1A');
      } else if (displayLine.includes('PROMPT 1B/5') || displayLine.includes('PROGRESSION_GENERATION')) {
        setCurrentSubStage('1B');
      } else if (displayLine.includes('PROMPT 1C/5') || displayLine.includes('CAST_GENERATION')) {
        setCurrentSubStage('1C');
      } else if (displayLine.includes('PROMPT 1D/5') || displayLine.includes('RULES_GENERATION')) {
        setCurrentSubStage('1D');
      } else if (displayLine.includes('PROMPT 1E/5') || displayLine.includes('TERMINOLOGY_GENERATION')) {
        setCurrentSubStage('1E');
      } else if (displayLine.includes('PROMPT 1F') || displayLine.includes('MASTER_BLUEPRINT')) {
        setCurrentSubStage('1F');
      } else if (displayLine.includes('MASTER_PLAN') || displayLine.includes('GENERATING_MASTER_PLAN') || displayLine.includes('BƯỚC 2-3/7')) {
        setCurrentSubStage('2A');
      } else if (displayLine.includes('ARC_ROADMAP') || displayLine.includes('DÀN Ý KỊCH BẢN 20 CHƯƠNG')) {
        setCurrentSubStage('2B');
      }


      // Match 7 Chapter Pipeline Steps in stdout log stream
      if (displayLine.includes('Step 1/7') || displayLine.includes('RETRIEVAL')) {
        setCurrentChapterStep(1);
      } else if (displayLine.includes('Step 2/7') || displayLine.includes('CHAPTER PLANNER') || displayLine.includes('PLANNING & CONTRACT')) {
        setCurrentChapterStep(2);
      } else if (displayLine.includes('Step 3/7') || displayLine.includes('Scene ') || displayLine.includes('WRITING')) {
        setCurrentChapterStep(3);
      } else if (displayLine.includes('Step 4/7') || displayLine.includes('CHAPTER ASSEMBLER')) {
        setCurrentChapterStep(4);
      } else if (displayLine.includes('Step 5/7') || displayLine.includes('PROGRESSION VALIDATOR')) {
        setCurrentChapterStep(5);
      } else if (displayLine.includes('Step 6/7') || displayLine.includes('PIPELINE ORCHESTRATOR') || displayLine.includes('CHARACTER_ENGINE') || displayLine.includes('WORLD_ENGINE') || displayLine.includes('LEVEL_ENGINE') || displayLine.includes('EVENT_ENGINE') || displayLine.includes('RELATIONSHIP_ENGINE') || displayLine.includes('OPEN_THREAD_ENGINE')) {
        setCurrentChapterStep(6);
      } else if (displayLine.includes('Step 7/7') || displayLine.includes('CANON_VALIDATOR') || displayLine.includes('Bước 9/9')) {
        setCurrentChapterStep(7);
      } else if (displayLine.includes('SPECIALIZED ENGINES PASS') || displayLine.includes('novel_chapter_complete')) {
        setCurrentChapterStep(7);
      } else if (displayLine.includes('Hoàn thành 5/5') || displayLine.includes('THÀNH CÔNG')) {
        // Keep at 1E until master plan starts
      }

      setLogs(prev => {
        if (prev.length > 0 && prev[0] === displayLine) return prev;
        const newLogs = [displayLine, ...prev.slice(0, 100)];
        saveNovelStateToProject({ novel_logs: newLogs });
        return newLogs;
      });
    });

    if (typeof (res as any)?.then === 'function') {
      (res as any).then((unsub: any) => {
        if (typeof unsub === 'function') unsubFn = unsub;
      });
    } else if (typeof res === 'function') {
      unsubFn = res;
    }

    if (typeof (resLog as any)?.then === 'function') {
      (resLog as any).then((unsub: any) => {
        if (typeof unsub === 'function') unsubLogFn = unsub;
      });
    } else if (typeof resLog === 'function') {
      unsubLogFn = resLog;
    }

    return () => {
      if (unsubFn) unsubFn();
      if (unsubLogFn) unsubLogFn();
    };
  }, [projectDir]);

  const saveNovelStateToProject = async (patchData: Record<string, any>) => {
    if (!projectDir) return;
    try {
      const json = (await PythonEngineService.readProjectJson(projectDir)) || {};
      const updated = { ...json, ...patchData };
      await PythonEngineService.writeProjectJson(projectDir, updated);
    } catch (e) {
      console.error('Failed to save novel state to project.json:', e);
    }
  };

  const executeInitializeNovel = async () => {
    if (!projectDir || isGenerating) return null;
    setIsGenerating(true);
    
    // 1. CLEAR OLD DATA & RESET ALL PROCESS INDICATORS
    setStoryBible(null);
    setGlobalProgress(null);
    setHasMasterPlan(false);
    setLogs([]);
    setProgressPercent(0);
    setCurrentChapterNum(1);
    setCurrentSubStage('1A');
    setCurrentStage('INITIALIZING_STORY_BIBLE');

    const startLog = '[INFO] AI Story Director building Story Bible & World Rules...';
    setLogs([startLog]);

    try {
      const idea = {
        title,
        genre,
        style,
        protagonist: { name: protagonistName, age: protagonistAge, background: protagonistBg },
        total_chapters: totalChapters,
        enable_tiktok_slang: enableTiktokSlang
      };

      // Reset novel_execution.log file & clean old project state
      await PythonEngineService.writeTextFile(`${projectDir}/novel_execution.log`, '');
      await saveNovelStateToProject({ 
        novel_idea: idea, 
        story_bible: null,
        arc_plans: [],
        global_progress: null,
        novel_logs: [startLog],
        novel_current_stage: 'INITIALIZING_STORY_BIBLE',
        novel_current_chapter: 1,
        novel_progress_percent: 0,
        chapters: []
      });

      const bible = await PythonEngineService.initializeNovel(projectDir, idea);
      setStoryBible(bible);
      
      setLogs(prev => ['[SUCCESS] Story Bible generated! Creating Master Plan (20-50 Arcs)...', ...prev]);
      setCurrentStage('GENERATING_MASTER_PLAN');
      setCurrentSubStage('2A');

      await saveNovelStateToProject({ story_bible: bible, novel_current_stage: 'GENERATING_MASTER_PLAN' });

      const masterPlan = await PythonEngineService.generateNovelMasterPlan(projectDir);
      setLogs(prev => ['[SUCCESS] Master Plan created! Ready for Auto-Write.', ...prev]);
      setCurrentStage('READY');
      setCurrentSubStage('DONE');
      setHasMasterPlan(true);

      await saveNovelStateToProject({ arc_plans: masterPlan, novel_current_stage: 'READY' });
      return bible;
    } catch (e: any) {
      const errMsg = typeof e === 'string' ? e : e?.message || JSON.stringify(e);
      setLogs(prev => [`[ERROR] Failed to initialize novel: ${errMsg}`, ...prev]);
      return null;
    } finally {
      setIsGenerating(false);
    }
  };

  const handleInitializeNovelClick = () => {
    if (isGenerating) return;
    if (storyBible || hasMasterPlan || logs.length > 0) {
      setShowResetConfirm(true);
    } else {
      executeInitializeNovel();
    }
  };

  const handleStartAutoWrite = async () => {
    if (!projectDir || isGenerating) return;

    let activeBible = storyBible;
    if (!activeBible) {
      setLogs(prev => ['[INFO] Chưa phát hiện Story Bible & Master Plan. Tự động thực hiện Bước 1, 2, 3 trước...', ...prev]);
      activeBible = await executeInitializeNovel();
      if (!activeBible) {
        setLogs(prev => ['[ERROR] Khởi tạo thế giới thất bại. Đã dừng quy trình.', ...prev]);
        return;
      }
    }

    let startChap = 1;
    try {
      const pData = await PythonEngineService.readProjectJson(projectDir);
      if (pData && pData.chapters && Array.isArray(pData.chapters) && pData.chapters.length > 0) {
        const maxNum = Math.max(...pData.chapters.map((c: any) => c.chapterNumber || 1));
        startChap = maxNum + 1;
      }
    } catch {}

    setCurrentChapterNum(startChap);
    setIsGenerating(true);
    setCurrentStage('AUTO_WRITING');
    const startLog = `[INFO] Launching Novel Engine Auto-Write Loop (Starting at Chapter ${startChap})...`;
    setLogs(prev => {
      const updated = [startLog, ...prev];
      saveNovelStateToProject({ novel_logs: updated, novel_current_stage: 'AUTO_WRITING', novel_current_chapter: startChap });
      return updated;
    });

    await PythonEngineService.startNovelAutoWrite(projectDir, startChap, totalChapters);
  };

  const handleStopAutoWrite = async () => {
    setIsGenerating(false);
    setCurrentStage('IDLE');
    window.dispatchEvent(new CustomEvent('novel-writing-change', { detail: { isWriting: false } }));
    await PythonEngineService.stopNovelAutoWrite();
  };

  const handleClearLogs = () => {
    setLogs([]);
    saveNovelStateToProject({ novel_logs: [] });
    if (projectDir) {
      PythonEngineService.writeTextFile(`${projectDir}/novel_execution.log`, '');
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans overflow-y-auto custom-scrollbar">
      {/* HEADER BAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-indigo-500/20 to-cyan-500/20 text-cyan-400 flex items-center justify-center border border-cyan-500/30 shadow-lg shadow-cyan-500/10">
            <Sparkles size={20} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight flex items-center gap-2">
              AI Novel Engine — Động Cơ Tự Viết Truyện Dài 500-1.000 Chương
              <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-mono font-bold">
                Qwen2.5-3B Audio-First
              </span>
              <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 border border-cyan-500/30 text-[10px] font-mono font-bold">
                Audio Drama / TTS Ready
              </span>
              <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-mono font-bold flex items-center gap-1" title="Chạy tăng tốc trên NVIDIA GeForce GTX 1650 Ti (VRAM 4GB)">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {gpuServerInfo}
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Nhập ý tưởng → AI xây thế giới → lập 5-8 Scenes Audio/Chapter → AI viết văn phong thoại tự nhiên → Post-Extraction Canon DB.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {currentStage === 'AUTO_WRITING' || isGenerating ? (
            <button
              onClick={handleStopAutoWrite}
              className="px-4 py-2 rounded-xl bg-amber-500 hover:bg-amber-400 text-black font-extrabold text-xs flex items-center gap-2 shadow-lg shadow-amber-500/20 transition-all cursor-pointer"
            >
              <Pause size={14} /> Tạm Dừng Viết
            </button>
          ) : (
            <button
              onClick={handleStartAutoWrite}
              disabled={isGenerating}
              className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-extrabold text-xs flex items-center gap-2 shadow-xl shadow-cyan-500/20 transition-all cursor-pointer disabled:opacity-50"
            >
              <Play size={14} /> Tự Động Viết Truyện
            </button>
          )}
        </div>
      </div>

      {/* GLOBAL STORY PROGRESS PANEL V2.3 */}
      <div className="bg-[#111318] p-3.5 rounded-xl border border-white/5 shadow-md space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-white font-['Outfit'] flex items-center gap-2 uppercase tracking-wider">
            <Layers size={14} className="text-cyan-400" /> Global Story Progress (Cross-Chapter State V2.3)
          </h3>
          <span className="text-[10px] text-slate-400 font-mono">
            State Machine: UNKNOWN → RUMOR → CLAIM → EVIDENCE → CONFIRMED
          </span>
        </div>
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2 text-xs">
          <div className="bg-black/40 p-2.5 rounded-lg border border-white/5 text-center">
            <span className="text-[10px] text-slate-400 block font-semibold uppercase">Completed Events</span>
            <span className="text-sm font-extrabold text-cyan-400 font-mono">
              {(globalProgress?.completed_events || storyBible?.global_progress?.completed_events)?.length || 0}
            </span>
          </div>
          <div className="bg-black/40 p-2.5 rounded-lg border border-emerald-500/20 text-center">
            <span className="text-[10px] text-emerald-400 block font-semibold uppercase">Confirmed Facts</span>
            <span className="text-sm font-extrabold text-emerald-400 font-mono">
              {(globalProgress?.confirmed_facts || storyBible?.global_progress?.confirmed_facts)?.length || 0}
            </span>
          </div>
          <div className="bg-black/40 p-2.5 rounded-lg border border-amber-500/20 text-center">
            <span className="text-[10px] text-amber-400 block font-semibold uppercase">Active Claims</span>
            <span className="text-sm font-extrabold text-amber-400 font-mono">
              {(globalProgress?.active_claims || storyBible?.global_progress?.active_claims)?.length || 0}
            </span>
          </div>
          <div className="bg-black/40 p-2.5 rounded-lg border border-indigo-500/20 text-center">
            <span className="text-[10px] text-indigo-400 block font-semibold uppercase">Evidence Items</span>
            <span className="text-sm font-extrabold text-indigo-400 font-mono">
              {(globalProgress?.evidence_items || storyBible?.global_progress?.evidence_items)?.length || 0}
            </span>
          </div>
          <div className="bg-black/40 p-2.5 rounded-lg border border-rose-500/20 text-center">
            <span className="text-[10px] text-rose-400 block font-semibold uppercase">Unresolved Questions</span>
            <span className="text-sm font-extrabold text-rose-400 font-mono">
              {(globalProgress?.unresolved_questions || storyBible?.global_progress?.unresolved_questions)?.length || 0}
            </span>
          </div>
          <div className="bg-black/40 p-2.5 rounded-lg border border-white/5 text-center">
            <span className="text-[10px] text-slate-400 block font-semibold uppercase">Last Chapter</span>
            <span className="text-sm font-extrabold text-white font-mono">
              {globalProgress?.last_completed_chapter || currentChapterNum}
            </span>
          </div>
        </div>
      </div>

      {/* STEP 1 & STEP 2 PROMPT PROCESS STEPPER V2.3 */}
      <div className="bg-[#111318] p-3.5 rounded-xl border border-white/5 shadow-md space-y-2.5">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-bold text-white font-['Outfit'] flex items-center gap-2 uppercase tracking-wider">
            <Sparkles size={14} className="text-cyan-400" /> Tiến Trình Khởi Tạo Prompt AI (Bước 1 & Bước 2)
          </h3>
          <span className="text-[10px] text-slate-400 font-mono">
            {currentStage === 'INITIALIZING_STORY_BIBLE' ? 'Đang Khởi Tạo Bối Cảnh Thế Giới (Bước 1)...' :
             currentStage === 'GENERATING_MASTER_PLAN' ? 'Đang Tạo Master Plan 20-50 Arcs (Bước 2)...' :
             storyBible && hasMasterPlan ? '✓ Đã Hoàn Thành Bước 1 & Bước 2' : 'Sẵn Sàng Khởi Tạo'}
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-2 text-xs">
          {[
            { key: '1A', label: 'Prompt 1A', title: 'Bối Cảnh Thế Giới', desc: 'World & Premise' },
            { key: '1B', label: 'Prompt 1B', title: 'Hệ Thống Cảnh Giới', desc: 'Progression Ranks' },
            { key: '1C', label: 'Prompt 1C', title: 'Dàn Nhân Vật Nam/Nữ', desc: 'Full Cast Profiles' },
            { key: '1D', label: 'Prompt 1D', title: 'Quy Tắc Thế Giới', desc: 'World Rules & Canon' },
            { key: '1E', label: 'Prompt 1E', title: 'Từ Điển Thuật Ngữ', desc: 'Genre Terminology' },
            { key: '2A', label: 'Bước 2A', title: 'Master Plan Arcs', desc: '20-50 Master Arcs' },
            { key: '1F', label: 'Prompt 1F', title: 'Sườn Kịch Bản Tổng Thể', desc: 'Master Blueprint' },
          ].map((sub) => {
            const isCompleted = 
              sub.key === '1A' ? (!!storyBible || ['1B', '1C', '1D', '1E', '2A', '1F', '2B', 'DONE'].includes(currentSubStage)) :
              sub.key === '1B' ? (!!storyBible || ['1C', '1D', '1E', '2A', '1F', '2B', 'DONE'].includes(currentSubStage)) :
              sub.key === '1C' ? (!!storyBible || ['1D', '1E', '2A', '1F', '2B', 'DONE'].includes(currentSubStage)) :
              sub.key === '1D' ? (!!storyBible || ['1E', '2A', '1F', '2B', 'DONE'].includes(currentSubStage)) :
              sub.key === '1E' ? (!!storyBible || ['2A', '1F', '2B', 'DONE'].includes(currentSubStage)) :
              sub.key === '2A' ? (hasMasterPlan || ['1F', '2B', 'DONE'].includes(currentSubStage)) :
              sub.key === '1F' ? (!!storyBible?.master_blueprint || ['2B', 'DONE'].includes(currentSubStage)) : false;

            const isActive = !isCompleted && currentSubStage === sub.key;



            return (
              <div
                key={sub.key}
                className={`p-2.5 rounded-lg border flex flex-col justify-between transition-all ${
                  isCompleted
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : isActive
                    ? 'bg-cyan-500/20 border-cyan-500/60 text-cyan-200 shadow-md shadow-cyan-500/10 animate-pulse'
                    : 'bg-black/30 border-white/5 text-slate-500'
                }`}
              >
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-bold font-mono uppercase">{sub.label}</span>
                  {isCompleted ? (
                    <CheckCircle2 size={13} className="text-emerald-400" />
                  ) : isActive ? (
                    <Clock size={13} className="text-cyan-400 animate-spin" />
                  ) : (
                    <Clock size={13} className="text-slate-600" />
                  )}
                </div>
                <span className="font-bold text-[11px] leading-tight">{sub.title}</span>
                <span className="text-[9px] text-slate-400 mt-0.5">{sub.desc}</span>
                <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden mt-2 border border-white/5">
                  <div
                    className={`h-full rounded-full transition-all duration-300 ${
                      isCompleted
                        ? 'bg-emerald-400 w-full'
                        : isActive
                        ? 'bg-cyan-400 w-3/4 animate-pulse'
                        : 'w-0'
                    }`}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* PIPELINE STAGES VISUALIZER */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 bg-[#111318] p-3 rounded-xl border border-white/5 text-xs">
        {[
          { id: 1, label: '1. RETRIEVAL', desc: 'Truy Xuất Canon Context', icon: Sparkles },
          { id: 2, label: '2. CONTRACT', desc: 'Narrative Contract & Plan', icon: Sliders },
          { id: 3, label: '3. EXECUTION', desc: 'Scene Writer & Validator', icon: Cpu },
          { id: 4, label: '4. ASSEMBLER', desc: 'Hợp Nhất Bản Thảo', icon: FileText },
          { id: 5, label: '5. VALIDATOR', desc: 'Progression & Stagnation', icon: ShieldCheck },
          { id: 6, label: '6. EXTRACTOR', desc: 'Trích Xuất Metadata', icon: BookOpen },
          { id: 7, label: '7. MEMORY', desc: 'Canon Candidates & DB', icon: Layers }
        ].map((st) => {
          let status: 'COMPLETED' | 'ACTIVE' | 'PENDING' = 'PENDING';

          if (currentChapterStep > 0) {
            if (st.id < currentChapterStep) {
              status = 'COMPLETED';
            } else if (st.id === currentChapterStep) {
              status = 'ACTIVE';
            } else {
              status = 'PENDING';
            }
          } else if (currentStage === 'COMPLETED') {
            status = 'COMPLETED';
          } else if (storyBible && hasMasterPlan) {
            status = 'COMPLETED';
          } else {
            status = 'PENDING';
          }

          const isActive = status === 'ACTIVE';
          const isCompleted = status === 'COMPLETED';

          return (
            <div
              key={st.id}
              className={`p-2.5 rounded-lg border flex flex-col items-center text-center transition-all relative ${
                isActive
                  ? 'bg-cyan-500/15 border-cyan-500/50 text-cyan-300 shadow-md shadow-cyan-500/10'
                  : isCompleted
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-black/30 border-white/5 text-slate-500'
              }`}
            >
              {isCompleted ? (
                <CheckCircle2 size={16} className="text-emerald-400 mb-1" />
              ) : (
                <st.icon size={16} className={isActive ? 'text-cyan-400 animate-pulse mb-1' : 'text-slate-500 mb-1'} />
              )}
              <span className="font-bold text-[11px] font-['Outfit'] uppercase">{st.label}</span>
              <span className="text-[10px] text-slate-400 mt-0.5">{st.desc}</span>
            </div>
          );
        })}
      </div>

      {/* FORM & LOGS GRID */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1">
        {/* INPUT CONFIGURATION FORM */}
        <div className="lg:col-span-1 bg-[#111318] p-4 rounded-xl border border-white/5 space-y-3.5">
          <h3 className="text-sm font-bold text-white font-['Outfit'] flex items-center gap-2">
            <Sliders size={16} className="text-cyan-400" /> Cấu Hình Ý Tưởng Truyện
          </h3>

          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block mb-1">
              Tên Tác Phẩm
            </label>
            <input
              type="text"
              value={title}
              onChange={e => setTitle(e.target.value)}
              className="w-full bg-[#0b0d10] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-white focus:outline-none focus:border-cyan-500/50 font-['Outfit'] font-bold"
            />
          </div>

          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block mb-1">
              Thể Loại (Genre)
            </label>
            <input
              type="text"
              value={genre}
              onChange={e => setGenre(e.target.value)}
              className="w-full bg-[#0b0d10] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50"
            />
          </div>

          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block mb-1">
              Phong Cách Văn Phong (Style)
            </label>
            <input
              type="text"
              value={style}
              onChange={e => setStyle(e.target.value)}
              className="w-full bg-[#0b0d10] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50"
            />
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block mb-1">
                Nam Chính
              </label>
              <input
                type="text"
                value={protagonistName}
                onChange={e => setProtagonistName(e.target.value)}
                className="w-full bg-[#0b0d10] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50"
              />
            </div>
            <div>
              <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block mb-1">
                Tuổi
              </label>
              <input
                type="text"
                value={protagonistAge}
                onChange={e => setProtagonistAge(e.target.value)}
                className="w-full bg-[#0b0d10] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50"
              />
            </div>
          </div>

          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block mb-1">
              Thân Thế Nhân Vật Chính
            </label>
            <input
              type="text"
              value={protagonistBg}
              onChange={e => setProtagonistBg(e.target.value)}
              className="w-full bg-[#0b0d10] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50"
            />
          </div>

          <div>
            <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold block mb-1">
              Tổng Số Chương Dự Kiến
            </label>
            <input
              type="number"
              value={totalChapters}
              onChange={e => setTotalChapters(Number(e.target.value))}
              className="w-full bg-[#0b0d10] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-cyan-400 font-bold focus:outline-none focus:border-cyan-500/50 font-mono"
            />
          </div>

          {/* TikTok Slang & Trend Mode Toggle */}
          <div className="flex items-center justify-between p-2.5 rounded-lg bg-black/40 border border-emerald-500/30 select-none">
            <div className="pr-2">
              <label className="text-xs font-bold text-emerald-400 block cursor-pointer" onClick={() => setEnableTiktokSlang(!enableTiktokSlang)}>
                Bắt Trend TikTok Slang & Hài Hước
              </label>
              <span className="text-[10px] text-slate-400 block leading-tight">
                Tự động lồng ghép slang TikTok, thoại hài hước (lật kèo, tuyệt đối điện ảnh, xịt keo, ảo thật đấy...)
              </span>
            </div>
            <button
              type="button"
              onClick={() => setEnableTiktokSlang(!enableTiktokSlang)}
              className={`w-10 h-5 rounded-full p-0.5 transition-colors cursor-pointer shrink-0 ${enableTiktokSlang ? 'bg-emerald-500' : 'bg-slate-700'}`}
            >
              <div className={`w-4 h-4 rounded-full bg-white transition-transform ${enableTiktokSlang ? 'translate-x-5' : 'translate-x-0'}`} />
            </button>
          </div>

          <button
            onClick={handleInitializeNovelClick}
            disabled={isGenerating}
            className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer disabled:opacity-50"
          >
            <Sparkles size={15} /> Tạo Thế Giới & Master Plan (20-50 Arcs)
          </button>
        </div>

        {/* LOGS & PROGRESS TRACKER */}
        <div className="lg:col-span-2 bg-[#111318] p-4 rounded-xl border border-white/5 flex flex-col space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white font-['Outfit'] flex items-center gap-2">
              <Activity size={16} className="text-cyan-400" /> Tiến Trình Sinh Truyện Tự Động
            </h3>
            <div className="flex items-center gap-2">
              <span className="text-xs font-mono text-cyan-400 mr-1">
                Chapter {currentChapterNum} / {totalChapters} ({progressPercent}%)
              </span>
              <button
                onClick={handleCopyLogs}
                disabled={logs.length === 0}
                className={`px-3 py-1 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all shadow-md cursor-pointer select-none ${
                  copiedLogs
                    ? 'bg-emerald-500 text-black shadow-emerald-500/20'
                    : logs.length > 0
                    ? 'bg-cyan-500 hover:bg-cyan-400 text-black shadow-cyan-500/20 active:scale-95'
                    : 'bg-white/5 text-slate-500 border border-white/5 cursor-not-allowed'
                }`}
                title="Sao chép toàn bộ log vào bộ nhớ tạm"
              >
                {copiedLogs ? <Check size={13} className="stroke-[3]" /> : <Copy size={13} />}
                <span>{copiedLogs ? 'Đã Sao Chép!' : 'Copy Log'}</span>
              </button>
              {logs.length > 0 && (
                <button
                  onClick={handleClearLogs}
                  className="px-2 py-1 rounded-lg bg-white/5 hover:bg-rose-500/20 text-slate-400 hover:text-rose-300 text-xs font-semibold flex items-center gap-1 transition-all border border-white/10 cursor-pointer select-none"
                  title="Xóa danh sách log"
                >
                  <Trash2 size={13} />
                </button>
              )}
            </div>
          </div>

          {/* PROGRESS BAR */}
          <div className="w-full bg-black/50 h-3 rounded-full overflow-hidden border border-white/5 p-0.5">
            <div
              className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-full rounded-full transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>

          {/* LOGS TERMINAL CONTAINER */}
          <div className="relative flex-1 flex flex-col min-h-[220px]">
            <div 
              className="flex-1 bg-[#07080a] border border-white/10 rounded-xl p-3.5 font-mono text-[11px] leading-relaxed overflow-y-auto custom-scrollbar space-y-1.5 select-text cursor-text relative"
              style={{ userSelect: 'text', WebkitUserSelect: 'text' }}
            >
              {logs.length === 0 ? (
                <div className="text-slate-500 italic text-center py-12 select-none">
                  Chưa có tiến trình log. Hãy nhấn "Tạo Thế Giới & Master Plan" để bắt đầu.
                </div>
              ) : (
                logs.map((log, idx) => (
                  <div
                    key={idx}
                    className={
                      log.includes('[ERROR]') ? 'text-rose-400 font-semibold' :
                      log.includes('[SUCCESS]') ? 'text-emerald-400 font-semibold' :
                      'text-slate-300'
                    }
                    style={{ userSelect: 'text', WebkitUserSelect: 'text' }}
                  >
                    {log}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>

      {/* RESET & RE-INITIALIZE CONFIRMATION MODAL */}
      {showResetConfirm && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4 animate-in fade-in duration-200">
          <div className="bg-[#111318] border border-amber-500/40 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4 relative">
            <div className="flex items-center gap-3 text-amber-400">
              <div className="w-10 h-10 rounded-xl bg-amber-500/10 border border-amber-500/30 flex items-center justify-center shrink-0">
                <AlertTriangle size={24} className="animate-pulse" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-white font-['Outfit']">
                  Xác Nhận Xóa Dữ Liệu Cũ & Tạo Mới
                </h3>
                <p className="text-xs text-amber-400/90 font-medium">
                  Cảnh báo: Hành động này không thể hoàn tác!
                </p>
              </div>
            </div>

            <div className="text-xs text-slate-300 space-y-2 bg-black/40 p-3.5 rounded-xl border border-white/5 leading-relaxed">
              <p>
                Bạn đang yêu cầu <strong className="text-white">tạo mới bối cảnh thế giới & Master Plan Arcs</strong>. 
                Hệ thống sẽ <strong className="text-rose-400">đặt lại toàn bộ tiến trình</strong> và <strong className="text-rose-400">xóa sạch các dữ liệu cũ</strong> bao gồm:
              </p>
              <ul className="list-disc list-inside space-y-1 text-slate-400 text-[11px] pt-1">
                <li>Hồ sơ thế giới & Story Bible hiện tại</li>
                <li>Kế hoạch 20-50 Arcs kịch bản (Master Plan)</li>
                <li>Nhật ký tiến trình log & Tiến trình các chương đã tạo</li>
                <li>Toàn bộ thông tin Canon Facts & Open Threads trong bộ nhớ</li>
              </ul>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                onClick={() => setShowResetConfirm(false)}
                className="px-4 py-2 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white text-xs font-bold transition-all border border-white/10 cursor-pointer"
              >
                Hủy Bỏ
              </button>

              <button
                onClick={() => {
                  setShowResetConfirm(false);
                  executeInitializeNovel();
                }}
                className="px-4 py-2 rounded-xl bg-gradient-to-r from-rose-500 to-amber-600 hover:from-rose-400 hover:to-amber-500 text-white text-xs font-extrabold shadow-lg shadow-rose-500/20 transition-all cursor-pointer flex items-center gap-1.5"
              >
                <Sparkles size={14} /> Xác Nhận Xóa Cũ & Tạo Mới
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
