import React, { useState } from 'react';
import { 
  Users, 
  Plus, 
  Edit3, 
  Lock, 
  Unlock, 
  Sparkles, 
  UserCheck, 
  Mic, 
  Image as ImageIcon,
  Sliders,
  Trash2
} from 'lucide-react';

export interface Character {
  id: string;
  name: string;
  alias: string;
  gender: string;
  age: string;
  personality: string;
  appearance: string;
  clothing: string;
  voice: string;
  speakingStyle: string;
  referenceImage?: string;
  locked: boolean;
}

interface CharacterBibleProps {
  onSelectCharacter?: (char: Character) => void;
}

export const CharacterBible: React.FC<CharacterBibleProps> = ({ onSelectCharacter }) => {
  const [characters, setCharacters] = useState<Character[]>([
    {
      id: 'char-1',
      name: 'A Lãng (阿浪)',
      alias: 'Swordsman',
      gender: 'Male',
      age: '24',
      personality: 'Brave, calm under pressure, fiercely loyal to companions.',
      appearance: 'Tall, dark hair tied in a high ponytail, sharp eyes.',
      clothing: 'Blue warrior robes with leather shoulder guards.',
      voice: 'vi_male_hero',
      speakingStyle: 'Decisive, slightly deep tone.',
      locked: true
    },
    {
      id: 'char-2',
      name: 'Lâm Mộc (林木)',
      alias: 'Mystic Scholar',
      gender: 'Female',
      age: '22',
      personality: 'Witty, scholarly, cautious, ancient lore master.',
      appearance: 'Fair skin, long black braided hair, jade pendant.',
      clothing: 'White scholar silk robes with silver embroidery.',
      voice: 'vi_female_soft',
      speakingStyle: 'Gentle, articulate, clear diction.',
      locked: false
    }
  ]);

  const [selectedCharId, setSelectedCharId] = useState<string>('char-1');

  const toggleLock = (id: string) => {
    setCharacters(prev => prev.map(c => c.id === id ? { ...c, locked: !c.locked } : c));
  };

  const selectedChar = characters.find(c => c.id === selectedCharId);

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* TOP HEADER */}
      <div className="flex items-center justify-between bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
            <Users size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Character Bible (Dự Án Truyện AI)
            </h2>
            <p className="text-xs text-slate-400">
              Manage character consistency, visual appearances, personalities, and TTS voices.
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            const newChar: Character = {
              id: `char-${Date.now()}`,
              name: 'New Character',
              alias: 'Alias',
              gender: 'Unknown',
              age: '20',
              personality: 'Personality description...',
              appearance: 'Visual features...',
              clothing: 'Robes / Outfit',
              voice: 'vi_female',
              speakingStyle: 'Standard',
              locked: false
            };
            setCharacters(prev => [...prev, newChar]);
            setSelectedCharId(newChar.id);
          }}
          className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition-all"
        >
          <Plus size={14} /> Add Character
        </button>
      </div>

      {/* CHARACTER GRID VIEW */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {characters.map(char => {
          const isSelected = selectedCharId === char.id;
          return (
            <div
              key={char.id}
              onClick={() => {
                setSelectedCharId(char.id);
                onSelectCharacter?.(char);
              }}
              className={`p-4 rounded-xl border transition-all cursor-pointer ${
                isSelected
                  ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                  : 'bg-[#111318] hover:bg-[#161a22] border-white/5'
              }`}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-cyan-500/20 to-indigo-500/20 border border-white/10 flex items-center justify-center font-bold text-cyan-300 font-['Outfit'] text-lg">
                    {char.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-white font-['Outfit']">{char.name}</h3>
                    <span className="text-[11px] text-slate-400 font-medium">{char.gender} • Age {char.age}</span>
                  </div>
                </div>

                <button
                  onClick={(e) => { e.stopPropagation(); toggleLock(char.id); }}
                  className={`p-1.5 rounded-lg transition-all ${
                    char.locked ? 'bg-amber-500/20 text-amber-300' : 'bg-white/5 text-slate-400 hover:text-white'
                  }`}
                  title={char.locked ? 'Locked Character Data' : 'Unlocked'}
                >
                  {char.locked ? <Lock size={14} /> : <Unlock size={14} />}
                </button>
              </div>

              <div className="space-y-1.5 text-xs text-slate-300 pt-2 border-t border-white/5">
                <p className="line-clamp-2"><strong className="text-slate-500">Personality:</strong> {char.personality}</p>
                <p className="line-clamp-2"><strong className="text-slate-500">Appearance:</strong> {char.appearance}</p>
                <div className="pt-2 flex items-center justify-between text-[11px]">
                  <span className="px-2 py-0.5 rounded bg-indigo-500/15 text-indigo-300 border border-indigo-500/30 font-semibold flex items-center gap-1">
                    <Mic size={10} /> {char.voice}
                  </span>
                  <span className="text-slate-500 font-mono">ID: {char.id}</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
