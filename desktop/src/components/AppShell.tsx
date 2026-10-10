import React, { useState, useRef, useCallback } from 'react';
import { TopBar } from './TopBar';
import { Sidebar, SidebarTab } from './Sidebar';
import { InspectorPanel } from './InspectorPanel';
import { TitleBar } from './TitleBar';
import { useWorkspaceState } from '../hooks/useWorkspaceState';
import { PipelineMode, StageName, StageProgressInfo, PipelineStatus } from '../types/pipeline';
import { ChevronUp, ChevronDown, SlidersHorizontal, Terminal, Activity, Layers } from 'lucide-react';

interface AppShellProps {
  projectName?: string | null;
  selectedProjectDir?: string | null;
  projectsList?: string[];
  onSelectProject?: (proj: string) => void;
  onCreateNewProject?: () => void;
  onDeleteProject?: (name: string) => void;
  activeTab: SidebarTab;
  setActiveTab: (tab: SidebarTab) => void;
  pipelineMode?: PipelineMode;
  pipelineStatus: PipelineStatus;
  stageProgresses: Partial<Record<StageName, StageProgressInfo>>;
  onStartPipeline: (force?: boolean) => void;
  onCancelPipeline: () => void;
  onOpenOutputFolder: () => void;
  ramMetrics?: string;
  vramMetrics?: string;
  isNovelWriting?: boolean;
  mainContent: React.ReactNode;
  inspectorContent?: React.ReactNode;
  inspectorTitle?: string;
  bottomPanelContent?: React.ReactNode;
  activeBottomTab?: 'timeline' | 'logs' | 'jobs';
  setActiveBottomTab?: (tab: 'timeline' | 'logs' | 'jobs') => void;
  onOpenCommandPalette?: () => void;
  onOpenNotifications?: () => void;
  onOpenSettings?: () => void;
  onOpenResourceMonitor?: () => void;
  saveStatus?: 'Saved' | 'Saving...' | 'Unsaved changes' | 'Auto-saved' | 'Error saving';
}

export const AppShell: React.FC<AppShellProps> = ({
  projectName,
  selectedProjectDir,
  projectsList = [],
  onSelectProject,
  onCreateNewProject,
  onDeleteProject,
  activeTab,
  setActiveTab,
  pipelineMode,
  pipelineStatus,
  stageProgresses,
  onStartPipeline,
  onCancelPipeline,
  onOpenOutputFolder,
  ramMetrics = '10.1 GB / 16.0 GB',
  vramMetrics = '0.28 GB / 4.00 GB',
  isNovelWriting = false,
  mainContent,
  inspectorContent,
  inspectorTitle,
  bottomPanelContent,
  activeBottomTab = 'timeline',
  setActiveBottomTab,
  onOpenCommandPalette,
  onOpenNotifications,
  onOpenSettings,
  onOpenResourceMonitor,
  saveStatus = 'Saved'
}) => {
  const workspace = useWorkspaceState();
  const effectivePipelineMode = pipelineMode || workspace.pipelineMode;

  // Resizing state handling
  const [isResizingSidebar, setIsResizingSidebar] = useState(false);
  const [isResizingInspector, setIsResizingInspector] = useState(false);
  const [isResizingBottomPanel, setIsResizingBottomPanel] = useState(false);

  const startResizingSidebar = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingSidebar(true);
    const startX = e.clientX;
    const startWidth = workspace.sidebarWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const delta = moveEvent.clientX - startX;
      workspace.setSidebarWidth(startWidth + delta);
    };

    const onMouseUp = () => {
      setIsResizingSidebar(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const startResizingInspector = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingInspector(true);
    const startX = e.clientX;
    const startWidth = workspace.inspectorWidth;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const delta = startX - moveEvent.clientX;
      workspace.setInspectorWidth(startWidth + delta);
    };

    const onMouseUp = () => {
      setIsResizingInspector(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const startResizingBottomPanel = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsResizingBottomPanel(true);
    const startY = e.clientY;
    const startHeight = workspace.bottomPanelHeight;

    const onMouseMove = (moveEvent: MouseEvent) => {
      const delta = startY - moveEvent.clientY;
      workspace.setBottomPanelHeight(startHeight + delta);
    };

    const onMouseUp = () => {
      setIsResizingBottomPanel(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  return (
    <div className="h-screen w-screen flex flex-col bg-[#0b0d10] text-slate-100 overflow-hidden font-sans select-none">
      {/* WINDOW TITLE BAR */}
      <TitleBar selectedProjectDir={selectedProjectDir} stageProgresses={stageProgresses} />

      {/* APPLICATION TOP BAR */}
      <TopBar
        projectName={projectName}
        pipelineMode={effectivePipelineMode}
        onModeChange={workspace.setPipelineMode}
        saveStatus={saveStatus}
        ramMetrics={ramMetrics}
        vramMetrics={vramMetrics}
        onOpenCommandPalette={onOpenCommandPalette}
        onOpenNotifications={onOpenNotifications}
        onOpenSettings={onOpenSettings}
        onOpenResourceMonitor={onOpenResourceMonitor}
        onOpenPreview={() => setActiveTab('preview')}
        onOpenRender={() => setActiveTab('render')}
        onOpenStoryWorkspace={() => setActiveTab('story')}
      />

      {/* MAIN LAYOUT CONTENT BODY */}
      <div className="flex-1 flex overflow-hidden relative">
        {/* LEFT SIDEBAR NAVIGATION */}
        <Sidebar
          activeTab={activeTab}
          setActiveTab={setActiveTab}
          pipelineMode={effectivePipelineMode}
          isCollapsed={workspace.isSidebarCollapsed}
          onToggleCollapse={workspace.toggleSidebar}
          width={workspace.sidebarWidth}
          projectsList={projectsList}
          selectedProjectDir={selectedProjectDir}
          onSelectProject={onSelectProject}
          onCreateNewProject={onCreateNewProject}
          onDeleteProject={onDeleteProject}
          isNovelWriting={isNovelWriting}
        />

        {/* SIDEBAR RESIZE HANDLE */}
        {!workspace.isSidebarCollapsed && (
          <div
            onMouseDown={startResizingSidebar}
            className={`w-1 hover:w-1.5 bg-transparent hover:bg-indigo-500/50 cursor-col-resize z-30 transition-all ${
              isResizingSidebar ? 'bg-indigo-500 w-1.5' : ''
            }`}
          />
        )}

        {/* MAIN WORKSPACE AREA & BOTTOM PANEL SPLIT */}
        <div className="flex-1 flex flex-col min-w-0 overflow-hidden bg-[#0d0f14] relative">
          {/* MAIN WORKSPACE AREA */}
          <main className="flex-1 overflow-auto relative p-0 custom-scrollbar">
            {mainContent}
          </main>

          {/* BOTTOM PANEL RESIZE HANDLE */}
          {!workspace.isBottomPanelCollapsed && bottomPanelContent && (
            <div
              onMouseDown={startResizingBottomPanel}
              className={`h-1 hover:h-1.5 bg-transparent hover:bg-indigo-500/50 cursor-row-resize z-30 transition-all ${
                isResizingBottomPanel ? 'bg-indigo-500 h-1.5' : ''
              }`}
            />
          )}

          {/* BOTTOM PANEL CONTAINER (TIMELINE / LOGS / JOBS) */}
          {bottomPanelContent && (
            <div
              className="bg-[#0e1015] border-t border-white/5 flex flex-col flex-shrink-0 relative transition-all duration-150 z-20"
              style={{ height: workspace.isBottomPanelCollapsed ? 32 : workspace.bottomPanelHeight }}
            >
              {/* BOTTOM PANEL HEADER BAR */}
              <div className="h-8 px-3 bg-[#111318] border-b border-white/5 flex items-center justify-between flex-shrink-0 select-none">
                <div className="flex items-center gap-1">
                  <button
                    onClick={() => setActiveBottomTab?.('timeline')}
                    className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-all ${
                      activeBottomTab === 'timeline'
                        ? 'bg-white/10 text-indigo-400'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <SlidersHorizontal size={13} />
                    <span>TIMELINE EDITOR</span>
                  </button>

                  <button
                    onClick={() => setActiveBottomTab?.('logs')}
                    className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-all ${
                      activeBottomTab === 'logs'
                        ? 'bg-white/10 text-cyan-400'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Terminal size={13} />
                    <span>CONSOLE LOGS</span>
                  </button>

                  <button
                    onClick={() => setActiveBottomTab?.('jobs')}
                    className={`px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1.5 transition-all ${
                      activeBottomTab === 'jobs'
                        ? 'bg-white/10 text-emerald-400'
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Activity size={13} />
                    <span>BACKGROUND JOBS</span>
                  </button>
                </div>

                <button
                  onClick={workspace.toggleBottomPanel}
                  className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-all"
                  title={workspace.isBottomPanelCollapsed ? 'Expand Panel' : 'Collapse Panel'}
                >
                  {workspace.isBottomPanelCollapsed ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                </button>
              </div>

              {/* BOTTOM PANEL CONTENT */}
              {!workspace.isBottomPanelCollapsed && (
                <div className="flex-1 overflow-hidden relative">
                  {bottomPanelContent}
                </div>
              )}
            </div>
          )}
        </div>

        {/* INSPECTOR PANEL RESIZE HANDLE */}
        {!workspace.isInspectorCollapsed && (
          <div
            onMouseDown={startResizingInspector}
            className={`w-1 hover:w-1.5 bg-transparent hover:bg-indigo-500/50 cursor-col-resize z-30 transition-all ${
              isResizingInspector ? 'bg-indigo-500 w-1.5' : ''
            }`}
          />
        )}

        {/* RIGHT INSPECTOR PANEL */}
        <InspectorPanel
          title={inspectorTitle || 'Inspector'}
          isCollapsed={workspace.isInspectorCollapsed}
          onToggleCollapse={workspace.toggleInspector}
          width={workspace.inspectorWidth}
          activeTab={workspace.activeInspectorTab}
          onTabChange={workspace.setActiveInspectorTab}
        >
          {inspectorContent}
        </InspectorPanel>
      </div>

      {/* FOOTER STATUS BAR */}
      <footer className="h-6 bg-[#090b0e] border-t border-white/5 px-3 flex items-center justify-between text-[11px] text-slate-400 flex-shrink-0 select-none z-40">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full ${
                pipelineStatus === 'RUNNING'
                  ? 'bg-cyan-400 animate-ping'
                  : pipelineStatus === 'COMPLETED'
                  ? 'bg-emerald-400'
                  : pipelineStatus === 'FAILED'
                  ? 'bg-rose-400'
                  : 'bg-slate-500'
              }`}
            />
            <span className="font-semibold text-slate-300">Status: {pipelineStatus}</span>
          </div>
          <span>Mode: <strong className="text-cyan-400">{workspace.pipelineMode}</strong></span>
        </div>

        <div className="flex items-center gap-4">
          <span>RAM: <strong className="text-slate-300">{ramMetrics.split('(')[0]}</strong></span>
          <span>VRAM: <strong className="text-slate-300">{vramMetrics.split('(')[0]}</strong></span>
        </div>
      </footer>
    </div>
  );
};
