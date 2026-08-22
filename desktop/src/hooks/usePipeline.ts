import { useState, useEffect } from 'react';
import { PythonEngineService } from '../services/pythonEngine';
import { PipelineStatus, StageName, StageProgressInfo, PipelineProgressEvent, StageStatus } from '../types/pipeline';
import { CompositionBuilder } from '../editor/state/compositionBuilder';
import { editorStore } from '../editor/state/editorStore';

const STAGE_ORDER: StageName[] = [
  'EXTRACT',
  'TRANSCRIBE',
  'TRANSLATE',
  'TTS',
  'SYNC',
  'RENDER'
];

export function usePipeline(selectedProjectDir: string | null, loadProjectJson: (path: string) => Promise<void>) {
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
  const [logs, setLogs] = useState<string[]>([]);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);

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
    } else if ((event.event === 'stage_complete' || event.event === 'stage_skipped') && event.stage) {
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

      if (selectedProjectDir) {
        loadProjectJson(selectedProjectDir);
      }
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

  const startPipeline = async (force = false) => {
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

  const cancelPipeline = async () => {
    if (!selectedProjectDir) return;
    try {
      await PythonEngineService.cancelPipeline();
      setPipelineStatus('CANCELLED');
      setLogs(prev => [...prev, `[WARNING] Đã gửi tín hiệu hủy tiến trình.`]);
    } catch (err) {
      console.error(err);
    }
  };

  const retryStage = async (stage: StageName) => {
    if (!selectedProjectDir) return;
    setPipelineStatus('RUNNING');
    setErrorDetails(null);
    setLogs(prev => [...prev, `[INFO] Đang chạy lại bước ${stage}...`]);

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

  return {
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
    startPipeline,
    cancelPipeline,
    retryStage
  };
}
