import React from 'react';
import { BookOpen, Download, ArrowUpDown, Check, FileText, FileJson, Trash2, Users, ChevronRight } from 'lucide-react';
import { Chapter } from './StoryWorkspace';

interface ChapterListSidebarProps {
  chapters: Chapter[];
  selectedChapId: string;
  sortAsc: boolean;
  copiedChapId: string | null;
  copiedType: 'content' | 'json' | 'formatted' | null;
  onSelectChapter: (chap: Chapter) => void;
  onToggleSort: () => void;
  onOpenImportModal: () => void;
  onCopyContentOnly: (chap: Chapter, e?: React.MouseEvent) => void;
  onCopyJson: (chap: Chapter, e?: React.MouseEvent) => void;
  onDeleteChapter: (id: string) => void;
}

export const ChapterListSidebar: React.FC<ChapterListSidebarProps> = ({
  chapters,
  selectedChapId,
  sortAsc,
  copiedChapId,
  copiedType,
  onSelectChapter,
  onToggleSort,
  onOpenImportModal,
  onCopyContentOnly,
  onCopyJson,
  onDeleteChapter,
}) => {
  const sortedChapters = [...chapters].sort((a, b) =>
    sortAsc ? (a.chapterNumber || 0) - (b.chapterNumber || 0) : (b.chapterNumber || 0) - (a.chapterNumber || 0)
  );

  return (
    <div className={`${selectedChapId ? 'w-[340px] min-w-[300px]' : 'w-full'} overflow-y-auto space-y-2.5 custom-scrollbar transition-all`}>
      {chapters.length > 0 && (
        <div className="flex items-center justify-between px-1 pb-1">
          <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
            Danh sách ({chapters.length} chương)
          </span>
          <button
            onClick={onToggleSort}
            className="text-[11px] font-semibold text-cyan-400 hover:text-cyan-300 flex items-center gap-1 bg-white/5 hover:bg-white/10 px-2 py-1 rounded cursor-pointer transition-all border border-white/5"
            title="Đổi thứ tự sắp xếp chương"
          >
            <ArrowUpDown size={12} /> {sortAsc ? 'Từ nhỏ ➔ lớn (1 ➔ N)' : 'Từ lớn ➔ nhỏ (N ➔ 1)'}
          </button>
        </div>
      )}

      {chapters.length === 0 ? (
        <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
          <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20 mb-4 shadow-lg shadow-cyan-500/10">
            <BookOpen size={28} />
          </div>
          <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Dự Án Chưa Có Chương Truyện Nào</h3>
          <p className="text-xs text-slate-400 max-w-md mb-5 leading-relaxed">
            Hãy nhập đường dẫn URL truyện web (Nettruyen, Webnovel...) hoặc tải file TXT để hệ thống tự động cào chương và dùng Qwen 2.5 AI viết lại kịch bản.
          </p>
          <button
            onClick={onOpenImportModal}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-bold text-xs flex items-center gap-2 shadow-xl shadow-cyan-500/20 transition-all cursor-pointer"
          >
            <Download size={16} /> Import Truyện (Web / File) Ngay
          </button>
        </div>
      ) : (
        sortedChapters.map(chap => {
          const isSelected = selectedChapId === chap.id;
          return (
            <div
              key={chap.id}
              onClick={() => onSelectChapter(chap)}
              className={`p-3.5 rounded-xl border transition-all cursor-pointer group ${
                isSelected
                  ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                  : 'bg-[#111318] hover:bg-[#161a22] border-white/5'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded bg-cyan-500/20 text-cyan-300 font-bold text-xs flex items-center justify-center border border-cyan-500/30 font-['Outfit']">
                    #{chap.chapterNumber}
                  </span>
                  <h3 className="text-sm font-bold text-white font-['Outfit'] truncate max-w-[200px]">{chap.title}</h3>
                </div>

                <div className="flex items-center gap-1">
                  <button
                    onClick={(e) => onCopyContentOnly(chap, e)}
                    className={`p-1 rounded transition-all cursor-pointer ${
                      copiedChapId === chap.id && copiedType === 'content'
                        ? 'bg-emerald-500/20 text-emerald-400 opacity-100'
                        : 'bg-white/0 hover:bg-white/10 text-slate-400 hover:text-white opacity-0 group-hover:opacity-100'
                    }`}
                    title="Copy chỉ nội dung"
                  >
                    {copiedChapId === chap.id && copiedType === 'content' ? <Check size={13} /> : <FileText size={13} />}
                  </button>
                  <button
                    onClick={(e) => onCopyJson(chap, e)}
                    className={`p-1 rounded transition-all cursor-pointer ${
                      copiedChapId === chap.id && copiedType === 'json'
                        ? 'bg-emerald-500/20 text-emerald-400 opacity-100'
                        : 'bg-white/0 hover:bg-white/10 text-slate-400 hover:text-white opacity-0 group-hover:opacity-100'
                    }`}
                    title="Copy định dạng JSON đầy đủ"
                  >
                    {copiedChapId === chap.id && copiedType === 'json' ? <Check size={13} /> : <FileJson size={13} />}
                  </button>
                  <button
                    onClick={(e) => { e.stopPropagation(); onDeleteChapter(chap.id); }}
                    className="p-1 rounded bg-rose-500/0 hover:bg-rose-500/20 text-transparent group-hover:text-rose-400 transition-all cursor-pointer"
                    title="Xóa chương"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              </div>

              <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2 mb-2">{chap.summary}</p>

              <div className="flex items-center justify-between text-[11px] text-slate-500">
                <div className="flex items-center gap-1">
                  <Users size={11} />
                  <span className="truncate max-w-[140px]">{chap.characters.join(', ')}</span>
                </div>
                {isSelected && (
                  <span className="text-cyan-400 font-semibold flex items-center gap-0.5">
                    Đang xem <ChevronRight size={11} />
                  </span>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
};
