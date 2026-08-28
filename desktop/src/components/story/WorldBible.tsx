import React, { useState, useEffect } from 'react';
import { Globe, Plus, Lock, Unlock, Shield, MapPin, Building, BookMarked, Search } from 'lucide-react';
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

const DEFAULT_WORLD_ENTITIES: WorldEntity[] = [
  { id: "w-cs-1", category: "Rule", name: "Cảnh Giới #1: Luyện Khí Kỳ", description: "Tích tụ linh khí vào đan điền, cảm ứng thiên địa linh khí", locked: true },
  { id: "w-cs-2", category: "Rule", name: "Cảnh Giới #2: Trúc Cơ Kỳ", description: "Đúc kết Linh Đài, hình thành chân nguyên nội lực", locked: true },
  { id: "w-cs-3", category: "Rule", name: "Cảnh Giới #3: Kim Đan Kỳ", description: "Ngưng tụ Kim Đan, phi hành bằng tiên kiếm", locked: true },
  { id: "w-cs-4", category: "Rule", name: "Cảnh Giới #4: Nguyên Anh Kỳ", description: "Phá Đan thành Anh, thọ nguyên ngàn năm", locked: true },
  { id: "w-cs-5", category: "Rule", name: "Cảnh Giới #5: Hóa Thần Kỳ", description: "Thần thức xuất khiếu, uy áp vạn dặm Phàm Giới", locked: true },
  { id: "w-loc-1", category: "Location", name: "Thanh Vân Tông", description: "Tông môn tu tiên cổ xưa đứng đầu Nam Châu", locked: true },
  { id: "w-loc-2", category: "Location", name: "Vạn Yêu Sâm Lâm", description: "Khu rừng rậm hoang dã cư ngụ vô số Yêu Tộc viễn cổ", locked: true },
  { id: "w-fac-1", category: "Organization", name: "Cửu Sương Ma Tộc", description: "Thế lực ma đạo vạn năm tích tụ tà khí", locked: true }
];

export const WorldBible: React.FC<WorldBibleProps> = ({ projectDir }) => {
  const [entities, setEntities] = useState<WorldEntity[]>(DEFAULT_WORLD_ENTITIES);

  React.useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(data => {
        if (data && data.world_lore && Array.isArray(data.world_lore) && data.world_lore.length > 0) {
          setEntities(data.world_lore);
        } else {
          setEntities(DEFAULT_WORLD_ENTITIES);
        }
      }).catch(() => {
        setEntities(DEFAULT_WORLD_ENTITIES);
      });
    }
  }, [projectDir]);

  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

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
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
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

        <button
          onClick={() => {
            const newEnt: WorldEntity = {
              id: `w-${Date.now()}`,
              category: 'Location',
              name: 'New Location / Rule',
              description: 'Lore details...',
              locked: false
            };
            saveEntitiesToProject([...entities, newEnt]);
          }}
          className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all"
        >
          <Plus size={14} /> Add World Lore
        </button>
      </div>

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
              className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-all ${
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
              Bạn có thể tự định nghĩa địa danh, tổ chức, quy luật thế giới quan để AI luôn tuân thủ nhất quán trong suốt câu chuyện.
            </p>
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
              }}
              className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-2 shadow-xl shadow-indigo-600/20 transition-all cursor-pointer"
            >
              <Plus size={16} /> Thêm Bối Cảnh Thế Giới Quan
            </button>
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

                <button
                  onClick={() => toggleLock(ent.id)}
                  className={`p-1.5 rounded-lg transition-all ${
                    ent.locked ? 'bg-amber-500/20 text-amber-300' : 'bg-white/5 text-slate-400 hover:text-white'
                  }`}
                  title={ent.locked ? 'Locked World Rule' : 'Unlocked'}
                >
                  {ent.locked ? <Lock size={14} /> : <Unlock size={14} />}
                </button>
              </div>

              <p className="text-xs text-slate-300 leading-relaxed">{ent.description}</p>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
