import React, { useState } from 'react';
import { 
  Brain, 
  Plus, 
  Lock, 
  Unlock, 
  Zap, 
  History, 
  Sparkles, 
  CheckCircle2, 
  Copy, 
  Check, 
  FileText, 
  FileJson,
  Edit3,
  Trash2,
  RefreshCw,
  X
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

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
  const [copiedMemId, setCopiedMemId] = useState<string | null>(null);
  const [copiedType, setCopiedType] = useState<'text' | 'json' | null>(null);
  const [copiedAllStatus, setCopiedAllStatus] = useState<'text' | 'json' | null>(null);

  const [editingMem, setEditingMem] = useState<MemoryItem | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const handleCopyMemText = (mem: MemoryItem, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const info = `[Thể loại: ${mem.category} | Mức độ: ${mem.importance}]\n${mem.content}`;
    navigator.clipboard.writeText(info);
    setCopiedMemId(mem.id);
    setCopiedType('text');
    setTimeout(() => { setCopiedMemId(null); setCopiedType(null); }, 2000);
  };

  const handleCopyMemJson = (mem: MemoryItem, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    navigator.clipboard.writeText(JSON.stringify(mem, null, 2));
    setCopiedMemId(mem.id);
    setCopiedType('json');
    setTimeout(() => { setCopiedMemId(null); setCopiedType(null); }, 2000);
  };

  const handleCopyAllText = () => {
    if (memories.length === 0) return;
    const header = `=== DANH SÁCH GHI NHỚ & KÝ ỨC AI (${memories.length} ghi nhớ) ===\n\n`;
    const body = memories.map((mem, index) => (
      `[${index + 1}] [${mem.category} | ${mem.importance}]\n` +
      `  • Nội dung: ${mem.content}\n` +
      `  • Độ tin cậy: ${(mem.confidence * 100).toFixed(0)}%`
    )).join('\n\n');

    navigator.clipboard.writeText(header + body);
    setCopiedAllStatus('text');
    setTimeout(() => setCopiedAllStatus(null), 2500);
  };

  const handleCopyAllJson = () => {
    if (memories.length === 0) return;
    navigator.clipboard.writeText(JSON.stringify(memories, null, 2));
    setCopiedAllStatus('json');
    setTimeout(() => setCopiedAllStatus(null), 2500);
  };

  React.useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(async data => {
        if (data && data.story_memory && Array.isArray(data.story_memory) && data.story_memory.length > 0) {
          const unique: MemoryItem[] = [];
          const seen = new Set<string>();
          for (const item of data.story_memory) {
            const key = (item.content || '').trim();
            if (key && !seen.has(key)) {
              seen.add(key);
              unique.push({ ...item, id: `mem-${unique.length}` });
            }
          }
          setMemories(unique);
        } else {
          try {
            const rawBible = await PythonEngineService.readTextFile(`${projectDir}/story_bible.json`);
            if (rawBible) {
              const bible = JSON.parse(rawBible);
              if (bible.rules && Array.isArray(bible.rules) && bible.rules.length > 0) {
                const unique: MemoryItem[] = [];
                const seen = new Set<string>();
                bible.rules.forEach((r: string) => {
                  const key = String(r || '').trim();
                  if (key && !seen.has(key)) {
                    seen.add(key);
                    unique.push({
                      id: `mem-${unique.length}`,
                      category: "World",
                      content: key,
                      importance: "HIGH",
                      confidence: 1.0,
                      locked: true
                    });
                  }
                });
                setMemories(unique);
                return;
              }
            }
          } catch (e) {}
          setMemories([]);
        }
      }).catch(() => {
        setMemories([]);
      });
    }
  }, [projectDir]);

  const saveMemoriesToProject = async (newMems: MemoryItem[]) => {
    setMemories(newMems);
    if (projectDir) {
      try {
        const json = (await PythonEngineService.readProjectJson(projectDir)) || {};
        json.story_memory = newMems;
        await PythonEngineService.writeProjectJson(projectDir, json);
      } catch (e) {
        console.error('Failed to save story_memory to project.json:', e);
      }
    }
  };

  const toggleLock = (id: string) => {
    const updated = memories.map(m => m.id === id ? { ...m, locked: !m.locked } : m);
    saveMemoriesToProject(updated);
  };

  const handleDeleteMemory = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!confirm('Bạn có chắc muốn xóa ghi nhớ này?')) return;
    const updated = memories.filter(m => m.id !== id);
    saveMemoriesToProject(updated);
  };

  const [regenStatus, setRegenStatus] = useState<string | null>(null);

  const handleRegenerateMemory = async () => {
    if (!projectDir) return;
    if (!confirm('Bạn có chắc muốn gọi AI Qwen 2.5 tái tạo lại dữ liệu Trí Nhớ & Quy Tắc cho dự án không?')) return;
    setIsRegenerating(true);
    setRegenStatus('Đang chạy Python Engine & AI Qwen 2.5 tạo lại trí nhớ...');
    try {
      const projJson = await PythonEngineService.readProjectJson(projectDir);
      let idea = projJson?.story_idea || projJson?.idea || {};
      if (!idea || !idea.title) {
        idea = {
          title: projJson?.name || "Kịch Bản Mới",
          genre: projJson?.genre || "Hành động viễn tưởng",
          protagonist: { name: "Diệp Phàm", background: "Nhân vật chính" },
          total_chapters: projJson?.total_chapters || 100
        };
      }

      const bible = await PythonEngineService.initializeNovel(projectDir, idea);
      const updatedProj = await PythonEngineService.readProjectJson(projectDir);

      if (updatedProj && updatedProj.story_memory && Array.isArray(updatedProj.story_memory) && updatedProj.story_memory.length > 0) {
        setMemories(updatedProj.story_memory);
      } else if (bible && bible.rules && Array.isArray(bible.rules)) {
        const unique: MemoryItem[] = [];
        const seen = new Set<string>();
        bible.rules.forEach((r: string) => {
          const key = String(r || '').trim();
          if (key && !seen.has(key)) {
            seen.add(key);
            unique.push({
              id: `mem-${unique.length}`,
              category: "World",
              content: key,
              importance: "HIGH",
              confidence: 1.0,
              locked: false
            });
          }
        });
        if (unique.length > 0) {
          saveMemoriesToProject(unique);
        }
      }
      setRegenStatus('Tái tạo danh sách trí nhớ bằng AI thành công!');
      setTimeout(() => setRegenStatus(null), 3000);
    } catch (e: any) {
      console.error("Lỗi khi tái tạo dữ liệu trí nhớ:", e);
      setRegenStatus(`Lỗi AI: ${e?.message || e}`);
      setTimeout(() => setRegenStatus(null), 4000);
    } finally {
      setIsRegenerating(false);
    }
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
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans relative">
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

        <div className="flex items-center gap-2">
          {memories.length > 0 && (
            <>
              <button
                onClick={handleCopyAllText}
                className={`px-3 py-1.5 rounded-lg border font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                  copiedAllStatus === 'text'
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-md shadow-emerald-500/10'
                    : 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300 hover:text-white'
                }`}
                title="Sao chép toàn bộ ghi nhớ dạng văn bản"
              >
                {copiedAllStatus === 'text' ? <Check size={14} className="text-emerald-400" /> : <FileText size={14} />}
                {copiedAllStatus === 'text' ? 'Đã Sao Chép Text!' : `Copy Tất Cả (${memories.length})`}
              </button>

              <button
                onClick={handleCopyAllJson}
                className={`px-3 py-1.5 rounded-lg border font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                  copiedAllStatus === 'json'
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-md shadow-emerald-500/10'
                    : 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300 hover:text-white'
                }`}
                title="Sao chép toàn bộ ghi nhớ dạng JSON"
              >
                {copiedAllStatus === 'json' ? <Check size={14} className="text-emerald-400" /> : <FileJson size={14} />}
                {copiedAllStatus === 'json' ? 'Đã Sao Chép JSON!' : 'Copy Tất Cả (JSON)'}
              </button>
            </>
          )}

          <button
            onClick={handleRegenerateMemory}
            disabled={isRegenerating}
            className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
            title="Tái tạo lại danh sách ghi nhớ bằng AI"
          >
            <RefreshCw size={14} className={isRegenerating ? "animate-spin" : ""} />
            {isRegenerating ? "Đang Tái Tạo..." : "Tái Tạo AI"}
          </button>

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
              saveMemoriesToProject([...memories, newMem]);
              setEditingMem(newMem);
            }}
            className="px-3.5 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-purple-600/20 transition-all cursor-pointer"
          >
            <Plus size={14} /> Add Memory Record
          </button>
        </div>
      </div>

      {/* REGEN STATUS BANNER */}
      {regenStatus && (
        <div className="bg-amber-500/15 border border-amber-500/40 text-amber-300 text-xs px-4 py-2.5 rounded-xl flex items-center gap-2.5 font-bold shadow-md shadow-amber-500/10 animate-pulse">
          <RefreshCw size={15} className="animate-spin text-amber-400" />
          <span>{regenStatus}</span>
        </div>
      )}

      {/* MEMORY ITEMS LIST */}
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {memories.length === 0 ? (
          <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20 mb-4 shadow-lg shadow-purple-500/10">
              <Brain size={28} />
            </div>
            <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Dự Án Chưa Có Trí Nhớ Dài Hạn</h3>
            <p className="text-xs text-slate-400 max-w-md mb-5 leading-relaxed">
              Trí nhớ AI (Memory) sẽ tự động lưu lại tình tiết quan trọng, quan hệ nhân vật khi Qwen 2.5 xử lý kịch bản truyện hoặc bấm Tái Tạo AI.
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={handleRegenerateMemory}
                className="px-4 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 font-bold text-xs flex items-center gap-2 transition-all cursor-pointer"
              >
                <RefreshCw size={16} /> Tái Tạo Trí Nhớ (AI)
              </button>
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
                  saveMemoriesToProject([...memories, newMem]);
                  setEditingMem(newMem);
                }}
                className="px-5 py-2.5 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-bold text-xs flex items-center gap-2 shadow-xl shadow-purple-600/20 transition-all cursor-pointer"
              >
                <Plus size={16} /> Thêm Ghi Nhớ Tình Tiết
              </button>
            </div>
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

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setEditingMem(mem)}
                    className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-white transition-all cursor-pointer"
                    title="Chỉnh sửa ghi nhớ này"
                  >
                    <Edit3 size={14} />
                  </button>
                  <button
                    onClick={(e) => handleCopyMemText(mem, e)}
                    className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                      copiedMemId === mem.id && copiedType === 'text' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-slate-400 hover:text-white'
                    }`}
                    title="Sao chép nội dung ghi nhớ này"
                  >
                    {copiedMemId === mem.id && copiedType === 'text' ? <Check size={14} /> : <FileText size={14} />}
                  </button>
                  <button
                    onClick={(e) => handleCopyMemJson(mem, e)}
                    className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                      copiedMemId === mem.id && copiedType === 'json' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-slate-400 hover:text-white'
                    }`}
                    title="Sao chép JSON ghi nhớ này"
                  >
                    {copiedMemId === mem.id && copiedType === 'json' ? <Check size={14} /> : <FileJson size={14} />}
                  </button>
                  <button
                    onClick={() => toggleLock(mem.id)}
                    className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                      mem.locked ? 'bg-amber-500/20 text-amber-300' : 'bg-white/5 text-slate-400 hover:text-white'
                    }`}
                    title={mem.locked ? 'Locked Memory' : 'Unlocked'}
                  >
                    {mem.locked ? <Lock size={14} /> : <Unlock size={14} />}
                  </button>
                  <button
                    onClick={(e) => handleDeleteMemory(mem.id, e)}
                    className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-rose-400 transition-all cursor-pointer"
                    title="Xóa ghi nhớ này"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed font-sans">{mem.content}</p>
            </div>
          ))
        )}
      </div>

      {/* EDIT MEMORY MODAL */}
      {editingMem && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111318] border border-white/10 rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-white font-['Outfit'] flex items-center gap-2">
                <Edit3 size={18} className="text-purple-400" /> Chỉnh Sửa Trí Nhớ & Quy Tắc
              </h3>
              <button onClick={() => setEditingMem(null)} className="text-slate-400 hover:text-white p-1 cursor-pointer">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Thể loại (Category)</label>
                  <select
                    value={editingMem.category}
                    onChange={e => setEditingMem({ ...editingMem, category: e.target.value as any })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="Character">Character (Nhân Vật)</option>
                    <option value="World">World (Quy Tắc Thế Giới)</option>
                    <option value="Timeline">Timeline (Niên Đại)</option>
                    <option value="Relationship">Relationship (Mối Quan Hệ)</option>
                    <option value="Important Event">Important Event (Sự Kiện Trọng Đại)</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Mức độ quan trọng (Importance)</label>
                  <select
                    value={editingMem.importance}
                    onChange={e => setEditingMem({ ...editingMem, importance: e.target.value as any })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-purple-500"
                  >
                    <option value="HIGH">HIGH (Rất quan trọng)</option>
                    <option value="MEDIUM">MEDIUM (Trung bình)</option>
                    <option value="LOW">LOW (Thấp)</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="text-slate-400 font-semibold mb-1 block">Nội dung ghi nhớ / Quy tắc</label>
                <textarea
                  rows={4}
                  value={editingMem.content}
                  onChange={e => setEditingMem({ ...editingMem, content: e.target.value })}
                  className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white custom-scrollbar focus:outline-none focus:border-purple-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <button
                onClick={() => setEditingMem(null)}
                className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-bold cursor-pointer"
              >
                Hủy
              </button>
              <button
                onClick={() => {
                  const updated = memories.map(m => m.id === editingMem.id ? editingMem : m);
                  saveMemoriesToProject(updated);
                  setEditingMem(null);
                }}
                className="px-4 py-2 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-xs font-extrabold shadow-md shadow-purple-600/20 cursor-pointer"
              >
                Lưu Thay Đổi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};


