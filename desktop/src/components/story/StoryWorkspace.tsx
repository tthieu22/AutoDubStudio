import React, { useState, useEffect } from 'react';
import { BookOpen, Download, Plus } from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';
import { StoryImportModal } from './StoryImportModal';
import { ChapterListSidebar } from './ChapterListSidebar';
import { ChapterEditorPanel, CopyConfig } from './ChapterEditorPanel';

export interface Chapter {
  id: string;
  chapterNumber: number;
  title: string;
  summary: string;
  characters: string[];
  scenesCount: number;
  content?: string;
}

interface StoryWorkspaceProps {
  projectDir?: string | null;
}

const formatChapterTitle = (chapNum: number, rawTitle?: string) => {
  if (!rawTitle) return `Chương ${chapNum}: Hành Trình Tu Tiên Khởi Đầu`;
  const clean = rawTitle.replace(new RegExp(`^Chương\\s*\\d+[:\\s-]*`, 'i'), '').trim();
  return `Chương ${chapNum}: ${clean || rawTitle}`;
};

export const StoryWorkspace: React.FC<StoryWorkspaceProps> = ({ projectDir }) => {
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [selectedChapId, setSelectedChapId] = useState<string>('');
  const [editingTitle, setEditingTitle] = useState('');
  const [editingSummary, setEditingSummary] = useState('');
  const [editingContent, setEditingContent] = useState('');
  const [editingChars, setEditingChars] = useState('');
  const [isEditing, setIsEditing] = useState(false);
  const [copiedChapId, setCopiedChapId] = useState<string | null>(null);
  const [copiedType, setCopiedType] = useState<'content' | 'json' | 'formatted' | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  const [showCopyConfig, setShowCopyConfig] = useState(false);
  const [copyConfig, setCopyConfig] = useState<CopyConfig>({
    includeTitle: true,
    includeCharacters: true,
    includeSummary: true,
    includeContent: true,
    includeMetadata: true
  });

  const selectedChap = chapters.find(c => c.id === selectedChapId);

  const triggerCopiedFeedback = (chapId: string, type: 'content' | 'json' | 'formatted') => {
    setCopiedChapId(chapId);
    setCopiedType(type);
    setTimeout(() => {
      setCopiedChapId(null);
      setCopiedType(null);
    }, 2000);
  };

  const handleCopyJson = (chap: Chapter, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const jsonObject: Record<string, any> = {};
    if (copyConfig.includeMetadata) {
      jsonObject.id = chap.id;
      jsonObject.chapterNumber = chap.chapterNumber;
      jsonObject.scenesCount = chap.scenesCount;
    }
    if (copyConfig.includeTitle) jsonObject.title = formatChapterTitle(chap.chapterNumber, chap.title);
    if (copyConfig.includeCharacters) jsonObject.characters = chap.characters;
    if (copyConfig.includeSummary) jsonObject.summary = chap.summary;
    if (copyConfig.includeContent) jsonObject.content = chap.content || '';

    navigator.clipboard.writeText(JSON.stringify(jsonObject, null, 2));
    triggerCopiedFeedback(chap.id, 'json');
  };

  const handleCopyContentOnly = (chap: Chapter, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const text = chap.content || chap.summary || chap.title;
    navigator.clipboard.writeText(text);
    triggerCopiedFeedback(chap.id, 'content');
  };

  const handleCopyFormattedText = (chap: Chapter, e?: React.MouseEvent) => {
    if (e) e.stopPropagation();
    const parts: string[] = [];
    if (copyConfig.includeTitle) parts.push(formatChapterTitle(chap.chapterNumber, chap.title));
    if (copyConfig.includeCharacters && chap.characters?.length) parts.push(`Nhân vật: ${chap.characters.join(', ')}`);
    if (copyConfig.includeSummary) parts.push(`Tóm tắt:\n${chap.summary}`);
    if (copyConfig.includeContent) parts.push(`Nội dung kịch bản:\n${chap.content || '(Chưa có nội dung)'}`);

    navigator.clipboard.writeText(parts.join('\n\n'));
    triggerCopiedFeedback(chap.id, 'formatted');
  };

  const saveChaptersToProject = async (newChaps: Chapter[]) => {
    const sorted = [...newChaps].sort((a, b) => (a.chapterNumber || 0) - (b.chapterNumber || 0));
    setChapters(sorted);
    if (projectDir) {
      try {
        const json = (await PythonEngineService.readProjectJson(projectDir)) || {};
        json.chapters = sorted;
        json.novel_current_chapter = sorted.length === 0 ? 1 : Math.max(...sorted.map(c => c.chapterNumber || 1)) + 1;
        await PythonEngineService.writeProjectJson(projectDir, json);
      } catch (e) {
        console.error('Failed to save chapters to project.json:', e);
      }
    }
  };

  useEffect(() => {
    if (!projectDir) return;
    const loadChapters = async () => {
      let loadedChaps: Chapter[] = [];
      try {
        const data = await PythonEngineService.readProjectJson(projectDir);
        if (data && data.chapters && Array.isArray(data.chapters) && data.chapters.length > 0) {
          loadedChaps = [...data.chapters];
        }
      } catch {}

      for (let i = 1; i <= 50; i++) {
        const padNum = String(i).padStart(4, '0');
        const chapFilePath = `${projectDir}/chapters/chapter_${padNum}.txt`;
        try {
          const content = await PythonEngineService.readTextFile(chapFilePath);
          if (content && content.trim().length > 0) {
            let titleFromContent = `Chương ${i}`;
            const matchTitle = content.match(/^#\s*(?:Chương\s*\d+\s*[:\-—]?\s*)?([^\n]+)/m);
            if (matchTitle && matchTitle[1]) {
              titleFromContent = matchTitle[1].trim();
            }

            const cleanSummaryText = content.replace(/^#+.*$/gm, '').replace(/###.*$/gm, '').replace(/\s+/g, ' ').trim();
            const summaryStr = (cleanSummaryText.slice(0, 140) || `Tóm tắt nội dung chương mới`) + '...';

            const existingIdx = loadedChaps.findIndex(c => c.chapterNumber === i);
            const chapObj: Chapter = {
              id: `chap-${padNum}`,
              chapterNumber: i,
              title: titleFromContent,
              summary: summaryStr,
              characters: ['Nhân vật chính'],
              scenesCount: 2,
              content: content
            };
            if (existingIdx >= 0) {
              loadedChaps[existingIdx] = {
                ...loadedChaps[existingIdx],
                title: loadedChaps[existingIdx].title ? loadedChaps[existingIdx].title.replace(/^Chương\s*\d+\s*[:\-—]?\s*/i, '') : titleFromContent,
                content: content,
                summary: loadedChaps[existingIdx].summary || summaryStr
              };
            } else {
              loadedChaps.push(chapObj);
            }
          }
        } catch {}
      }

      loadedChaps.sort((a, b) => (a.chapterNumber || 0) - (b.chapterNumber || 0));
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

  const handleDeleteChapter = async (id: string) => {
    const confirmed = window.confirm('Bạn có chắc chắn muốn xóa chương này?');
    if (!confirmed) return;
    const targetChap = chapters.find(c => c.id === id);
    const updated = chapters.filter(c => c.id !== id).map((c, i) => ({ ...c, chapterNumber: i + 1 }));

    if (projectDir) {
      if (targetChap) {
        const padNum = String(targetChap.chapterNumber).padStart(4, '0');
        await PythonEngineService.writeTextFile(`${projectDir}/chapters/chapter_${padNum}.txt`, '');
      }
      if (updated.length === 0) {
        for (let i = 1; i <= 50; i++) {
          const padNum = String(i).padStart(4, '0');
          await PythonEngineService.writeTextFile(`${projectDir}/chapters/chapter_${padNum}.txt`, '');
        }
      }
    }

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
        <ChapterListSidebar
          chapters={chapters}
          selectedChapId={selectedChapId}
          sortAsc={sortAsc}
          copiedChapId={copiedChapId}
          copiedType={copiedType}
          onSelectChapter={handleSelectChapter}
          onToggleSort={() => setSortAsc(!sortAsc)}
          onOpenImportModal={() => setIsImportModalOpen(true)}
          onCopyContentOnly={handleCopyContentOnly}
          onCopyJson={handleCopyJson}
          onDeleteChapter={handleDeleteChapter}
        />

        {selectedChap ? (
          <ChapterEditorPanel
            selectedChap={selectedChap}
            isEditing={isEditing}
            editingTitle={editingTitle}
            editingSummary={editingSummary}
            editingContent={editingContent}
            editingChars={editingChars}
            showCopyConfig={showCopyConfig}
            copyConfig={copyConfig}
            copiedChapId={copiedChapId}
            copiedType={copiedType}
            setEditingTitle={setEditingTitle}
            setEditingSummary={setEditingSummary}
            setEditingContent={setEditingContent}
            setEditingChars={setEditingChars}
            setShowCopyConfig={setShowCopyConfig}
            setCopyConfig={setCopyConfig}
            setIsEditing={setIsEditing}
            onSaveEdit={handleSaveEdit}
            onSelectChapter={handleSelectChapter}
            onCopyContentOnly={handleCopyContentOnly}
            onCopyJson={handleCopyJson}
            onCopyFormattedText={handleCopyFormattedText}
            onClose={() => setSelectedChapId('')}
            onDeleteChapter={handleDeleteChapter}
          />
        ) : (
          <div className="flex-1 flex flex-col items-center justify-center border border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center space-y-4">
            <div className="w-12 h-12 rounded-xl bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20 shadow-lg shadow-cyan-500/10">
              <BookOpen size={24} />
            </div>
            <div className="max-w-md space-y-1.5">
              <h3 className="text-base font-bold text-white font-['Outfit']">
                Chưa Có Nội Dung Chương
              </h3>
              <p className="text-xs text-slate-400 leading-relaxed">
                Thế giới quan và Master Plan (Arcs) đã sẵn sàng! Nội dung kịch bản chi tiết từng chương sẽ tự động xuất hiện tại đây khi AI bắt đầu tiến trình viết chương (Chapter Writer).
              </p>
            </div>
            <div className="flex items-center gap-2 pt-2">
              <button
                onClick={() => setIsImportModalOpen(true)}
                className="px-3.5 py-2 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-bold text-xs flex items-center gap-2 shadow-md transition-all cursor-pointer"
              >
                <Download size={14} /> Import Truyện Có Sẵn
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
                className="px-3.5 py-2 rounded-xl bg-cyan-500 hover:bg-cyan-400 text-black font-extrabold text-xs flex items-center gap-2 shadow-md transition-all cursor-pointer"
              >
                <Plus size={14} /> Tự Tạo Chương Mới
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
