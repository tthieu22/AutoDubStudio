import React, { useState, useEffect, useRef } from 'react';
import { Activity, Terminal, Video, Settings, FileText, Mic, ShieldCheck, Share2, Layers, Cpu } from 'lucide-react';
import { PythonEngineService } from './services/pythonEngine';
import { PipelineStatus, StageName, StageProgressInfo, PipelineProgressEvent, StageStatus } from './types/pipeline';
import { usePipeline } from './hooks/usePipeline';

import { Sidebar } from './components/Sidebar';
import { Header } from './components/Header';
import { NewProjectModal } from './components/NewProjectModal';
import { Dashboard } from './components/Dashboard';
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

import { SidebarTab } from './components/Sidebar';
import { AppShell } from './components/AppShell';
import { TranscriptEditor } from './components/dubbing/TranscriptEditor';
import { TranslationEditor } from './components/dubbing/TranslationEditor';

import { StoryWorkspace } from './components/story/StoryWorkspace';
import { CharacterBible } from './components/story/CharacterBible';
import { WorldBible } from './components/story/WorldBible';
import { StoryMemory } from './components/story/StoryMemory';
import { SceneBoard } from './components/story/SceneBoard';

import { ImageGenerationStudio } from './components/production/ImageGenerationStudio';
import { ResourceMonitorModal } from './components/production/ResourceMonitorModal';
import { ReviewDashboard } from './components/review/ReviewDashboard';

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
  const [activeTab, setActiveTab] = useState<SidebarTab>('overview');
  const [activeBottomTab, setActiveBottomTab] = useState<'timeline' | 'logs' | 'jobs'>('timeline');
  const [pipelineMode, setPipelineMode] = useState<'STORY' | 'DUBBING'>('STORY');
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

  const startPhase1Pipeline = async (force = false) => {
    if (selectedProjectDir) {
      try {
        const json = await PythonEngineService.readProjectJson(selectedProjectDir);
        if (json && json.pipeline) {
          json.pipeline.tts = { status: 'pending', progress: 0, current: 0, total: 0, error: null };
          json.pipeline.sync = { status: 'pending', progress: 0, current: 0, total: 0, error: null };
          json.pipeline.render = { status: 'pending', progress: 0, current: 0, total: 0, error: null };
          await PythonEngineService.writeProjectJson(selectedProjectDir, json);
        }
      } catch (e) {
        console.error('Failed to reset downstream stages in project.json:', e);
      }
    }
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
      // Prioritize workflow step: If translate just finished and TTS is pending, jump directly to Subtitle Editor
      if (stageProgresses['TRANSLATE']?.status === 'COMPLETED' && stageProgresses['TTS']?.status !== 'COMPLETED') {
        setActiveTab('subtitles');
      } else if (stageProgresses['SYNC']?.status === 'COMPLETED' && stageProgresses['RENDER']?.status !== 'COMPLETED') {
        setActiveTab('timeline');
      } else if (stageProgresses['RENDER']?.status === 'COMPLETED') {
        setActiveTab('preview');
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
    translationModel: 'hachimi-60m',
    translationBatchSize: 20,
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
      if (list.length > 0 && !selectedProjectDir) {
        handleSelectProject(list[0]);
      }
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
    setActiveTab('overview');
    
    loadProjectJson(fullPath);
  };

  const isPipelineRunningRef = useRef(false);
  useEffect(() => {
    isPipelineRunningRef.current = pipelineStatus === 'RUNNING';
  }, [pipelineStatus]);

  const [activeProjectStyle, setActiveProjectStyle] = useState<string>('general');
  const [targetLanguage, setTargetLanguage] = useState<string>('vi');

  const loadProjectJson = async (path: string) => {
    try {
      const json = await PythonEngineService.readProjectJson(path);
      if (json) {
        if (json.mode === 'MODE_STORY' || json.mode === 'STORY') {
          setPipelineMode('STORY');
        } else {
          setPipelineMode('DUBBING');
        }
        if (json.settings) {
          if (json.settings.translation_style) {
            setActiveProjectStyle(json.settings.translation_style);
          } else {
            setActiveProjectStyle('general');
          }
          if (json.settings.translation_model) {
            setSettings(prev => ({ ...prev, translationModel: json.settings.translation_model }));
          }
        }
        if (json.target && json.target.language) {
          setTargetLanguage(json.target.language);
        }
      }
      
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
          layers: compData?.layers || [],
          compositionWidth: compData?.width || undefined,
          compositionHeight: compData?.height || undefined,
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

  const handleCreateProject = async (name: string, videoPath: string, style?: string, customStyle?: string, mode?: 'STORY' | 'DUBBING', storyText?: string) => {
    setIsCreatingProject(true);
    try {
      const path = await PythonEngineService.createProject(name, videoPath, style, customStyle);
      const selMode = mode || 'DUBBING';
      setPipelineMode(selMode);
      setActiveProjectStyle(style || 'general');

      try {
        const json = await PythonEngineService.readProjectJson(path);
        if (json) {
          json.mode = selMode === 'STORY' ? 'MODE_STORY' : 'MODE_DUBBING';
          await PythonEngineService.writeProjectJson(path, json);
        }
      } catch (e) {
        console.error('Failed to set mode in project.json:', e);
      }

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

  const handleChangeTranslationModel = async (newModel: string) => {
    setSettings(prev => ({ ...prev, translationModel: newModel }));
    if (selectedProjectDir) {
      try {
        const json = await PythonEngineService.readProjectJson(selectedProjectDir);
        if (!json.settings) json.settings = {};
        json.settings.translation_model = newModel;
        await PythonEngineService.writeProjectJson(selectedProjectDir, json);
      } catch (e) {
        console.error('Failed to save translation_model:', e);
      }
    }
  };

  const handleChangeTranslationStyle = async (newStyle: string) => {
    setActiveProjectStyle(newStyle);
    if (selectedProjectDir) {
      try {
        const json = await PythonEngineService.readProjectJson(selectedProjectDir);
        if (!json.settings) json.settings = {};
        json.settings.translation_style = newStyle;
        await PythonEngineService.writeProjectJson(selectedProjectDir, json);
      } catch (e) {
        console.error('Failed to save translation_style:', e);
      }
    }
  };

  const handleChangeTargetLanguage = async (newLang: string) => {
    setTargetLanguage(newLang);
    if (selectedProjectDir) {
      try {
        const json = await PythonEngineService.readProjectJson(selectedProjectDir);
        if (!json.target) json.target = {};
        json.target.language = newLang;
        await PythonEngineService.writeProjectJson(selectedProjectDir, json);
      } catch (e) {
        console.error('Failed to save target language:', e);
      }
    }
  };

  const handleTabChange = (tab: SidebarTab) => {
    setActiveTab(tab);
    if (selectedProjectDir) {
      setCurrentScreen('project');
    }
  };

  const renderMainContent = () => {
    if (!selectedProjectDir || currentScreen === 'home') {
      return (
        <NewProjectModal
          isCreating={isCreatingProject}
          onCreateProject={handleCreateProject}
        />
      );
    }

    switch (activeTab) {
      case 'overview':
        return (
          <Dashboard
            projectName={selectedProjectDir.split('/').pop()?.split('\\').pop() || 'MyStory'}
            mode={pipelineMode}
            status={pipelineStatus}
            overallProgress={overallProgress}
            stageProgresses={stageProgresses}
            telemetry={{
              gpu_util_percent: 87,
              vram_used_gb: parseFloat(realVram.split(' ')[0]) || 2.1,
              vram_total_gb: 4.0,
              vram_percent: Math.round(((parseFloat(realVram.split(' ')[0]) || 2.1) / 4.0) * 100),
              ram_used_gb: parseFloat(realRam.split(' ')[0]) || 11.0,
              ram_total_gb: parseFloat(realRam.split('/')[1]?.split('GB')[0]) || 16.0,
              ram_percent: Math.round(((parseFloat(realRam.split(' ')[0]) || 11.0) / 16.0) * 100),
              cpu_percent: 64,
              temp_c: 48,
              gpu_name: 'NVIDIA GeForce GTX 1650 Ti'
            }}
            logs={logs}
            onStart={() => startPhase1Pipeline(false)}
            onPause={() => setPipelineStatus('PAUSED')}
            onResume={() => handleResumePipeline()}
            onRetry={() => handleRetryStage('RENDER')}
            onCancel={handleCancelPipeline}
            onReview={() => setActiveTab('subtitles')}
            onApproveGate={async () => {
              setPipelineStatus('APPROVED');
              await handleResumePipeline();
            }}
            onRejectGate={() => {
              setPipelineStatus('IDLE');
            }}
          />
        );

      case 'source':
        return (
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
            translationStyle={activeProjectStyle}
            translationModel={settings.translationModel}
            targetLanguage={targetLanguage}
            onChangeTranslationModel={handleChangeTranslationModel}
            onChangeTranslationStyle={handleChangeTranslationStyle}
            onChangeTargetLanguage={handleChangeTargetLanguage}
          />
        );

      case 'transcript':
        return (
          <TranscriptEditor
            projectDir={selectedProjectDir}
            onProceedToTranslation={() => setActiveTab('translation')}
          />
        );

      case 'story':
      case 'chapters':
        return <StoryWorkspace />;

      case 'characters':
        return <CharacterBible />;

      case 'world':
        return <WorldBible />;

      case 'memory':
        return <StoryMemory />;

      case 'scenes':
        return <SceneBoard />;

      case 'images':
        return <ImageGenerationStudio />;

      case 'translation':
        return (
          <TranslationEditor
            projectDir={selectedProjectDir}
            onProceedToVoice={() => setActiveTab('voice')}
          />
        );

      case 'subtitles':
        return (
          <SubtitleEditor
            projectDir={selectedProjectDir}
            activeTab={activeTab}
            onProceedToVoices={() => setActiveTab('voice')}
          />
        );

      case 'voice':
        return (
          <VoiceStudio
            projectDir={selectedProjectDir}
            pipelineStatus={pipelineStatus}
            stageProgresses={stageProgresses}
            onResumePipeline={handleResumePipeline}
          />
        );

      case 'review':
        return (
          <ReviewDashboard
            onNavigateTab={handleTabChange}
            onApproveAll={() => setPipelineStatus('APPROVED')}
          />
        );

      case 'timeline':
        return (
          <div className="w-full h-full relative">
            <EditorLayout
              onBackToApp={() => setActiveTab('overview')}
              onRender={handleTimelineRender}
              isRendering={pipelineStatus === 'RUNNING'}
            />
          </div>
        );

      case 'preview':
        return (
          <OutputPreview
            selectedProjectDir={selectedProjectDir}
            onOpenOutputFolder={handleOpenOutputFolder}
          />
        );

      case 'export':
      case 'render':
        return <ExportPresets projectDir={selectedProjectDir} />;

      case 'logs':
        return <ConsoleLogs logs={logs} onClearLogs={() => setLogs([])} />;

      case 'settings':
        return <SystemSettings settings={settings} onSettingsChange={setSettings} />;

      default:
        return (
          <div className="p-8 text-center text-slate-400">
            <h3 className="text-lg font-bold text-slate-200 uppercase font-['Outfit'] mb-2">{activeTab} Workspace</h3>
            <p className="text-sm text-slate-500">Module view ready for feature configuration.</p>
          </div>
        );
    }
  };

  const renderBottomPanelContent = () => {
    if (activeBottomTab === 'logs') {
      return <ConsoleLogs logs={logs} onClearLogs={() => setLogs([])} />;
    }
    if (activeBottomTab === 'jobs') {
      return (
        <div className="p-4 bg-[#111318] h-full overflow-y-auto text-xs space-y-2 font-sans">
          <h4 className="font-bold text-slate-300 uppercase font-['Outfit'] tracking-wider">Background AI Processing Tasks</h4>
          <div className="p-3 rounded-lg bg-black/40 border border-white/5 flex justify-between items-center text-slate-300">
            <span>Task #102: Whisper STT Extraction</span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-300 font-mono text-[10px] font-bold">RUNNING</span>
          </div>
        </div>
      );
    }
    return null;
  };

  const [isResourceModalOpen, setIsResourceModalOpen] = useState(false);

  return (
    <>
      <AppShell
        projectName={selectedProjectDir ? selectedProjectDir.split('/').pop()?.split('\\').pop() : 'New Studio Project'}
        selectedProjectDir={selectedProjectDir}
        projectsList={projectsList}
        onSelectProject={handleSelectProject}
        onCreateNewProject={() => {
          setSelectedProjectDir(null);
          setCurrentScreen('home');
        }}
        onDeleteProject={handleDeleteProject}
        activeTab={activeTab}
        setActiveTab={handleTabChange}
        pipelineStatus={pipelineStatus}
        stageProgresses={stageProgresses}
        onStartPipeline={startPhase1Pipeline}
        onCancelPipeline={handleCancelPipeline}
        onOpenOutputFolder={handleOpenOutputFolder}
        ramMetrics={realRam}
        vramMetrics={realVram}
        mainContent={renderMainContent()}
        bottomPanelContent={selectedProjectDir && activeTab !== 'timeline' && (activeBottomTab === 'logs' || activeBottomTab === 'jobs') ? renderBottomPanelContent() : undefined}
        activeBottomTab={activeBottomTab}
        setActiveBottomTab={setActiveBottomTab}
        onOpenCommandPalette={() => console.log('Open Cmd Palette')}
        onOpenNotifications={() => console.log('Open Notifications')}
        onOpenSettings={() => setActiveTab('settings')}
        onOpenResourceMonitor={() => setIsResourceModalOpen(true)}
        saveStatus="Saved"
      />

      <ResourceMonitorModal
        isOpen={isResourceModalOpen}
        onClose={() => setIsResourceModalOpen(false)}
        telemetry={{
          gpu_util_percent: 87,
          vram_used_gb: parseFloat(realVram.split(' ')[0]) || 3.4,
          vram_total_gb: 4.0,
          vram_percent: Math.round(((parseFloat(realVram.split(' ')[0]) || 3.4) / 4.0) * 100),
          ram_used_gb: parseFloat(realRam.split(' ')[0]) || 10.1,
          ram_total_gb: parseFloat(realRam.split('/')[1]?.split('GB')[0]) || 16.0,
          ram_percent: Math.round(((parseFloat(realRam.split(' ')[0]) || 10.1) / 16.0) * 100),
          cpu_percent: 64,
          temp_c: 48,
          gpu_name: 'NVIDIA GeForce GTX 1650 Ti'
        }}
      />
    </>
  );
}

