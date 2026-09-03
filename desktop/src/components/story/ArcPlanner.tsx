import React, { useState, useEffect } from 'react';
import { Layers, Search, Target, Flame, Eye, Copy, Check, Compass, ChevronDown, ChevronRight, BookOpen, GitCommit, List, LayoutGrid, RefreshCw } from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

export interface ArcPlanItem {
  id: string;
  arc_num: number;
  title: string;
  start_chapter: number;
  end_chapter: number;
  goal: string;
  conflict: string;
  major_reveal: string;
  character_development: string;
  status: string;
}

export interface MasterBlueprintData {
  overall_arc_summary?: string;
  core_conflicts_and_mysteries?: string[];
  protagonist_growth_milestones?: string[];
  major_climaxes_and_twists?: string[];
  world_timeline_events?: string[];
}

export interface ChapterRoadmapItem {
  chapter_num: number;
  title: string;
  goal: string;
  trigger_event?: string;
  conflict?: string;
  revelation?: string;
  transition_hook?: string;
}

interface ArcPlannerProps {
  projectDir?: string | null;
}

export const ArcPlanner: React.FC<ArcPlannerProps> = ({ projectDir }) => {
  const [arcs, setArcs] = useState<ArcPlanItem[]>([]);
  const [blueprint, setBlueprint] = useState<MasterBlueprintData | null>(null);
  const [roadmaps, setRoadmaps] = useState<Record<string, ChapterRoadmapItem[]>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedArcId, setSelectedArcId] = useState<string>('');
  const [showBlueprint, setShowBlueprint] = useState<boolean>(true);
  const [expandedArcRoadmaps, setExpandedArcRoadmaps] = useState<Record<string, boolean>>({});
  const [copiedAll, setCopiedAll] = useState(false);
  const [copiedArcId, setCopiedArcId] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<'arcs' | 'timeline'>('arcs');
  const [allExpanded, setAllExpanded] = useState<boolean>(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [regenStatus, setRegenStatus] = useState<string | null>(null);

  useEffect(() => {
    const loadData = () => {
      if (projectDir) {
        PythonEngineService.readProjectJson(projectDir).then(data => {
          if (data) {
            if (data.arc_plans && Array.isArray(data.arc_plans)) {
              setArcs(data.arc_plans);
            } else {
              setArcs([]);
            }
            if (data.story_bible && data.story_bible.master_blueprint) {
              setBlueprint(data.story_bible.master_blueprint);
            } else if (data.master_blueprint) {
              setBlueprint(data.master_blueprint);
            } else {
              setBlueprint(null);
            }
            if (data.arc_roadmaps && typeof data.arc_roadmaps === 'object') {
              setRoadmaps(data.arc_roadmaps);
            } else {
              setRoadmaps({});
            }
          }
        }).catch(() => {
          setArcs([]);
        });
      }
    };

    loadData();
    window.addEventListener('story_data_updated', loadData);
    return () => window.removeEventListener('story_data_updated', loadData);
  }, [projectDir]);

  const handleRegenerateArcPlan = async () => {
    if (!projectDir) return;
    if (!confirm('Bạn có chắc muốn gọi AI Qwen 2.5 tái tạo lại Sườn Kịch Bản & Các Arcs Cốt Truyện cho dự án không?')) return;
    setIsRegenerating(true);
    setRegenStatus('Đang chạy Python Engine & AI Qwen 2.5 lập Master Plan Sườn Kịch Bản...');
    try {
      const masterPlan = await PythonEngineService.generateNovelMasterPlan(projectDir);
      const updatedProj = await PythonEngineService.readProjectJson(projectDir);
      if (updatedProj && updatedProj.arc_plans && Array.isArray(updatedProj.arc_plans) && updatedProj.arc_plans.length > 0) {
        setArcs(updatedProj.arc_plans);
      } else if (masterPlan && Array.isArray(masterPlan)) {
        setArcs(masterPlan);
      }
      if (updatedProj && updatedProj.arc_roadmaps) {
        setRoadmaps(updatedProj.arc_roadmaps);
      }
      if (updatedProj && (updatedProj.story_bible?.master_blueprint || updatedProj.master_blueprint)) {
        setBlueprint(updatedProj.story_bible?.master_blueprint || updatedProj.master_blueprint);
      }
      setRegenStatus('Tái tạo Sườn Kịch Bản & Arcs bằng AI thành công!');
      setTimeout(() => setRegenStatus(null), 3000);
    } catch (e: any) {
      console.error("Lỗi khi tái tạo Master Plan:", e);
      setRegenStatus(`Lỗi AI: ${e?.message || e}`);
      setTimeout(() => setRegenStatus(null), 4000);
    } finally {
      setIsRegenerating(false);
    }
  };

  const toggleRoadmapExpand = (arcNum: number, e: React.MouseEvent) => {
    e.stopPropagation();
    const key = `arc_${arcNum}`;
    setExpandedArcRoadmaps(prev => ({ ...prev, [key]: !prev[key] }));
  };

  const handleToggleExpandAllRoadmaps = () => {
    const nextState = !allExpanded;
    setAllExpanded(nextState);
    const newExpandedMap: Record<string, boolean> = {};
    arcs.forEach(a => {
      newExpandedMap[`arc_${a.arc_num}`] = nextState;
    });
    setExpandedArcRoadmaps(newExpandedMap);
  };

  const handleCopyAllArcs = () => {
    if (arcs.length === 0) return;
    const formatted = arcs.map(a => {
      const rItems = roadmaps[`arc_${a.arc_num}`] || roadmaps[`arc_${String(a.arc_num).padStart(2, '0')}`] || [];
      let rText = '';
      if (rItems.length > 0) {
        rText = '\n  * **Dàn ý chi tiết từng chương**:\n' + rItems.map(c => `    - Chương ${c.chapter_num} (${c.title}): ${c.goal}`).join('\n');
      }
      return `### Arc #${a.arc_num}: ${a.title} (Chương ${a.start_chapter} - ${a.end_chapter})\n- **Mục tiêu Arc**: ${a.goal || 'N/A'}\n- **Xung đột chính**: ${a.conflict || 'N/A'}\n- **Tiết lộ lớn**: ${a.major_reveal || 'N/A'}\n- **Phát triển nhân vật**: ${a.character_development || 'N/A'}${rText}`;
    }).join('\n\n---\n\n');

    const textToCopy = `# MASTER PLAN & SƯỜN KỊCH BẢN TỔNG THỂ (${arcs.length} Arcs)\n\n${formatted}`;
    navigator.clipboard.writeText(textToCopy);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const handleCopySingleArc = (arc: ArcPlanItem, e: React.MouseEvent) => {
    e.stopPropagation();
    const rItems = roadmaps[`arc_${arc.arc_num}`] || roadmaps[`arc_${String(arc.arc_num).padStart(2, '0')}`] || [];
    let rText = '';
    if (rItems.length > 0) {
      rText = '\n\n**Dàn ý chi tiết các chương:**\n' + rItems.map(c => `- Chương ${c.chapter_num}: ${c.title}\n  + Mục tiêu: ${c.goal}\n  + Xung đột: ${c.conflict || 'N/A'}\n  + Tiết lộ: ${c.revelation || 'N/A'}`).join('\n');
    }
    const formatted = `### Arc #${arc.arc_num}: ${arc.title} (Chương ${arc.start_chapter} - ${arc.end_chapter})\n- **Mục tiêu Arc**: ${arc.goal || 'N/A'}\n- **Xung đột chính**: ${arc.conflict || 'N/A'}\n- **Tiết lộ lớn**: ${arc.major_reveal || 'N/A'}\n- **Phát triển nhân vật**: ${arc.character_development || 'N/A'}${rText}`;
    
    navigator.clipboard.writeText(formatted);
    const arcKey = arc.id || String(arc.arc_num);
    setCopiedArcId(arcKey);
    setTimeout(() => setCopiedArcId(null), 2000);
  };

  const filteredArcs = arcs.filter(a =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.goal.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Flatten all roadmaps into a continuous timeline of chapters
  const allTimelineChapters: Array<{ arc: ArcPlanItem; chapter: ChapterRoadmapItem }> = [];
  arcs.forEach(arc => {
    const items = roadmaps[`arc_${arc.arc_num}`] || roadmaps[`arc_${String(arc.arc_num).padStart(2, '0')}`] || [];
    items.forEach(c => {
      if (!searchQuery || c.title.toLowerCase().includes(searchQuery.toLowerCase()) || c.goal.toLowerCase().includes(searchQuery.toLowerCase())) {
        allTimelineChapters.push({ arc, chapter: c });
      }
    });
  });

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans relative">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
            <Layers size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight flex items-center gap-2">
              Master Plan & Sườn Kịch Bản ({arcs.length} Arcs)
              {arcs.length > 0 && (
                <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-mono font-bold">
                  {arcs.length} Arcs Liên Hoàn
                </span>
              )}
            </h2>
            <p className="text-xs text-slate-400">
              Sườn kịch bản đại cục & Dàn ý liên hoàn từng chương định hướng tuyệt đối cho AI Sáng Tác.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {viewMode === 'arcs' && arcs.length > 0 && (
            <button
              onClick={handleToggleExpandAllRoadmaps}
              className="px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all bg-white/5 hover:bg-white/10 border border-white/10 text-slate-300 cursor-pointer"
              title="Mở rộng hoặc gom tất cả Dàn ý 20 chương của các Arc"
            >
              <BookOpen size={14} />
              <span>{allExpanded ? 'Gom Dàn Ý' : 'Mở Dàn Ý các Arc'}</span>
            </button>
          )}

          <button
            onClick={handleRegenerateArcPlan}
            disabled={isRegenerating}
            className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
            title="Tái tạo lại Master Plan Sườn Kịch Bản bằng AI"
          >
            <RefreshCw size={14} className={isRegenerating ? "animate-spin" : ""} />
            {isRegenerating ? "Đang Tái Tạo..." : "Tái Tạo AI"}
          </button>

          <button
            onClick={handleCopyAllArcs}
            disabled={arcs.length === 0}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all shadow-md cursor-pointer select-none ${
              copiedAll
                ? 'bg-emerald-500 text-black shadow-emerald-500/20'
                : arcs.length > 0
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20 active:scale-95'
                : 'bg-white/5 text-slate-500 border border-white/5 cursor-not-allowed'
            }`}
            title="Sao chép toàn bộ danh sách Arcs & Dàn ý kịch bản"
          >
            {copiedAll ? <Check size={14} className="stroke-[3]" /> : <Copy size={14} />}
            <span>{copiedAll ? 'Đã Copy!' : 'Copy Tất Cả'}</span>
          </button>
        </div>
      </div>

      {/* FILTER & SEARCH SUB-TOOLBAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-3 rounded-xl border border-white/5 text-xs shadow-sm">
        {/* WIDE SEARCH INPUT */}
        <div className="relative flex-1 max-w-md w-full">
          <Search size={15} className="absolute left-3.5 top-2.5 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm Arc, tên chương, mục tiêu cốt truyện..."
            className="w-full bg-[#0b0d10] border border-white/10 rounded-lg pl-10 pr-3 py-2 text-xs text-slate-100 placeholder-slate-500 focus:outline-none focus:border-indigo-500/50"
          />
        </div>

        {/* VIEW MODE SWITCHER */}
        <div className="flex items-center gap-2 shrink-0">
          <span className="text-slate-400 font-medium">Chế độ xem:</span>
          <div className="flex items-center bg-[#0b0d10] p-1 rounded-lg border border-white/10">
            <button
              onClick={() => setViewMode('arcs')}
              className={`px-3 py-1 rounded text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                viewMode === 'arcs' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
              title="Hiển thị dạng Danh sách các Arc"
            >
              <LayoutGrid size={13} /> Theo Danh Sách Arc
            </button>
            <button
              onClick={() => setViewMode('timeline')}
              className={`px-3 py-1 rounded text-xs font-bold flex items-center gap-1.5 transition-all cursor-pointer ${
                viewMode === 'timeline' ? 'bg-indigo-600 text-white shadow-sm' : 'text-slate-400 hover:text-white'
              }`}
              title="Hiển thị Sườn Kịch Bản toàn bộ các chương liên tục"
            >
              <List size={13} /> Toàn Bộ Kịch Bản Chương
            </button>
          </div>
        </div>
      </div>

      {/* REGEN STATUS BANNER */}
      {regenStatus && (
        <div className="bg-amber-500/15 border border-amber-500/40 text-amber-300 text-xs px-4 py-2.5 rounded-xl flex items-center gap-2.5 font-bold shadow-md shadow-amber-500/10 animate-pulse">
          <RefreshCw size={15} className="animate-spin text-amber-400" />
          <span>{regenStatus}</span>
        </div>
      )}

      {/* MASTER BLUEPRINT SKELETON CARD */}
      {blueprint && (
        <div className="bg-[#111318] rounded-xl border border-indigo-500/20 p-4 shadow-lg space-y-3">
          <div
            onClick={() => setShowBlueprint(!showBlueprint)}
            className="flex items-center justify-between cursor-pointer select-none"
          >
            <div className="flex items-center gap-2.5">
              <Compass size={18} className="text-amber-400" />
              <h3 className="text-sm font-bold text-white font-['Outfit'] flex items-center gap-2">
                Sườn Kịch Bản Tổng Thể (Master Blueprint Skeleton)
                <span className="px-2 py-0.5 rounded bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[10px] font-mono">
                  Kim Chỉ Nam AI
                </span>
              </h3>
            </div>
            <button className="text-slate-400 hover:text-white transition-colors">
              {showBlueprint ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
            </button>
          </div>

          {showBlueprint && (
            <div className="space-y-3 text-xs pt-2 border-t border-white/5">
              {blueprint.overall_arc_summary && (
                <div className="bg-[#0b0d10] p-3 rounded-lg border border-white/5">
                  <span className="text-[10px] text-amber-400 font-bold uppercase tracking-wider block mb-1">
                    Tóm Tắt Tiến Trình Kịch Bản Đại Cục:
                  </span>
                  <p className="text-slate-300 leading-relaxed">{blueprint.overall_arc_summary}</p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                {blueprint.core_conflicts_and_mysteries && (
                  <div className="bg-[#0b0d10] p-3 rounded-lg border border-white/5 space-y-1">
                    <span className="text-[10px] text-rose-400 font-bold uppercase tracking-wider flex items-center gap-1">
                      <Flame size={11} /> Mâu Thuẫn & Đại Bí Ẩn Cốt Lõi
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                      {blueprint.core_conflicts_and_mysteries.map((m, idx) => (
                        <li key={idx}>{m}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {blueprint.protagonist_growth_milestones && (
                  <div className="bg-[#0b0d10] p-3 rounded-lg border border-white/5 space-y-1">
                    <span className="text-[10px] text-emerald-400 font-bold uppercase tracking-wider flex items-center gap-1">
                      <Target size={11} /> Cột Mốc Phát Triển Nhân Vật
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                      {blueprint.protagonist_growth_milestones.map((ms, idx) => (
                        <li key={idx}>{ms}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {blueprint.major_climaxes_and_twists && (
                  <div className="bg-[#0b0d10] p-3 rounded-lg border border-white/5 space-y-1">
                    <span className="text-[10px] text-cyan-400 font-bold uppercase tracking-wider flex items-center gap-1">
                      <Eye size={11} /> Climaxes & Twists Bước Ngoặt
                    </span>
                    <ul className="list-disc list-inside space-y-1 text-slate-300 text-[11px]">
                      {blueprint.major_climaxes_and_twists.map((t, idx) => (
                        <li key={idx}>{t}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* VIEW MODE A: ARCS GRID */}
      {viewMode === 'arcs' ? (
        <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
          {filteredArcs.length === 0 ? (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
              <Layers size={32} className="text-indigo-400 mb-3" />
              <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Chưa Có Kế Hoạch Arc</h3>
              <p className="text-xs text-slate-400 max-w-md">
                Vào Novel Dashboard và nhấn "Tạo Thế Giới & Master Plan" để AI xây dựng Sườn kịch bản và dàn ý liên hoàn cho bộ truyện.
              </p>
            </div>
          ) : (
            filteredArcs.map(arc => {
              const arcKey = arc.id || String(arc.arc_num);
              const isSelected = selectedArcId === arcKey;
              const isCopied = copiedArcId === arcKey;
              const isRoadmapExpanded = !!expandedArcRoadmaps[`arc_${arc.arc_num}`];
              const arcRoadmapItems = roadmaps[`arc_${arc.arc_num}`] || roadmaps[`arc_${String(arc.arc_num).padStart(2, '0')}`] || [];

              return (
                <div
                  key={arcKey}
                  onClick={() => setSelectedArcId(arcKey)}
                  className={`p-4 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-indigo-500/10 border-indigo-500/50 shadow-md shadow-indigo-500/10'
                      : 'bg-[#111318] hover:bg-[#161a22] border-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold font-mono">
                        Arc #{arc.arc_num}
                      </span>
                      <h3 className="text-sm font-bold text-white font-['Outfit']">{arc.title}</h3>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-cyan-400 font-semibold mr-2">
                        Chương {arc.start_chapter} – {arc.end_chapter}
                      </span>

                      {arcRoadmapItems.length > 0 && (
                        <button
                          onClick={e => toggleRoadmapExpand(arc.arc_num, e)}
                          className="px-2.5 py-1 rounded-md text-[11px] font-semibold flex items-center gap-1 transition-all bg-indigo-500/20 hover:bg-indigo-500/30 text-indigo-300 border border-indigo-500/40 select-none cursor-pointer"
                          title="Xem Dàn ý 20 chương liên hoàn của Arc"
                        >
                          <BookOpen size={12} />
                          <span>Dàn Ý {arcRoadmapItems.length} Chương</span>
                          {isRoadmapExpanded ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
                        </button>
                      )}

                      <button
                        onClick={e => handleCopySingleArc(arc, e)}
                        className={`px-2.5 py-1 rounded-md text-[11px] font-semibold flex items-center gap-1 transition-all border select-none cursor-pointer ${
                          isCopied
                            ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40'
                            : 'bg-white/5 hover:bg-white/10 text-slate-300 border-white/10'
                        }`}
                        title={`Copy nội dung Arc #${arc.arc_num}`}
                      >
                        {isCopied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                        <span>{isCopied ? 'Đã Copy' : 'Copy Arc'}</span>
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-2 border-t border-white/5">
                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                        <Target size={11} className="text-emerald-400" /> Mục Tiêu Arc
                      </span>
                      <p className="text-slate-300">{arc.goal || 'N/A'}</p>
                    </div>
                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                        <Flame size={11} className="text-rose-400" /> Xung Đột Chính
                      </span>
                      <p className="text-slate-300">{arc.conflict || 'N/A'}</p>
                    </div>
                    <div className="space-y-1">
                      <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                        <Eye size={11} className="text-amber-400" /> Tiết Lộ Lớn (Major Reveal)
                      </span>
                      <p className="text-slate-300">{arc.major_reveal || 'N/A'}</p>
                    </div>
                  </div>

                  {/* ARC CHAPTER ROADMAP ACCORDION */}
                  {isRoadmapExpanded && arcRoadmapItems.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-indigo-500/20 bg-[#0b0d10] p-3 rounded-lg space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-indigo-300 flex items-center gap-1.5 font-mono">
                          <GitCommit size={13} className="text-indigo-400" />
                          DÀN Ý KỊCH BẢN CHƯƠNG LIÊN HOÀN (CAUSAL ROADMAP - ARC {arc.arc_num})
                        </span>
                      </div>

                      <div className="space-y-2 max-h-[350px] overflow-y-auto custom-scrollbar pr-1">
                        {arcRoadmapItems.map((item, idx) => (
                          <div key={idx} className="p-2.5 rounded-lg bg-[#111318] border border-white/5 text-[11px] space-y-1 hover:border-indigo-500/30 transition-all">
                            <div className="flex items-center justify-between font-bold text-white">
                              <span className="text-cyan-400 font-mono">Chương {item.chapter_num}: {item.title}</span>
                            </div>
                            <p className="text-slate-300"><strong className="text-slate-400">Mục tiêu:</strong> {item.goal}</p>
                            {item.trigger_event && <p className="text-slate-400"><strong className="text-emerald-400">Khởi đầu:</strong> {item.trigger_event}</p>}
                            {item.conflict && <p className="text-slate-400"><strong className="text-rose-400">Xung đột:</strong> {item.conflict}</p>}
                            {item.revelation && <p className="text-slate-400"><strong className="text-amber-400">Tiết lộ:</strong> {item.revelation}</p>}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })
          )}
        </div>
      ) : (
        /* VIEW MODE B: CONTINUOUS TIMELINE FOR ALL CHAPTERS */
        <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar bg-[#111318] p-4 rounded-xl border border-white/5">
          <div className="flex items-center justify-between pb-2 border-b border-white/5">
            <h3 className="text-xs font-bold text-indigo-300 font-mono uppercase tracking-wider flex items-center gap-2">
              <GitCommit size={15} className="text-indigo-400" />
              SƯỜN KỊCH BẢN CHI TIẾT TOÀN BỘ CHƯƠNG (CHRONOLOGICAL ROADMAP)
            </h3>
            <span className="text-xs text-slate-400 font-mono">
              Tổng số: {allTimelineChapters.length} Chương đã tạo dàn ý
            </span>
          </div>

          {allTimelineChapters.length === 0 ? (
            <div className="h-[200px] flex flex-col items-center justify-center text-center">
              <BookOpen size={28} className="text-slate-600 mb-2" />
              <p className="text-xs text-slate-400">Chưa có dàn ý chi tiết chương nào được sinh ra.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {allTimelineChapters.map(({ arc, chapter }, idx) => (
                <div key={idx} className="bg-[#0b0d10] p-3 rounded-xl border border-white/5 hover:border-indigo-500/40 transition-all space-y-1.5">
                  <div className="flex items-center justify-between border-b border-white/5 pb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 text-[10px] font-mono font-bold">
                        Chương {chapter.chapter_num}
                      </span>
                      <h4 className="text-xs font-bold text-white font-['Outfit']">{chapter.title}</h4>
                    </div>
                    <span className="text-[10px] font-mono text-indigo-400 bg-indigo-500/10 px-2 py-0.5 rounded border border-indigo-500/20">
                      Arc #{arc.arc_num}: {arc.title}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs pt-1">
                    <div>
                      <span className="text-[10px] text-slate-500 uppercase font-bold block">Mục tiêu kịch bản:</span>
                      <p className="text-slate-300 text-[11px]">{chapter.goal}</p>
                    </div>
                    {chapter.trigger_event && (
                      <div>
                        <span className="text-[10px] text-emerald-500 uppercase font-bold block">Sự kiện khởi đầu:</span>
                        <p className="text-slate-300 text-[11px]">{chapter.trigger_event}</p>
                      </div>
                    )}
                    {chapter.conflict && (
                      <div>
                        <span className="text-[10px] text-rose-500 uppercase font-bold block">Xung đột kịch tính:</span>
                        <p className="text-slate-300 text-[11px]">{chapter.conflict}</p>
                      </div>
                    )}
                    {chapter.revelation && (
                      <div>
                        <span className="text-[10px] text-amber-500 uppercase font-bold block">Bí mật / Tiết lộ mới:</span>
                        <p className="text-slate-300 text-[11px]">{chapter.revelation}</p>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
