import React from 'react';
import {
  Save, Sparkles, Search, Globe, Undo, Redo,
  AlertTriangle, BookOpen, ArrowRight
} from 'lucide-react';

interface SubtitleToolbarProps {
  projectStyle: string;
  searchQuery: string;
  hasChanges: boolean;
  isSaving: boolean;
  isTranslating: boolean;
  canUndo: boolean;
  canRedo: boolean;
  subtitlesCount: number;
  onSearchChange: (q: string) => void;
  onUndo: () => void;
  onRedo: () => void;
  onOpenDictModal: () => void;
  onOpenBulkModal: () => void;
  onOpenPreTtsModal: () => void;
  onAiRepairAll: () => void;
  onAutoPrepareTtsText: () => void;
  onSaveSubtitles: () => void;
  onProceedToVoices: () => void;
}

export const SubtitleToolbar: React.FC<SubtitleToolbarProps> = ({
  projectStyle,
  searchQuery,
  hasChanges,
  isSaving,
  isTranslating,
  canUndo,
  canRedo,
  subtitlesCount,
  onSearchChange,
  onUndo,
  onRedo,
  onOpenDictModal,
  onOpenBulkModal,
  onOpenPreTtsModal,
  onAiRepairAll,
  onAutoPrepareTtsText,
  onSaveSubtitles,
  onProceedToVoices,
}) => {
  return (
    <div className="flex flex-col md:flex-row items-stretch md:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
      {/* LEFT: TITLE & SEARCH */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
          <Globe size={18} />
        </div>
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Biên Tập Phụ Đề & Vietsub
            </h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-extrabold uppercase bg-cyan-500/10 text-cyan-400 border border-cyan-500/20">
              Style: {projectStyle}
            </span>
          </div>
          <p className="text-xs text-slate-400">
            Tổng số: <span className="text-white font-semibold">{subtitlesCount}</span> segments phụ đề
          </p>
        </div>
      </div>

      {/* SEARCH BAR */}
      <div className="relative flex-1 max-w-xs">
        <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => onSearchChange(e.target.value)}
          placeholder="Tìm kiếm nội dung..."
          className="w-full bg-[#161a22] border border-white/10 rounded-lg pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyan-500/50"
        />
      </div>

      {/* ACTIONS */}
      <div className="flex items-center gap-2 flex-wrap justify-end">
        {/* UNDO / REDO */}
        <div className="flex items-center bg-[#161a22] rounded-lg border border-white/10 p-0.5">
          <button
            onClick={onUndo}
            disabled={!canUndo}
            className="p-1.5 text-slate-300 hover:text-white disabled:text-slate-600 disabled:cursor-not-allowed rounded hover:bg-white/5 transition-colors"
            title="Hoàn tác (Undo)"
          >
            <Undo size={14} />
          </button>
          <div className="w-[1px] h-4 bg-white/10" />
          <button
            onClick={onRedo}
            disabled={!canRedo}
            className="p-1.5 text-slate-300 hover:text-white disabled:text-slate-600 disabled:cursor-not-allowed rounded hover:bg-white/5 transition-colors"
            title="Làm lại (Redo)"
          >
            <Redo size={14} />
          </button>
        </div>

        {/* DICTIONARY MODAL */}
        <button
          onClick={onOpenDictModal}
          className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 text-amber-300 border border-amber-500/20 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
          title="Mở Từ điển phát âm & Phiên âm Tiếng Việt"
        >
          <BookOpen size={13} /> Từ điển
        </button>

        {/* BULK VIETSUB MODAL */}
        <button
          onClick={onOpenBulkModal}
          disabled={isTranslating}
          className="px-3 py-1.5 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
          title="Dịch tự động hàng loạt toàn bộ phụ đề"
        >
          <Sparkles size={13} /> Dịch Hàng Loạt
        </button>

        {/* PRE-TTS VALIDATE MODAL */}
        <button
          onClick={onOpenPreTtsModal}
          className="px-3 py-1.5 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-300 border border-emerald-500/20 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
          title="Kiểm tra chất lượng phụ đề trước khi tạo giọng nói TTS"
        >
          <AlertTriangle size={13} /> Kiểm Tra Pre-TTS
        </button>

        {/* AI REPAIR ALL */}
        <button
          onClick={onAiRepairAll}
          className="px-3 py-1.5 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 border border-indigo-500/30 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
          title="Dùng AI tự động sửa các câu dịch lỗi"
        >
          <Sparkles size={13} /> Sửa Lỗi Dịch AI
        </button>

        {/* SAVE SUBTITLES */}
        <button
          onClick={onSaveSubtitles}
          disabled={isSaving}
          className={`px-3.5 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
            hasChanges
              ? 'bg-amber-500 hover:bg-amber-400 text-black shadow-md shadow-amber-500/20'
              : 'bg-emerald-600 hover:bg-emerald-500 text-white shadow-md shadow-emerald-600/20'
          }`}
        >
          <Save size={13} /> {isSaving ? 'Đang lưu...' : hasChanges ? 'Lưu Thay Đổi' : 'Đã Lưu'}
        </button>

        {/* PROCEED TO VOICES */}
        <button
          onClick={onProceedToVoices}
          className="px-4 py-1.5 rounded-lg bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition-all cursor-pointer"
        >
          Tiếp Theo: Lồng Tiếng <ArrowRight size={13} />
        </button>
      </div>
    </div>
  );
};
