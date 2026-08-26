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

export const StoryMemory: React.FC = () => {
  const [memories, setMemories] = useState<MemoryItem[]>([
    {
      id: 'mem-1',
      category: 'Important Event',
      content: 'A Lãng and Lâm Mộc agreed to travel to Đà Lạt together after defeating the bandits at the valley.',
      importance: 'HIGH',
      confidence: 0.98,
      locked: true
    },
    {
      id: 'mem-2',
      category: 'Relationship',
      content: 'A Lãng respects Lâm Mộc for her ancient botany knowledge.',
      importance: 'MEDIUM',
      confidence: 0.92,
      locked: false
    }
  ]);

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
              content: 'New narrative memory record...',
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
        {memories.map(mem => (
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
        ))}
      </div>
    </div>
  );
};
