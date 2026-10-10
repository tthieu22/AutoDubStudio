import React, { useState } from 'react';
import { 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  RefreshCw, 
  Search, 
  Check, 
  Sparkles, 
  X, 
  Download, 
  FileText, 
  Sliders,
  CheckSquare,
  Square,
  ChevronRight,
  ShieldCheck
} from 'lucide-react';

export interface DiscoveredChapter {
  number: number;
  title: string;
  url: string;
  discoveredBy?: string[];
  status: 'VALID' | 'MISSING' | 'INVALID' | 'PENDING';
}

export interface DiscoveryRegistryData {
  storyUrl: string;
  pattern: string | null;
  patternStatus: string;
  confidence: 'HIGH' | 'MEDIUM' | 'LOW';
  highestChapter: number;
  lowestChapter: number;
  totalCandidates: number;
  validatedCount: number;
  invalidCount: number;
  missingChapters: number[];
  discoveryMethods: string[];
  chapters: DiscoveredChapter[];
}

interface DiscoveryReviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  registry: DiscoveryRegistryData | null;
  onApprove: (selectedChapters: DiscoveredChapter[]) => void;
  onReScan?: () => void;
}

export const DiscoveryReviewModal: React.FC<DiscoveryReviewModalProps> = ({
  isOpen,
  onClose,
  registry,
  onApprove,
  onReScan
}) => {
  const [rangeMode, setRangeMode] = useState<'ALL' | '1-100' | '500-1000' | 'CUSTOM'>('ALL');
  const [startRange, setStartRange] = useState<number>(1);
  const [endRange, setEndRange] = useState<number>(100);
  const [selectedNumbers, setSelectedNumbers] = useState<Set<number>>(new Set());

  if (!isOpen || !registry) return null;

  const domain = registry.storyUrl ? registry.storyUrl.replace(/^https?:\/\//, '').split('/')[0] : 'story-site';
  const storyTitle = registry.storyUrl ? registry.storyUrl.split('/').pop()?.replace(/-/g, ' ').toUpperCase() : 'BÁCH LUYỆN THÀNH THẦN';

  // Initialize selected chapters based on range preset
  const getFilteredChapters = (): DiscoveredChapter[] => {
    let list = registry.chapters;
    if (rangeMode === '1-100') {
      return list.filter(c => c.number >= 1 && c.number <= 100);
    } else if (rangeMode === '500-1000') {
      return list.filter(c => c.number >= 500 && c.number <= 1000);
    } else if (rangeMode === 'CUSTOM') {
      return list.filter(c => c.number >= startRange && c.number <= endRange);
    }
    return list;
  };

  const activeChapters = getFilteredChapters();

  const handleApprove = () => {
    onApprove(activeChapters);
  };

  return (
    <div className="fixed inset-0 bg-black/80 backdrop-blur-md z-50 flex items-center justify-center p-4">
      <div className="bg-[#111318] border border-purple-500/30 rounded-2xl w-full max-w-4xl p-6 shadow-2xl flex flex-col max-h-[92vh] text-slate-100 font-sans">
        
        {/* HEADER */}
        <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-purple-600/20 text-purple-400 flex items-center justify-center border border-purple-500/30 shadow-inner">
              <ShieldCheck size={22} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold text-white font-['Outfit'] tracking-tight">
                  STORY DISCOVERY REVIEW
                </h2>
                <span className={`px-2.5 py-0.5 rounded-full text-[11px] font-extrabold uppercase font-mono tracking-wider border ${
                  registry.confidence === 'HIGH' 
                    ? 'bg-emerald-500/15 text-emerald-400 border-emerald-500/30'
                    : registry.confidence === 'MEDIUM'
                    ? 'bg-amber-500/15 text-amber-400 border-amber-500/30'
                    : 'bg-rose-500/15 text-rose-400 border-rose-500/30'
                }`}>
                  CONFIDENCE: {registry.confidence}
                </span>
              </div>
              <p className="text-xs text-slate-400 font-mono">
                Source: <span className="text-purple-300">{domain}</span> | URL: {registry.storyUrl}
              </p>
            </div>
          </div>

          <button onClick={onClose} className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-white/10">
            <X size={18} />
          </button>
        </div>

        {/* SUMMARY STATS GRID */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-1">
            <span className="text-[11px] text-slate-400 uppercase font-semibold block">Detected Pattern</span>
            <span className="text-xs font-mono font-bold text-cyan-300 truncate block" title={registry.pattern || 'N/A'}>
              {registry.pattern || 'Non-standard'}
            </span>
            <span className="text-[10px] text-emerald-400 font-bold block">Status: {registry.patternStatus}</span>
          </div>

          <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-1">
            <span className="text-[11px] text-slate-400 uppercase font-semibold block">Chapter Bounds</span>
            <div className="text-xs font-mono font-bold text-white flex items-center gap-1">
              <span>Low: #{registry.lowestChapter}</span>
              <ChevronRight size={12} className="text-slate-500" />
              <span>High: #{registry.highestChapter}</span>
            </div>
            <span className="text-[10px] text-slate-400 font-mono block">Missing: {registry.missingChapters.length} chapters</span>
          </div>

          <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-1">
            <span className="text-[11px] text-slate-400 uppercase font-semibold block">Discovered & Validated</span>
            <div className="text-xs font-mono font-bold text-purple-300 flex items-center gap-2">
              <span>Candidates: {registry.totalCandidates}</span>
            </div>
            <span className="text-[10px] text-emerald-400 font-bold block">
              Validated: {registry.validatedCount} | Invalid: {registry.invalidCount}
            </span>
          </div>

          <div className="p-3 rounded-xl bg-black/40 border border-white/5 space-y-1">
            <span className="text-[11px] text-slate-400 uppercase font-semibold block">Discovery Methods</span>
            <div className="flex flex-wrap gap-1 pt-0.5">
              {(registry.discoveryMethods || ['HTML_LINK', 'URL_PATTERN']).map(m => (
                <span key={m} className="px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-300 text-[10px] font-mono font-bold border border-purple-500/30">
                  ✓ {m}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* RANGE SELECTION PRESETS */}
        <div className="p-3 rounded-xl bg-purple-950/20 border border-purple-500/20 mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Sliders size={15} className="text-purple-400" />
            <span className="text-xs font-bold text-white font-['Outfit']">Phạm Vi Chương Tải (Range Selection):</span>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {[
              { id: 'ALL', label: `Tất Cả (${registry.chapters.length})` },
              { id: '1-100', label: 'Chapter 1 → 100' },
              { id: '500-1000', label: 'Chapter 500 → 1000' },
              { id: 'CUSTOM', label: 'Tùy Chỉnh Range' }
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setRangeMode(tab.id as any)}
                className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                  rangeMode === tab.id
                    ? 'bg-purple-600 text-white shadow-md shadow-purple-600/30'
                    : 'bg-black/40 text-slate-400 hover:text-white border border-white/5'
                }`}
              >
                {tab.label}
              </button>
            ))}

            {rangeMode === 'CUSTOM' && (
              <div className="flex items-center gap-1.5 bg-black/60 px-2 py-0.5 rounded-lg border border-purple-500/30 text-xs">
                <input
                  type="number"
                  value={startRange}
                  onChange={e => setStartRange(Number(e.target.value))}
                  className="w-12 bg-transparent text-center font-mono text-purple-300 font-bold focus:outline-none"
                />
                <span className="text-slate-500">→</span>
                <input
                  type="number"
                  value={endRange}
                  onChange={e => setEndRange(Number(e.target.value))}
                  className="w-12 bg-transparent text-center font-mono text-purple-300 font-bold focus:outline-none"
                />
              </div>
            )}
          </div>
        </div>

        {/* CHAPTERS TABLE LIST */}
        <div className="flex-1 flex flex-col overflow-hidden bg-black/40 rounded-xl border border-white/5 p-3 space-y-2 mb-4">
          <div className="flex items-center justify-between text-xs pb-2 border-b border-white/5 font-semibold text-slate-400">
            <span>DANH SÁCH CHAPTER ĐÃ PHÁT HIỆN ({activeChapters.length} ĐƯỢC CHỌN)</span>
            <span className="font-mono">URL Canonical</span>
            <span>TRẠNG THÁI VALIDATION</span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-1.5 custom-scrollbar pr-1">
            {activeChapters.map(chap => (
              <div
                key={chap.number}
                className="p-2 rounded-lg bg-[#161922] border border-white/5 hover:border-purple-500/30 text-xs flex items-center justify-between transition-all"
              >
                <div className="flex items-center gap-2.5 min-w-[200px]">
                  <span className="px-1.5 py-0.5 rounded bg-purple-600/20 text-purple-300 font-mono font-bold text-[11px] border border-purple-500/30">
                    #{String(chap.number).padStart(3, '0')}
                  </span>
                  <span className="font-bold text-slate-200 truncate">{chap.title}</span>
                </div>

                <span className="font-mono text-[11px] text-slate-400 truncate max-w-[320px]" title={chap.url}>
                  {chap.url}
                </span>

                <div className="flex items-center gap-2 min-w-[120px] justify-end">
                  {chap.status === 'VALID' && (
                    <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-400 font-bold text-[11px] flex items-center gap-1 border border-emerald-500/30">
                      <CheckCircle2 size={12} /> VALID
                    </span>
                  )}
                  {chap.status === 'MISSING' && (
                    <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-400 font-bold text-[11px] flex items-center gap-1 border border-amber-500/30">
                      <AlertTriangle size={12} /> MISSING
                    </span>
                  )}
                  {chap.status === 'INVALID' && (
                    <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-400 font-bold text-[11px] flex items-center gap-1 border border-rose-500/30">
                      <XCircle size={12} /> INVALID
                    </span>
                  )}
                  {chap.status === 'PENDING' && (
                    <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-medium text-[11px]">
                      PENDING
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* FOOTER ACTIONS */}
        <div className="pt-3 border-t border-white/10 flex items-center justify-between">
          <div className="flex items-center gap-2">
            {onReScan && (
              <button
                onClick={onReScan}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-xs font-semibold text-slate-300 flex items-center gap-1.5"
              >
                <RefreshCw size={13} /> Quét Lại (Re-Scan)
              </button>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button onClick={onClose} className="px-4 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-xs font-semibold text-slate-300">
              Hủy
            </button>

            <button
              onClick={handleApprove}
              className="px-5 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-extrabold text-xs flex items-center gap-2 shadow-lg shadow-purple-600/30 transition-all"
            >
              <Sparkles size={14} /> APPROVE DISCOVERY & CHỌN {activeChapters.length} CHƯƠNG TẢI
            </button>
          </div>
        </div>

      </div>
    </div>
  );
};
