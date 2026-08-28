import React, { useState } from 'react';
import { BookOpen, Layers, Users, Calendar, Sparkles, ChevronRight, FileText, Plus, Edit3, Trash2, Save, X, RefreshCw } from 'lucide-react';

export interface Chapter {
  id: string;
  chapterNumber: number;
  title: string;
  summary: string;
  characters: string[];
  scenesCount: number;
  content?: string;
}

import { PythonEngineService } from '../../services/pythonEngine';
import { StoryImportModal } from './StoryImportModal';
import { Download } from 'lucide-react';

interface StoryWorkspaceProps {
  projectDir?: string | null;
}

export const StoryWorkspace: React.FC<StoryWorkspaceProps> = ({ projectDir }) => {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [selectedChapId, setSelectedChapId] = useState<string>('');
  const [editingTitle, setEditingTitle] = useState('');
  const [editingSummary, setEditingSummary] = useState('');
  const [editingContent, setEditingContent] = useState('');
  const [editingChars, setEditingChars] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const selectedChap = chapters.find(c => c.id === selectedChapId);

  const saveChaptersToProject = async (newChaps: Chapter[]) => {
    setChapters(newChaps);
    if (projectDir) {
      try {
        const json = (await PythonEngineService.readProjectJson(projectDir)) || {};
        json.chapters = newChaps;
        await PythonEngineService.writeProjectJson(projectDir, json);
      } catch (e) {
        console.error('Failed to save chapters to project.json:', e);
      }
    }
  };

  React.useEffect(() => {
    if (!projectDir) return;
    const loadChapters = async () => {
      let loadedChaps: Chapter[] = [];
      try {
        const data = await PythonEngineService.readProjectJson(projectDir);
        if (data && data.chapters && Array.isArray(data.chapters) && data.chapters.length > 0) {
          loadedChaps = [...data.chapters];
        }
      } catch {}

      // Scan chapters/chapter_0001.txt to chapter_0050.txt from disk
      for (let i = 1; i <= 50; i++) {
        const padNum = String(i).padStart(4, '0');
        const chapFilePath = `${projectDir}/chapters/chapter_${padNum}.txt`;
        try {
          const content = await PythonEngineService.readTextFile(chapFilePath);
          if (content && content.trim().length > 0) {
            const existingIdx = loadedChaps.findIndex(c => c.chapterNumber === i);
            const chapObj: Chapter = {
              id: `chap-${padNum}`,
              chapterNumber: i,
              title: `Chương ${i}: Hành Trình Tu Tiên Khởi Đầu`,
              summary: content.slice(0, 120).replace(/\n/g, ' ') + '...',
              characters: ['Lâm Phàm', 'Lý Thanh Vân'],
              scenesCount: 2,
              content: content
            };
            if (existingIdx >= 0) {
              loadedChaps[existingIdx] = {
                ...loadedChaps[existingIdx],
                content: content,
                summary: loadedChaps[existingIdx].summary || chapObj.summary
              };
            } else {
              loadedChaps.push(chapObj);
            }
          }
        } catch {}
      }

      setChapters(loadedChaps);
      if (loadedChaps.length > 0) {
        const first = loadedChaps[0];
        setSelectedChapId(first.id);
        setEditingTitle(first.title);
        setEditingSummary(first.summary);
        setEditingContent(first.content || '');
        setEditingChars((first.characters || []).join(', '));
      }
    };

    loadChapters();
  }, [projectDir]);

  const handleSelectChapter = (chap: Chapter) => {
    setSelectedChapId(chap.id);
    setEditingTitle(chap.title);
    setEditingSummary(chap.summary);
    setEditingContent(chap.content || '');
    setEditingChars(chap.characters.join(', '));
    setIsEditing(false);
  };

  const handleSaveEdit = () => {
    if (!selectedChap) return;
    const updated = chapters.map(c => c.id === selectedChap.id ? {
      ...c,
      title: editingTitle,
      summary: editingSummary,
      content: editingContent,
      characters: editingChars.split(',').map(s => s.trim()).filter(Boolean)
    } : c);
    saveChaptersToProject(updated);
    setIsEditing(false);
  };

  const handleDeleteChapter = (id: string) => {
    const confirmed = window.confirm('Bạn có chắc chắn muốn xóa chương này?');
    if (!confirmed) return;
    const updated = chapters.filter(c => c.id !== id).map((c, i) => ({ ...c, chapterNumber: i + 1 }));
    saveChaptersToProject(updated);
    if (selectedChapId === id) {
      setSelectedChapId('');
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
            <BookOpen size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Story & Chapter Workspace (MODE_STORY)
            </h2>
            <p className="text-xs text-slate-400">
              Breakdown your story into chapters, scene outlines, character arcs, and AI plot summaries.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsImportModalOpen(true)}
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all cursor-pointer"
          >
            <Download size={14} /> Import Truyện (Web / File)
          </button>

          <button
            onClick={() => {
              const newChap: Chapter = {
                id: `chap-${Date.now()}`,
                chapterNumber: chapters.length + 1,
                title: `Chapter ${chapters.length + 1}`,
                summary: 'Chapter summary text...',
                characters: ['AutoDetect'],
                scenesCount: 0,
                content: ''
              };
              saveChaptersToProject([...chapters, newChap]);
              handleSelectChapter(newChap);
            }}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition-all cursor-pointer"
          >
            <Plus size={14} /> Add Chapter
          </button>
        </div>
      </div>

      <StoryImportModal
        isOpen={isImportModalOpen}
        onClose={() => setIsImportModalOpen(false)}
        projectDir={projectDir}
        onImportComplete={(count) => {
          setIsImportModalOpen(false);
          // Reload chapters from project.json (Python already saved them with content)
          if (projectDir) {
            PythonEngineService.readProjectJson(projectDir).then(data => {
              if (data && data.chapters && Array.isArray(data.chapters)) {
                setChapters(data.chapters);
              }
            }).catch(console.error);
          }
          alert(`Đã tải thành công ${count} chương truyện vào dự án!`);
        }}
      />

      {/* MAIN CONTENT: SPLIT PANEL */}
      <div className="flex-1 flex gap-4 overflow-hidden min-h-0">
        {/* LEFT: CHAPTERS LIST */}
        <div className={`${selectedChap ? 'w-[340px] min-w-[300px]' : 'w-full'} overflow-y-auto space-y-2.5 custom-scrollbar transition-all`}>
          {chapters.length === 0 ? (
            <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
              <div className="w-14 h-14 rounded-2xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20 mb-4 shadow-lg shadow-cyan-500/10">
                <BookOpen size={28} />
              </div>
              <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Dự Án Chưa Có Chương Truyện Nào</h3>
              <p className="text-xs text-slate-400 max-w-md mb-5 leading-relaxed">
                Hãy nhập đường dẫn URL truyện web (Nettruyen, Webnovel...) hoặc tải file TXT để hệ thống tự động cào chương và dùng Qwen 2.5 AI viết lại kịch bản.
              </p>
              <button
                onClick={() => setIsImportModalOpen(true)}
                className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-cyan-500 to-indigo-600 hover:from-cyan-400 hover:to-indigo-500 text-white font-bold text-xs flex items-center gap-2 shadow-xl shadow-cyan-500/20 transition-all cursor-pointer"
              >
                <Download size={16} /> Import Truyện (Web / File) Ngay
              </button>
            </div>
          ) : (
            chapters.map(chap => {
              const isSelected = selectedChapId === chap.id;
              return (
                <div
                  key={chap.id}
                  onClick={() => handleSelectChapter(chap)}
                  className={`p-3.5 rounded-xl border transition-all cursor-pointer group ${
                    isSelected
                      ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                      : 'bg-[#111318] hover:bg-[#161a22] border-white/5'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <div className="flex items-center gap-2">
                      <span className="w-6 h-6 rounded bg-cyan-500/20 text-cyan-300 font-bold text-xs flex items-center justify-center border border-cyan-500/30 font-['Outfit']">
                        #{chap.chapterNumber}
                      </span>
                      <h3 className="text-sm font-bold text-white font-['Outfit'] truncate max-w-[200px]">{chap.title}</h3>
                    </div>

                    <button
                      onClick={(e) => { e.stopPropagation(); handleDeleteChapter(chap.id); }}
                      className="p-1 rounded bg-rose-500/0 hover:bg-rose-500/20 text-transparent group-hover:text-rose-400 transition-all"
                      title="Xóa chương"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>

                  <p className="text-[11px] text-slate-400 leading-relaxed line-clamp-2 mb-2">{chap.summary}</p>

                  <div className="flex items-center justify-between text-[11px] text-slate-500">
                    <div className="flex items-center gap-1">
                      <Users size={11} />
                      <span className="truncate max-w-[140px]">{chap.characters.join(', ')}</span>
                    </div>
                    {isSelected && (
                      <span className="text-cyan-400 font-semibold flex items-center gap-0.5">
                        Đang xem <ChevronRight size={11} />
                      </span>
                    )}
                  </div>
                </div>
              );
            })
          )}
        </div>

        {/* RIGHT: CHAPTER DETAIL PANEL */}
        {selectedChap && (
          <div className="flex-1 overflow-y-auto bg-[#111318] rounded-xl border border-white/5 p-5 space-y-5 custom-scrollbar">
            {/* DETAIL HEADER */}
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="w-8 h-8 rounded-lg bg-cyan-500/20 text-cyan-300 font-bold text-sm flex items-center justify-center border border-cyan-500/30 font-['Outfit']">
                  #{selectedChap.chapterNumber}
                </span>
                <div>
                  {isEditing ? (
                    <input
                      value={editingTitle}
                      onChange={e => setEditingTitle(e.target.value)}
                      className="bg-black/40 border border-cyan-500/30 rounded-lg px-3 py-1.5 text-sm font-bold text-white font-['Outfit'] focus:outline-none focus:border-cyan-400 w-full max-w-sm"
                      placeholder="Tên chương..."
                    />
                  ) : (
                    <h3 className="text-lg font-bold text-white font-['Outfit'] tracking-tight">{selectedChap.title}</h3>
                  )}
                  <p className="text-[11px] text-slate-500 mt-0.5">ID: {selectedChap.id}</p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {isEditing ? (
                  <>
                    <button
                      onClick={handleSaveEdit}
                      className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
                    >
                      <Save size={13} /> Lưu
                    </button>
                    <button
                      onClick={() => { setIsEditing(false); handleSelectChapter(selectedChap); }}
                      className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
                    >
                      <X size={13} /> Hủy
                    </button>
                  </>
                ) : (
                  <>
                    <button
                      onClick={() => setIsEditing(true)}
                      className="px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
                    >
                      <Edit3 size={13} /> Chỉnh sửa
                    </button>
                    <button
                      onClick={() => setSelectedChapId('')}
                      className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 font-bold text-xs flex items-center gap-1.5 transition-all cursor-pointer"
                    >
                      <X size={13} /> Đóng
                    </button>
                  </>
                )}
              </div>
            </div>

            {/* METADATA ROW */}
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-black/30 rounded-lg p-3 border border-white/5">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 font-semibold">Chương số</p>
                <p className="text-sm font-bold text-cyan-400 font-['Outfit']">#{selectedChap.chapterNumber}</p>
              </div>
              <div className="bg-black/30 rounded-lg p-3 border border-white/5">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 font-semibold">Số Scenes</p>
                <p className="text-sm font-bold text-indigo-400 font-['Outfit']">{selectedChap.scenesCount}</p>
              </div>
              <div className="bg-black/30 rounded-lg p-3 border border-white/5">
                <p className="text-[10px] text-slate-500 uppercase tracking-wider mb-1 font-semibold">Nhân vật</p>
                <p className="text-sm font-bold text-amber-400 font-['Outfit']">{selectedChap.characters.length}</p>
              </div>
            </div>

            {/* CHARACTERS SECTION */}
            <div>
              <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mb-2 block">
                Nhân Vật Trong Chương
              </label>
              {isEditing ? (
                <input
                  value={editingChars}
                  onChange={e => setEditingChars(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50"
                  placeholder="Nhân vật 1, Nhân vật 2, ..."
                />
              ) : (
                <div className="flex flex-wrap gap-1.5">
                  {selectedChap.characters.map((char, i) => (
                    <span key={i} className="px-2.5 py-1 rounded-lg bg-amber-500/10 text-amber-300 border border-amber-500/20 text-[11px] font-semibold">
                      {char}
                    </span>
                  ))}
                </div>
              )}
            </div>

            {/* SUMMARY SECTION */}
            <div>
              <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mb-2 block">
                Tóm Tắt Nội Dung
              </label>
              {isEditing ? (
                <textarea
                  value={editingSummary}
                  onChange={e => setEditingSummary(e.target.value)}
                  rows={3}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50 resize-none"
                  placeholder="Tóm tắt nội dung chương..."
                />
              ) : (
                <div className="bg-black/30 rounded-lg p-3 border border-white/5">
                  <p className="text-xs text-slate-300 leading-relaxed">{selectedChap.summary}</p>
                </div>
              )}
            </div>

            {/* CONTENT / SCRIPT SECTION */}
            <div>
              <label className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold mb-2 block">
                Nội Dung / Kịch Bản Chương
              </label>
              {isEditing ? (
                <textarea
                  value={editingContent}
                  onChange={e => setEditingContent(e.target.value)}
                  rows={12}
                  className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-xs text-slate-200 focus:outline-none focus:border-cyan-500/50 resize-none font-mono leading-relaxed"
                  placeholder="Nội dung đầy đủ hoặc kịch bản AI của chương truyện..."
                />
              ) : (
                <div className="bg-black/30 rounded-lg p-4 border border-white/5 min-h-[180px]">
                  {selectedChap.content ? (
                    <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap font-mono">{selectedChap.content}</p>
                  ) : selectedChap.summary && selectedChap.summary !== 'Chapter summary text...' ? (
                    <div>
                      <p className="text-[10px] text-cyan-500/60 uppercase tracking-wider font-semibold mb-2">Tóm tắt (chưa có kịch bản chi tiết)</p>
                      <p className="text-xs text-slate-300 leading-relaxed whitespace-pre-wrap">{selectedChap.summary}</p>
                      <div className="mt-4 pt-3 border-t border-white/5 flex items-center gap-2">
                        <button
                          onClick={() => setIsEditing(true)}
                          className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 font-semibold text-[11px] flex items-center gap-1.5 border border-cyan-500/20 transition-all cursor-pointer"
                        >
                          <Edit3 size={12} /> Viết kịch bản chi tiết
                        </button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex flex-col items-center justify-center h-full min-h-[140px] text-center">
                      <FileText size={24} className="text-slate-600 mb-2" />
                      <p className="text-[11px] text-slate-500 mb-3">Chương chưa có nội dung kịch bản</p>
                      <button
                        onClick={() => setIsEditing(true)}
                        className="px-3 py-1.5 rounded-lg bg-cyan-600/20 hover:bg-cyan-600/30 text-cyan-400 font-semibold text-[11px] flex items-center gap-1.5 border border-cyan-500/20 transition-all cursor-pointer"
                      >
                        <Edit3 size={12} /> Viết nội dung
                      </button>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* ACTION BAR */}
            <div className="flex items-center gap-2 pt-3 border-t border-white/5">
              <button
                className="px-3.5 py-2 rounded-lg bg-indigo-600/20 hover:bg-indigo-600/30 text-indigo-300 font-semibold text-xs flex items-center gap-1.5 border border-indigo-500/20 transition-all cursor-pointer"
              >
                <Sparkles size={13} /> AI Viết Lại Kịch Bản
              </button>
              <button
                className="px-3.5 py-2 rounded-lg bg-purple-600/20 hover:bg-purple-600/30 text-purple-300 font-semibold text-xs flex items-center gap-1.5 border border-purple-500/20 transition-all cursor-pointer"
              >
                <RefreshCw size={13} /> Tạo Scenes Tự Động
              </button>
              <button
                onClick={() => handleDeleteChapter(selectedChap.id)}
                className="px-3.5 py-2 rounded-lg bg-rose-600/10 hover:bg-rose-600/20 text-rose-400 font-semibold text-xs flex items-center gap-1.5 border border-rose-500/20 transition-all cursor-pointer ml-auto"
              >
                <Trash2 size={13} /> Xóa Chương
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

