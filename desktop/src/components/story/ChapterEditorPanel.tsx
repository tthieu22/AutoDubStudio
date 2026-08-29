import React from 'react';
import { SlidersHorizontal, X, Save, FileText, Check, FileJson, Copy, Edit3, Sparkles, RefreshCw, Trash2 } from 'lucide-react';
import { Chapter } from './StoryWorkspace';

export interface CopyConfig {
  includeTitle: boolean;
  includeCharacters: boolean;
  includeSummary: boolean;
  includeContent: boolean;
  includeMetadata: boolean;
}

interface ChapterEditorPanelProps {
  selectedChap: Chapter;
  isEditing: boolean;
  editingTitle: string;
  editingSummary: string;
  editingContent: string;
  editingChars: string;
  showCopyConfig: boolean;
  copyConfig: CopyConfig;
  copiedChapId: string | null;
  copiedType: 'content' | 'json' | 'formatted' | null;
  setEditingTitle: (val: string) => void;
  setEditingSummary: (val: string) => void;
  setEditingContent: (val: string) => void;
  setEditingChars: (val: string) => void;
  setShowCopyConfig: (val: boolean) => void;
  setCopyConfig: (cfg: CopyConfig) => void;
  setIsEditing: (val: boolean) => void;
  onSaveEdit: () => void;
  onSelectChapter: (chap: Chapter) => void;
  onCopyContentOnly: (chap: Chapter) => void;
  onCopyJson: (chap: Chapter) => void;
  onCopyFormattedText: (chap: Chapter) => void;
  onClose: () => void;
  onDeleteChapter: (id: string) => void;
}

export const ChapterEditorPanel: React.FC<ChapterEditorPanelProps> = ({
  selectedChap,
  isEditing,
  editingTitle,
  editingSummary,
  editingContent,
  editingChars,
  showCopyConfig,
  copyConfig,
  copiedChapId,
  copiedType,
  setEditingTitle,
  setEditingSummary,
  setEditingContent,
  setEditingChars,
  setShowCopyConfig,
  setCopyConfig,
  setIsEditing,
  onSaveEdit,
  onSelectChapter,
  onCopyContentOnly,
  onCopyJson,
  onCopyFormattedText,
  onClose,
  onDeleteChapter,
}) => {
  return (
    <div className="flex-1 overflow-y-auto bg-[#111318] rounded-xl border border-white/5 p-5 space-y-5 custom-scrollbar">
      {/* DETAIL HEADER */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-300 font-bold text-sm flex items-center justify-center border border-cyan-500/30 font-['Outfit']">
            #{selectedChap.chapterNumber}
          </span>
          <div>
            {isEditing ? (
              <input
                value={editingTitle}
                onChange={e => setEditingTitle(e.target.value)}
                className="bg-black/40 border border-cyan-500/30 rounded-lg px-3 py-1.5 text-sm font-bold text-white font-['Outfit'] focus:outline-none focus:border-cyan-400 w-full max-w-sm"
                placeholder="Tên chương..."
              />
            ) : (
              <h3 className="text-lg font-bold text-white font-['Outfit'] tracking-tight">{selectedChap.title}</h3>
            )}
            <p className="text-[11px] text-slate-500 mt-0.5">ID: {selectedChap.id}</p>
          </div>
        </div>

        <div className="flex items-center gap-2 relative">
          {/* CONFIG POPUP TOGGLE */}
          <button
            onClick={() => setShowCopyConfig(!showCopyConfig)}
            className={`p-1.5 rounded-lg border transition-all cursor-pointer ${
              showCopyConfig
                ? 'bg-cyan-500/20 text-cyan-300 border-cyan-500/40'
                : 'bg-white/5 hover:bg-white/10 text-slate-400 border-white/10'
            }`}
            title="Cấu hình các trường thông tin sao chép"
          >
            <SlidersHorizontal size={14} />
          </button>

          {showCopyConfig && (
            <div className="absolute right-0 top-10 z-50 w-64 bg-[#161922] border border-white/15 rounded-xl p-3.5 shadow-2xl space-y-2 backdrop-blur-xl animate-in fade-in zoom-in-95">
              <div className="flex items-center justify-between border-b border-white/10 pb-2 mb-1">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <SlidersHorizontal size={13} className="text-cyan-400" /> Cấu hình sao chép
                </span>
                <button onClick={() => setShowCopyConfig(false)} className="text-slate-400 hover:text-white p-0.5">
                  <X size={13} />
                </button>
              </div>

              <div className="space-y-2 text-xs">
                <label className="flex items-center gap-2 text-slate-300 hover:text-white cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={copyConfig.includeTitle}
                    onChange={e => setCopyConfig({ ...copyConfig, includeTitle: e.target.checked })}
                    className="rounded border-white/20 bg-black/40 text-cyan-500 focus:ring-0"
                  />
                  Tiêu đề chương
                </label>
                <label className="flex items-center gap-2 text-slate-300 hover:text-white cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={copyConfig.includeCharacters}
                    onChange={e => setCopyConfig({ ...copyConfig, includeCharacters: e.target.checked })}
                    className="rounded border-white/20 bg-black/40 text-cyan-500 focus:ring-0"
                  />
                  Danh sách nhân vật
                </label>
                <label className="flex items-center gap-2 text-slate-300 hover:text-white cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={copyConfig.includeSummary}
                    onChange={e => setCopyConfig({ ...copyConfig, includeSummary: e.target.checked })}
                    className="rounded border-white/20 bg-black/40 text-cyan-500 focus:ring-0"
                  />
                  Tóm tắt nội dung
                </label>
                <label className="flex items-center gap-2 text-slate-300 hover:text-white cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={copyConfig.includeContent}
                    onChange={e => setCopyConfig({ ...copyConfig, includeContent: e.target.checked })}
                    className="rounded border-white/20 bg-black/40 text-cyan-500 focus:ring-0"
                  />
                  Kịch bản / Nội dung chương
                </label>
                <label className="flex items-center gap-2 text-slate-300 hover:text-white cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={copyConfig.includeMetadata}
                    onChange={e => setCopyConfig({ ...copyConfig, includeMetadata: e.target.checked })}
                    className="rounded border-white/20 bg-black/40 text-cyan-500 focus:ring-0"
                  />
                  Metadata (ID, Số chương, Scenes)
                </label>
              </div>
            </div>
          )}

          {isEditing ? (
            <>
              <button
                onClick={onSaveEdit}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
              >
                <Save size={13} /> Lưu
              </button>
              <button
                onClick={() => { setIsEditing(false); onSelectChapter(selectedChap); }}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
              >
                <X size={13} /> Hủy
              </button>
            </>
          ) : (
            <>
              <button
                onClick={() => onCopyContentOnly(selectedChap)}
                className={`px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                  copiedChapId === selectedChap.id && copiedType === 'content'
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                    : 'bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-300 border border-cyan-500/30'
                }`}
                title="Chỉ sao chép văn bản kịch bản"
              >
                {copiedChapId === selectedChap.id && copiedType === 'content' ? (
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
                onClick={() => onCopyJson(selectedChap)}
                className={`px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                  copiedChapId === selectedChap.id && copiedType === 'json'
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                    : 'bg-indigo-600/30 hover:bg-indigo-600/50 text-indigo-200 border border-indigo-500/30'
                }`}
                title="Sao chép toàn bộ thông tin dưới dạng JSON"
              >
                {copiedChapId === selectedChap.id && copiedType === 'json' ? (
                  <>
                    <Check size={13} /> Đã chép JSON
                  </>
                ) : (
                  <>
                    <FileJson size={13} /> Copy JSON
                  </>
                )}
              </button>

              <button
                onClick={() => onCopyFormattedText(selectedChap)}
                className={`px-3 py-1.5 rounded-lg font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                  copiedChapId === selectedChap.id && copiedType === 'formatted'
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-600/20'
                    : 'bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 border border-purple-500/30'
                }`}
                title="Sao chép các trường đã chọn dạng văn bản"
              >
                {copiedChapId === selectedChap.id && copiedType === 'formatted' ? (
                  <>
                    <Check size={13} /> Đã chép Tất cả
                  </>
                ) : (
                  <>
                    <Copy size={13} /> Copy Tất Cả
                  </>
                )}
              </button>

              <button
                onClick={() => setIsEditing(true)}
                className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
              >
                <Edit3 size={13} /> Chỉnh sửa
              </button>
              <button
                onClick={onClose}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
              >
                <X size={13} /> Đóng
              </button>
            </>
          )}
        </div>
      </div>

      {/* METADATA ROW */}
      <div className="grid grid-cols-3 gap-3">
        <div className="bg-black/30 rounded-lg p-3 border border-white/5">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 font-semibold">Chương số</p>
          <p className="text-sm font-bold text-cyan-400 font-['Outfit']">#{selectedChap.chapterNumber}</p>
        </div>
        <div className="bg-black/30 rounded-lg p-3 border border-white/5">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 font-semibold">Số Scenes</p>
          <p className="text-sm font-bold text-indigo-400 font-['Outfit']">{selectedChap.scenesCount}</p>
        </div>
        <div className="bg-black/30 rounded-lg p-3 border border-white/5">
          <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 font-semibold">Nhân vật</p>
          <p className="text-sm font-bold text-amber-400 font-['Outfit']">{selectedChap.characters.length}</p>
        </div>
      </div>

      {/* CHARACTERS SECTION */}
      <div>
        <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mb-2 block">
          Nhân Vật Trong Chương
        </label>
        {isEditing ? (
          <input
            value={editingChars}
            onChange={e => setEditingChars(e.target.value)}
            className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50"
            placeholder="Nhân vật 1, Nhân vật 2, ..."
          />
        ) : (
          <div className="flex flex-wrap gap-1.5">
            {selectedChap.characters.map((char, i) => (
              <span key={i} className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[11px] font-semibold">
                {char}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* SUMMARY SECTION */}
      <div>
        <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mb-2 block">
          Tóm Tắt Nội Dung
        </label>
        {isEditing ? (
          <textarea
            value={editingSummary}
            onChange={e => setEditingSummary(e.target.value)}
            rows={3}
            className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50 resize-none"
            placeholder="Tóm tắt nội dung chương..."
          />
        ) : (
          <div className="bg-black/30 rounded-lg p-3 border border-white/5">
            <p className="text-xs text-slate-300 leading-relaxed">{selectedChap.summary}</p>
          </div>
        )}
      </div>

      {/* CONTENT / SCRIPT SECTION */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">
            Nội Dung / Kịch Bản Chương
          </label>
          {!isEditing && (
            <button
              onClick={() => onCopyContentOnly(selectedChap)}
              className="text-[11px] text-cyan-400 hover:text-cyan-300 font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              {copiedChapId === selectedChap.id && copiedType === 'content' ? (
                <>
                  <Check size={12} className="text-emerald-400" /> <span className="text-emerald-400 font-bold">Đã sao chép</span>
                </>
              ) : (
                <>
                  <FileText size={12} /> Sao chép kịch bản
                </>
              )}
            </button>
          )}
        </div>
        {isEditing ? (
          <textarea
            value={editingContent}
            onChange={e => setEditingContent(e.target.value)}
            rows={12}
            className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50 resize-none font-mono leading-relaxed"
            placeholder="Nội dung đầy đủ hoặc kịch bản AI của chương truyện..."
          />
        ) : (
          <div className="bg-black/30 rounded-lg p-4 border border-white/5 min-h-[180px]">
            {selectedChap.content ? (
              <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap font-mono">{selectedChap.content}</p>
            ) : selectedChap.summary && selectedChap.summary !== 'Chapter summary text...' ? (
              <div>
                <p className="text-[10px] text-cyan-500/60 uppercase tracking-wider font-semibold mb-2">Tóm tắt (chưa có kịch bản chi tiết)</p>
                <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{selectedChap.summary}</p>
                <div className="mt-4 pt-3 border-t border-white/5 flex items-center gap-2">
                  <button
                    onClick={() => setIsEditing(true)}
                    className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 font-semibold text-[11px] flex items-center gap-1.5 border border-cyan-500/20 transition-all cursor-pointer"
                  >
                    <Edit3 size={12} /> Viết kịch bản chi tiết
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center h-full min-h-[140px] text-center">
                <FileText size={24} className="text-slate-600 mb-2" />
                <p className="text-[11px] text-slate-500 mb-3">Chương chưa có nội dung kịch bản</p>
                <button
                  onClick={() => setIsEditing(true)}
                  className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 font-semibold text-[11px] flex items-center gap-1.5 border border-cyan-500/20 transition-all cursor-pointer"
                >
                  <Edit3 size={12} /> Viết nội dung
                </button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* ACTION BAR */}
      <div className="flex items-center gap-2 pt-3 border-t border-white/5">
        <button
          className="px-3.5 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 font-semibold text-xs flex items-center gap-1.5 border border-indigo-500/20 transition-all cursor-pointer"
        >
          <Sparkles size={13} /> AI Viết Lại Kịch Bản
        </button>
        <button
          className="px-3.5 py-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 font-semibold text-xs flex items-center gap-1.5 border border-purple-500/20 transition-all cursor-pointer"
        >
          <RefreshCw size={13} /> Tạo Scenes Tự Động
        </button>
        <button
          onClick={() => onDeleteChapter(selectedChap.id)}
          className="px-3.5 py-2 rounded-lg bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 font-semibold text-xs flex items-center gap-1.5 border border-rose-500/20 transition-all cursor-pointer ml-auto"
        >
          <Trash2 size={13} /> Xóa Chương
        </button>
      </div>
    </div>
  );
};
