import React, { useState, useEffect, useRef } from 'react';
import { Activity, Terminal, Video, Settings } from 'lucide-react';
import { PythonEngineService } from './services/pythonEngine';
import { PipelineStatus, StageName, StageProgressInfo, PipelineProgressEvent, StageStatus } from './types/pipeline';

import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { NewProjectModal } from './components/NewProjectModal';
import { PipelineWorkflow } from './components/PipelineWorkflow';
import { ConsoleLogs } from './components/ConsoleLogs';
import { OutputPreview } from './components/OutputPreview';
import { SystemSettings } from './components/SystemSettings';

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
  const [activeTab, setActiveTab] = useState<'pipeline' | 'logs' | 'preview' | 'settings'>('pipeline');
  
  // Projects state
  const [projectsList, setProjectsList] = useState<string[]>([]);
  const [selectedProjectDir, setSelectedProjectDir] = useState<string | null>(null);
  const [isCreatingProject, setIsCreatingProject] = useState(false);
  
  // Pipeline status & progresses
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus>('IDLE');
  const [overallProgress, setOverallProgress] = useState(0);
  const [stageProgresses, setStageProgresses] = useState<Record<StageName, StageProgressInfo>>({
    EXTRACT: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null },
    TRANSCRIBE: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null },
    TRANSLATE: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null },
    TTS: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null },
    SYNC: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null },
    RENDER: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null }
  });
  
  // Logs & Metrics
  const [logs, setLogs] = useState<string[]>([]);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
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

  // Event Listener Subscriptions for Live Pipeline Progress
  useEffect(() => {
    let unsubProgress: any = null;
    let unsubLog: any = null;
    let unsubTerminated: any = null;

    const setupListeners = async () => {
      unsubProgress = await PythonEngineService.subscribeProgress((evt: PipelineProgressEvent) => {
        handleProgressEvent(evt);
      });

      unsubLog = await PythonEngineService.subscribeLog((line: string) => {
        setLogs(prev => [...prev, line]);
      });

      unsubTerminated = await PythonEngineService.subscribeTerminated((code: number) => {
        if (code === 0) {
          setPipelineStatus('COMPLETED');
          setOverallProgress(100);
          if (selectedProjectDir) {
            loadProjectJson(selectedProjectDir);
          }
        } else {
          setPipelineStatus('FAILED');
        }
      });
    };

    setupListeners();

    return () => {
      if (typeof unsubProgress === 'function') unsubProgress();
      if (typeof unsubLog === 'function') unsubLog();
      if (typeof unsubTerminated === 'function') unsubTerminated();
    };
  }, [selectedProjectDir]);

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

  const handleStartPipeline = async (force: boolean = false) => {
    if (!selectedProjectDir) return;
    setPipelineStatus('RUNNING');
    setErrorDetails(null);
    setLogs(prev => [...prev, `[INFO] ${new Date().toLocaleTimeString()} Bắt đầu tiến trình AutoDub...`]);

    if (force) {
      setStageProgresses({
        EXTRACT: { status: 'RUNNING', progress: 0, current: 0, total: 0, error: null },
        TRANSCRIBE: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null },
        TRANSLATE: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null },
        TTS: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null },
        SYNC: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null },
        RENDER: { status: 'PENDING', progress: 0, current: 0, total: 0, error: null }
      });
      setOverallProgress(0);
    }

    try {
      await PythonEngineService.startPipeline(selectedProjectDir, force);
    } catch (err: any) {
      setPipelineStatus('FAILED');
      setErrorDetails(`Lỗi chạy tiến trình: ${err}`);
    }
  };

  const handleRetryStage = async (stage: StageName) => {
    if (!selectedProjectDir) return;
    setPipelineStatus('RUNNING');
    setErrorDetails(null);
    setLogs(prev => [...prev, `[INFO] Đang chạy lại bước ${stage}...`]);

    // Reset targeted stage to RUNNING and subsequent stages to PENDING
    const stageIdx = STAGE_ORDER.indexOf(stage);
    setStageProgresses(prev => {
      const updated = { ...prev };
      STAGE_ORDER.forEach((st, idx) => {
        if (idx === stageIdx) {
          updated[st] = { status: 'RUNNING', progress: 0, current: 0, total: 0, error: null };
        } else if (idx > stageIdx) {
          updated[st] = { status: 'PENDING', progress: 0, current: 0, total: 0, error: null };
        }
      });
      return updated;
    });

    setOverallProgress(Math.round((stageIdx / STAGE_ORDER.length) * 100));

    try {
      await PythonEngineService.retryPipeline(selectedProjectDir, stage, true);
    } catch (err: any) {
      setPipelineStatus('FAILED');
      setErrorDetails(`Lỗi chạy lại bước ${stage}: ${err}`);
      setStageProgresses(prev => ({
        ...prev,
        [stage]: { ...prev[stage], status: 'FAILED', error: String(err) }
      }));
    }
  };

  const handleCancelPipeline = async () => {
    if (!selectedProjectDir) return;
    try {
      await PythonEngineService.cancelPipeline();
      setPipelineStatus('CANCELLED');
      setLogs(prev => [...prev, `[WARNING] Đã gửi tín hiệu hủy tiến trình.`]);
    } catch (err) {
      console.error(err);
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

  const handleProgressEvent = (event: PipelineProgressEvent) => {
    if (event.event === 'stage_start' && event.stage) {
      const st = event.stage.toUpperCase() as StageName;
      setPipelineStatus('RUNNING');
      setStageProgresses(prev => ({
        ...prev,
        [st]: { ...prev[st], status: 'RUNNING', progress: 0 }
      }));
    } else if (event.event === 'progress' && event.stage) {
      const st = event.stage.toUpperCase() as StageName;
      const pct = Math.round(event.percent || 0);
      setStageProgresses(prev => ({
        ...prev,
        [st]: { ...prev[st], status: 'RUNNING', progress: pct, current: event.current || 0, total: event.total || 0 }
      }));
      if (event.message) {
        setLogs(prev => [...prev, `[${st}] ${event.message}`]);
      }
    } else if (event.event === 'stage_complete' && event.stage) {
      const st = event.stage.toUpperCase() as StageName;
      setStageProgresses(prev => {
        const updated = {
          ...prev,
          [st]: { ...prev[st], status: 'COMPLETED' as StageStatus, progress: 100 }
        };
        const completedCount = STAGE_ORDER.filter(s => updated[s].status === 'COMPLETED' || updated[s].status === 'SKIPPED').length;
        const newOverall = Math.round((completedCount / STAGE_ORDER.length) * 100);
        setOverallProgress(newOverall);
        if (completedCount === STAGE_ORDER.length || st === 'RENDER') {
          setPipelineStatus('COMPLETED');
        }
        return updated;
      });
    } else if (event.event === 'pipeline_complete') {
      setPipelineStatus('COMPLETED');
      setOverallProgress(100);
      setStageProgresses(prev => {
        const updated = { ...prev };
        STAGE_ORDER.forEach(st => {
          updated[st] = { ...updated[st], status: 'COMPLETED', progress: 100 };
        });
        return updated;
      });
      if (selectedProjectDir) {
        loadProjectJson(selectedProjectDir);
      }
    } else if (event.event === 'pipeline_error') {
      setPipelineStatus('FAILED');
      if (event.error) {
        setErrorDetails(event.error);
      }
    } else if (event.event === 'stage_error' && event.stage) {
      const st = event.stage.toUpperCase() as StageName;
      const err = event.error || 'Lỗi chưa xác định';
      setPipelineStatus('FAILED');
      setStageProgresses(prev => ({
        ...prev,
        [st]: { ...prev[st], status: 'FAILED' as StageStatus, error: err }
      }));
      setErrorDetails(`[${st}] ${err}`);
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{ display: 'flex', width: '100vw', height: '100vh', background: 'var(--bg-dark)' }}>
      {/* SIDEBAR */}
      <Sidebar
        projectsList={projectsList}
        selectedProjectDir={selectedProjectDir}
        realRam={realRam}
        realVram={realVram}
        onSelectProject={handleSelectProject}
        onCreateNewProjectClick={() => setCurrentScreen('home')}
        onRefreshList={loadProjects}
      />

      {/* MAIN WORKSPACE */}
      <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', height: '100vh', overflow: 'hidden' }}>
        {currentScreen === 'home' && (
          <NewProjectModal isCreating={isCreatingProject} onCreateProject={handleCreateProject} />
        )}

        {currentScreen === 'project' && selectedProjectDir && (
          <div style={{ display: 'flex', flexDirection: 'column', height: '100%', flexGrow: 1 }}>
            {/* WORKSPACE HEADER */}
            <Header
              selectedProjectDir={selectedProjectDir}
              pipelineStatus={pipelineStatus}
              onStartPipeline={handleStartPipeline}
              onCancelPipeline={handleCancelPipeline}
              onOpenOutputFolder={handleOpenOutputFolder}
            />

            {/* TAB NAVIGATION HEADER */}
            <div style={{ display: 'flex', background: 'rgba(2, 6, 23, 0.6)', borderBottom: '1px solid var(--border-glass)', padding: '0 24px' }}>
              <button
                onClick={() => setActiveTab('pipeline')}
                style={{
                  padding: '14px 20px', background: 'transparent',
                  color: activeTab === 'pipeline' ? 'var(--cyan)' : 'var(--text-muted)',
                  border: 'none', borderBottom: activeTab === 'pipeline' ? '2px solid var(--cyan)' : '2px solid transparent',
                  cursor: 'pointer', fontWeight: 700, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px'
                }}
              >
                <Activity size={16} /> Tiến Trình (Pipeline Workflow)
              </button>

              <button
                onClick={() => setActiveTab('logs')}
                style={{
                  padding: '14px 20px', background: 'transparent',
                  color: activeTab === 'logs' ? 'var(--cyan)' : 'var(--text-muted)',
                  border: 'none', borderBottom: activeTab === 'logs' ? '2px solid var(--cyan)' : '2px solid transparent',
                  cursor: 'pointer', fontWeight: 700, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px'
                }}
              >
                <Terminal size={16} /> Console Logs
              </button>

              <button
                onClick={() => setActiveTab('preview')}
                style={{
                  padding: '14px 20px', background: 'transparent',
                  color: activeTab === 'preview' ? 'var(--cyan)' : 'var(--text-muted)',
                  border: 'none', borderBottom: activeTab === 'preview' ? '2px solid var(--cyan)' : '2px solid transparent',
                  cursor: 'pointer', fontWeight: 700, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px'
                }}
              >
                <Video size={16} /> Xem Trước Video (Preview)
              </button>

              <button
                onClick={() => setActiveTab('settings')}
                style={{
                  padding: '14px 20px', background: 'transparent',
                  color: activeTab === 'settings' ? 'var(--cyan)' : 'var(--text-muted)',
                  border: 'none', borderBottom: activeTab === 'settings' ? '2px solid var(--cyan)' : '2px solid transparent',
                  cursor: 'pointer', fontWeight: 700, fontSize: '13px', display: 'flex', alignItems: 'center', gap: '8px'
                }}
              >
                <Settings size={16} /> Cấu Hình Hệ Thống
              </button>
            </div>

            {/* TAB CONTENTS */}
            <div style={{ flexGrow: 1, padding: '24px', overflowY: 'auto' }}>
              {activeTab === 'pipeline' && (
                <PipelineWorkflow
                  overallProgress={overallProgress}
                  elapsedTime={elapsedTime}
                  stageProgresses={stageProgresses}
                  errorDetails={errorDetails}
                  onRetryStage={handleRetryStage}
                  formatTime={formatTime}
                />
              )}

              {activeTab === 'logs' && (
                <ConsoleLogs logs={logs} onClearLogs={() => setLogs([])} />
              )}

              {activeTab === 'preview' && (
                <OutputPreview selectedProjectDir={selectedProjectDir} onOpenOutputFolder={handleOpenOutputFolder} />
              )}

              {activeTab === 'settings' && (
                <SystemSettings settings={settings} onSettingsChange={setSettings} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
