import React, { useState, useEffect } from 'react';
import { Layers, Search, Target, Flame, Eye, Copy, Check } from 'lucide-react';
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

interface ArcPlannerProps {
  projectDir?: string | null;
}

export const ArcPlanner: React.FC<ArcPlannerProps> = ({ projectDir }) => {
  const [arcs, setArcs] = useState<ArcPlanItem[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedArcId, setSelectedArcId] = useState<string>('');
  const [copiedAll, setCopiedAll] = useState(false);
  const [copiedArcId, setCopiedArcId] = useState<string | null>(null);

  useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(data => {
        if (data && data.arc_plans && Array.isArray(data.arc_plans) && data.arc_plans.length > 0) {
          setArcs(data.arc_plans);
        } else {
          setArcs([]);
        }
      }).catch(() => {
        setArcs([]);
      });
    }
  }, [projectDir]);

  const handleCopyAllArcs = () => {
    if (arcs.length === 0) return;
    const formatted = arcs.map(a => 
      `### Arc #${a.arc_num}: ${a.title} (Chương ${a.start_chapter} - ${a.end_chapter})\n- **Mục tiêu Arc**: ${a.goal || 'N/A'}\n- **Xung đột chính**: ${a.conflict || 'N/A'}\n- **Tiết lộ lớn**: ${a.major_reveal || 'N/A'}\n- **Phát triển nhân vật**: ${a.character_development || 'N/A'}`
    ).join('\n\n---\n\n');

    const textToCopy = `# MASTER PLAN ARCS (${arcs.length} Arcs)\n\n${formatted}`;
    navigator.clipboard.writeText(textToCopy);
    setCopiedAll(true);
    setTimeout(() => setCopiedAll(false), 2000);
  };

  const handleCopySingleArc = (arc: ArcPlanItem, e: React.MouseEvent) => {
    e.stopPropagation();
    const formatted = `### Arc #${arc.arc_num}: ${arc.title} (Chương ${arc.start_chapter} - ${arc.end_chapter})\n- **Mục tiêu Arc**: ${arc.goal || 'N/A'}\n- **Xung đột chính**: ${arc.conflict || 'N/A'}\n- **Tiết lộ lớn**: ${arc.major_reveal || 'N/A'}\n- **Phát triển nhân vật**: ${arc.character_development || 'N/A'}`;
    
    navigator.clipboard.writeText(formatted);
    const arcKey = arc.id || String(arc.arc_num);
    setCopiedArcId(arcKey);
    setTimeout(() => setCopiedArcId(null), 2000);
  };

  const filteredArcs = arcs.filter(a =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.goal.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
            <Layers size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight flex items-center gap-2">
              Master Plan — Danh Sách {arcs.length > 0 ? `${arcs.length} Arcs` : 'Arcs'} Truyện AI
              {arcs.length > 0 && (
                <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-[10px] font-mono font-bold">
                  {arcs.length} Arcs Master Plan
                </span>
              )}
            </h2>
            <p className="text-xs text-slate-400">
              Cấu trúc tổng thể kịch bản do AI sáng tạo định hướng toàn bộ câu chuyện.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 max-w-md w-full justify-end">
          <div className="relative flex-1">
            <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              placeholder="Tìm kiếm Arc..."
              className="w-full bg-[#0b0d10] border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none"
            />
          </div>

          <button
            onClick={handleCopyAllArcs}
            disabled={arcs.length === 0}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold flex items-center gap-1.5 transition-all shadow-md shrink-0 cursor-pointer select-none ${
              copiedAll
                ? 'bg-emerald-500 text-black shadow-emerald-500/20'
                : arcs.length > 0
                ? 'bg-indigo-600 hover:bg-indigo-500 text-white shadow-indigo-600/20 active:scale-95'
                : 'bg-white/5 text-slate-500 border border-white/5 cursor-not-allowed'
            }`}
            title="Sao chép toàn bộ danh sách Arcs kịch bản"
          >
            {copiedAll ? <Check size={14} className="stroke-[3]" /> : <Copy size={14} />}
            <span>{copiedAll ? 'Đã Copy Tất Cả!' : 'Copy Tất Cả Arcs'}</span>
          </button>
        </div>
      </div>

      {/* ARCS GRID */}
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {filteredArcs.length === 0 ? (
          <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
            <Layers size={32} className="text-indigo-400 mb-3" />
            <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Chưa Có Kế Hoạch Arc</h3>
            <p className="text-xs text-slate-400 max-w-md">
              Vào Novel Dashboard và nhấn "Tạo Thế Giới & Master Plan" để AI xây dựng toàn bộ Arcs cho bộ truyện dài.
            </p>
          </div>
        ) : (
          filteredArcs.map(arc => {
            const arcKey = arc.id || String(arc.arc_num);
            const isSelected = selectedArcId === arcKey;
            const isCopied = copiedArcId === arcKey;

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

                  <div className="flex items-center gap-3">
                    <span className="text-xs font-mono text-cyan-400 font-semibold">
                      Chương {arc.start_chapter} – {arc.end_chapter}
                    </span>

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
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
