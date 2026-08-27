import React, { useState } from 'react';
import { BookOpen, Layers, Users, Calendar, Sparkles, ChevronRight, FileText, Plus } from 'lucide-react';

export interface Chapter {
  id: string;
  chapterNumber: number;
  title: string;
  summary: string;
  characters: string[];
  scenesCount: number;
}

import { StoryImportModal } from './StoryImportModal';
import { Download } from 'lucide-react';

interface StoryWorkspaceProps {
  projectDir?: string | null;
}

export const StoryWorkspace: React.FC<StoryWorkspaceProps> = ({ projectDir }) => {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [chapters, setChapters] = useState<Chapter[]>([]);

  const [selectedChapId, setSelectedChapId] = useState<string>('');

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
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/20 transition-all"
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
                characters: ['A Lãng'],
                scenesCount: 3
              };
              setChapters(prev => [...prev, newChap]);
            }}
            className="px-3.5 py-1.5 rounded-lg bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-cyan-500/20 transition-all"
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
          const newChaps: Chapter[] = Array.from({ length: count }, (_, i) => ({
            id: `imported-${Date.now()}-${i + 1}`,
            chapterNumber: chapters.length + i + 1,
            title: `Chương ${chapters.length + i + 1} (Đã tải)`,
            summary: `Nội dung chương ${chapters.length + i + 1} đã được tải về dự án và sẵn sàng viết lại kịch bản AI.`,
            characters: ['AutoDetect'],
            scenesCount: 4
          }));
          setChapters(prev => [...prev, ...newChaps]);
          alert(`Đã tải thành công ${count} chương truyện vào dự án!`);
        }}
      />

      {/* CHAPTERS LIST */}
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
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
                onClick={() => setSelectedChapId(chap.id)}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-cyan-500/10 border-cyan-500/50 shadow-md shadow-cyan-500/10'
                    : 'bg-[#111318] hover:bg-[#161a22] border-white/5'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="w-6 h-6 rounded bg-cyan-500/20 text-cyan-300 font-bold text-xs flex items-center justify-center border border-cyan-500/30 font-['Outfit']">
                      #{chap.chapterNumber}
                    </span>
                    <h3 className="text-sm font-bold text-white font-['Outfit']">{chap.title}</h3>
                  </div>

                  <span className="px-2 py-0.5 rounded bg-white/5 text-slate-400 text-[11px] font-mono">
                    {chap.scenesCount} Scenes
                  </span>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed mb-3">{chap.summary}</p>

                <div className="flex items-center justify-between pt-2 border-t border-white/5 text-xs text-slate-400">
                  <div className="flex items-center gap-1.5">
                    <Users size={13} className="text-slate-500" />
                    <span>Characters: {chap.characters.join(', ')}</span>
                  </div>
                  <span className="text-cyan-400 font-semibold flex items-center gap-1">
                    Open Chapter Scenes <ChevronRight size={13} />
                  </span>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
