import React, { useState, useEffect } from 'react';
import { 
  Loader2, RefreshCw, AlertCircle, Layers, FileText, 
  Globe, Zap, Clock, Video, CheckCircle
} from 'lucide-react';
import { StageName, StageProgressInfo, PipelineStatus } from '../types/pipeline';

interface PipelineWorkflowProps {
  overallProgress: number;
  elapsedTime: number;
  stageProgresses: Record<StageName, StageProgressInfo>;
  errorDetails: string | null;
  onRetryStage: (stage: StageName) => void;
  onOpenTimeline?: () => void;
  formatTime: (seconds: number) => string;
  pipelineStatus: PipelineStatus;
  onStartPipeline: (force?: boolean) => void;
  onCancelPipeline: () => void;
  onResumePipeline: (stopAt?: string) => void;
  translationStyle?: string;
  translationModel?: string;
  onChangeTranslationModel?: (model: string) => void;
  onChangeTranslationStyle?: (style: string) => void;
}

const STYLE_NAME_MAP: Record<string, string> = {
  general: 'General / Tự động',
  modern: 'Hiện đại',
  ancient: 'Cổ trang',
  time_travel: 'Xuyên không',
  xianxia: 'Tiên hiệp / Kiếm hiệp',
  palace: 'Cung đấu',
  cartoon: 'Hoạt hình / Trẻ em',
  custom: 'Tùy chỉnh'
};

const STAGE_ORDER: StageName[] = [
  'EXTRACT',
  'TRANSCRIBE',
  'TRANSLATE',
  'TTS',
  'SYNC',
  'RENDER'
];

const STAGE_LABELS: Record<StageName, string> = {
  EXTRACT: 'Audio Extraction',
  TRANSCRIBE: 'Transcription (STT)',
  TRANSLATE: 'Translation',
  TTS: 'Voice Synthesis (TTS)',
  SYNC: 'Timeline Audio Sync',
  RENDER: 'Video Composite Render'
};

const STAGE_ICONS: Record<StageName, React.ReactNode> = {
  EXTRACT: <Layers size={20} style={{ color: '#06b6d4' }} />,
  TRANSCRIBE: <FileText size={20} style={{ color: '#6366f1' }} />,
  TRANSLATE: <Globe size={20} style={{ color: '#10b981' }} />,
  TTS: <Zap size={20} style={{ color: '#f59e0b' }} />,
  SYNC: <Clock size={20} style={{ color: '#a855f7' }} />,
  RENDER: <Video size={20} style={{ color: '#ef4444' }} />
};

export const PipelineWorkflow: React.FC<PipelineWorkflowProps> = ({
  overallProgress,
  elapsedTime,
  stageProgresses,
  errorDetails,
  onRetryStage,
  onOpenTimeline,
  formatTime,
  pipelineStatus,
  onStartPipeline,
  onCancelPipeline,
  onResumePipeline,
  translationStyle = 'general',
  translationModel = 'hachimi-60m',
  onChangeTranslationModel,
  onChangeTranslationStyle
}) => {
  const [activeInspectorStage, setActiveInspectorStage] = useState<StageName>('EXTRACT');
  const styleDisplayName = STYLE_NAME_MAP[translationStyle] || translationStyle;

  // Automatically select the running stage in the inspector
  useEffect(() => {
    const running = STAGE_ORDER.find(st => stageProgresses[st]?.status === 'RUNNING');
    if (running) {
      setActiveInspectorStage(running);
    }
  }, [stageProgresses]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED':
      case 'SKIPPED':
        return '#10b981';
      case 'RUNNING':
        return '#06b6d4';
      case 'FAILED':
        return '#ef4444';
      default:
        return '#475569';
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'COMPLETED':
      case 'SKIPPED':
        return <span style={{ color: '#10b981', fontSize: '11px', fontWeight: 700 }}>✓ COMPLETED</span>;
      case 'RUNNING':
        return (
          <span style={{ color: '#06b6d4', fontSize: '11px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Loader2 size={12} className="animate-spin" /> RUNNING
          </span>
        );
      case 'FAILED':
        return <span style={{ color: '#ef4444', fontSize: '11px', fontWeight: 700 }}>! FAILED</span>;
      default:
        return <span style={{ color: '#64748b', fontSize: '11px', fontWeight: 700 }}>PENDING</span>;
    }
  };

  const selectedProgressInfo = stageProgresses[activeInspectorStage] || {
    status: 'PENDING',
    progress: 0,
    current: 0,
    total: 0,
    error: null
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
      {/* 1. OVERALL PROGRESS HERO PANEL */}
      <div 
        style={{ 
          background: '#111318', 
          border: '1px solid rgba(255, 255, 255, 0.08)', 
          borderRadius: '12px', 
          padding: '16px 20px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap: '20px'
        }}
      >
        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', minWidth: '180px' }}>
          <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#fff' }}>Global Pipeline Execution</h3>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>Elapsed Time: {formatTime(elapsedTime)}</span>
        </div>

        {/* Translation Meta Badge */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', padding: '6px 14px', background: 'rgba(15, 23, 42, 0.7)', border: '1px solid rgba(255, 255, 255, 0.08)', borderRadius: '10px', fontSize: '12px' }}>
          <div>
            <span style={{ color: '#64748b', display: 'block', fontSize: '10px', textTransform: 'uppercase', fontWeight: 700 }}>Translation</span>
            <span style={{ color: '#f8fafc', fontWeight: 600 }}>🇨🇳 ZH → 🇻🇳 VI</span>
          </div>
          <div style={{ height: '24px', width: '1px', background: 'rgba(255, 255, 255, 0.1)' }} />
          <div>
            <span style={{ color: '#64748b', display: 'block', fontSize: '10px', textTransform: 'uppercase', fontWeight: 700, marginBottom: '2px' }}>Style</span>
            {onChangeTranslationStyle ? (
              <select
                value={translationStyle}
                onChange={e => onChangeTranslationStyle(e.target.value)}
                disabled={pipelineStatus === 'RUNNING'}
                style={{
                  background: 'rgba(14, 165, 233, 0.15)',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  borderRadius: '6px',
                  color: '#38bdf8',
                  fontSize: '11px',
                  fontWeight: 600,
                  padding: '2px 6px',
                  outline: 'none',
                  cursor: pipelineStatus === 'RUNNING' ? 'not-allowed' : 'pointer'
                }}
              >
                {Object.entries(STYLE_NAME_MAP).map(([val, label]) => (
                  <option key={val} value={val} style={{ background: '#0f172a', color: '#fff' }}>🎬 {label}</option>
                ))}
              </select>
            ) : (
              <span style={{ color: '#38bdf8', fontWeight: 600 }}>🎬 {styleDisplayName}</span>
            )}
          </div>
          <div style={{ height: '24px', width: '1px', background: 'rgba(255, 255, 255, 0.1)' }} />
          <div>
            <span style={{ color: '#64748b', display: 'block', fontSize: '10px', textTransform: 'uppercase', fontWeight: 700, marginBottom: '2px' }}>Model</span>
            {onChangeTranslationModel ? (
              <select
                value={translationModel === 'hachimi-60m' ? 'hachimi-60m' : 'qwen2.5:3b'}
                onChange={e => onChangeTranslationModel(e.target.value)}
                disabled={pipelineStatus === 'RUNNING'}
                style={{
                  background: translationModel === 'hachimi-60m' ? 'rgba(16, 185, 129, 0.15)' : 'rgba(168, 85, 247, 0.15)',
                  border: translationModel === 'hachimi-60m' ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(168, 85, 247, 0.4)',
                  borderRadius: '6px',
                  color: translationModel === 'hachimi-60m' ? '#34d399' : '#c084fc',
                  fontSize: '11px',
                  fontWeight: 700,
                  padding: '2px 6px',
                  outline: 'none',
                  cursor: pipelineStatus === 'RUNNING' ? 'not-allowed' : 'pointer'
                }}
              >
                <option value="hachimi-60m" style={{ background: '#0f172a', color: '#34d399' }}>🟢 HachimiMT-60 (GPU FP16, ~260MB)</option>
                <option value="qwen2.5:3b" style={{ background: '#0f172a', color: '#c084fc' }}>🔵 Qwen2.5:3B (Ollama LLM)</option>
              </select>
            ) : (
              <span style={{ color: '#a855f7', fontWeight: 600 }}>{translationModel}</span>
            )}
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexGrow: 1, maxWidth: '300px' }}>
          <div style={{ flexGrow: 1, background: '#0B0D10', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
            <div style={{ width: `${overallProgress}%`, background: 'linear-gradient(90deg, #6366f1, #06b6d4, #10b981)', height: '100%', transition: 'width 0.4s ease' }} />
          </div>
          <span style={{ fontSize: '16px', fontWeight: 800, color: '#fff', minWidth: '40px', textAlign: 'right' }}>{overallProgress}%</span>
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          {pipelineStatus === 'RUNNING' ? (
            <button 
              className="btn-secondary" 
              onClick={onCancelPipeline} 
              style={{ 
                borderColor: 'rgba(239, 68, 68, 0.4)', 
                color: '#ef4444', 
                padding: '6px 14px', 
                fontSize: '12px', 
                background: 'rgba(239, 68, 68, 0.08)',
                cursor: 'pointer'
              }}
            >
              Cancel Pipeline
            </button>
          ) : (
            <button 
              className="btn-primary" 
              onClick={() => {
                const isPartiallyDone = stageProgresses['EXTRACT']?.status === 'COMPLETED';
                onStartPipeline(!isPartiallyDone);
              }}
              style={{ padding: '6px 16px', fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
            >
              {stageProgresses['TRANSCRIBE']?.status === 'COMPLETED' && stageProgresses['TRANSLATE']?.status !== 'COMPLETED'
                ? 'TIẾP TỤC DỊCH (TRANSLATE) ➔'
                : 'START PIPELINE ➔'}
            </button>
          )}
        </div>
      </div>


      {/* 2. LAYOUT: HORIZONTAL PIPELINE ROW + INSPECTOR PANEL */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 320px', gap: '20px', flexGrow: 1, minHeight: 0 }}>
        {/* Horizontal flow column */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div 
            style={{ 
              background: '#111318', 
              border: '1px solid rgba(255, 255, 255, 0.05)', 
              borderRadius: '10px', 
              padding: '24px', 
              display: 'flex', 
              justifyContent: 'space-between', 
              alignItems: 'center',
              position: 'relative'
            }}
          >
            {STAGE_ORDER.map((st, idx) => {
              const info = stageProgresses[st] || { status: 'PENDING' };
              const isSelected = activeInspectorStage === st;
              const isRunning = info.status === 'RUNNING';
              
              return (
                <React.Fragment key={st}>
                  <div
                    onClick={() => setActiveInspectorStage(st)}
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      alignItems: 'center',
                      cursor: 'pointer',
                      zIndex: 2,
                      width: '90px',
                      padding: '12px 6px',
                      borderRadius: '8px',
                      background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                      border: '1px solid',
                      borderColor: isSelected ? '#6366f1' : 'transparent',
                      transition: 'all 0.15s ease'
                    }}
                  >
                    <div 
                      style={{ 
                        width: '38px', 
                        height: '38px', 
                        borderRadius: '50%', 
                        background: '#0B0D10', 
                        border: '2px solid', 
                        borderColor: getStatusColor(info.status), 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center',
                        marginBottom: '8px',
                        boxShadow: isRunning ? '0 0 10px rgba(6, 182, 212, 0.4)' : 'none'
                      }}
                    >
                      {STAGE_ICONS[st]}
                    </div>
                    <span style={{ fontSize: '11px', fontWeight: 700, color: isSelected ? '#fff' : '#94a3b8' }}>
                      {st}
                    </span>
                    <div style={{ marginTop: '4px' }}>
                      {getStatusBadge(info.status)}
                    </div>
                  </div>

                  {idx < STAGE_ORDER.length - 1 && (
                    <div 
                      style={{ 
                        flexGrow: 1, 
                        height: '2px', 
                        background: 'rgba(255,255,255,0.05)', 
                        margin: '0 -15px', 
                        alignSelf: 'center',
                        zIndex: 1
                      }} 
                    />
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Workflow instruction tip */}
          <div style={{ background: '#111318', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '10px', padding: '16px 20px', fontSize: '12px', color: '#94a3b8', lineHeight: 1.5 }}>
            <strong style={{ color: '#fff' }}>Pipeline Flow Guide:</strong> Select any processing node above to inspect its metrics, logs, and sub-stage progress. Click the primary button in the header at any time to execute/resume execution.
          </div>
        </div>

        {/* Dynamic Inspector Panel */}
        <div 
          style={{ 
            background: '#111318', 
            border: '1px solid rgba(255, 255, 255, 0.05)', 
            borderRadius: '10px', 
            padding: '20px', 
            display: 'flex', 
            flexDirection: 'column', 
            gap: '16px' 
          }}
        >
          <div style={{ borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '12px' }}>
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Stage Inspector
            </span>
            <h4 style={{ margin: '4px 0 0 0', fontSize: '15px', fontWeight: 700, color: '#fff' }}>
              {STAGE_LABELS[activeInspectorStage]}
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', flexGrow: 1 }}>
            <div>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>Status</span>
              <div style={{ marginTop: '4px' }}>
                {getStatusBadge(selectedProgressInfo.status)}
              </div>
            </div>

            <div>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>Progress</span>
              {(() => {
                const isFinalizing = selectedProgressInfo.progress >= 100 && selectedProgressInfo.status === 'RUNNING';
                const displayProgress = isFinalizing ? 99 : selectedProgressInfo.progress;
                return (
                  <>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginTop: '4px' }}>
                      <div style={{ flexGrow: 1, background: '#0B0D10', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
                        <div 
                          style={{ 
                            width: `${displayProgress}%`, 
                            background: getStatusColor(selectedProgressInfo.status), 
                            height: '100%', 
                            transition: 'width 0.3s ease' 
                          }} 
                        />
                      </div>
                      <span style={{ fontSize: '12px', fontWeight: 700, color: '#fff' }}>{displayProgress}%</span>
                    </div>
                    <span style={{ fontSize: '11px', color: '#64748b', display: 'block', marginTop: '4px' }}>
                      {selectedProgressInfo.total > 0 && activeInspectorStage !== 'RENDER' && activeInspectorStage !== 'SYNC' && activeInspectorStage !== 'EXTRACT'
                        ? `Completed: ${selectedProgressInfo.current} / ${selectedProgressInfo.total} items` 
                        : isFinalizing
                          ? `Status: Finalizing output files...`
                          : `Percentage: ${displayProgress}%`
                      }
                    </span>
                  </>
                );
              })()}
            </div>

            {selectedProgressInfo.error && (
              <div 
                style={{ 
                  background: 'rgba(239, 68, 68, 0.08)', 
                  border: '1px solid rgba(239, 68, 68, 0.2)', 
                  borderRadius: '6px', 
                  padding: '10px', 
                  color: '#ef4444', 
                  fontSize: '11px', 
                  lineHeight: 1.4 
                }}
              >
                <div style={{ fontWeight: 700, display: 'flex', alignItems: 'center', gap: '4px', marginBottom: '4px' }}>
                  <AlertCircle size={12} /> Execution Error
                </div>
                {selectedProgressInfo.error}
              </div>
            )}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', borderTop: '1px solid rgba(255, 255, 255, 0.05)', paddingTop: '12px' }}>
            {selectedProgressInfo.status === 'PENDING' ? (
              <button 
                className="btn-primary" 
                onClick={() => onResumePipeline(activeInspectorStage.toLowerCase())}
                style={{ width: '100%', justifyContent: 'center', padding: '8px', fontSize: '12px' }}
              >
                ▶️ Chạy Bước Này ({STAGE_LABELS[activeInspectorStage]})
              </button>
            ) : (
              <button 
                className="btn-secondary" 
                onClick={() => onRetryStage(activeInspectorStage)}
                style={{ width: '100%', justifyContent: 'center', padding: '8px', fontSize: '12px' }}
              >
                <RefreshCw size={13} /> Chạy Lại Stage Này
              </button>
            )}
          </div>
        </div>
      </div>

      {errorDetails && (
        <div style={{ padding: '12px 16px', borderRadius: '8px', border: '1px solid #ef4444', background: 'rgba(239, 68, 68, 0.06)', display: 'flex', gap: '10px', alignItems: 'center' }}>
          <AlertCircle size={16} color="#ef4444" />
          <span style={{ fontSize: '12px', color: '#ef4444' }}>{errorDetails}</span>
        </div>
      )}
    </div>
  );
};
