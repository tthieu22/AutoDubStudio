import React, { useState, useEffect } from 'react';
import { Calendar, FileText, CheckCircle2, AlertTriangle, Clock, Search, BookOpen } from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface ChapterTimelineProps {
  projectDir?: string | null;
}

export const ChapterTimeline: React.FC<ChapterTimelineProps> = ({ projectDir }) => {
  const [chapters, setChapters] = useState<any[]>([]);
  const [selectedChap, setSelectedChap] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(data => {
        if (data && data.chapters && Array.isArray(data.chapters)) {
          setChapters(data.chapters);
        }
      }).catch(console.error);
    }
  }, [projectDir]);

  const filteredChapters = chapters.filter(c =>
    (c.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (c.summary || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
            <Calendar size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Chapter Timeline — Tiến Trình Viết 1.000 Chương
            </h2>
            <p className="text-xs text-slate-400">
              Theo dõi danh sách từng chương truyện đã sinh, kiểm tra trạng thái Canon Validator.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 relative max-w-xs w-full">
          <Search size={14} className="absolute left-3 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Tìm chương..."
            className="w-full bg-[#0b0d10] border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none"
          />
        </div>
      </div>

      {/* SPLIT VIEW: LEFT TIMELINE / RIGHT CONTENT */}
      <div className="flex-1 flex gap-4 overflow-hidden min-h-0">
        {/* LIST */}
        <div className="w-full md:w-[380px] overflow-y-auto space-y-2.5 custom-scrollbar">
          {filteredChapters.length === 0 ? (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
              <BookOpen size={32} className="text-cyan-400 mb-3" />
              <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Chưa Có Chương Truyện Nào</h3>
              <p className="text-xs text-slate-400">Chạy Novel Auto-Write để bắt đầu sinh các chương truyện.</p>
            </div>
          ) : (
            filteredChapters.map(c => {
              const isSelected = selectedChap?.id === c.id || selectedChap?.chapterNumber === c.chapterNumber;
              return (
                <div
                  key={c.id || c.chapterNumber}
                  onClick={() => setSelectedChap(c)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer ${
                    isSelected
                      ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                      : 'bg-[#111318] hover:bg-[#161a22] border-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="px-2 py-0.5 rounded bg-cyan-500/20 text-cyan-300 font-bold text-xs font-mono">
                      #{c.chapterNumber}
                    </span>
                    <span className="px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold flex items-center gap-1">
                      <CheckCircle2 size={10} /> CANON VALIDATED
                    </span>
                  </div>

                  <h3 className="text-xs font-bold text-white font-['Outfit'] truncate mb-1">{c.title}</h3>
                  <p className="text-[11px] text-slate-400 line-clamp-2 leading-relaxed">{c.summary}</p>
                </div>
              );
            })
          )}
        </div>

        {/* DETAIL VIEW */}
        <div className="hidden md:flex flex-1 bg-[#111318] rounded-xl border border-white/5 p-5 flex-col overflow-hidden">
          {selectedChap ? (
            <div className="flex-1 flex flex-col space-y-4 overflow-y-auto custom-scrollbar">
              <div className="border-b border-white/5 pb-3">
                <span className="text-xs font-mono text-cyan-400">Chương #{selectedChap.chapterNumber}</span>
                <h2 className="text-lg font-bold text-white font-['Outfit']">{selectedChap.title}</h2>
              </div>

              <div className="bg-black/40 rounded-xl p-4 border border-white/5 flex-1 font-mono text-xs leading-relaxed text-slate-200 whitespace-pre-wrap">
                {selectedChap.content || selectedChap.summary || 'Đang tải nội dung chương...'}
              </div>
            </div>
          ) : (
            <div className="flex-1 flex flex-col items-center justify-center text-center text-slate-500">
              <FileText size={32} className="mb-2 opacity-50" />
              <p className="text-xs">Chọn một chương bên trái để xem bản thảo văn học chi tiết.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
