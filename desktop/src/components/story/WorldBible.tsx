import React, { useState, useEffect } from 'react';
import { 
  Globe, 
  Plus, 
  Lock, 
  Unlock, 
  Shield, 
  MapPin, 
  Building, 
  BookMarked, 
  Search,
  Edit3,
  Trash2,
  RefreshCw,
  X,
  Check,
  Copy,
  FileText,
  FileJson
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

export interface WorldEntity {
  id: string;
  category: 'Location' | 'Organization' | 'Rule' | 'Terminology' | 'History';
  name: string;
  description: string;
  locked: boolean;
}

interface WorldBibleProps {
  projectDir?: string | null;
}

export const WorldBible: React.FC<WorldBibleProps> = ({ projectDir }) => {
  const [entities, setEntities] = useState<WorldEntity[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const [copiedEntId, setCopiedEntId] = useState<string | null>(null);
  const [copiedType, setCopiedType] = useState<'text' | 'json' | null>(null);
  const [copiedAllStatus, setCopiedAllStatus] = useState<'text' | 'json' | null>(null);

  const [editingEntity, setEditingEntity] = useState<WorldEntity | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const handleCopyEntText = (ent: WorldEntity, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const info = `[${ent.category}: ${ent.name}]\n${ent.description}`;
    navigator.clipboard.writeText(info);
    setCopiedEntId(ent.id);
    setCopiedType('text');
    setTimeout(() => { setCopiedEntId(null); setCopiedType(null); }, 2000);
  };

  const handleCopyEntJson = (ent: WorldEntity, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    navigator.clipboard.writeText(JSON.stringify(ent, null, 2));
    setCopiedEntId(ent.id);
    setCopiedType('json');
    setTimeout(() => { setCopiedEntId(null); setCopiedType(null); }, 2000);
  };

  const handleCopyAllText = () => {
    if (entities.length === 0) return;
    const header = `=== THẾ GIỚI QUAN & BỐI CẢNH DỰ ÁN (${entities.length} mục) ===\n\n`;
    const body = entities.map((ent, index) => (
      `[${index + 1}] [${ent.category}] ${ent.name}\n` +
      `  • Mô tả: ${ent.description}`
    )).join('\n\n');

    navigator.clipboard.writeText(header + body);
    setCopiedAllStatus('text');
    setTimeout(() => setCopiedAllStatus(null), 2500);
  };

  const handleCopyAllJson = () => {
    if (entities.length === 0) return;
    navigator.clipboard.writeText(JSON.stringify(entities, null, 2));
    setCopiedAllStatus('json');
    setTimeout(() => setCopiedAllStatus(null), 2500);
  };

  React.useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(async data => {
        if (data && data.world_lore && Array.isArray(data.world_lore) && data.world_lore.length > 0) {
          setEntities(data.world_lore);
        } else {
          try {
            const rawBible = await PythonEngineService.readTextFile(`${projectDir}/story_bible.json`);
            if (rawBible) {
              const bible = JSON.parse(rawBible);
              const formatted: WorldEntity[] = [];
              const worldInfo = bible.world || {};
              (worldInfo.locations || []).forEach((loc: any, idx: number) => {
                formatted.push({
                  id: `w-loc-${idx}`,
                  category: 'Location',
                  name: typeof loc === 'string' ? loc : (loc.name || 'Địa Danh'),
                  description: typeof loc === 'string' ? `Địa danh thuộc ${worldInfo.continent_name || 'bối cảnh'}` : (loc.description || ''),
                  locked: true
                });
              });
              (worldInfo.factions || []).forEach((fac: any, idx: number) => {
                formatted.push({
                  id: `w-fac-${idx}`,
                  category: 'Organization',
                  name: typeof fac === 'string' ? fac : (fac.name || 'Thế Lực'),
                  description: 'Thế lực chính trong thế giới',
                  locked: true
                });
              });
              const ranks = bible.cultivation_system || (bible.progression_system?.ranks || []);
              ranks.forEach((cs: any, idx: number) => {
                formatted.push({
                  id: `w-cs-${idx}`,
                  category: 'Rule',
                  name: `Cảnh Giới #${cs.rank || idx + 1}: ${cs.name}`,
                  description: cs.description || 'Cấp độ sức mạnh',
                  locked: true
                });
              });
              if (formatted.length > 0) {
                setEntities(formatted);
                return;
              }
            }
          } catch (e) {}
          setEntities([]);
        }
      }).catch(() => {
        setEntities([]);
      });
    }
  }, [projectDir]);

  const saveEntitiesToProject = async (newEntities: WorldEntity[]) => {
    setEntities(newEntities);
    if (projectDir) {
      try {
        const json = (await PythonEngineService.readProjectJson(projectDir)) || {};
        json.world_lore = newEntities;
        await PythonEngineService.writeProjectJson(projectDir, json);
      } catch (e) {
        console.error('Failed to save world_lore to project.json:', e);
      }
    }
  };

  const toggleLock = (id: string) => {
    const updated = entities.map(e => e.id === id ? { ...e, locked: !e.locked } : e);
    saveEntitiesToProject(updated);
  };

  const handleDeleteEntity = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!confirm('Bạn có chắc muốn xóa mục thế giới quan này?')) return;
    const updated = entities.filter(ent => ent.id !== id);
    saveEntitiesToProject(updated);
  };

  const [regenStatus, setRegenStatus] = useState<string | null>(null);

  const handleRegenerateWorldLore = async () => {
    if (!projectDir) return;
    if (!confirm('Bạn có chắc muốn gọi AI Qwen 2.5 tái tạo lại toàn bộ Thế Giới Quan cho dự án không?')) return;
    setIsRegenerating(true);
    setRegenStatus('Đang chạy Python Engine & AI Qwen 2.5 tạo lại thế giới quan...');
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

      if (updatedProj && updatedProj.world_lore && Array.isArray(updatedProj.world_lore) && updatedProj.world_lore.length > 0) {
        setEntities(updatedProj.world_lore);
      } else if (bible) {
        const formatted: WorldEntity[] = [];
        const worldInfo = bible.world || {};
        (worldInfo.locations || []).forEach((loc: any, idx: number) => {
          formatted.push({
            id: `w-loc-${idx}`,
            category: 'Location',
            name: typeof loc === 'string' ? loc : (loc.name || 'Địa Danh'),
            description: typeof loc === 'string' ? `Địa danh thuộc ${worldInfo.continent_name || 'bối cảnh'}` : (loc.description || ''),
            locked: false
          });
        });
        (worldInfo.factions || []).forEach((fac: any, idx: number) => {
          formatted.push({
            id: `w-fac-${idx}`,
            category: 'Organization',
            name: typeof fac === 'string' ? fac : (fac.name || 'Thế Lực'),
            description: 'Thế lực chính trong thế giới',
            locked: false
          });
        });
        const ranks = bible.cultivation_system || (bible.progression_system?.ranks || []);
        ranks.forEach((cs: any, idx: number) => {
          formatted.push({
            id: `w-cs-${idx}`,
            category: 'Rule',
            name: `Cảnh Giới #${cs.rank || idx + 1}: ${cs.name}`,
            description: cs.description || 'Cấp độ sức mạnh',
            locked: false
          });
        });
        if (formatted.length > 0) {
          saveEntitiesToProject(formatted);
        }
      }
      setRegenStatus('Tái tạo thế giới quan bằng AI thành công!');
      setTimeout(() => setRegenStatus(null), 3000);
    } catch (e: any) {
      console.error("Lỗi khi tái tạo dữ liệu thế giới quan:", e);
      setRegenStatus(`Lỗi AI: ${e?.message || e}`);
      setTimeout(() => setRegenStatus(null), 4000);
    } finally {
      setIsRegenerating(false);
    }
  };

  const filteredEntities = entities.filter(e => {
    const matchesCat = selectedCategory === 'ALL' || e.category === selectedCategory;
    const matchesSearch = e.name.toLowerCase().includes(searchQuery.toLowerCase()) || e.description.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Location': return <MapPin size={14} className="text-cyan-400" />;
      case 'Organization': return <Building size={14} className="text-purple-400" />;
      case 'Rule': return <Shield size={14} className="text-amber-400" />;
      case 'Terminology': return <BookMarked size={14} className="text-emerald-400" />;
      default: return <Globe size={14} className="text-indigo-400" />;
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans relative">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
            <Globe size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              World Bible & Lore Dictionary
            </h2>
            <p className="text-xs text-slate-400">
              Set fixed rules, locations, and terminology. AI cannot modify locked world data.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {entities.length > 0 && (
            <>
              <button
                onClick={handleCopyAllText}
                className={`px-3 py-1.5 rounded-lg border font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                  copiedAllStatus === 'text'
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-md shadow-emerald-500/10'
                    : 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300 hover:text-white'
                }`}
                title="Sao chép toàn bộ thế giới quan dạng văn bản"
              >
                {copiedAllStatus === 'text' ? <Check size={14} className="text-emerald-400" /> : <FileText size={14} />}
                {copiedAllStatus === 'text' ? 'Đã Sao Chép Text!' : `Copy Tất Cả (${entities.length})`}
              </button>

              <button
                onClick={handleCopyAllJson}
                className={`px-3 py-1.5 rounded-lg border font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                  copiedAllStatus === 'json'
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-md shadow-emerald-500/10'
                    : 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300 hover:text-white'
                }`}
                title="Sao chép toàn bộ thế giới quan dạng JSON"
              >
                {copiedAllStatus === 'json' ? <Check size={14} className="text-emerald-400" /> : <FileJson size={14} />}
                {copiedAllStatus === 'json' ? 'Đã Sao Chép JSON!' : 'Copy Tất Cả (JSON)'}
              </button>
            </>
          )}

          <button
            onClick={handleRegenerateWorldLore}
            disabled={isRegenerating}
            className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
            title="Tái tạo lại thế giới quan bằng AI"
          >
            <RefreshCw size={14} className={isRegenerating ? "animate-spin" : ""} />
            {isRegenerating ? "Đang Tái Tạo..." : "Tái Tạo AI"}
          </button>

          <button
            onClick={() => {
              const newEnt: WorldEntity = {
                id: `w-${Date.now()}`,
                category: 'Location',
                name: 'Địa Danh Mới',
                description: 'Chi tiết bối cảnh...',
                locked: false
              };
              saveEntitiesToProject([...entities, newEnt]);
              setEditingEntity(newEnt);
            }}
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Plus size={14} /> Add World Lore
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

      {/* FILTER BAR */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-3 rounded-xl border border-white/5 text-xs">
        <div className="flex items-center gap-2 relative max-w-xs w-full">
          <Search size={14} className="absolute left-3 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search lore, locations, terms..."
            className="w-full bg-[#0b0d10] border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none"
          />
        </div>

        <div className="flex items-center gap-2 overflow-x-auto">
          {['ALL', 'Location', 'Organization', 'Rule', 'Terminology', 'History'].map(cat => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                selectedCategory === cat
                  ? 'bg-indigo-600/20 text-indigo-300 border border-indigo-500/40'
                  : 'text-slate-400 hover:bg-white/5'
              }`}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* ENTITIES LIST */}
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {filteredEntities.length === 0 ? (
          <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
            <div className="w-14 h-14 rounded-2xl bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20 mb-4 shadow-lg shadow-indigo-500/10">
              <Globe size={28} />
            </div>
            <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Dự Án Chưa Có Bối Cảnh / Thế Giới Quan</h3>
            <p className="text-xs text-slate-400 max-w-md mb-5 leading-relaxed">
              Bạn có thể tự định nghĩa địa danh, tổ chức, quy luật thế giới quan để AI luôn tuân thủ nhất quán trong suốt câu chuyện hoặc bấm Tái Tạo AI.
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={handleRegenerateWorldLore}
                className="px-4 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 font-bold text-xs flex items-center gap-2 transition-all cursor-pointer"
              >
                <RefreshCw size={16} /> Tái Tạo Thế Giới Quan (AI)
              </button>
              <button
                onClick={() => {
                  const newEnt: WorldEntity = {
                    id: `w-${Date.now()}`,
                    category: 'Location',
                    name: 'Địa Danh / Quy Luật Mới',
                    description: 'Chi tiết bối cảnh thế giới quan...',
                    locked: false
                  };
                  saveEntitiesToProject([...entities, newEnt]);
                  setEditingEntity(newEnt);
                }}
                className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-2 shadow-xl shadow-indigo-600/20 transition-all cursor-pointer"
              >
                <Plus size={16} /> Thêm Bối Cảnh Thế Giới Quan
              </button>
            </div>
          </div>
        ) : (
          filteredEntities.map(ent => (
            <div key={ent.id} className="p-4 rounded-xl bg-[#111318] border border-white/5 space-y-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getCategoryIcon(ent.category)}
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-wider font-['Outfit']">{ent.category}</span>
                  <h3 className="text-sm font-bold text-white font-['Outfit']">{ent.name}</h3>
                </div>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => setEditingEntity(ent)}
                    className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-white transition-all cursor-pointer"
                    title="Chỉnh sửa thế giới quan"
                  >
                    <Edit3 size={14} />
                  </button>
                  <button
                    onClick={(e) => handleCopyEntText(ent, e)}
                    className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                      copiedEntId === ent.id && copiedType === 'text' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-slate-400 hover:text-white'
                    }`}
                    title="Sao chép văn bản"
                  >
                    {copiedEntId === ent.id && copiedType === 'text' ? <Check size={14} /> : <FileText size={14} />}
                  </button>
                  <button
                    onClick={(e) => handleCopyEntJson(ent, e)}
                    className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                      copiedEntId === ent.id && copiedType === 'json' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-slate-400 hover:text-white'
                    }`}
                    title="Sao chép JSON"
                  >
                    {copiedEntId === ent.id && copiedType === 'json' ? <Check size={14} /> : <FileJson size={14} />}
                  </button>
                  <button
                    onClick={() => toggleLock(ent.id)}
                    className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                      ent.locked ? 'bg-amber-500/20 text-amber-300' : 'bg-white/5 text-slate-400 hover:text-white'
                    }`}
                    title={ent.locked ? 'Locked World Rule' : 'Unlocked'}
                  >
                    {ent.locked ? <Lock size={14} /> : <Unlock size={14} />}
                  </button>
                  <button
                    onClick={(e) => handleDeleteEntity(ent.id, e)}
                    className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-rose-400 transition-all cursor-pointer"
                    title="Xóa mục thế giới quan này"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{ent.description}</p>
            </div>
          ))
        )}
      </div>

      {/* EDIT WORLD LORE MODAL */}
      {editingEntity && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111318] border border-white/10 rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-white font-['Outfit'] flex items-center gap-2">
                <Edit3 size={18} className="text-indigo-400" /> Chỉnh Sửa Thế Giới Quan & Bối Cảnh
              </h3>
              <button onClick={() => setEditingEntity(null)} className="text-slate-400 hover:text-white p-1 cursor-pointer">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Phân loại (Category)</label>
                  <select
                    value={editingEntity.category}
                    onChange={e => setEditingEntity({ ...editingEntity, category: e.target.value as any })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Location">Location (Địa Danh)</option>
                    <option value="Organization">Organization (Thế Lực/Tổ Chức)</option>
                    <option value="Rule">Rule (Cảnh Giới/Quy Luật)</option>
                    <option value="Terminology">Terminology (Thuật Ngữ)</option>
                    <option value="History">History (Lịch Sử)</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Tên địa danh / Quy luật</label>
                  <input
                    type="text"
                    value={editingEntity.name}
                    onChange={e => setEditingEntity({ ...editingEntity, name: e.target.value })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-400 font-semibold mb-1 block">Mô tả chi tiết thế giới quan</label>
                <textarea
                  rows={4}
                  value={editingEntity.description}
                  onChange={e => setEditingEntity({ ...editingEntity, description: e.target.value })}
                  className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white custom-scrollbar focus:outline-none focus:border-indigo-500"
                />
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <button
                onClick={() => setEditingEntity(null)}
                className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-bold cursor-pointer"
              >
                Hủy
              </button>
              <button
                onClick={() => {
                  const updated = entities.map(e => e.id === editingEntity.id ? editingEntity : e);
                  saveEntitiesToProject(updated);
                  setEditingEntity(null);
                }}
                className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-extrabold shadow-md shadow-indigo-600/20 cursor-pointer"
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

