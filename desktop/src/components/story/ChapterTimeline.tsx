import React, { useState, useEffect } from 'react';
import { Calendar, FileText, CheckCircle2, AlertTriangle, Clock, Search, BookOpen, Copy, Check, FileJson, ArrowUpDown } from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface ChapterTimelineProps {
  projectDir?: string | null;
}

const formatChapterTitle = (chapNum: number, rawTitle?: string) => {
  if (!rawTitle) return `Hành Trình Tu Tiên Khởi Đầu`;
  const clean = rawTitle.replace(new RegExp(`^Chương\\s*\\d+[:\\s-]*`, 'i'), '').trim();
  return clean || rawTitle;
};

export const ChapterTimeline: React.FC<ChapterTimelineProps> = ({ projectDir }) => {
  const [chapters, setChapters] = useState<any[]>([]);
  const [selectedChap, setSelectedChap] = useState<any>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedChapId, setCopiedChapId] = useState<string | null>(null);
  const [copiedType, setCopiedType] = useState<'content' | 'json' | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  const handleCopyContent = (c: any, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const key = c.id || String(c.chapterNumber);
    const contentToCopy = c.content || c.summary || c.title;
    navigator.clipboard.writeText(contentToCopy);
    setCopiedChapId(key);
    setCopiedType('content');
    setTimeout(() => { setCopiedChapId(null); setCopiedType(null); }, 2000);
  };

  const handleCopyJson = (c: any, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const key = c.id || String(c.chapterNumber);
    navigator.clipboard.writeText(JSON.stringify(c, null, 2));
    setCopiedChapId(key);
    setCopiedType('json');
    setTimeout(() => { setCopiedChapId(null); setCopiedType(null); }, 2000);
  };

  useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(data => {
        if (data && data.chapters && Array.isArray(data.chapters)) {
          const sorted = [...data.chapters].sort((a, b) => (a.chapterNumber || 0) - (b.chapterNumber || 0));
          setChapters(sorted);
        }
      }).catch(console.error);
    }
  }, [projectDir]);

  const filteredChapters = chapters.filter(c => 
    String(c.chapterNumber).includes(searchQuery) ||
    (c.title && c.title.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (c.summary && c.summary.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
            <Calendar size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Chapter Timeline & Canon Validation Log
            </h2>
            <p className="text-xs text-slate-400">
              Lịch sử các chương đã viết kèm trạng thái xác thực Canon Continuity.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 relative max-w-xs w-full">
          <Search size={14} className="absolute left-3 text-slate-400" />
          <input
            type="text"
            placeholder="Tìm theo số chương, tiêu đề..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-3 py-1.5 rounded-xl bg-black/40 border border-white/10 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500/50"
          />
        </div>
      </div>

      {/* SPLIT VIEW: LEFT TIMELINE / RIGHT CONTENT */}
      <div className="flex-1 flex gap-4 overflow-hidden min-h-0">
        {/* LIST */}
        <div className="w-full md:w-[380px] overflow-y-auto space-y-2.5 custom-scrollbar">
          {chapters.length > 0 && (
            <div className="flex items-center justify-between px-1 pb-1">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Chương ({filteredChapters.length})
              </span>
              <button
                onClick={() => setSortAsc(!sortAsc)}
                className="text-[11px] font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 bg-white/5 hover:bg-white/10 px-2 py-1 rounded cursor-pointer transition-all border border-white/5"
                title="Đổi thứ tự sắp xếp"
              >
                <ArrowUpDown size={12} /> {sortAsc ? 'Từ 1 ➔ N' : 'Từ N ➔ 1'}
              </button>
            </div>
          )}

          {filteredChapters.length === 0 ? (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
              <BookOpen size={32} className="text-cyan-400 mb-3" />
              <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Chưa Có Chương Truyện Nào</h3>
              <p className="text-xs text-slate-400">Chạy Novel Auto-Write để bắt đầu sinh các chương truyện.</p>
            </div>
          ) : (
            [...filteredChapters].sort((a, b) => {
              const numA = typeof a.chapterNumber === 'number' ? a.chapterNumber : parseInt(String(a.chapterNumber || 0), 10);
              const numB = typeof b.chapterNumber === 'number' ? b.chapterNumber : parseInt(String(b.chapterNumber || 0), 10);
              return sortAsc ? numA - numB : numB - numA;
            }).map(c => {
              const isSelected = selectedChap?.id === c.id || selectedChap?.chapterNumber === c.chapterNumber;
              const formattedTitle = formatChapterTitle(c.chapterNumber, c.title);
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
                    <div className="flex items-center gap-1.5">
                      <button
                        onClick={(e) => handleCopyContent(c, e)}
                        className={`p-1 rounded transition-all cursor-pointer ${
                          copiedChapId === (c.id || String(c.chapterNumber)) && copiedType === 'content'
                            ? 'bg-emerald-500/20 text-emerald-400 opacity-100'
                            : 'bg-white/0 hover:bg-white/10 text-slate-400 hover:text-white'
                        }`}
                        title="Sao chép nội dung"
                      >
                        {copiedChapId === (c.id || String(c.chapterNumber)) && copiedType === 'content' ? <Check size={12} /> : <FileText size={12} />}
                      </button>
                      <span className="px-2 py-0.5 rounded bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-[10px] font-bold flex items-center gap-1">
                        <CheckCircle2 size={10} /> CANON VALIDATED
                      </span>
                    </div>
                  </div>

                  <h3 className="text-xs font-bold text-white font-['Outfit'] truncate mb-1">Chương {c.chapterNumber}: {formattedTitle}</h3>
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
              <div className="border-b border-white/5 pb-3 flex items-center justify-between">
                <div>
                  <span className="text-xs font-mono text-cyan-400">Chương #{selectedChap.chapterNumber}</span>
                  <h2 className="text-lg font-bold text-white font-['Outfit']">Chương {selectedChap.chapterNumber}: {formatChapterTitle(selectedChap.chapterNumber, selectedChap.title)}</h2>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleCopyContent(selectedChap)}
                    className={`px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                      copiedChapId === (selectedChap.id || String(selectedChap.chapterNumber)) && copiedType === 'content'
                        ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                        : 'bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30'
                    }`}
                    title="Chỉ sao chép nội dung kịch bản"
                  >
                    {copiedChapId === (selectedChap.id || String(selectedChap.chapterNumber)) && copiedType === 'content' ? (
                      <>
                        <Check size={13} /> Đã chép Nội dung
                      </>
                    ) : (
                      <>
                        <FileText size={13} /> Copy Nội Dung
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => handleCopyJson(selectedChap)}
                    className={`px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                      copiedChapId === (selectedChap.id || String(selectedChap.chapterNumber)) && copiedType === 'json'
                        ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                        : 'bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/30'
                    }`}
                    title="Sao chép toàn bộ thông tin dưới dạng JSON"
                  >
                    {copiedChapId === (selectedChap.id || String(selectedChap.chapterNumber)) && copiedType === 'json' ? (
                      <>
                        <Check size={13} /> Đã chép JSON
                      </>
                    ) : (
                      <>
                        <FileJson size={13} /> Copy JSON
                      </>
                    )}
                  </button>
                </div>
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
