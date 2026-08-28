import React from 'react';
import { 
  FolderKanban, 
  FileText, 
  Languages, 
  BookOpen, 
  Users, 
  Globe, 
  Brain, 
  Clapperboard, 
  Image as ImageIcon, 
  Mic, 
  Subtitles, 
  SlidersHorizontal, 
  CheckCircle2, 
  Terminal, 
  Settings, 
  ChevronLeft, 
  ChevronRight,
  Plus,
  Trash2,
  Flame,
  Sparkles,
  Layers,
  ShieldCheck
} from 'lucide-react';
import { PipelineMode } from '../types/pipeline';

export type SidebarTab =
  | 'overview'
  | 'novel_dashboard'
  | 'arc_planner'
  | 'canon_explorer'
  | 'trends'
  | 'source'
  | 'transcript'
  | 'translation'
  | 'story'
  | 'characters'
  | 'world'
  | 'memory'
  | 'chapters'
  | 'scenes'
  | 'images'
  | 'voice'
  | 'subtitles'
  | 'timeline'
  | 'preview'
  | 'review'
  | 'render'
  | 'export'
  | 'logs'
  | 'settings';

interface SidebarProps {
  activeTab: SidebarTab;
  setActiveTab: (tab: SidebarTab) => void;
  pipelineMode: PipelineMode;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  width: number;
  projectsList?: string[];
  selectedProjectDir?: string | null;
  onSelectProject?: (proj: string) => void;
  onCreateNewProject?: () => void;
  onDeleteProject?: (name: string) => void;
  isNovelWriting?: boolean;
  badges?: {
    scenesCount?: string;
    imagesCount?: string;
    reviewCount?: number;
    jobsCount?: number;
    errorsCount?: number;
  };
}

export const Sidebar: React.FC<SidebarProps> = ({
  activeTab,
  setActiveTab,
  pipelineMode,
  isCollapsed,
  onToggleCollapse,
  width,
  projectsList = [],
  selectedProjectDir,
  onSelectProject,
  onCreateNewProject,
  onDeleteProject,
  isNovelWriting = false,
  badges = {}
}) => {
  const currentProjName = selectedProjectDir
    ? selectedProjectDir.split('/').pop()?.split('\\').pop() || selectedProjectDir
    : '';

  const renderNavGroup = (title: string, items: Array<{ id: SidebarTab; label: string; icon: React.ReactNode; badge?: string | number; badgeColor?: string }>) => {
    const isNarrativeGroup = title === 'Story Narrative';
    const isGroupDisabled = isNovelWriting && !isNarrativeGroup;

    return (
      <div className="mb-4">
        {!isCollapsed && (
          <div className="px-3 mb-1 text-[10px] font-extrabold uppercase tracking-wider text-slate-500 font-['Outfit'] flex items-center justify-between">
            <span>{title}</span>
            {isGroupDisabled && (
              <span className="text-[9px] text-amber-400/80 font-bold lowercase tracking-normal">🔒 khóa khi AI viết</span>
            )}
          </div>
        )}
        <div className="space-y-0.5">
          {items.map(item => {
            const isActive = activeTab === item.id;
            const isDisabled = isGroupDisabled;

            return (
              <button
                key={item.id}
                disabled={isDisabled}
                onClick={() => !isDisabled && setActiveTab(item.id)}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-all group ${
                  isDisabled
                    ? 'opacity-30 cursor-not-allowed pointer-events-none text-slate-600 border-l-2 border-transparent'
                    : isActive
                    ? 'bg-indigo-600/15 text-indigo-300 border-l-2 border-indigo-500 font-semibold'
                    : 'text-slate-400 hover:text-slate-200 hover:bg-white/5 border-l-2 border-transparent'
                }`}
                title={isDisabled ? 'AI đang tự động viết truyện. Bạn chỉ có thể xem các tab trong Story Narrative.' : isCollapsed ? item.label : undefined}
              >
                <div className="flex items-center gap-2.5 min-w-0">
                  <span className={`${isDisabled ? 'text-slate-600' : isActive ? 'text-indigo-400' : 'text-slate-400 group-hover:text-slate-200'}`}>
                    {item.icon}
                  </span>
                  {!isCollapsed && <span className="truncate">{item.label}</span>}
                </div>

                {!isCollapsed && item.badge !== undefined && item.badge !== null && item.badge !== 0 && (
                  <span
                    className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                      item.badgeColor || 'bg-white/10 text-slate-300'
                    }`}
                  >
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    );
  };

  // Distinct non-duplicative navigation items per mode
  const dubbingPipelineItems: Array<{ id: SidebarTab; label: string; icon: React.ReactNode; badge?: string | number; badgeColor?: string }> = [
    { id: 'overview', label: 'Overview', icon: <FolderKanban size={15} /> },
    { id: 'transcript', label: 'Transcript STT', icon: <FileText size={15} /> },
    { id: 'translation', label: 'Translation', icon: <Languages size={15} /> },
    { id: 'voice', label: 'Voice Studio', icon: <Mic size={15} /> },
    { id: 'subtitles', label: 'Subtitles', icon: <Subtitles size={15} /> }
  ];

  const storyItems: Array<{ id: SidebarTab; label: string; icon: React.ReactNode; badge?: string | number; badgeColor?: string }> = [
    { id: 'overview', label: 'Overview', icon: <FolderKanban size={15} /> },
    { id: 'novel_dashboard', label: 'AI Novel Engine', icon: <Sparkles size={15} className="text-cyan-400" />, badge: 'Qwen 3B', badgeColor: 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' },
    { id: 'arc_planner', label: '20-30 Arcs Plan', icon: <Layers size={15} /> },
    { id: 'story', label: 'Story & Chapters', icon: <BookOpen size={15} /> },
    { id: 'canon_explorer', label: 'Canon DB & Threads', icon: <ShieldCheck size={15} className="text-emerald-400" /> },
    { id: 'trends', label: 'TikTok Slang Trends', icon: <Flame size={15} className="text-amber-400" /> },
    { id: 'characters', label: 'Character Bible', icon: <Users size={15} /> },
    { id: 'world', label: 'World & Lore', icon: <Globe size={15} /> },
    { id: 'memory', label: 'Story Memory', icon: <Brain size={15} /> },
    { id: 'scenes', label: 'Scene Board', icon: <Clapperboard size={15} />, badge: badges.scenesCount, badgeColor: 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30' }
  ];

  const storyProductionItems: Array<{ id: SidebarTab; label: string; icon: React.ReactNode; badge?: string | number; badgeColor?: string }> = [
    { id: 'images', label: 'AI Image Gen', icon: <ImageIcon size={15} />, badge: badges.imagesCount, badgeColor: 'bg-purple-500/20 text-purple-300 border border-purple-500/30' },
    { id: 'voice', label: 'Voice Studio', icon: <Mic size={15} /> },
    { id: 'timeline', label: 'Timeline Editor', icon: <SlidersHorizontal size={15} /> }
  ];

  const dubbingProductionItems: Array<{ id: SidebarTab; label: string; icon: React.ReactNode; badge?: string | number; badgeColor?: string }> = [
    { id: 'timeline', label: 'Timeline Editor', icon: <SlidersHorizontal size={15} /> }
  ];

  const outputAndSystemItems: Array<{ id: SidebarTab; label: string; icon: React.ReactNode; badge?: string | number; badgeColor?: string }> = [
    { 
      id: 'review', 
      label: 'Review & QC', 
      icon: <CheckCircle2 size={15} />, 
      badge: badges.reviewCount, 
      badgeColor: 'bg-amber-500/20 text-amber-300 border border-amber-500/30' 
    },
    { id: 'render', label: 'Render & Export', icon: <Clapperboard size={15} /> },
    { 
      id: 'logs', 
      label: 'Logs & Jobs', 
      icon: <Terminal size={15} />, 
      badge: badges.errorsCount && badges.errorsCount > 0 ? `${badges.errorsCount} ERR` : undefined, 
      badgeColor: 'bg-rose-500/20 text-rose-300 border border-rose-500/30' 
    },
    { id: 'settings', label: 'Settings', icon: <Settings size={15} /> }
  ];

  return (
    <aside
      className="bg-[#0e1015] border-r border-white/5 flex flex-col justify-between select-none relative flex-shrink-0 transition-all duration-200 z-20"
      style={{ width: isCollapsed ? 56 : width }}
    >
      {/* COLLAPSE TOGGLE BUTTON */}
      <button
        onClick={onToggleCollapse}
        className="absolute -right-3 top-3 w-6 h-6 rounded-full bg-[#181c24] border border-white/10 text-slate-400 hover:text-white flex items-center justify-center shadow-md z-30 transition-all hover:scale-105"
        title={isCollapsed ? 'Expand Sidebar' : 'Collapse Sidebar'}
      >
        {isCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
      </button>

      {/* PROJECT SWITCHER HEADER */}
      {!isCollapsed && (
        <div className="p-3 border-b border-white/5 bg-black/40 space-y-2">
          <div className="flex items-center justify-between text-[10px] font-extrabold uppercase tracking-wider text-slate-500 font-['Outfit']">
            <span>Active Project</span>
            <button
              onClick={onCreateNewProject}
              className="px-1.5 py-0.5 rounded bg-indigo-600/20 hover:bg-indigo-600/40 text-indigo-300 border border-indigo-500/30 text-[10px] font-bold flex items-center gap-1 transition-all"
              title="Create New Project"
            >
              <Plus size={10} /> New
            </button>
          </div>

          <div className="flex items-center gap-1.5 min-w-0 w-full">
            <div className="flex-1 min-w-0">
              <select
                value={currentProjName}
                onChange={e => {
                  if (e.target.value === '__NEW__') {
                    onCreateNewProject?.();
                  } else if (onSelectProject) {
                    onSelectProject(e.target.value);
                  }
                }}
                className="w-full bg-[#111318] border border-white/10 rounded-lg px-2 py-1.5 text-xs font-semibold text-slate-200 focus:outline-none focus:border-indigo-500 truncate cursor-pointer"
              >
                {projectsList.map(p => {
                  const isStory = p.toLowerCase().includes('story') || p.toLowerCase().includes('truyen');
                  const isAudio = p.toLowerCase().includes('audio') || p.toLowerCase().includes('podcast') || p.toLowerCase().includes('radio');
                  const prefix = isStory ? '📖' : isAudio ? '🎙️' : '🎬';
                  return (
                    <option key={p} value={p} className="bg-[#111318] text-slate-200">
                      {prefix} {p}
                    </option>
                  );
                })}
                <option value="__NEW__" className="bg-[#111318] text-cyan-400 font-bold">+ Tạo dự án mới...</option>
              </select>
            </div>

            {currentProjName && onDeleteProject && (
              <button
                onClick={() => onDeleteProject(currentProjName)}
                className="h-7 w-7 flex items-center justify-center rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 hover:text-rose-300 border border-rose-500/20 transition-all flex-shrink-0 cursor-pointer"
                title={`Xóa dự án ${currentProjName}`}
              >
                <Trash2 size={13} />
              </button>
            )}
          </div>
        </div>
      )}

      {/* NAVIGATION CONTENT CONTAINER */}
      <div className="flex-1 overflow-y-auto overflow-x-hidden p-2 custom-scrollbar">
        {pipelineMode === 'STORY' ? (
          <>
            {renderNavGroup('Story Narrative', storyItems)}
            {renderNavGroup('Production', storyProductionItems)}
          </>
        ) : (
          <>
            {renderNavGroup('Dubbing Pipeline', dubbingPipelineItems)}
            {renderNavGroup('Production', dubbingProductionItems)}
          </>
        )}
        
        {renderNavGroup('Output & System', outputAndSystemItems)}
      </div>

      {/* FOOTER BADGE STATUS */}
      {!isCollapsed && (
        <div className="p-3 border-t border-white/5 bg-black/20 flex items-center justify-between text-[11px] text-slate-400">
          <div className="flex items-center gap-1.5">
            <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Studio Engine Ready</span>
          </div>
          <span className="text-[10px] font-mono text-slate-600">v0.2.0</span>
        </div>
      )}
    </aside>
  );
};
