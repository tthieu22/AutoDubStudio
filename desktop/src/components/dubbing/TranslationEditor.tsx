import React, { useState, useEffect } from 'react';
import { 
  Languages, 
  Search, 
  CheckCircle2, 
  AlertTriangle, 
  Lock, 
  BookOpen, 
  Sparkles, 
  ArrowRight, 
  Check, 
  RefreshCw,
  SlidersHorizontal
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface TranslationPair {
  id: number;
  start: number;
  end: number;
  sourceText: string;
  translatedText: string;
  speaker: string;
  approved: boolean;
  warning?: string | null;
}

interface TranslationEditorProps {
  projectDir?: string | null;
  onProceedToVoice?: () => void;
}

export const TranslationEditor: React.FC<TranslationEditorProps> = ({
  projectDir,
  onProceedToVoice
}) => {
  const [pairs, setPairs] = useState<TranslationPair[]>([
    {
      id: 1,
      start: 1.2,
      end: 4.96,
      sourceText: "Hello everyone, welcome to our travel documentary.",
      translatedText: "Xin chào mọi người, chào mừng đến với thước phim tài liệu du lịch của chúng tôi.",
      speaker: "Narrator",
      approved: true
    },
    {
      id: 2,
      start: 6.12,
      end: 9.16,
      sourceText: "Today we will explore the breathtaking scenery of Da Lat.",
      translatedText: "Hôm nay chúng ta sẽ cùng khám phá thắng cảnh tuyệt đẹp của Đà Lạt.",
      speaker: "Narrator",
      approved: true
    },
    {
      id: 3,
      start: 10.0,
      end: 14.2,
      sourceText: "The weather here is cool and refreshing all year round.",
      translatedText: "Thời tiết tại vùng núi này quanh năm luôn mát mẻ và trong lành sảng khoái.",
      speaker: "A Lang",
      approved: false,
      warning: "Translation text length (+28%) exceeds audio window."
    },
    {
      id: 4,
      start: 15.1,
      end: 19.5,
      sourceText: "Let's take a look at the famous flower garden.",
      translatedText: "Chúng ta hãy cùng tham quan vườn hoa nổi tiếng nhé.",
      speaker: "B Lang",
      approved: false
    }
  ]);

  const [searchQuery, setSearchQuery] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(1);

  useEffect(() => {
    if (projectDir) {
      PythonEngineService.readSubtitles(projectDir).then(data => {
        if (Array.isArray(data) && data.length > 0) {
          setPairs(data.map(s => ({
            id: s.id,
            start: Number(s.start || 0),
            end: Number(s.end || 0),
            sourceText: s.text || '',
            translatedText: s.translated_text || s.translation || '',
            speaker: s.speaker || 'Narrator',
            approved: false,
            warning: (s.translated_text || '').length > (s.text || '').length * 1.5 ? 'Translation significantly longer than source' : null
          })));
        }
      }).catch(e => console.error('Failed to read translation pairs:', e));
    }
  }, [projectDir]);

  const handleTranslationChange = (id: number, val: string) => {
    setPairs(prev => prev.map(p => p.id === id ? { ...p, translatedText: val } : p));
  };

  const toggleApprove = (id: number) => {
    setPairs(prev => prev.map(p => p.id === id ? { ...p, approved: !p.approved } : p));
  };

  const handleBatchApprove = () => {
    setPairs(prev => prev.map(p => ({ ...p, approved: true })));
  };

  const filteredPairs = pairs.filter(p => 
    p.sourceText.toLowerCase().includes(searchQuery.toLowerCase()) ||
    p.translatedText.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* TOP CONTROL BAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
            <Languages size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Dual-Pane Translation Editor (ZH / EN ➔ VI)
            </h2>
            <p className="text-xs text-slate-400">
              Side-by-side source & translated text verification with character name locks & length warnings.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleBatchApprove}
            className="px-3 py-1.5 rounded-lg bg-emerald-500/15 hover:bg-emerald-500/25 border border-emerald-500/30 text-xs font-semibold text-emerald-300 flex items-center gap-1.5 transition-all"
          >
            <CheckCircle2 size={14} /> Batch Approve All
          </button>
          <button
            onClick={onProceedToVoice}
            className="px-4 py-1.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-500/20 transition-all"
          >
            <Sparkles size={14} /> Proceed to Voice Studio ➔
          </button>
        </div>
      </div>

      {/* DUAL PANE EDITOR GRID HEADER */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs font-extrabold uppercase tracking-wider text-slate-400 px-1 font-['Outfit']">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-cyan-400" />
          <span>ORIGINAL SOURCE TEXT (ZH / EN)</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-400" />
          <span>TRANSLATED TEXT (VIETNAMESE)</span>
        </div>
      </div>

      {/* DUAL PANE LIST CONTAINER */}
      <div className="flex-1 bg-[#111318] rounded-xl border border-white/5 overflow-y-auto p-3 space-y-3 custom-scrollbar">
        {filteredPairs.map((pair, idx) => {
          const isSelected = selectedId === pair.id;
          return (
            <div
              key={pair.id}
              onClick={() => setSelectedId(pair.id)}
              className={`p-3.5 rounded-xl border transition-all ${
                isSelected
                  ? 'bg-white/[0.03] border-indigo-500/40 shadow-sm'
                  : 'bg-[#0b0d10]/70 hover:bg-[#0b0d10] border-white/5'
              }`}
            >
              {/* META BAR */}
              <div className="flex items-center justify-between mb-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className="text-[10px] font-bold font-mono px-2 py-0.5 rounded bg-white/5 text-slate-400">
                    #{idx + 1}
                  </span>
                  <span className="font-mono text-cyan-400 font-semibold text-[11px]">
                    {pair.start.toFixed(2)}s - {pair.end.toFixed(2)}s
                  </span>
                  <span className="text-slate-400 font-semibold">• {pair.speaker}</span>
                </div>

                <div className="flex items-center gap-2">
                  {pair.warning && (
                    <span className="px-2 py-0.5 rounded bg-amber-500/15 border border-amber-500/30 text-amber-300 text-[10px] font-bold flex items-center gap-1">
                      <AlertTriangle size={11} /> {pair.warning}
                    </span>
                  )}
                  <button
                    onClick={(e) => { e.stopPropagation(); toggleApprove(pair.id); }}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-extrabold flex items-center gap-1 transition-all ${
                      pair.approved
                        ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/40'
                        : 'bg-white/5 text-slate-400 hover:text-white border border-white/10'
                    }`}
                  >
                    <Check size={12} /> {pair.approved ? 'APPROVED' : 'APPROVE'}
                  </button>
                </div>
              </div>

              {/* DUAL PANE COMPARISON GRID */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {/* LEFT: SOURCE TEXT */}
                <div className="p-2.5 rounded-lg bg-black/40 border border-white/5 text-xs text-slate-300 leading-relaxed font-sans">
                  {pair.sourceText}
                </div>

                {/* RIGHT: TRANSLATED TEXT EDITOR */}
                <textarea
                  value={pair.translatedText}
                  onChange={e => handleTranslationChange(pair.id, e.target.value)}
                  rows={2}
                  className="w-full bg-black/50 border border-emerald-500/20 focus:border-emerald-500/60 rounded-lg p-2.5 text-xs text-emerald-200 focus:outline-none resize-none font-sans leading-relaxed transition-all"
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
