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
    cancelPipeline: handleCancelPipeline,
    retryStage: handleRetryStage
  } = usePipeline(selectedProjectDir, (path: string) => loadProjectJson(path));
  
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
          projectId: json.name || path.split('/').pop() || 'project',
          projectName: json.name || 'AutoDub Project',
          videoDuration: json.source?.duration || 120,
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

      if (json.pipeline) {
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
    <div style={{ display: 'flex', width: '100vw', height: '100vh', background: 'var(--bg-dark)', overflow: 'hidden' }}>
      {/* SIDEBAR activity bar */}
      <Sidebar
        projectsList={projectsList}
        selectedProjectDir={selectedProjectDir}
        activeTab={activeTab}
        setActiveTab={(tab) => {
          if (selectedProjectDir) setActiveTab(tab);
        }}
        onSelectProject={handleSelectProject}
        onCreateNewProjectClick={() => setCurrentScreen('home')}
        onRefreshList={loadProjects}
      />

      {/* MAIN CONTAINER */}
      <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden', position: 'relative' }}>
        {currentScreen === 'home' && (
          <NewProjectModal isCreating={isCreatingProject} onCreateProject={handleCreateProject} />
        )}

        {currentScreen === 'project' && selectedProjectDir && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', flexGrow: 1, overflow: 'hidden' }}>
            {/* WORKSPACE HEADER */}
            <Header
              selectedProjectDir={selectedProjectDir}
              pipelineStatus={pipelineStatus}
              stageProgresses={stageProgresses}
              onStartPipeline={handleStartPipeline}
              onCancelPipeline={handleCancelPipeline}
              onOpenOutputFolder={handleOpenOutputFolder}
              activeTab={activeTab}
              setActiveTab={setActiveTab}
            />

            {/* TAB CONTENTS CONTAINER */}
            <div style={{ flexGrow: 1, position: 'relative', overflow: 'hidden' }}>
              <div style={{ display: activeTab === 'pipeline' ? 'block' : 'none', height: '100%', padding: '24px', overflowY: 'auto' }}>
                <PipelineWorkflow
                  overallProgress={overallProgress}
                  elapsedTime={elapsedTime}
                  stageProgresses={stageProgresses}
                  errorDetails={errorDetails}
                  onRetryStage={handleRetryStage}
                  onOpenTimeline={() => setActiveTab('timeline')}
                  formatTime={formatTime}
                />
              </div>

              <div style={{ display: activeTab === 'subtitles' ? 'block' : 'none', height: '100%', padding: '24px', overflowY: 'auto' }}>
                <SubtitleEditor projectDir={selectedProjectDir} />
              </div>

              <div style={{ display: activeTab === 'timeline' ? 'block' : 'none', height: '100%', overflow: 'hidden' }}>
                <div style={{ width: '100%', height: 'calc(100vh - 82px)', position: 'relative' }}>
                  <EditorLayout onBackToApp={() => setActiveTab('pipeline')} />
                </div>
              </div>

              <div style={{ display: activeTab === 'voices' ? 'block' : 'none', height: '100%', padding: '24px', overflowY: 'auto' }}>
                <VoiceStudio projectDir={selectedProjectDir} />
              </div>

              <div style={{ display: activeTab === 'qc' ? 'block' : 'none', height: '100%', padding: '24px', overflowY: 'auto' }}>
                <QualityControl projectDir={selectedProjectDir} />
              </div>

              <div style={{ display: activeTab === 'logs' ? 'block' : 'none', height: '100%', padding: '24px', overflowY: 'auto' }}>
                <ConsoleLogs logs={logs} onClearLogs={() => setLogs([])} />
              </div>

              <div style={{ display: activeTab === 'preview' ? 'block' : 'none', height: '100%', padding: '24px', overflowY: 'auto' }}>
                <OutputPreview selectedProjectDir={selectedProjectDir} onOpenOutputFolder={handleOpenOutputFolder} />
              </div>

              <div style={{ display: activeTab === 'export' ? 'block' : 'none', height: '100%', padding: '24px', overflowY: 'auto' }}>
                <ExportPresets projectDir={selectedProjectDir} />
              </div>

              <div style={{ display: activeTab === 'settings' ? 'block' : 'none', height: '100%', padding: '24px', overflowY: 'auto' }}>
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

            {/* STATUS BAR */}
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
                <button
                  onClick={() => setIsConsoleDrawerOpen(!isConsoleDrawerOpen)}
                  style={{
                    background: 'transparent',
                    border: 'none',
                    color: isConsoleDrawerOpen ? '#6366f1' : '#64748b',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    fontSize: '11px'
                  }}
                >
                  <Terminal size={12} /> {isConsoleDrawerOpen ? 'Hide Terminal' : 'Show Terminal'}
                </button>
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
        )}
      </div>
    </div>
  );
}
