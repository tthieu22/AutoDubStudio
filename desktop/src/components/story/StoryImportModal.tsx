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
  Copy
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';
import { DiscoveryReviewModal, DiscoveryRegistryData, DiscoveredChapter } from './DiscoveryReviewModal';

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
  { id: 'meme', name: 'TikTok Meme & Hài Hước', desc: 'Bắt trend TikTok (Tuyệt đối điện ảnh, Server gốc, Thu thập dữ liệu xã hội...)' },
  { id: 'ancient', name: 'Cổ Trang & Tiên Hiệp (Trùng Sinh)', desc: 'Trùng sinh nghịch thiên cải mệnh, văn phong hoa mỹ kiếm hiệp.' },
  { id: 'emotional', name: 'U Buồn & Chữa Lành (Chill Lofi)', desc: 'Giọng kể da diết, chữa lành tâm hồn, lắng đọng cảm xúc.' },
  { id: 'dramatic', name: 'Review Phim Kịch Tính (Hook 3s)', desc: 'Hook 3 giây đầu, pha lật kèo kinh hoàng, tiết tấu dồn dập.' },
  { id: 'summary', name: 'Tóm Tắt Nhanh (3 Phút Short)', desc: 'Tóm tắt súc tích cao trào chính cho Video Short/Reels.' }
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
  const [availableModels, setAvailableModels] = useState<string[]>([]);
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(false);

  const fetchLocalModels = async () => {
    setIsLoadingModels(true);
    try {
      const models = await PythonEngineService.getOllamaModels();
      setAvailableModels(models);
      if (models.length > 0 && !models.includes(qwenModel)) {
        setQwenModel(models[0]);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoadingModels(false);
    }
  };

  React.useEffect(() => {
    if (isOpen) {
      fetchLocalModels();
    }
  }, [isOpen]);

  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [storyInfo, setStoryInfo] = useState<{ title: string; author: string; totalChapters: number } | null>(null);
  const [chapters, setChapters] = useState<ChapterItem[]>([]);
  const [isDownloading, setIsDownloading] = useState(false);
  const [progress, setProgress] = useState(0);

  const [discoveryRegistry, setDiscoveryRegistry] = useState<DiscoveryRegistryData | null>(null);
  const [isReviewOpen, setIsReviewOpen] = useState(false);
  const [discoveryStage, setDiscoveryStage] = useState('');
  const [discoveryPercent, setDiscoveryPercent] = useState(0);
  const [discoveryLogs, setDiscoveryLogs] = useState<string[]>([]);

  if (!isOpen) return null;

  const handleAnalyzeUrl = async () => {
    if (!urlInput.trim()) return;
    setIsAnalyzing(true);
    setDiscoveryPercent(5);
    setDiscoveryStage('Đang kết nối website và phân tích HTML...');
    setDiscoveryLogs([`[${new Date().toLocaleTimeString()}] Bắt đầu phân tích URL: ${urlInput.trim()}`]);

    const unlistenPromise = PythonEngineService.subscribeDiscoveryProgress((evt) => {
      if (evt) {
        if (evt.percent) setDiscoveryPercent(evt.percent);
        if (evt.message) {
          setDiscoveryStage(evt.message);
          setDiscoveryLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ${evt.message}`]);
        }
      }
    });

    try {
      const res = await PythonEngineService.discoverStoryUrl(urlInput.trim(), projectDir || undefined);
      const unlisten = await unlistenPromise;
      if (typeof unlisten === 'function') unlisten();
      setIsAnalyzing(false);

      if (res && res.chapters) {
        setDiscoveryLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Phân tích thành công! Phát hiện ${res.chapters.length} chương.`]);
        setDiscoveryRegistry(res);
        setIsReviewOpen(true);
      } else {
        setDiscoveryLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Lỗi: Kết quả không có dữ liệu chương.`]);
        alert(`Không phát hiện được chương từ URL này. Vui lòng kiểm tra lại đường dẫn.`);
      }
    } catch (e: any) {
      const unlisten = await unlistenPromise;
      if (typeof unlisten === 'function') unlisten();
      setIsAnalyzing(false);
      const errMsg = e?.message || String(e);
      setDiscoveryLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] ❌ Lỗi: ${errMsg}`]);
      alert(`Phân tích URL thất bại: ${errMsg}`);
    }
  };

  const handleApproveDiscovery = (selectedChapters: DiscoveredChapter[]) => {
    setIsReviewOpen(false);
    const converted: ChapterItem[] = selectedChapters.map(c => ({
      number: c.number,
      title: c.title,
      url: c.url,
      selected: true,
      status: 'PENDING'
    }));

    setStoryInfo({
      title: urlInput.split('/').pop()?.replace(/-/g, ' ').toUpperCase() || 'TRUYỆN DISCOVERED',
      author: 'Web AutoDetect',
      totalChapters: converted.length
    });

    setChapters(converted);
  };

  const toggleSelectAll = (select: boolean) => {
    setChapters(prev => prev.map(c => ({ ...c, selected: select })));
  };

  const toggleChapterSelected = (num: number) => {
    setChapters(prev => prev.map(c => c.number === num ? { ...c, selected: !c.selected } : c));
  };

  const handleStartImport = async () => {
    const selectedList = chapters.filter(c => c.selected);
    if (selectedList.length === 0) {
      alert('Vui lòng chọn ít nhất một chương để tải!');
      return;
    }

    setIsDownloading(true);
    setProgress(0);

    const unlistenPromise = PythonEngineService.subscribeChapterImportProgress((evt) => {
      if (evt && typeof evt.percent === 'number') {
        setProgress(evt.percent);
      }
      if (evt && evt.stage === 'CHAPTER_COMPLETED' && evt.record) {
        setChapters(prev => prev.map(c => c.number === evt.record.number ? { ...c, status: evt.record.status === 'SUCCESS' ? 'SUCCESS' : 'FAILED' } : c));
      }
    });

    try {
      if (projectDir) {
        await PythonEngineService.startStoryImport(projectDir, selectedList);
      } else {
        // Fallback simulation mode
        for (let i = 0; i < selectedList.length; i++) {
          await new Promise(r => setTimeout(r, 100));
          setProgress(Math.round(((i + 1) / selectedList.length) * 100));
        }
      }
      const unlisten = await unlistenPromise;
      if (typeof unlisten === 'function') unlisten();
      setIsDownloading(false);
      onImportComplete?.(selectedList.length, narrationStyle);
    } catch (err: any) {
      const unlisten = await unlistenPromise;
      if (typeof unlisten === 'function') unlisten();
      setIsDownloading(false);
      alert(`Tải chương truyện thất bại: ${err?.message || err}`);
    }
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

            {/* REAL-TIME PROGRESS & LIVE LOG BOX */}
            {(isAnalyzing || discoveryLogs.length > 0) && (
              <div className="p-3 rounded-xl bg-[#111318] border border-purple-500/30 space-y-2 text-xs">
                <div className="flex items-center justify-between">
                  <span className="font-bold text-purple-300 flex items-center gap-1.5 font-['Outfit']">
                    {isAnalyzing ? <RefreshCw size={12} className="animate-spin text-purple-400" /> : <Check size={12} className="text-emerald-400" />}
                    <span>{discoveryStage || 'Tiến trình phân tích URL'}</span>
                  </span>
                  <div className="flex items-center gap-2">
                    <span className="font-mono font-bold text-cyan-400">{discoveryPercent}%</span>
                    {discoveryLogs.length > 0 && (
                      <button
                        onClick={() => navigator.clipboard.writeText(discoveryLogs.join('\n'))}
                        className="px-2 py-0.5 rounded bg-white/5 hover:bg-white/10 text-slate-300 hover:text-white text-[10px] flex items-center gap-1 transition-all border border-white/10 cursor-pointer select-none"
                        title="Sao chép log"
                      >
                        <Copy size={11} />
                        <span>Sao chép</span>
                      </button>
                    )}
                  </div>
                </div>

                <div className="w-full bg-black/50 h-2 rounded-full overflow-hidden p-0.5 border border-white/5">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-purple-500 to-cyan-400 transition-all duration-300 shadow-sm shadow-purple-500/30"
                    style={{ width: `${discoveryPercent}%` }}
                  />
                </div>

                {/* LOG TERMINAL BOX */}
                <div 
                  className="max-h-28 overflow-y-auto bg-black/60 rounded-lg border border-white/5 p-2 font-mono text-[11px] space-y-1 text-slate-300 custom-scrollbar select-text cursor-text"
                  style={{ userSelect: 'text', WebkitUserSelect: 'text' }}
                >
                  {discoveryLogs.map((log, idx) => (
                    <div 
                      key={idx} 
                      className={log.includes('❌') ? 'text-rose-400 font-bold' : log.includes('thành công') ? 'text-emerald-300 font-bold' : 'text-slate-300'}
                      style={{ userSelect: 'text', WebkitUserSelect: 'text' }}
                    >
                      {log}
                    </div>
                  ))}
                </div>
              </div>
            )}

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
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 items-start">
                  <div>
                    <div className="flex items-center mb-1 h-5">
                      <label className="text-[11px] text-slate-400 font-medium">Phong cách diễn đạt</label>
                    </div>
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
                    <div className="flex items-center justify-between mb-1 h-5">
                      <label className="text-[11px] text-slate-400 font-medium truncate" title="Mô hình AI LLM (models/llm)">
                        Mô hình AI <span className="text-[10px] text-slate-500 font-normal">(models/llm)</span>
                      </label>
                      <button
                        onClick={fetchLocalModels}
                        disabled={isLoadingModels}
                        className="text-[10px] text-purple-400 hover:text-purple-300 flex items-center gap-1 font-semibold whitespace-nowrap bg-purple-500/10 hover:bg-purple-500/20 px-1.5 py-0.5 rounded border border-purple-500/20 transition-all cursor-pointer"
                        title="Quét lại thư mục models/llm"
                      >
                        <RefreshCw size={10} className={isLoadingModels ? 'animate-spin' : ''} />
                        <span>Quét lại</span>
                      </button>
                    </div>
                    <select
                      value={qwenModel}
                      onChange={e => setQwenModel(e.target.value)}
                      className="w-full bg-[#111318] border border-white/10 rounded-lg p-1.5 text-xs text-slate-200 focus:outline-none font-mono"
                    >
                      {availableModels.length === 0 ? (
                        <option value="qwen2.5-3b-instruct-q4_k_m.gguf">qwen2.5-3b-instruct-q4_k_m.gguf</option>
                      ) : (
                        availableModels.map(m => (
                          <option key={m} value={m}>
                            {m}
                          </option>
                        ))
                      )}
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

        {/* DISCOVERY REVIEW MODAL */}
        <DiscoveryReviewModal
          isOpen={isReviewOpen}
          onClose={() => setIsReviewOpen(false)}
          registry={discoveryRegistry}
          onApprove={handleApproveDiscovery}
          onReScan={handleAnalyzeUrl}
        />
      </div>
    </div>
  );
};
