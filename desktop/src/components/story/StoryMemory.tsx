import React, { useState } from 'react';
import { Brain, Plus, Lock, Unlock, Zap, History, Sparkles, CheckCircle2 } from 'lucide-react';

export interface MemoryItem {
  id: string;
  category: 'Character' | 'World' | 'Timeline' | 'Relationship' | 'Important Event';
  content: string;
  importance: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence: number;
  locked: boolean;
}

interface StoryMemoryProps {
  projectDir?: string | null;
}

export const StoryMemory: React.FC<StoryMemoryProps> = ({ projectDir }) => {
  const [memories, setMemories] = useState<MemoryItem[]>([]);

  const toggleLock = (id: string) => {
    setMemories(prev => prev.map(m => m.id === id ? { ...m, locked: !m.locked } : m));
  };

  const getImportanceBadge = (imp: MemoryItem['importance']) => {
    switch (imp) {
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30 text-[10px] font-bold">HIGH IMPORTANCE</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded bg-amber-500/15 text-amber-300 border border-amber-500/30 text-[10px] font-bold">MEDIUM</span>;
      case 'LOW':
      default:
        return <span className="px-2 py-0.5 rounded bg-slate-500/15 text-slate-300 border border-slate-500/30 text-[10px] font-bold">LOW</span>;
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20">
            <Brain size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              AI Story Memory & Context Manager
            </h2>
            <p className="text-xs text-slate-400">
              Tracks plot events, relationships, and context memory for LLM story generation.
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            const newMem: MemoryItem = {
              id: `mem-${Date.now()}`,
              category: 'Important Event',
              content: 'Ghi nhớ sự kiện quan trọng...',
              importance: 'MEDIUM',
              confidence: 0.9,
              locked: false
            };
            setMemories(prev => [...prev, newMem]);
          }}
          className="px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-purple-600/20 transition-all"
        >
          <Plus size={14} /> Add Memory Record
        </button>
      </div>

      {/* MEMORY ITEMS LIST */}
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {memories.length === 0 ? (
          <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20 mb-4 shadow-lg shadow-purple-500/10">
              <Brain size={28} />
            </div>
            <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Dự Án Chưa Có Trí Nhớ Dài Hạn</h3>
            <p className="text-xs text-slate-400 max-w-md mb-5 leading-relaxed">
              Trí nhớ AI (Memory) sẽ tự động lưu lại tình tiết quan trọng, quan hệ nhân vật khi Qwen 2.5 xử lý kịch bản truyện.
            </p>
            <button
              onClick={() => {
                const newMem: MemoryItem = {
                  id: `mem-${Date.now()}`,
                  category: 'Important Event',
                  content: 'Ghi nhớ sự kiện quan trọng của kịch bản...',
                  importance: 'HIGH',
                  confidence: 0.95,
                  locked: false
                };
                setMemories([newMem]);
              }}
              className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-2 shadow-xl shadow-purple-600/20 transition-all cursor-pointer"
            >
              <Plus size={16} /> Thêm Ghi Nhớ Tình Tiết
            </button>
          </div>
        ) : (
          memories.map(mem => (
            <div key={mem.id} className="p-4 rounded-xl bg-[#111318] border border-white/5 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-purple-400 uppercase tracking-wider font-['Outfit']">{mem.category}</span>
                  {getImportanceBadge(mem.importance)}
                  <span className="text-[11px] font-mono text-slate-500">• Confidence: {(mem.confidence * 100).toFixed(0)}%</span>
                </div>

                <button
                  onClick={() => toggleLock(mem.id)}
                  className={`p-1.5 rounded-lg transition-all ${
                    mem.locked ? 'bg-amber-500/20 text-amber-300' : 'bg-white/5 text-slate-400 hover:text-white'
                  }`}
                  title={mem.locked ? 'Locked Memory' : 'Unlocked'}
                >
                  {mem.locked ? <Lock size={14} /> : <Unlock size={14} />}
                </button>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-sans">{mem.content}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
