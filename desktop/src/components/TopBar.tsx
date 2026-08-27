import React from 'react';
import { 
  Film, 
  BookOpen, 
  RotateCcw, 
  RotateCw, 
  Play, 
  Clapperboard, 
  Bell, 
  Cpu, 
  Settings, 
  Command, 
  CheckCircle2, 
  Clock, 
  AlertCircle, 
  Save, 
  ChevronRight
} from 'lucide-react';
import { PipelineMode } from '../types/pipeline';

interface TopBarProps {
  projectName?: string | null;
  pipelineMode: PipelineMode;
  onModeChange: (mode: PipelineMode) => void;
  saveStatus?: 'Saved' | 'Saving...' | 'Unsaved changes' | 'Auto-saved' | 'Error saving';
  onUndo?: () => void;
  onRedo?: () => void;
  canUndo?: boolean;
  canRedo?: boolean;
  onOpenPreview?: () => void;
  onOpenRender?: () => void;
  onOpenNotifications?: () => void;
  onOpenResourceMonitor?: () => void;
  onOpenCommandPalette?: () => void;
  onOpenSettings?: () => void;
  ramMetrics?: string;
  vramMetrics?: string;
  unreadNotificationsCount?: number;
  onOpenStoryWorkspace?: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  projectName = 'Untitled Project',
  pipelineMode,
  onModeChange,
  saveStatus = 'Saved',
  onUndo,
  onRedo,
  canUndo = false,
  canRedo = false,
  onOpenPreview,
  onOpenRender,
  onOpenNotifications,
  onOpenResourceMonitor,
  onOpenCommandPalette,
  onOpenSettings,
  onOpenStoryWorkspace,
  ramMetrics = '10.1 GB / 16 GB',
  vramMetrics = '0.28 GB / 4 GB',
  unreadNotificationsCount = 0
}) => {
  const getSaveStatusBadge = () => {
    switch (saveStatus) {
      case 'Saving...':
        return (
          <span className="flex items-center gap-1 text-xs text-cyan-400 animate-pulse" title="Saving changes to disk">
            <Clock size={12} />
            <span>Saving...</span>
          </span>
        );
      case 'Unsaved changes':
        return (
          <span className="flex items-center gap-1 text-xs text-amber-400" title="You have unsaved changes">
            <AlertCircle size={12} />
            <span>Unsaved</span>
          </span>
        );
      case 'Auto-saved':
        return (
          <span className="flex items-center gap-1 text-xs text-emerald-400" title="Automatically saved">
            <CheckCircle2 size={12} />
            <span>Auto-saved</span>
          </span>
        );
      case 'Error saving':
        return (
          <span className="flex items-center gap-1 text-xs text-rose-400" title="Error saving project state">
            <AlertCircle size={12} />
            <span>Save error</span>
          </span>
        );
      case 'Saved':
      default:
        return (
          <span className="flex items-center gap-1 text-xs text-slate-400" title="All changes saved">
            <Save size={12} className="text-emerald-500" />
            <span>Saved</span>
          </span>
        );
    }
  };

  return (
    <header className="h-12 bg-[#111318] border-b border-white/5 px-3 flex items-center justify-between flex-shrink-0 select-none text-slate-200 z-40">
      {/* LEFT SECTION: BRAND + PROJECT NAME + MODE TOGGLE */}
      <div className="flex items-center gap-3">
        {/* LOGO */}
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-gradient-to-tr from-indigo-600 to-cyan-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Film size={16} className="text-white" />
          </div>
          <span className="font-bold tracking-tight text-white font-['Outfit'] text-sm hidden sm:inline">
            AutoDub<span className="text-cyan-400">Studio</span>
            <span className="ml-1 text-[10px] px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">v0.2</span>
          </span>
        </div>

        <div className="h-4 w-px bg-white/10 mx-1" />

        {/* PROJECT NAME & SAVE STATUS */}
        <div className="flex items-center gap-2 max-w-[200px] sm:max-w-xs truncate">
          <span className="text-xs font-semibold text-slate-200 truncate" title={projectName || 'Untitled Project'}>
            {projectName || 'Untitled Project'}
          </span>
          {getSaveStatusBadge()}
        </div>

        <div className="h-4 w-px bg-white/10 mx-1" />

        {/* FIXED PROJECT MODE BADGE */}
        <div className="flex items-center">
          {pipelineMode === 'DUBBING' ? (
            <span className="px-2.5 py-1 rounded-lg bg-indigo-600/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold flex items-center gap-1.5 shadow-sm" title="Project Type: Video Dubbing Mode">
              <Film size={13} className="text-indigo-400" />
              <span>MODE_DUBBING (Lồng Tiếng Video)</span>
            </span>
          ) : (
            <button 
              onClick={onOpenStoryWorkspace}
              className="px-2.5 py-1 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-300 border border-cyan-500/30 text-xs font-bold flex items-center gap-1.5 shadow-sm cursor-pointer transition-all" 
              title="Bấm để mở Story & Chapters Workspace"
            >
              <BookOpen size={13} className="text-cyan-400" />
              <span>MODE_STORY (Video Truyện AI)</span>
            </button>
          )}
        </div>
      </div>

      {/* CENTER SECTION: UNDO / REDO / PREVIEW / RENDER QUICK CONTROLS */}
      <div className="hidden md:flex items-center gap-2">
        <div className="flex items-center bg-black/20 rounded-md p-0.5 border border-white/5">
          <button
            onClick={onUndo}
            disabled={!canUndo}
            className={`p-1.5 rounded text-xs transition-colors ${
              canUndo ? 'text-slate-300 hover:bg-white/10 hover:text-white' : 'text-slate-600 cursor-not-allowed'
            }`}
            title="Undo (Ctrl+Z)"
          >
            <RotateCcw size={14} />
          </button>
          <button
            onClick={onRedo}
            disabled={!canRedo}
            className={`p-1.5 rounded text-xs transition-colors ${
              canRedo ? 'text-slate-300 hover:bg-white/10 hover:text-white' : 'text-slate-600 cursor-not-allowed'
            }`}
            title="Redo (Ctrl+Shift+Z)"
          >
            <RotateCw size={14} />
          </button>
        </div>

        <button
          onClick={onOpenPreview}
          className="px-3 py-1.5 rounded-md bg-white/5 hover:bg-white/10 text-xs font-medium text-slate-200 border border-white/10 flex items-center gap-1.5 transition-all"
          title="Open Video Preview Panel"
        >
          <Play size={13} className="text-cyan-400" />
          <span>Preview</span>
        </button>

        <button
          onClick={onOpenRender}
          className="px-3 py-1.5 rounded-md bg-indigo-600/20 hover:bg-indigo-600/30 text-xs font-semibold text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5 transition-all"
          title="Open Render Queue & Export"
        >
          <Clapperboard size={13} className="text-indigo-400" />
          <span>Render</span>
        </button>
      </div>

      {/* RIGHT SECTION: HARDWARE TELEMETRY + NOTIFICATIONS + CMD PALETTE + SETTINGS */}
      <div className="flex items-center gap-2">
        {/* RESOURCE MONITOR MINI BADGE */}
        <button
          onClick={onOpenResourceMonitor}
          className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-md bg-black/40 hover:bg-black/60 border border-white/5 text-[11px] text-slate-400 transition-all"
          title="Open Hardware Resource Monitor"
        >
          <Cpu size={13} className="text-cyan-400 animate-pulse" />
          <span className="truncate max-w-[130px]">VRAM: {vramMetrics.split('(')[0]}</span>
        </button>

        {/* COMMAND PALETTE */}
        <button
          onClick={onOpenCommandPalette}
          className="px-2 py-1 rounded-md bg-white/5 hover:bg-white/10 text-xs text-slate-400 border border-white/5 flex items-center gap-1 transition-all"
          title="Open Command Palette (Ctrl+K)"
        >
          <Command size={13} />
          <span className="hidden xl:inline text-[11px]">Ctrl+K</span>
        </button>

        {/* NOTIFICATIONS */}
        <button
          onClick={onOpenNotifications}
          className="p-1.5 rounded-md bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200 border border-white/5 relative transition-all"
          title="Notification Center"
        >
          <Bell size={14} />
          {unreadNotificationsCount > 0 && (
            <span className="absolute -top-1 -right-1 w-4 h-4 bg-rose-500 text-white rounded-full text-[9px] font-bold flex items-center justify-center shadow-sm">
              {unreadNotificationsCount}
            </span>
          )}
        </button>

        {/* SETTINGS */}
        <button
          onClick={onOpenSettings}
          className="p-1.5 rounded-md bg-white/5 hover:bg-white/10 text-slate-400 hover:text-slate-200 border border-white/5 transition-all"
          title="System Settings"
        >
          <Settings size={14} />
        </button>
      </div>
    </header>
  );
};
