import React, { useState } from 'react';
import { Globe, Plus, Lock, Unlock, Shield, MapPin, Building, BookMarked, Search } from 'lucide-react';

export interface WorldEntity {
  id: string;
  category: 'Location' | 'Organization' | 'Rule' | 'Terminology' | 'History';
  name: string;
  description: string;
  locked: boolean;
}

export const WorldBible: React.FC = () => {
  const [entities, setEntities] = useState<WorldEntity[]>([
    {
      id: 'w-1',
      category: 'Location',
      name: 'Đà Lạt (Thành phố Ngàn Hoa)',
      description: 'Mountain city in the Central Highlands, famous for foggy pine forests, cool climate, and European-style villas.',
      locked: true
    },
    {
      id: 'w-2',
      category: 'Organization',
      name: 'Vạn Hương Các (Guild of Fragrance)',
      description: 'Ancient merchant guild specializing in rare botanicals and tea craftsmanship.',
      locked: false
    },
    {
      id: 'w-3',
      category: 'Terminology',
      name: 'Linh Khí (Spiritual Qi)',
      description: 'Environmental energy density flowing through high altitude mountain peaks.',
      locked: true
    }
  ]);

  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [searchQuery, setSearchQuery] = useState<string>('');

  const toggleLock = (id: string) => {
    setEntities(prev => prev.map(e => e.id === id ? { ...e, locked: !e.locked } : e));
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
            setEntities(prev => [...prev, newEnt]);
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
        {filteredEntities.map(ent => (
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
        ))}
      </div>
    </div>
  );
};
