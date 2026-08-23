import React, { useState, useEffect, useRef } from 'react';
import { Activity, Terminal, Video, Settings, FileText, Mic, ShieldCheck, Share2, Layers, Cpu } from 'lucide-react';
import { PythonEngineService } from './services/pythonEngine';
import { PipelineStatus, StageName, StageProgressInfo, PipelineProgressEvent, StageStatus } from './types/pipeline';
import { usePipeline } from './hooks/usePipeline';

import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { NewProjectModal } from './components/NewProjectModal';
import { PipelineWorkflow } from './components/PipelineWorkflow';
import { ConsoleLogs } from './components/ConsoleLogs';
import { OutputPreview } from './components/OutputPreview';
import { SystemSettings } from './components/SystemSettings';
import { SubtitleEditor } from './components/SubtitleEditor';
import { VoiceStudio } from './components/VoiceStudio';
import { QualityControl } from './components/QualityControl';
import { ExportPresets } from './components/ExportPresets';
import { EditorLayout } from './components/editor/EditorLayout';
import { CompositionBuilder } from './editor/state/compositionBuilder';
import { editorStore } from './editor/state/editorStore';
import { TitleBar } from './components/TitleBar';

const STAGE_ORDER: StageName[] = [
  'EXTRACT',
  'TRANSCRIBE',
  'TRANSLATE',
  'TTS',
  'SYNC',
  'RENDER'
];

export default function App() {
  // Screen & Navigation
  const [currentScreen, setCurrentScreen] = useState<'home' | 'project'>('home');
  const [activeTab, setActiveTab] = useState<'pipeline' | 'subtitles' | 'timeline' | 'voices' | 'qc' | 'logs' | 'preview' | 'export' | 'settings'>('pipeline');
  const [isConsoleDrawerOpen, setIsConsoleDrawerOpen] = useState(false);
  
  // Projects state
  const [projectsList, setProjectsList] = useState<string[]>([]);
  const [selectedProjectDir, setSelectedProjectDir] = useState<string | null>(null);
  const [isCreatingProject, setIsCreatingProject] = useState(false);

  // Custom Pipeline Hook Integration
  const {
    pipelineStatus,
    setPipelineStatus,
    overallProgress,
    setOverallProgress,
    stageProgresses,
    setStageProgresses,
    logs,
    setLogs,
    errorDetails,
    setErrorDetails,
    elapsedTime,
    setElapsedTime,
    startPipeline: handleStartPipeline,
    resumePipeline: handleResumePipeline,
    cancelPipeline: handleCancelPipeline,
    retryStage: handleRetryStage
  } = usePipeline(selectedProjectDir, (path: string) => loadProjectJson(path));

  const startPhase1Pipeline = (force = false) => {
    handleStartPipeline(force, 'translate');
  };

  const handleTimelineRender = async (preset: string) => {
    if (!selectedProjectDir) return;
    try {
      const json = await PythonEngineService.readProjectJson(selectedProjectDir);
      if (!json.settings) json.settings = {};
      if (!json.settings.render) json.settings.render = {};
      
      if (preset === '16:9') {
        json.settings.render.subtitle_mode = 'BURN_IN';
        json.settings.render.audio_mode = 'DUCK_ORIGINAL';
        json.settings.render.video_codec = 'H264';
      } else if (preset === '9:16') {
        json.settings.render.subtitle_mode = 'BURN_IN';
        json.settings.render.audio_mode = 'DUCK_ORIGINAL';
        json.settings.render.video_codec = 'H264'; // Custom crop options can be read on python backend
      } else if (preset === 'audio') {
        json.settings.render.subtitle_mode = 'NONE';
        json.settings.render.audio_mode = 'DUB_ONLY';
      } else if (preset === 'srt') {
        json.settings.render.subtitle_mode = 'COPY';
        json.settings.render.audio_mode = 'ORIGINAL_ONLY';
      }

      await PythonEngineService.writeProjectJson(selectedProjectDir, json);
      await handleResumePipeline('render');
    } catch (err: any) {
      alert(`Khởi động Render thất bại: ${err}`);
    }
  };

  const prevStatusRef = useRef(pipelineStatus);
  // Auto-navigation on pipeline progress/stage transitions
  useEffect(() => {
    if (prevStatusRef.current === 'RUNNING' && pipelineStatus === 'COMPLETED') {
      if (stageProgresses['RENDER']?.status === 'COMPLETED') {
        setActiveTab('preview');
      } else if (stageProgresses['SYNC']?.status === 'COMPLETED') {
        setActiveTab('timeline');
      } else if (stageProgresses['TRANSLATE']?.status === 'COMPLETED') {
        setActiveTab('subtitles');
      }
    }
    prevStatusRef.current = pipelineStatus;
  }, [pipelineStatus, stageProgresses]);
  
  // Timer Reference
  const timerRef = useRef<any>(null);

  // Dynamic Telemetry
  const [realRam, setRealRam] = useState<string>('10.1 GB / 16.0 GB (63%)');
  const [realVram, setRealVram] = useState<string>('0.28 GB / 4.00 GB (GeForce GTX 1650 Ti)');

  // Settings state
  const [settings, setSettings] = useState({
    whisperModel: 'small',
    translationModel: 'qwen2.5:3b',
    ttsVoice: 'vi_VN-vais1000-medium',
    encoder: 'NVENC'
  });

  useEffect(() => {
    loadProjects();
    const updateHardwareMetrics = async () => {
      try {
        const metrics = await PythonEngineService.getSystemMetrics();
        setRealRam(metrics.ram_usage);
        setRealVram(metrics.vram_usage);
      } catch (e) {
        console.error(e);
      }
    };
    updateHardwareMetrics();
    const interval = setInterval(updateHardwareMetrics, 3000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (pipelineStatus === 'RUNNING') {
      timerRef.current = setInterval(() => setElapsedTime(prev => prev + 1), 1000);
    } else {
      if (timerRef.current) clearInterval(timerRef.current);
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current); };
  }, [pipelineStatus]);

  const loadProjects = async () => {
    try {
      const list = await PythonEngineService.listProjects();
      setProjectsList(list);
    } catch (err) {
      console.error('Failed to list projects:', err);
    }
  };

  const handleSelectProject = async (projNameOrPath: string) => {
    let fullPath = projNameOrPath;
    if (!projNameOrPath.includes('/') && !projNameOrPath.includes('\\')) {
      fullPath = `d:/FullStack/AutoDubStudio/projects/${projNameOrPath}`;
    }

    setSelectedProjectDir(fullPath);
    setCurrentScreen('project');
    setLogs([]);
    setElapsedTime(0);
    setErrorDetails(null);
    setOverallProgress(0);
    setActiveTab('pipeline');
    
    loadProjectJson(fullPath);
  };

  const isPipelineRunningRef = useRef(false);
  useEffect(() => {
    isPipelineRunningRef.current = pipelineStatus === 'RUNNING';
  }, [pipelineStatus]);

  const loadProjectJson = async (path: string) => {
    try {
      const json = await PythonEngineService.readProjectJson(path);
      
      // Auto Sync to Timeline Editor Store
      try {
        const subs = await PythonEngineService.readSubtitles(path);
        const compData = await PythonEngineService.readComposition(path);
        const segments = (subs || []).map((s: any) => ({
          id: s.id,
          start: Number(s.start),
          end: Number(s.end),
          text: s.translated_text || s.text || '',
          speaker: s.speaker,
        }));

        const newComp = CompositionBuilder.buildFromArtifacts({
          projectId: path,
          projectName: json.name || 'AutoDub Project',
          videoDuration: json.metadata?.media?.duration || json.metadata?.audio?.duration || json.source?.duration || undefined,
          sourceVideoPath: json.source?.path || 'source/input.mp4',
          segments: segments,
          dubbedAudioPath: 'audio/dubbed_synchronized.wav',
          dubbedAudioDuration: segments.length > 0 ? Math.max(...segments.map((s: any) => s.end)) : 60,
          layers: compData?.layers || []
        });

        editorStore.setComposition(newComp, false);
      } catch (syncErr) {
        console.error('Failed to sync to timeline editorStore:', syncErr);
      }

      // Only reload pipeline progress states from disk if the pipeline is not currently running.
      // This prevents race conditions where stale disk data (lagging behind stdout events) overwrites active state.
      if (json.pipeline && !isPipelineRunningRef.current) {
        const progresses = { ...stageProgresses };
        let totalCompleted = 0;
        let isAllCompleted = true;

        STAGE_ORDER.forEach(st => {
          const key = st.toLowerCase();
          const info = json.pipeline[key];
          if (info) {
            const statusUpper = (info.status || 'PENDING').toUpperCase() as StageStatus;
            progresses[st] = {
              status: statusUpper,
              progress: info.progress || (statusUpper === 'COMPLETED' ? 100 : 0),
              current: info.current || 0,
              total: info.total || 0,
              error: info.error || null
            };
            if (statusUpper === 'COMPLETED' || statusUpper === 'SKIPPED') {
              totalCompleted++;
            } else {
              isAllCompleted = false;
            }
          }
        });

        setStageProgresses(progresses);
        if (isAllCompleted && totalCompleted === STAGE_ORDER.length) {
          setPipelineStatus('COMPLETED');
          setOverallProgress(100);
        } else {
          setOverallProgress(Math.round((totalCompleted / STAGE_ORDER.length) * 100));
        }
      }
    } catch (err) {
      console.error('Read project json error:', err);
    }
  };

  const handleCreateProject = async (name: string, videoPath: string) => {
    setIsCreatingProject(true);
    try {
      const path = await PythonEngineService.createProject(name, videoPath);
      await loadProjects();
      handleSelectProject(path);
    } catch (err: any) {
      alert(`Tạo dự án thất bại: ${err}`);
    } finally {
      setIsCreatingProject(false);
    }
  };

  const handleDeleteProject = async (name: string) => {
    const confirmDelete = window.confirm(`Bạn có chắc chắn muốn xóa dự án "${name}" không? Thao tác này sẽ xóa toàn bộ tệp tin liên quan và không thể khôi phục.`);
    if (!confirmDelete) return;

    try {
      await PythonEngineService.deleteProject(name);
      await loadProjects();
      if (selectedProjectDir && (selectedProjectDir.endsWith(name) || selectedProjectDir.endsWith(name + '/') || selectedProjectDir.endsWith(name + '\\'))) {
        setSelectedProjectDir(null);
        setCurrentScreen('home');
      }
    } catch (err: any) {
      alert(`Xóa dự án thất bại: ${err}`);
    }
  };

  const handleOpenOutputFolder = async () => {
    if (!selectedProjectDir) return;
    try {
      await PythonEngineService.openOutputFolder(selectedProjectDir);
    } catch (err) {
      alert(`Không thể mở thư mục: ${err}`);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', width: '100vw', height: '100vh', background: 'var(--bg-dark)', overflow: 'hidden' }}>
      <TitleBar selectedProjectDir={selectedProjectDir} stageProgresses={stageProgresses} />
      <div style={{ display: 'flex', flexGrow: 1, overflow: 'hidden', width: '100%', minHeight: 0 }}>
        {/* SIDEBAR activity bar */}
        <Sidebar
        projectsList={projectsList}
        selectedProjectDir={selectedProjectDir}
        activeTab={activeTab}
        setActiveTab={(tab) => {
          if (selectedProjectDir) {
            setActiveTab(tab);
            if (tab === 'subtitles' || tab === 'timeline' || tab === 'voices' || tab === 'qc') {
              setIsConsoleDrawerOpen(false);
            }
          }
        }}
        onSelectProject={handleSelectProject}
        onCreateNewProjectClick={() => setCurrentScreen('home')}
        onRefreshList={loadProjects}
        onDeleteProject={handleDeleteProject}
      />

      {/* MAIN CONTAINER */}
      <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden', position: 'relative', minHeight: 0 }}>
        {currentScreen === 'home' && (
          <NewProjectModal isCreating={isCreatingProject} onCreateProject={handleCreateProject} />
        )}

        {currentScreen === 'project' && selectedProjectDir && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', flexGrow: 1, overflow: 'hidden', minHeight: 0 }}>
            {/* TAB CONTENTS CONTAINER */}
            <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', position: 'relative', overflow: 'hidden', minHeight: 0 }}>
              <div style={{ display: activeTab === 'pipeline' ? 'flex' : 'none', flexGrow: 1, minHeight: 0, padding: '24px', boxSizing: 'border-box', flexDirection: 'column', overflow: 'hidden' }}>
                <PipelineWorkflow
                  overallProgress={overallProgress}
                  elapsedTime={elapsedTime}
                  stageProgresses={stageProgresses}
                  errorDetails={errorDetails}
                  onRetryStage={handleRetryStage}
                  onOpenTimeline={() => setActiveTab('timeline')}
                  formatTime={formatTime}
                  pipelineStatus={pipelineStatus}
                  onStartPipeline={startPhase1Pipeline}
                  onCancelPipeline={handleCancelPipeline}
                  onResumePipeline={handleResumePipeline}
                />
              </div>

              <div style={{ display: activeTab === 'subtitles' ? 'flex' : 'none', flexGrow: 1, minHeight: 0, padding: '24px', boxSizing: 'border-box', flexDirection: 'column', overflow: 'hidden' }}>
                <SubtitleEditor projectDir={selectedProjectDir} onProceedToVoices={() => setActiveTab('voices')} />
              </div>

              <div style={{ display: activeTab === 'timeline' ? 'flex' : 'none', flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>
                <div style={{ width: '100%', height: '100%', position: 'relative' }}>
                  <EditorLayout 
                    onBackToApp={() => setActiveTab('pipeline')} 
                    onRender={handleTimelineRender}
                    isRendering={pipelineStatus === 'RUNNING'}
                  />
                </div>
              </div>

              <div style={{ display: activeTab === 'voices' ? 'flex' : 'none', flexGrow: 1, minHeight: 0, padding: '24px', boxSizing: 'border-box', flexDirection: 'column', overflow: 'hidden' }}>
                <VoiceStudio 
                  projectDir={selectedProjectDir} 
                  pipelineStatus={pipelineStatus}
                  stageProgresses={stageProgresses}
                  onResumePipeline={handleResumePipeline}
                />
              </div>

              <div style={{ display: activeTab === 'qc' ? 'flex' : 'none', flexGrow: 1, minHeight: 0, padding: '24px', boxSizing: 'border-box', flexDirection: 'column', overflow: 'hidden' }}>
                <QualityControl projectDir={selectedProjectDir} />
              </div>

              <div style={{ display: activeTab === 'logs' ? 'flex' : 'none', flexGrow: 1, minHeight: 0, padding: '24px', boxSizing: 'border-box', flexDirection: 'column', overflow: 'hidden' }}>
                <ConsoleLogs logs={logs} onClearLogs={() => setLogs([])} />
              </div>

              {activeTab === 'preview' && (
                <div style={{ display: 'flex', flexGrow: 1, minHeight: 0, padding: '24px', boxSizing: 'border-box', flexDirection: 'column', overflow: 'hidden' }}>
                  <OutputPreview selectedProjectDir={selectedProjectDir} onOpenOutputFolder={handleOpenOutputFolder} />
                </div>
              )}

              <div style={{ display: activeTab === 'export' ? 'flex' : 'none', flexGrow: 1, minHeight: 0, padding: '24px', boxSizing: 'border-box', flexDirection: 'column', overflow: 'hidden' }}>
                <ExportPresets projectDir={selectedProjectDir} />
              </div>

              <div style={{ display: activeTab === 'settings' ? 'flex' : 'none', flexGrow: 1, minHeight: 0, padding: '24px', boxSizing: 'border-box', flexDirection: 'column', overflow: 'hidden' }}>
                <SystemSettings settings={settings} onSettingsChange={setSettings} />
              </div>
            </div>

            {/* BOTTOM COLLAPSIBLE CONSOLE DRAWER */}
            {isConsoleDrawerOpen && (
              <div 
                style={{ 
                  height: '200px', 
                  borderTop: '1px solid rgba(255, 255, 255, 0.08)', 
                  background: '#0B0D10', 
                  display: 'flex', 
                  flexDirection: 'column', 
                  overflow: 'hidden' 
                }}
              >
                <ConsoleLogs logs={logs} onClearLogs={() => setLogs([])} />
              </div>
            )}
          </div>
        )}
      </div>
      </div>

      {/* GLOBAL STATUS BAR */}
      <div 
        style={{ 
          height: '30px', 
          background: '#0B0D10', 
          borderTop: '1px solid rgba(255, 255, 255, 0.05)', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between', 
          padding: '0 16px', 
          fontSize: '11px', 
          color: '#64748b', 
          flexShrink: 0 
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: pipelineStatus === 'RUNNING' ? '#06b6d4' : '#10b981' }} />
            {pipelineStatus === 'RUNNING' ? 'AI Sync Active' : 'System Ready'}
          </span>
        </div>

        {/* Hardware Telemetry stats */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '20px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cpu size={12} /> RAM: <strong style={{ color: '#cbd5e1' }}>{realRam.split(' ')[0] || '10.1'} GB</strong>
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Video size={12} /> VRAM: <strong style={{ color: '#06b6d4' }}>{realVram.split(' ')[0] || '0.28'} GB</strong>
          </span>
        </div>
      </div>
    </div>
  );
}
