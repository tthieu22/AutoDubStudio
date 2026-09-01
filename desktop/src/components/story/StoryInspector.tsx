import React, { useState, useEffect } from 'react';
import { 
  Sliders, 
  Database, 
  GitBranch, 
  ShieldCheck, 
  BookOpen, 
  User, 
  Globe, 
  Layers, 
  Activity, 
  RefreshCw, 
  Copy, 
  Check, 
  FileText, 
  Sparkles, 
  AlertCircle,
  Cpu
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface StoryInspectorProps {
  projectDir?: string | null;
}

export const StoryInspector: React.FC<StoryInspectorProps> = ({ projectDir }) => {
  const [projectData, setProjectData] = useState<any>(null);
  const [canonFacts, setCanonFacts] = useState<any[]>([]);
  const [plotThreads, setPlotThreads] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [copiedText, setCopiedText] = useState<string | null>(null);

  // Real-time process state
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [currentChapter, setCurrentChapter] = useState<number>(1);
  const [chapterStep, setChapterStep] = useState<number>(0);
  const [recentLog, setRecentLog] = useState<string>('Sẵn sàng xử lý tác phẩm');

  const loadData = async () => {
    if (!projectDir) return;
    setIsLoading(true);
    try {
      const data = await PythonEngineService.readProjectJson(projectDir);
      setProjectData(data);

      const facts = await PythonEngineService.getCanonFacts(projectDir, 20);
      if (Array.isArray(facts)) setCanonFacts(facts);

      const threads = await PythonEngineService.getPlotThreads(projectDir);
      if (Array.isArray(threads)) setPlotThreads(threads);
    } catch (e) {
      console.error('StoryInspector failed to load DB data:', e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();

    let unsubProgFn: any = null;
    let unsubLogFn: any = null;

    const resProg = PythonEngineService.subscribeNovelProgress((evt: any) => {
      if (evt.event === 'novel_chapter_start') {
        setIsGenerating(true);
        setCurrentChapter(evt.current || 1);
        setChapterStep(1);
      } else if (evt.event === 'novel_sub_stage') {
        const stepName = String(evt.step || '').toUpperCase();
        if (['RETRIEVAL', 'HARDWARE'].includes(stepName)) setChapterStep(1);
        else if (['PLANNING', 'CONTRACT'].includes(stepName)) setChapterStep(2);
        else if (['SCENE_EXECUTION', 'WRITING'].includes(stepName)) setChapterStep(3);
        else if (['ASSEMBLER', 'CHAPTER_ASSEMBLER'].includes(stepName)) setChapterStep(4);
        else if (['PROGRESSION_VALIDATOR'].includes(stepName)) setChapterStep(5);
        else if (['METADATA_EXTRACTOR', 'EXTRACTOR'].includes(stepName)) setChapterStep(6);
        else if (['CANON_VALIDATOR', 'MEMORY'].includes(stepName)) setChapterStep(7);
      } else if (evt.event === 'novel_chapter_complete') {
        setCurrentChapter((prev) => prev + 1);
        setChapterStep(7);
        loadData(); // Refresh DB stats on chapter completion
      } else if (evt.event === 'novel_complete') {
        setIsGenerating(false);
        setChapterStep(7);
        loadData();
      }
    });

    if (resProg && typeof (resProg as any).then === 'function') {
      (resProg as any).then((fn: any) => { unsubProgFn = fn; });
    } else {
      unsubProgFn = resProg;
    }

    const resLog = PythonEngineService.subscribeNovelLogs((evt: any) => {
      const line = typeof evt === 'string' ? evt : evt.message || '';
      if (line && line.trim()) {
        setRecentLog(line.trim());
      }
    });

    if (resLog && typeof (resLog as any).then === 'function') {
      (resLog as any).then((fn: any) => { unsubLogFn = fn; });
    } else {
      unsubLogFn = resLog;
    }

    return () => {
      if (typeof unsubProgFn === 'function') unsubProgFn();
      if (typeof unsubLogFn === 'function') unsubLogFn();
    };
  }, [projectDir]);


  const handleCopyText = (text: string, label: string) => {
    navigator.clipboard.writeText(text);
    setCopiedText(label);
    setTimeout(() => setCopiedText(null), 2000);
  };

  const idea = projectData?.novel_idea || {};
  const bible = projectData?.story_bible || {};
  const globalProg = projectData?.global_progress || bible?.global_progress || {};
  const masterPlan = projectData?.arc_plans || [];
  const masterBlueprint = bible?.master_blueprint || {};
  const characters = projectData?.characters || bible?.characters || [];
  const locations = bible?.world?.locations || [];

  return (
    <div className="flex flex-col h-full space-y-3 font-sans text-slate-200">
      {/* HEADER & REFRESH ACTION */}
      <div className="flex items-center justify-between bg-[#111318] p-2.5 rounded-lg border border-white/5">
        <div className="flex items-center gap-2">
          <div className="w-6 h-6 rounded bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
            <Sliders size={13} />
          </div>
          <div>
            <h3 className="text-xs font-bold text-white font-['Outfit'] truncate">
              {idea.title || 'Novel Inspector'}
            </h3>
            <p className="text-[10px] text-slate-400">SQLite DB Telemetry & Context</p>
          </div>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="p-1.5 rounded bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-all cursor-pointer"
          title="Làm mới dữ liệu từ DB"
        >
          <RefreshCw size={13} className={isLoading ? 'animate-spin text-indigo-400' : ''} />
        </button>
      </div>

      {/* REAL-TIME EXECUTION STATUS CARD */}
      <div className="bg-[#111318] p-2.5 rounded-lg border border-white/5 space-y-2">
        <div className="flex items-center justify-between text-[11px]">
          <span className="font-bold text-slate-300 font-['Outfit'] uppercase flex items-center gap-1.5">
            <Activity size={13} className={isGenerating ? 'text-cyan-400 animate-pulse' : 'text-slate-500'} />
            Trạng Thái Thực Thi Real-Time
          </span>
          <span className={`px-1.5 py-0.5 rounded text-[9px] font-bold font-mono ${
            isGenerating ? 'bg-cyan-500/20 text-cyan-300 animate-pulse' : 'bg-emerald-500/20 text-emerald-300'
          }`}>
            {isGenerating ? `WRITING CH #${currentChapter}` : 'IDLE / READY'}
          </span>
        </div>

        {/* STEPPER PROGRESS BADGE */}
        {chapterStep > 0 && (
          <div className="bg-black/40 p-1.5 rounded border border-white/5 flex items-center justify-between text-[10px]">
            <span className="text-slate-400">7-Step Execution:</span>
            <span className="font-bold text-cyan-300 font-mono">Step {chapterStep}/7</span>
          </div>
        )}

        <div className="bg-black/40 p-2 rounded border border-white/5 text-[10px] font-mono text-slate-400 truncate">
          {recentLog}
        </div>
      </div>

      {/* NOVEL ENGINE DB STATS METRICS GRID */}
      <div className="grid grid-cols-2 gap-2 text-xs">
        <div className="bg-[#111318] p-2 rounded-lg border border-white/5 flex flex-col">
          <span className="text-[10px] text-slate-400 flex items-center gap-1 font-semibold uppercase">
            <Database size={11} className="text-emerald-400" /> Canon Facts
          </span>
          <span className="text-sm font-extrabold text-emerald-300 font-mono mt-0.5">
            {canonFacts.length}
          </span>
        </div>

        <div className="bg-[#111318] p-2 rounded-lg border border-white/5 flex flex-col">
          <span className="text-[10px] text-slate-400 flex items-center gap-1 font-semibold uppercase">
            <GitBranch size={11} className="text-indigo-400" /> Open Threads
          </span>
          <span className="text-sm font-extrabold text-indigo-300 font-mono mt-0.5">
            {plotThreads.length}
          </span>
        </div>

        <div className="bg-[#111318] p-2 rounded-lg border border-white/5 flex flex-col">
          <span className="text-[10px] text-slate-400 flex items-center gap-1 font-semibold uppercase">
            <Layers size={11} className="text-amber-400" /> Master Arcs
          </span>
          <span className="text-sm font-extrabold text-amber-300 font-mono mt-0.5">
            {masterPlan.length}
          </span>
        </div>

        <div className="bg-[#111318] p-2 rounded-lg border border-white/5 flex flex-col">
          <span className="text-[10px] text-slate-400 flex items-center gap-1 font-semibold uppercase">
            <User size={11} className="text-purple-400" /> Cast & Lore
          </span>
          <span className="text-sm font-extrabold text-purple-300 font-mono mt-0.5">
            {characters.length} nhân vật
          </span>
        </div>
      </div>

      {/* PROJECT GENERAL DETAILS */}
      <div className="bg-[#111318] p-2.5 rounded-lg border border-white/5 space-y-1.5 text-xs">
        <h4 className="font-bold text-slate-300 text-[11px] font-['Outfit'] uppercase flex items-center justify-between">
          <span>Thông Tin Tác Phẩm</span>
          <button
            onClick={() => handleCopyText(JSON.stringify(idea, null, 2), 'idea')}
            className="text-slate-500 hover:text-white cursor-pointer"
            title="Copy Json Idea"
          >
            {copiedText === 'idea' ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
          </button>
        </h4>

        <div className="space-y-1 text-[11px]">
          <div className="flex justify-between">
            <span className="text-slate-400">Thể loại:</span>
            <span className="font-semibold text-slate-200">{idea.genre || 'Tiên Hiệp'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Nhân vật chính:</span>
            <span className="font-semibold text-cyan-300">{idea.protagonist?.name || 'Diệp Phàm'}</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Tổng số chương:</span>
            <span className="font-semibold text-amber-300 font-mono">{idea.total_chapters || 1000} chương</span>
          </div>
          <div className="flex justify-between">
            <span className="text-slate-400">Đã hoàn thành:</span>
            <span className="font-semibold text-emerald-300 font-mono">Chương #{globalProg.last_completed_chapter || 0}</span>
          </div>
        </div>
      </div>

      {/* RECENT CANON FACTS FROM SQLITE DB */}
      <div className="bg-[#111318] p-2.5 rounded-lg border border-white/5 space-y-2 flex-1 overflow-hidden flex flex-col">
        <div className="flex items-center justify-between">
          <h4 className="font-bold text-slate-300 text-[11px] font-['Outfit'] uppercase flex items-center gap-1.5">
            <ShieldCheck size={13} className="text-emerald-400" /> Top Canon Facts (SQLite DB)
          </h4>
          <span className="text-[9px] text-slate-500 font-mono">{canonFacts.length} facts</span>
        </div>

        <div className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pr-1">
          {canonFacts.length > 0 ? (
            canonFacts.slice(0, 8).map((fact, idx) => (
              <div
                key={fact.id || idx}
                className="p-2 rounded bg-black/40 border border-white/5 text-[11px] space-y-1 hover:border-emerald-500/30 transition-all"
              >
                <div className="flex items-center justify-between text-[10px]">
                  <span className="px-1.5 py-0.2 rounded bg-emerald-500/10 text-emerald-400 font-mono font-bold">
                    Chương #{fact.chapter_num || fact.chapter || 1}
                  </span>
                  <span className="text-[9px] text-slate-500 uppercase">{fact.category || 'General'}</span>
                </div>
                <p className="text-slate-300 text-[10px] leading-relaxed">
                  {fact.fact_text || fact.object || fact.subject || ''}
                </p>
              </div>
            ))
          ) : (
            <div className="text-center py-6 text-slate-500 text-[11px]">
              Chưa có Canon Facts trong SQLite DB
            </div>
          )}
        </div>
      </div>

      {/* ACTIVE PLOT THREADS LIST */}
      {plotThreads.length > 0 && (
        <div className="bg-[#111318] p-2.5 rounded-lg border border-white/5 space-y-1.5 text-xs max-h-36 overflow-y-auto custom-scrollbar">
          <h4 className="font-bold text-slate-300 text-[11px] font-['Outfit'] uppercase flex items-center gap-1.5">
            <GitBranch size={13} className="text-indigo-400" /> Tuyến Truyện Mở (Open Threads)
          </h4>
          <div className="space-y-1 text-[11px]">
            {plotThreads.slice(0, 4).map((t, idx) => (
              <div key={t.id || idx} className="p-1.5 rounded bg-black/30 border border-white/5 flex items-center justify-between">
                <span className="truncate text-slate-300 font-medium text-[10px]">{t.title || 'Plot Thread'}</span>
                <span className="px-1 py-0.2 rounded bg-indigo-500/20 text-indigo-300 text-[9px] font-bold">
                  {t.status || 'OPEN'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
