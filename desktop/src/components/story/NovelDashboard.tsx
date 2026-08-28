import React, { useState, useEffect } from 'react';
import { 
  Sparkles, Play, Pause, RefreshCw, BookOpen, Layers, ShieldCheck, 
  Brain, FileText, CheckCircle2, AlertCircle, Sliders, Cpu, Activity, Clock, Copy, Check, Trash2
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface NovelDashboardProps {
  projectDir?: string | null;
}

export const NovelDashboard: React.FC<NovelDashboardProps> = ({ projectDir }) => {
  const [title, setTitle] = useState('Vô Địch Hệ Thống Tiên Đế');
  const [genre, setGenre] = useState('Tiên hiệp + Xuyên không + Hệ thống');
  const [style, setStyle] = useState('Dễ đọc, tiết tấu nhanh, nhiều đối thoại');
  const [protagonistName, setProtagonistName] = useState('Lâm Phàm');
  const [protagonistAge, setProtagonistAge] = useState('20');
  const [protagonistBg, setProtagonistBg] = useState('Hiện đại xuyên không');
  const [totalChapters, setTotalChapters] = useState(1000);

  const [isGenerating, setIsGenerating] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>('IDLE');
  const [progressPercent, setProgressPercent] = useState(0);
  const [currentChapterNum, setCurrentChapterNum] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [storyBible, setStoryBible] = useState<any>(null);
  const [copiedLogs, setCopiedLogs] = useState(false);

  const handleCopyLogs = () => {
    if (logs.length === 0) return;
    navigator.clipboard.writeText(logs.join('\n'));
    setCopiedLogs(true);
    setTimeout(() => setCopiedLogs(false), 2000);
  };

  useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(data => {
        if (!data) return;
        if (data.novel_idea) {
          setTitle(data.novel_idea.title || title);
          setGenre(data.novel_idea.genre || genre);
          setStyle(data.novel_idea.style || style);
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
          setCurrentStage(prev => prev === 'IDLE' ? 'READY' : prev);
        }
        if (data.novel_logs && Array.isArray(data.novel_logs)) {
          setLogs(data.novel_logs);
        }
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
        setCurrentChapterNum(evt.current);
        setProgressPercent(evt.percent || 0);
        setCurrentStage(`WRITING_CHAPTER_${evt.current}`);
        setLogs(prev => {
          const newLogs = [`[INFO] Starting Chapter ${evt.current} generation pipeline...`, ...prev.slice(0, 100)];
          saveNovelStateToProject({ novel_logs: newLogs, novel_current_chapter: evt.current, novel_progress_percent: evt.percent || 0, novel_current_stage: `WRITING_CHAPTER_${evt.current}` });
          return newLogs;
        });
      } else if (evt.event === 'novel_sub_stage') {
        setCurrentStage(evt.step || 'WRITING');
        setLogs(prev => {
          const newLogs = [`[INFO] ${evt.message}`, ...prev.slice(0, 100)];
          saveNovelStateToProject({ novel_logs: newLogs });
          return newLogs;
        });
      } else if (evt.event === 'novel_chapter_complete') {
        setLogs(prev => {
          const wordInfo = evt.chapter_data?.skipped ? 'Skipped (already exists)' : `${evt.chapter_data?.word_count || 0} words`;
          const newLogs = [`[SUCCESS] Chapter ${evt.current} generated & validated into Canon DB! (${wordInfo})`, ...prev.slice(0, 100)];
          saveNovelStateToProject({ novel_logs: newLogs, novel_current_chapter: evt.current });
          return newLogs;
        });
      }
    });

    const resLog = PythonEngineService.subscribeLog((line: string) => {
      setLogs(prev => {
        const newLogs = [line, ...prev.slice(0, 100)];
        saveNovelStateToProject({ novel_logs: newLogs });
        return newLogs;
      });
    });

    if (res && typeof (res as any).then === 'function') {
      (res as Promise<any>).then(unsub => {
        if (typeof unsub === 'function') unsubFn = unsub;
      });
    } else if (typeof res === 'function') {
      unsubFn = res;
    }

    if (resLog && typeof (resLog as any).then === 'function') {
      (resLog as Promise<any>).then(unsub => {
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

  const handleInitializeNovel = async () => {
    if (!projectDir) return null;
    setIsGenerating(true);
    setCurrentStage('INITIALIZING_STORY_BIBLE');
    setLogs(prev => ['[INFO] AI Story Director building Story Bible & World Rules...', ...prev]);

    try {
      const idea = {
        title,
        genre,
        style,
        protagonist: { name: protagonistName, age: protagonistAge, background: protagonistBg },
        total_chapters: totalChapters
      };

      await saveNovelStateToProject({ novel_idea: idea, novel_current_stage: 'INITIALIZING_STORY_BIBLE' });

      const bible = await PythonEngineService.initializeNovel(projectDir, idea);
      setStoryBible(bible);
      
      setLogs(prev => ['[SUCCESS] Story Bible generated! Creating Master Plan (20-30 Arcs)...', ...prev]);
      setCurrentStage('GENERATING_MASTER_PLAN');

      await saveNovelStateToProject({ story_bible: bible, novel_current_stage: 'GENERATING_MASTER_PLAN' });

      const masterPlan = await PythonEngineService.generateNovelMasterPlan(projectDir);
      setLogs(prev => ['[SUCCESS] Master Plan created! Ready for Auto-Write.', ...prev]);
      setCurrentStage('READY');

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

  const handleStartAutoWrite = async () => {
    if (!projectDir) return;

    let activeBible = storyBible;
    if (!activeBible) {
      setLogs(prev => ['[INFO] Chưa phát hiện Story Bible & Master Plan. Tự động thực hiện Bước 1, 2, 3 trước...', ...prev]);
      activeBible = await handleInitializeNovel();
      if (!activeBible) {
        setLogs(prev => ['[ERROR] Khởi tạo thế giới thất bại. Đã dừng quy trình.', ...prev]);
        return;
      }
    }

    setIsGenerating(true);
    setCurrentStage('AUTO_WRITING');
    const startLog = '[INFO] Launching Novel Engine Auto-Write Loop...';
    setLogs(prev => {
      const updated = [startLog, ...prev];
      saveNovelStateToProject({ novel_logs: updated, novel_current_stage: 'AUTO_WRITING' });
      return updated;
    });
    await PythonEngineService.startNovelAutoWrite(projectDir, 1, totalChapters);
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
                Qwen2.5-3B Local
              </span>
            </h2>
            <p className="text-xs text-slate-400">
              Nhập ý tưởng + phong cách → AI tự xây thế giới → tự lập kế hoạch → tự viết → kiểm tra Canon continuity.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {currentStage === 'AUTO_WRITING' ? (
            <button
              onClick={() => setIsGenerating(false)}
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

      {/* PIPELINE STAGES VISUALIZER */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-7 gap-2 bg-[#111318] p-3 rounded-xl border border-white/5 text-xs">
        {[
          { id: 1, label: '1. IDEA', desc: 'Ý Tưởng Truyện', icon: Sparkles },
          { id: 2, label: '2. STORY BIBLE', desc: 'Hồ Sơ Thế Giới', icon: BookOpen },
          { id: 3, label: '3. MASTER PLAN', desc: '20-30 Arcs Plan', icon: Layers },
          { id: 4, label: '4. SCENE PLAN', desc: 'Lập 3-5 Scenes', icon: Sliders },
          { id: 5, label: '5. AI WRITER', desc: 'Qwen 3B Viết', icon: Cpu },
          { id: 6, label: '6. EDITOR', desc: 'Biên Tập Văn Phong', icon: FileText },
          { id: 7, label: '7. CANON DB', desc: 'Xác Nhận Facts', icon: ShieldCheck }
        ].map((st) => {
          let status: 'COMPLETED' | 'ACTIVE' | 'PENDING' = 'PENDING';

          const hasBible = !!storyBible;
          const isInitializingBible = currentStage === 'INITIALIZING_STORY_BIBLE';
          const isGeneratingMasterPlan = currentStage === 'GENERATING_MASTER_PLAN';

          if (st.id === 1) {
            status = hasBible || currentStage !== 'IDLE' ? 'COMPLETED' : 'ACTIVE';
          } else if (st.id === 2) {
            if (isInitializingBible) status = 'ACTIVE';
            else if (hasBible) status = 'COMPLETED';
            else status = 'PENDING';
          } else if (st.id === 3) {
            if (isGeneratingMasterPlan) status = 'ACTIVE';
            else if (hasBible && !isInitializingBible) status = 'COMPLETED';
            else status = 'PENDING';
          } else if (st.id === 4) {
            if (!hasBible || isInitializingBible || isGeneratingMasterPlan) {
              status = 'PENDING';
            } else if (['CHAPTER_PLANNER', 'CREATIVE_ENGINE', 'SCENE_PLANNER', 'AUTO_WRITING'].includes(currentStage) || currentStage.startsWith('WRITING')) {
              status = 'ACTIVE';
            } else if (['WRITER', 'WRITING_SCENE', 'EDITOR', 'VALIDATOR', 'MEMORY_EXTRACTOR'].includes(currentStage)) {
              status = 'COMPLETED';
            } else {
              status = 'PENDING';
            }
          } else if (st.id === 5) {
            if (!hasBible || isInitializingBible || isGeneratingMasterPlan) {
              status = 'PENDING';
            } else if (['WRITER', 'WRITING_SCENE'].includes(currentStage)) {
              status = 'ACTIVE';
            } else if (['EDITOR', 'VALIDATOR', 'MEMORY_EXTRACTOR'].includes(currentStage)) {
              status = 'COMPLETED';
            } else {
              status = 'PENDING';
            }
          } else if (st.id === 6) {
            if (!hasBible || isInitializingBible || isGeneratingMasterPlan) {
              status = 'PENDING';
            } else if (currentStage === 'EDITOR') {
              status = 'ACTIVE';
            } else if (['VALIDATOR', 'MEMORY_EXTRACTOR'].includes(currentStage)) {
              status = 'COMPLETED';
            } else {
              status = 'PENDING';
            }
          } else if (st.id === 7) {
            if (!hasBible || isInitializingBible || isGeneratingMasterPlan) {
              status = 'PENDING';
            } else if (['VALIDATOR', 'MEMORY_EXTRACTOR'].includes(currentStage)) {
              status = 'ACTIVE';
            } else {
              status = 'PENDING';
            }
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

          <button
            onClick={handleInitializeNovel}
            disabled={isGenerating}
            className="w-full py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/20 transition-all cursor-pointer disabled:opacity-50"
          >
            <Sparkles size={15} /> Tạo Thế Giới & Master Plan (20-30 Arcs)
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
                  onClick={() => setLogs([])}
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
    </div>
  );
};
