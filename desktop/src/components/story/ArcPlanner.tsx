import React, { useState, useEffect } from 'react';
import { Layers, Search, ChevronRight, Target, Flame, Eye, Sparkles } from 'lucide-react';
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
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Master Plan — Danh Sách Arcs Truyện AI
            </h2>
            <p className="text-xs text-slate-400">
              Cấu trúc tổng thể kịch bản do AI sáng tạo định hướng toàn bộ câu chuyện.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 relative max-w-xs w-full">
          <Search size={14} className="absolute left-3 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm Arc..."
            className="w-full bg-[#0b0d10] border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none"
          />
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
            const isSelected = selectedArcId === arc.id;
            return (
              <div
                key={arc.id || arc.arc_num}
                onClick={() => setSelectedArcId(arc.id || String(arc.arc_num))}
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

                  <span className="text-xs font-mono text-cyan-400 font-semibold">
                    Chương {arc.start_chapter} – {arc.end_chapter}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-2 border-t border-white/5">
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                      <Target size={11} className="text-emerald-400" /> Mục Tiêu Arc
                    </span>
                    <p className="text-slate-300">{arc.goal}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                      <Flame size={11} className="text-rose-400" /> Xung Đột Chính
                    </span>
                    <p className="text-slate-300">{arc.conflict}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                      <Eye size={11} className="text-amber-400" /> Tiết Lộ Lớn (Major Reveal)
                    </span>
                    <p className="text-slate-300">{arc.major_reveal}</p>
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
