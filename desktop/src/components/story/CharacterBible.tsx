import React, { useState, useEffect } from 'react';
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
  Trash2,
  Copy,
  Check,
  FileJson,
  FileText,
  RefreshCw,
  X
} from 'lucide-react';

import { PythonEngineService } from '../../services/pythonEngine';

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
  projectDir?: string | null;
  onSelectCharacter?: (char: Character) => void;
}

export const CharacterBible: React.FC<CharacterBibleProps> = ({ projectDir, onSelectCharacter }) => {
  const [characters, setCharacters] = useState<Character[]>([]);
  const [selectedCharId, setSelectedCharId] = useState<string>('');
  const [copiedCharId, setCopiedCharId] = useState<string | null>(null);
  const [copiedType, setCopiedType] = useState<'text' | 'json' | null>(null);
  const [copiedAllStatus, setCopiedAllStatus] = useState<'text' | 'json' | null>(null);

  const [editingChar, setEditingChar] = useState<Character | null>(null);
  const [isRegenerating, setIsRegenerating] = useState(false);

  const handleCopyCharText = (char: Character, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const info = `[Tên: ${char.name}] (${char.alias})\nGiới tính: ${char.gender} | Tuổi: ${char.age}\nTính cách: ${char.personality}\nNgoại hình: ${char.appearance}\nTrang phục/Cảnh giới: ${char.clothing}\nGiọng đọc: ${char.voice} | Phong cách: ${char.speakingStyle}`;
    navigator.clipboard.writeText(info);
    setCopiedCharId(char.id);
    setCopiedType('text');
    setTimeout(() => { setCopiedCharId(null); setCopiedType(null); }, 2000);
  };

  const handleCopyCharJson = (char: Character, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    navigator.clipboard.writeText(JSON.stringify(char, null, 2));
    setCopiedCharId(char.id);
    setCopiedType('json');
    setTimeout(() => { setCopiedCharId(null); setCopiedType(null); }, 2000);
  };

  const handleCopyAllText = () => {
    if (characters.length === 0) return;
    const header = `=== DANH SÁCH BẢN ĐỒ NHÂN VẬT (${characters.length} nhân vật) ===\n\n`;
    const body = characters.map((char, index) => (
      `[${index + 1}] ${char.name} (${char.alias || 'Chưa rõ'})\n` +
      `  • Giới tính: ${char.gender} | Tuổi: ${char.age}\n` +
      `  • Tính cách: ${char.personality}\n` +
      `  • Ngoại hình/Mục tiêu: ${char.appearance}\n` +
      `  • Cảnh giới/Vị trí: ${char.clothing}\n` +
      `  • Mẫu giọng: ${char.voice} (${char.speakingStyle})`
    )).join('\n\n');

    navigator.clipboard.writeText(header + body);
    setCopiedAllStatus('text');
    setTimeout(() => setCopiedAllStatus(null), 2500);
  };

  const handleCopyAllJson = () => {
    if (characters.length === 0) return;
    navigator.clipboard.writeText(JSON.stringify(characters, null, 2));
    setCopiedAllStatus('json');
    setTimeout(() => setCopiedAllStatus(null), 2500);
  };

  React.useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(async data => {
        if (data && data.characters && Array.isArray(data.characters) && data.characters.length > 0) {
          setCharacters(data.characters);
        } else {
          try {
            const rawBible = await PythonEngineService.readTextFile(`${projectDir}/story_bible.json`);
            if (rawBible) {
              const bible = JSON.parse(rawBible);
              if (bible.characters && Array.isArray(bible.characters) && bible.characters.length > 0) {
                const formatted = bible.characters.map((c: any, idx: number) => ({
                  id: c.id || `char_${String(idx + 1).padStart(3, '0')}`,
                  name: c.name || "Nhân vật",
                  alias: c.alias || c.role || c.realm || "Khởi Đầu",
                  gender: c.gender || "Nam",
                  age: String(c.age || (19 + (idx * 4) % 20)),
                  personality: Array.isArray(c.personality) ? c.personality.join(", ") : String(c.personality || "Quyết đoán"),
                  appearance: c.appearance || `Mục tiêu: ${c.goal || "Khám phá thế giới"}`,
                  clothing: c.clothing || `Cảnh giới: ${c.realm || "Khởi Đầu"} • Vị trí: ${c.location || "Vùng Khởi Đầu"}`,
                  voice: c.voice || (c.gender === "Nữ" ? "vi_female_hero" : "vi_male_hero"),
                  speakingStyle: c.speakingStyle || "Trang trọng",
                  locked: c.locked ?? true
                }));
                setCharacters(formatted);
                return;
              }
            }
          } catch (e) {}
          setCharacters([]);
        }
      }).catch(() => {
        setCharacters([]);
      });
    }
  }, [projectDir]);

  const saveCharactersToProject = async (newChars: Character[]) => {
    setCharacters(newChars);
    if (projectDir) {
      try {
        const json = (await PythonEngineService.readProjectJson(projectDir)) || {};
        json.characters = newChars;
        await PythonEngineService.writeProjectJson(projectDir, json);
      } catch (e) {
        console.error('Failed to save characters to project.json:', e);
      }
    }
  };

  const toggleLock = (id: string) => {
    const updated = characters.map(c => c.id === id ? { ...c, locked: !c.locked } : c);
    saveCharactersToProject(updated);
  };

  const handleDeleteCharacter = (id: string, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    if (!confirm('Bạn có chắc chắn muốn xóa nhân vật này khỏi danh sách?')) return;
    const updated = characters.filter(c => c.id !== id);
    saveCharactersToProject(updated);
    if (selectedCharId === id) setSelectedCharId('');
  };

  const [regenStatus, setRegenStatus] = useState<string | null>(null);

  const handleRegenerateCharacters = async () => {
    if (!projectDir) return;
    if (!confirm('Bạn có chắc muốn gọi AI Qwen 2.5 tái tạo lại toàn bộ dàn nhân vật cho dự án không?')) return;
    setIsRegenerating(true);
    setRegenStatus('Đang chạy Python Engine & AI Qwen 2.5 tạo lại dàn nhân vật...');
    try {
      const projJson = await PythonEngineService.readProjectJson(projectDir);
      let idea = projJson?.story_idea || projJson?.idea || {};
      if (!idea || !idea.title) {
        idea = {
          title: projJson?.name || "Kịch Bản Mới",
          genre: projJson?.genre || "Hành động viễn tưởng",
          protagonist: projJson?.characters?.[0] ? { name: projJson.characters[0].name, background: "Nhân vật chính" } : { name: "Diệp Phàm", background: "Nhân vật chính" },
          total_chapters: projJson?.total_chapters || 100
        };
      }

      const bible = await PythonEngineService.initializeNovel(projectDir, idea);
      const updatedProj = await PythonEngineService.readProjectJson(projectDir);

      if (updatedProj && updatedProj.characters && Array.isArray(updatedProj.characters) && updatedProj.characters.length > 0) {
        setCharacters(updatedProj.characters);
      } else if (bible && bible.characters && Array.isArray(bible.characters)) {
        const formatted = bible.characters.map((c: any, idx: number) => ({
          id: c.id || `char_${String(idx + 1).padStart(3, '0')}`,
          name: c.name || `Nhân vật ${idx + 1}`,
          alias: c.alias || c.role || c.realm || "Khởi Đầu",
          gender: c.gender || (idx % 2 === 0 ? "Nam" : "Nữ"),
          age: String(c.age || (19 + (idx * 4) % 25)),
          personality: Array.isArray(c.personality) ? c.personality.join(", ") : String(c.personality || "Quyết đoán"),
          appearance: c.appearance || `Mục tiêu: ${c.goal || "Khám phá thế giới"}`,
          clothing: c.clothing || `Cảnh giới: ${c.realm || "Khởi Đầu"} • Vị trí: ${c.location || "Vùng Khởi Đầu"}`,
          voice: c.voice || (c.gender === "Nữ" ? "vi_female_hero" : "vi_male_hero"),
          speakingStyle: c.speakingStyle || "Trang trọng",
          locked: false
        }));
        saveCharactersToProject(formatted);
      }
      setRegenStatus('Tái tạo dàn nhân vật bằng AI thành công!');
      setTimeout(() => setRegenStatus(null), 3000);
    } catch (e: any) {
      console.error("Lỗi khi tái tạo dữ liệu nhân vật:", e);
      setRegenStatus(`Lỗi AI: ${e?.message || e}`);
      setTimeout(() => setRegenStatus(null), 4000);
    } finally {
      setIsRegenerating(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans relative">
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

        <div className="flex items-center gap-2">
          {characters.length > 0 && (
            <>
              <button
                onClick={handleCopyAllText}
                className={`px-3 py-1.5 rounded-lg border font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                  copiedAllStatus === 'text'
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-md shadow-emerald-500/10'
                    : 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300 hover:text-white'
                }`}
                title="Sao chép toàn bộ danh sách nhân vật dạng văn bản đọc"
              >
                {copiedAllStatus === 'text' ? <Check size={14} className="text-emerald-400" /> : <FileText size={14} />}
                {copiedAllStatus === 'text' ? 'Đã Sao Chép Text!' : `Copy Tất Cả (${characters.length})`}
              </button>

              <button
                onClick={handleCopyAllJson}
                className={`px-3 py-1.5 rounded-lg border font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer ${
                  copiedAllStatus === 'json'
                    ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-300 shadow-md shadow-emerald-500/10'
                    : 'bg-white/5 hover:bg-white/10 border-white/10 text-slate-300 hover:text-white'
                }`}
                title="Sao chép toàn bộ danh sách nhân vật dạng JSON"
              >
                {copiedAllStatus === 'json' ? <Check size={14} className="text-emerald-400" /> : <FileJson size={14} />}
                {copiedAllStatus === 'json' ? 'Đã Sao Chép JSON!' : 'Copy Tất Cả (JSON)'}
              </button>
            </>
          )}

          <button
            onClick={handleRegenerateCharacters}
            disabled={isRegenerating}
            className="px-3 py-1.5 rounded-lg bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50"
            title="Tái tạo lại danh sách nhân vật bằng AI"
          >
            <RefreshCw size={14} className={isRegenerating ? "animate-spin" : ""} />
            {isRegenerating ? "Đang Tái Tạo..." : "Tái Tạo AI"}
          </button>

          <button
            onClick={() => {
              const newChar: Character = {
                id: `char-${Date.now()}`,
                name: 'New Character',
                alias: 'Alias',
                gender: 'Nam',
                age: '20',
                personality: 'Personality description...',
                appearance: 'Visual features...',
                clothing: 'Robes / Outfit',
                voice: 'vi_male_hero',
                speakingStyle: 'Standard',
                locked: false
              };
              saveCharactersToProject([...characters, newChar]);
              setSelectedCharId(newChar.id);
              setEditingChar(newChar);
            }}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition-all cursor-pointer"
          >
            <Plus size={14} /> Add Character
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

      {/* CHARACTER GRID VIEW */}
      {characters.length === 0 ? (
        <div className="flex-1 min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
          <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20 mb-4 shadow-lg shadow-cyan-500/10">
            <Users size={28} />
          </div>
          <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Dự Án Chưa Có Nhân Vật Nào</h3>
          <p className="text-xs text-slate-400 max-w-md mb-5 leading-relaxed">
            Hồ sơ nhân vật sẽ được tự động nhận diện khi Qwen 2.5 AI viết lại kịch bản truyện, hoặc bạn có thể tự thêm nhân vật thủ công hay bấm Tái Tạo AI.
          </p>
          <div className="flex items-center gap-3">
            <button
              onClick={handleRegenerateCharacters}
              className="px-4 py-2.5 rounded-xl bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 border border-amber-500/40 font-bold text-xs flex items-center gap-2 transition-all cursor-pointer"
            >
              <RefreshCw size={16} /> Tái Tạo Nhân Vật (AI)
            </button>
            <button
              onClick={() => {
                const newChar: Character = {
                  id: `char-${Date.now()}`,
                  name: 'Nhân Vật Mới',
                  alias: 'Hero',
                  gender: 'Nam',
                  age: '24',
                  personality: 'Dũng cảm, thông minh...',
                  appearance: 'Cao ráo, mắt sáng...',
                  clothing: 'Trang phục cổ trang',
                  voice: 'vi_male_hero',
                  speakingStyle: 'Mạnh mẽ',
                  locked: false
                };
                saveCharactersToProject([...characters, newChar]);
                setSelectedCharId(newChar.id);
                setEditingChar(newChar);
              }}
              className="px-5 py-2.5 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-bold text-xs flex items-center gap-2 shadow-xl shadow-cyan-500/20 transition-all cursor-pointer"
            >
              <Plus size={16} /> Thêm Nhân Vật Mới
            </button>
          </div>
        </div>
      ) : (
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

                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={(e) => { e.stopPropagation(); setEditingChar(char); }}
                      className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-white transition-all cursor-pointer"
                      title="Chỉnh sửa hồ sơ nhân vật"
                    >
                      <Edit3 size={14} />
                    </button>
                    <button
                      onClick={(e) => handleCopyCharText(char, e)}
                      className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                        copiedCharId === char.id && copiedType === 'text' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-slate-400 hover:text-white'
                      }`}
                      title="Sao chép văn bản hồ sơ nhân vật"
                    >
                      {copiedCharId === char.id && copiedType === 'text' ? <Check size={14} /> : <FileText size={14} />}
                    </button>
                    <button
                      onClick={(e) => handleCopyCharJson(char, e)}
                      className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                        copiedCharId === char.id && copiedType === 'json' ? 'bg-emerald-500/20 text-emerald-400' : 'bg-white/5 text-slate-400 hover:text-white'
                      }`}
                      title="Sao chép JSON nhân vật đầy đủ"
                    >
                      {copiedCharId === char.id && copiedType === 'json' ? <Check size={14} /> : <FileJson size={14} />}
                    </button>
                    <button
                      onClick={(e) => { e.stopPropagation(); toggleLock(char.id); }}
                      className={`p-1.5 rounded-lg transition-all cursor-pointer ${
                        char.locked ? 'bg-amber-500/20 text-amber-300' : 'bg-white/5 text-slate-400 hover:text-white'
                      }`}
                      title={char.locked ? 'Locked Character Data' : 'Unlocked'}
                    >
                      {char.locked ? <Lock size={14} /> : <Unlock size={14} />}
                    </button>
                    <button
                      onClick={(e) => handleDeleteCharacter(char.id, e)}
                      className="p-1.5 rounded-lg bg-white/5 text-slate-400 hover:text-rose-400 transition-all cursor-pointer"
                      title="Xóa nhân vật khỏi danh sách"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
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
      )}

      {/* EDIT CHARACTER MODAL */}
      {editingChar && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#111318] border border-white/10 rounded-2xl w-full max-w-lg p-6 space-y-4 shadow-2xl">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <h3 className="text-base font-bold text-white font-['Outfit'] flex items-center gap-2">
                <Edit3 size={18} className="text-cyan-400" /> Chỉnh Sửa Hồ Sơ Nhân Vật
              </h3>
              <button onClick={() => setEditingChar(null)} className="text-slate-400 hover:text-white p-1 cursor-pointer">
                <X size={18} />
              </button>
            </div>

            <div className="space-y-3 text-xs">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Tên nhân vật</label>
                  <input
                    type="text"
                    value={editingChar.name}
                    onChange={e => setEditingChar({ ...editingChar, name: e.target.value })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Danh hiệu / Vai trò</label>
                  <input
                    type="text"
                    value={editingChar.alias}
                    onChange={e => setEditingChar({ ...editingChar, alias: e.target.value })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Giới tính</label>
                  <select
                    value={editingChar.gender}
                    onChange={e => setEditingChar({ ...editingChar, gender: e.target.value })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
                  >
                    <option value="Nam">Nam</option>
                    <option value="Nữ">Nữ</option>
                    <option value="Khác">Khác</option>
                  </select>
                </div>
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Tuổi</label>
                  <input
                    type="text"
                    value={editingChar.age}
                    onChange={e => setEditingChar({ ...editingChar, age: e.target.value })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>

              <div>
                <label className="text-slate-400 font-semibold mb-1 block">Tính cách</label>
                <input
                  type="text"
                  value={editingChar.personality}
                  onChange={e => setEditingChar({ ...editingChar, personality: e.target.value })}
                  className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold mb-1 block">Ngoại hình / Mục tiêu</label>
                <textarea
                  rows={2}
                  value={editingChar.appearance}
                  onChange={e => setEditingChar({ ...editingChar, appearance: e.target.value })}
                  className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white custom-scrollbar focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div>
                <label className="text-slate-400 font-semibold mb-1 block">Trang phục / Cảnh giới</label>
                <input
                  type="text"
                  value={editingChar.clothing}
                  onChange={e => setEditingChar({ ...editingChar, clothing: e.target.value })}
                  className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Giọng đọc (TTS Voice)</label>
                  <input
                    type="text"
                    value={editingChar.voice}
                    onChange={e => setEditingChar({ ...editingChar, voice: e.target.value })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white font-mono focus:outline-none focus:border-cyan-500"
                  />
                </div>
                <div>
                  <label className="text-slate-400 font-semibold mb-1 block">Phong cách nói</label>
                  <input
                    type="text"
                    value={editingChar.speakingStyle}
                    onChange={e => setEditingChar({ ...editingChar, speakingStyle: e.target.value })}
                    className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-white focus:outline-none focus:border-cyan-500"
                  />
                </div>
              </div>
            </div>

            <div className="flex items-center justify-end gap-2 pt-2 border-t border-white/10">
              <button
                onClick={() => setEditingChar(null)}
                className="px-4 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-bold cursor-pointer"
              >
                Hủy
              </button>
              <button
                onClick={() => {
                  const updated = characters.map(c => c.id === editingChar.id ? editingChar : c);
                  saveCharactersToProject(updated);
                  setEditingChar(null);
                }}
                className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black text-xs font-extrabold shadow-md shadow-cyan-500/20 cursor-pointer"
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

