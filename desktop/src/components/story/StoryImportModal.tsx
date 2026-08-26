import React, { useState } from 'react';
import { 
  Globe, 
  FileText, 
  BookOpen, 
  FileJson, 
  X, 
  Search, 
  Check, 
  RefreshCw, 
  AlertCircle, 
  Download, 
  CheckSquare, 
  Square,
  Sparkles,
  Smile,
  Zap,
  Flame,
  Heart,
  Film
} from 'lucide-react';

interface StoryImportModalProps {
  isOpen: boolean;
  onClose: () => void;
  projectDir?: string | null;
  onImportComplete?: (importedCount: number, style?: string) => void;
}

export interface ChapterItem {
  number: number;
  title: string;
  url: string;
  selected: boolean;
  status: 'PENDING' | 'DOWNLOADING' | 'SUCCESS' | 'FAILED';
  errorMsg?: string;
}

const NARRATION_STYLES = [
  { id: 'meme', name: '🤣 TikTok Meme & Hài Hước 2026', desc: 'Bắt trend TikTok (Tuyệt đối điện ảnh, Server gốc, Thu thập dữ liệu xã hội...)' },
  { id: 'ancient', name: '🎭 Cổ Trang & Tiên Hiệp (Trùng Sinh)', desc: 'Trùng sinh nghịch thiên cải mệnh, văn phong hoa mỹ kiếm hiệp.' },
  { id: 'emotional', name: '😢 U Buồn & Chữa Lành (Chill Lofi)', desc: 'Giọng kể da diết, chữa lành tâm hồn, lắng đọng cảm xúc.' },
  { id: 'dramatic', name: '⚡ Review Phim Kịch Tính (Hook 3s)', desc: 'Hook 3 giây đầu, pha lật kèo kinh hoàng, tiết tấu dồn dập.' },
  { id: 'summary', name: '🌟 Tóm Tắt Nhanh (3 Phút Short)', desc: 'Tóm tắt súc tích cao trào chính cho Video Short/Reels.' }
];

export const StoryImportModal: React.FC<StoryImportModalProps> = ({
  isOpen,
  onClose,
  projectDir,
  onImportComplete
}) => {
  const [importType, setImportType] = useState<'URL' | 'TXT' | 'EPUB' | 'JSON'>('URL');
  const [urlInput, setUrlInput] = useState('https://webnovel.vn/mang-theo-sieu-thi-tro-ve-thap-nien-80/');
  
  const [narrationStyle, setNarrationStyle] = useState<string>('meme');
  const [useQwenReteller, setUseQwenReteller] = useState<boolean>(true);
  const [qwenModel, setQwenModel] = useState<string>('qwen2.5:7b-instruct');

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [storyInfo, setStoryInfo] = useState<{ title: string; author: string; totalChapters: number } | null>(null);
  const [chapters, setChapters] = useState<ChapterItem[]>([]);
  
  const [isDownloading, setIsDownloading] = useState(false);
  const [progress, setProgress] = useState(0);

  if (!isOpen) return null;

  const handleAnalyzeUrl = async () => {
    if (!urlInput.trim()) return;
    setIsAnalyzing(true);
    
    setTimeout(() => {
      const mockList: ChapterItem[] = Array.from({ length: 30 }, (_, i) => ({
        number: i + 1,
        title: `Chương ${i + 1}: Hành Trình Mới (Phần ${i + 1})`,
        url: `${urlInput}/chuong-${i + 1}`,
        selected: true,
        status: 'PENDING'
      }));

      setStoryInfo({
        title: 'Mang Theo Siêu Thị Trở Về Thập Niên 80',
        author: 'Tác giả Webnovel',
        totalChapters: mockList.length
      });
      setChapters(mockList);
      setIsAnalyzing(false);
    }, 1000);
  };

  const toggleSelectAll = (select: boolean) => {
    setChapters(prev => prev.map(c => ({ ...c, selected: select })));
  };

  const toggleChapterSelected = (num: number) => {
    setChapters(prev => prev.map(c => c.number === num ? { ...c, selected: !c.selected } : c));
  };

  const handleStartImport = () => {
    const selectedCount = chapters.filter(c => c.selected).length;
    if (selectedCount === 0) {
      alert('Vui lòng chọn ít nhất một chương để tải!');
      return;
    }

    setIsDownloading(true);
    setProgress(0);

    let completed = 0;
    const interval = setInterval(() => {
      completed += 1;
      const pct = Math.round((completed / selectedCount) * 100);
      setProgress(pct);

      setChapters(prev => {
        const next = [...prev];
        const targetIdx = next.findIndex(c => c.selected && c.status === 'PENDING');
        if (targetIdx !== -1) {
          next[targetIdx].status = 'SUCCESS';
        }
        return next;
      });

      if (completed >= selectedCount) {
        clearInterval(interval);
        setIsDownloading(false);
        onImportComplete?.(selectedCount, narrationStyle);
      }
    }, 150);
  };

  const selectedCount = chapters.filter(c => c.selected).length;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111318] border border-white/10 rounded-2xl w-full max-w-2xl p-6 shadow-2xl flex flex-col max-h-[90vh] text-slate-100 font-sans">
        
        {/* HEADER */}
        <div className="flex items-center justify-between border-b border-white/5 pb-3 mb-4">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-purple-600/20 text-purple-400 flex items-center justify-center border border-purple-500/30">
              <Sparkles size={18} />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-['Outfit']">Import Truyện & Qwen 2.5 AI Story Reteller</h3>
              <p className="text-xs text-slate-400">Tự động tải chương từ Web/File và dùng Qwen 2.5 Instruct viết lại kịch bản</p>
            </div>
          </div>

          <button onClick={onClose} className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-white/10">
            <X size={16} />
          </button>
        </div>

        {/* IMPORT SOURCE TABS */}
        <div className="grid grid-cols-4 gap-2 mb-4">
          {[
            { id: 'URL', label: 'Web URL Importer', icon: <Globe size={14} /> },
            { id: 'TXT', label: 'File TXT / Directory', icon: <FileText size={14} /> },
            { id: 'EPUB', label: 'EPUB E-Book', icon: <BookOpen size={14} /> },
            { id: 'JSON', label: 'JSON Payload', icon: <FileJson size={14} /> }
          ].map(t => (
            <button
              key={t.id}
              onClick={() => setImportType(t.id as any)}
              className={`p-2 rounded-lg text-xs font-semibold flex items-center justify-center gap-1.5 transition-all ${
                importType === t.id
                  ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30 font-bold'
                  : 'bg-black/30 text-slate-400 hover:bg-white/5 hover:text-white'
              }`}
            >
              {t.icon} {t.label}
            </button>
          ))}
        </div>

        {/* URL CRAWLER & QWEN SETTINGS BODY */}
        {importType === 'URL' && (
          <div className="flex-1 flex flex-col overflow-hidden space-y-3">
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={urlInput}
                onChange={e => setUrlInput(e.target.value)}
                placeholder="Nhập URL truyện (e.g. https://webnovel.vn/...)"
                className="flex-1 bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500 font-mono"
              />
              <button
                onClick={handleAnalyzeUrl}
                disabled={isAnalyzing}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-purple-600/20"
              >
                {isAnalyzing ? <RefreshCw size={14} className="animate-spin" /> : <Search size={14} />}
                <span>{isAnalyzing ? 'Đang phân tích...' : 'Phân tích URL'}</span>
              </button>
            </div>

            {/* QWEN 2.5 NARRATION STYLE SELECTOR */}
            <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-purple-300 font-['Outfit'] uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles size={13} /> Phong Cách Kể Chuyện (Qwen 2.5 AI Reteller)
                </span>
                <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={useQwenReteller}
                    onChange={e => setUseQwenReteller(e.target.checked)}
                    className="accent-purple-500 rounded"
                  />
                  <span>Dùng Qwen 2.5 Viết Lại Kịch Bản</span>
                </label>
              </div>

              {useQwenReteller && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                  <div>
                    <label className="text-[11px] text-slate-400 font-medium block mb-1">Phong cách diễn đạt</label>
                    <select
                      value={narrationStyle}
                      onChange={e => setNarrationStyle(e.target.value)}
                      className="w-full bg-[#111318] border border-white/10 rounded-lg p-1.5 text-xs text-purple-300 font-bold focus:outline-none"
                    >
                      {NARRATION_STYLES.map(s => (
                        <option key={s.id} value={s.id}>
                          {s.name}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] text-slate-400 font-medium block mb-1">Mô hình AI LLM</label>
                    <select
                      value={qwenModel}
                      onChange={e => setQwenModel(e.target.value)}
                      className="w-full bg-[#111318] border border-white/10 rounded-lg p-1.5 text-xs text-slate-200 focus:outline-none"
                    >
                      <option value="qwen2.5:7b-instruct">Qwen 2.5 7B Instruct (Khuyên dùng)</option>
                      <option value="qwen2.5:3b-instruct">Qwen 2.5 3B Instruct (Nhanh / Nhẹ)</option>
                      <option value="qwen2.5:14b-instruct">Qwen 2.5 14B Instruct (Chất lượng cao)</option>
                    </select>
                  </div>
                </div>
              )}
            </div>

            {/* DETECTED STORY INFO */}
            {storyInfo && (
              <div className="p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 text-xs flex justify-between items-center">
                <div>
                  <h4 className="font-bold text-white font-['Outfit'] text-sm">{storyInfo.title}</h4>
                  <span className="text-slate-400">Tác giả: {storyInfo.author}</span>
                </div>
                <span className="px-2.5 py-1 rounded bg-purple-600/30 text-purple-300 font-mono font-bold">
                  {storyInfo.totalChapters} Chương phát hiện
                </span>
              </div>
            )}

            {/* CHAPTER CHECKBOX LIST */}
            {chapters.length > 0 && (
              <div className="flex-1 flex flex-col overflow-hidden bg-black/40 rounded-xl border border-white/5 p-3 space-y-2">
                <div className="flex items-center justify-between text-xs pb-2 border-b border-white/5">
                  <span className="font-bold text-slate-300 uppercase font-['Outfit']">
                    Chọn Chương ({selectedCount} / {chapters.length})
                  </span>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => toggleSelectAll(true)}
                      className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-slate-300 text-[11px] font-semibold"
                    >
                      Chọn tất cả
                    </button>
                    <button
                      onClick={() => toggleSelectAll(false)}
                      className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-slate-400 text-[11px]"
                    >
                      Bỏ chọn
                    </button>
                  </div>
                </div>

                <div className="flex-1 overflow-y-auto space-y-1 custom-scrollbar pr-1">
                  {chapters.map(c => (
                    <div
                      key={c.number}
                      onClick={() => toggleChapterSelected(c.number)}
                      className={`p-2 rounded-lg text-xs flex items-center justify-between cursor-pointer transition-all ${
                        c.selected ? 'bg-purple-600/15 border border-purple-500/30 text-slate-200' : 'bg-black/20 text-slate-500 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center gap-2">
                        {c.selected ? <CheckSquare size={14} className="text-purple-400" /> : <Square size={14} className="text-slate-600" />}
                        <span className="font-mono font-semibold">#{String(c.number).padStart(3, '0')}</span>
                        <span>{c.title}</span>
                      </div>

                      <div>
                        {c.status === 'SUCCESS' && <span className="text-emerald-400 font-bold text-[11px]">✓ Đã tải & Viết lại</span>}
                        {c.status === 'DOWNLOADING' && <span className="text-cyan-400 font-bold text-[11px] flex items-center gap-1"><RefreshCw size={10} className="animate-spin" /> Đang tải...</span>}
                        {c.status === 'FAILED' && <span className="text-rose-400 font-bold text-[11px]">× Lỗi (Thử lại)</span>}
                        {c.status === 'PENDING' && <span className="text-slate-600 text-[11px]">○ Chờ tải</span>}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* PROGRESS BAR */}
            {isDownloading && (
              <div className="space-y-1">
                <div className="flex justify-between text-xs font-mono text-purple-300 font-bold">
                  <span>Đang tải & viết lại kịch bản bằng Qwen 2.5...</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-black/60 h-2 rounded-full overflow-hidden border border-white/10">
                  <div className="bg-gradient-to-r from-purple-500 to-cyan-400 h-full rounded-full transition-all duration-200" style={{ width: `${progress}%` }} />
                </div>
              </div>
            )}
          </div>
        )}

        {/* FOOTER ACTIONS */}
        <div className="pt-4 border-t border-white/5 flex items-center justify-between">
          <button onClick={onClose} className="px-4 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-xs font-semibold text-slate-300">
            Hủy
          </button>

          {importType === 'URL' && chapters.length > 0 && (
            <button
              onClick={handleStartImport}
              disabled={isDownloading || selectedCount === 0}
              className="px-5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-extrabold text-xs flex items-center gap-2 shadow-lg shadow-purple-600/30"
            >
              <Sparkles size={14} /> TẢI & QWEN 2.5 VIẾT LẠI ({selectedCount} CHƯƠNG)
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
