import React, { useState, useEffect } from 'react';
import { ShieldCheck, Search, Database, GitBranch, Copy, Check } from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface CanonExplorerProps {
  projectDir?: string | null;
}

export const CanonExplorer: React.FC<CanonExplorerProps> = ({ projectDir }) => {
  const [activeTab, setActiveTab] = useState<'facts' | 'threads'>('facts');
  const [facts, setFacts] = useState<any[]>([]);
  const [threads, setThreads] = useState<any[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (projectDir) {
      PythonEngineService.getCanonFacts(projectDir, 100).then(res => {
        if (Array.isArray(res)) setFacts(res);
      }).catch(console.error);

      PythonEngineService.getPlotThreads(projectDir).then(res => {
        if (Array.isArray(res)) setThreads(res);
      }).catch(console.error);
    }
  }, [projectDir]);

  const handleCopyFact = (fact: any, e: React.MouseEvent) => {
    e.stopPropagation();
    const text = `[Canon Fact - ${fact.category || 'General'}] (Chương #${fact.chapter_num || fact.chapter || 1}): ${fact.fact_text || fact.object || fact.subject || ''}`;
    navigator.clipboard.writeText(text);
    setCopiedId(`fact-${fact.id}`);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleCopyThread = (thread: any, e: React.MouseEvent) => {
    e.stopPropagation();
    const text = `[Plot Thread - ${thread.status || 'OPEN'}] ${thread.title || ''} (Từ chương #${thread.since_chapter || 1}): ${thread.description || ''}`;
    navigator.clipboard.writeText(text);
    setCopiedId(`thread-${thread.id}`);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredFacts = facts.filter(f =>
    (f.fact_text || f.object || f.subject || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (f.category || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  const filteredThreads = threads.filter(t =>
    (t.title || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (t.description || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
            <ShieldCheck size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Canon Database & Plot Threads Explorer (V2.3)
            </h2>
            <p className="text-xs text-slate-400">
              Tra cứu các sự thật Canon đã xác lập và các tuyến truyện chưa giải quyết (Open Threads).
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setActiveTab('facts')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer select-none ${
              activeTab === 'facts' ? 'bg-emerald-500 text-black shadow-md' : 'bg-white/5 text-slate-400 hover:text-white'
            }`}
          >
            <Database size={13} className="inline mr-1" /> Canon Facts ({facts.length})
          </button>
          <button
            onClick={() => setActiveTab('threads')}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all cursor-pointer select-none ${
              activeTab === 'threads' ? 'bg-indigo-600 text-white shadow-md' : 'bg-white/5 text-slate-400 hover:text-white'
            }`}
          >
            <GitBranch size={13} className="inline mr-1" /> Open Threads ({threads.length})
          </button>
        </div>
      </div>

      {/* FILTER SEARCH */}
      <div className="flex items-center gap-2 bg-[#111318] p-3 rounded-xl border border-white/5">
        <Search size={14} className="text-slate-400 ml-2" />
        <input
          type="text"
          value={searchQuery}
          onChange={e => setSearchQuery(e.target.value)}
          placeholder="Tìm kiếm dữ liệu Canon hoặc Tuyến Truyện..."
          className="w-full bg-[#0b0d10] border border-white/10 rounded-lg px-3 py-1.5 text-xs text-slate-200 focus:outline-none"
        />
      </div>

      {/* CONTENT LIST */}
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {activeTab === 'facts' ? (
          filteredFacts.length === 0 ? (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
              <ShieldCheck size={32} className="text-emerald-400 mb-3" />
              <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Chưa Có Canon Facts</h3>
              <p className="text-xs text-slate-400">Các sự thật đã xác nhận sẽ tự động trích xuất và lưu tại đây khi sinh chương.</p>
            </div>
          ) : (
            filteredFacts.map((fact, idx) => {
              const itemKey = `fact-${fact.id || idx}`;
              const isCopied = copiedId === itemKey;

              return (
                <div key={itemKey} className="p-3.5 rounded-xl bg-[#111318] border border-white/5 space-y-1.5 hover:border-white/10 transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold uppercase font-mono">
                        {fact.category || 'General'}
                      </span>
                      <span className="text-[11px] font-mono text-slate-500">Chương #{fact.chapter_num || fact.chapter || 1}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-mono text-cyan-400">
                        Confidence: {((fact.confidence || 1.0) * 100).toFixed(0)}%
                      </span>
                      <button
                        onClick={e => handleCopyFact(fact, e)}
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 transition-all border select-none cursor-pointer ${
                          isCopied ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-white/5 hover:bg-white/10 text-slate-300 border-white/10'
                        }`}
                        title="Copy Canon Fact"
                      >
                        {isCopied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                        <span>{isCopied ? 'Đã Copy' : 'Copy'}</span>
                      </button>
                    </div>
                  </div>
                  <p className="text-xs text-slate-200 font-sans leading-relaxed">
                    {fact.fact_text || `${fact.subject || ''} ${fact.predicate || ''} ${fact.object || ''}`}
                  </p>
                </div>
              );
            })
          )
        ) : (
          filteredThreads.length === 0 ? (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
              <GitBranch size={32} className="text-indigo-400 mb-3" />
              <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Chưa Có Open Plot Threads</h3>
              <p className="text-xs text-slate-400">Các tuyến kịch bản mở sẽ tự động được ghi nhận và quản lý tại đây.</p>
            </div>
          ) : (
            filteredThreads.map((t, idx) => {
              const itemKey = `thread-${t.id || idx}`;
              const isCopied = copiedId === itemKey;

              return (
                <div key={itemKey} className="p-3.5 rounded-xl bg-[#111318] border border-white/5 space-y-1.5 hover:border-white/10 transition-all">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                        t.status === 'OPEN' ? 'bg-amber-500/20 text-amber-300 border border-amber-500/30' : 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30'
                      }`}>
                        {t.status || 'OPEN'}
                      </span>
                      <h3 className="text-xs font-bold text-white font-['Outfit']">{t.title}</h3>
                    </div>

                    <div className="flex items-center gap-2">
                      <span className="text-[11px] font-mono text-slate-500">Từ Chương #{t.since_chapter || 1}</span>
                      <button
                        onClick={e => handleCopyThread(t, e)}
                        className={`px-2 py-0.5 rounded text-[10px] font-semibold flex items-center gap-1 transition-all border select-none cursor-pointer ${
                          isCopied ? 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40' : 'bg-white/5 hover:bg-white/10 text-slate-300 border-white/10'
                        }`}
                        title="Copy Open Thread"
                      >
                        {isCopied ? <Check size={11} className="text-emerald-400" /> : <Copy size={11} />}
                        <span>{isCopied ? 'Đã Copy' : 'Copy'}</span>
                      </button>
                    </div>
                  </div>
                  <p className="text-xs text-slate-300 leading-relaxed">{t.description}</p>
                </div>
              );
            })
          )
        )}
      </div>
    </div>
  );
};
