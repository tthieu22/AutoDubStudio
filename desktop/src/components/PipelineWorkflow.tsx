import React from 'react';
import { 
  Loader2, 
  RefreshCw, 
  AlertCircle, 
  Layers, 
  FileText, 
  Globe, 
  Zap, 
  Clock, 
  Video 
} from 'lucide-react';
import { StageName, StageProgressInfo } from '../types/pipeline';

interface PipelineWorkflowProps {
  overallProgress: number;
  elapsedTime: number;
  stageProgresses: Record<StageName, StageProgressInfo>;
  errorDetails: string | null;
  onRetryStage: (stage: StageName) => void;
  onOpenTimeline?: () => void;
  formatTime: (seconds: number) => string;
}

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
  TRANSCRIBE: 'Whisper Speech-to-Text',
  TRANSLATE: 'Ollama AI Translation',
  TTS: 'Piper Voice Synthesis',
  SYNC: 'Audio Time-Sync & Pacing',
  RENDER: 'FFmpeg NVENC Video Render'
};

const STAGE_ICONS: Record<StageName, React.ReactNode> = {
  EXTRACT: <Layers size={18} className="text-cyan-400" />,
  TRANSCRIBE: <FileText size={18} className="text-indigo-400" />,
  TRANSLATE: <Globe size={18} className="text-emerald-400" />,
  TTS: <Zap size={18} className="text-amber-400" />,
  SYNC: <Clock size={18} className="text-purple-400" />,
  RENDER: <Video size={18} className="text-rose-400" />
};

export const PipelineWorkflow: React.FC<PipelineWorkflowProps> = ({
  overallProgress,
  elapsedTime,
  stageProgresses,
  errorDetails,
  onRetryStage,
  onOpenTimeline,
  formatTime
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', maxWidth: '1000px', margin: '0 auto' }}>
      
      {/* OVERALL PROGRESS PANEL */}
      <div className="glass-panel" style={{ padding: '20px', borderRadius: '16px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 800 }}>Tiến Độ Tổng Thể</h3>
            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Thời gian thực hiện: {formatTime(elapsedTime)}</span>
          </div>
          <span className="gradient-text" style={{ fontSize: '24px' }}>{overallProgress}%</span>
        </div>

        <div style={{ width: '100%', background: '#020617', height: '12px', borderRadius: '6px', overflow: 'hidden' }}>
          <div style={{ width: `${overallProgress}%`, background: 'linear-gradient(90deg, #6366f1, #06b6d4, #10b981)', height: '100%', transition: 'width 0.4s ease' }}></div>
        </div>
      </div>

      {/* PIPELINE COMPLETED PROMINENT BANNER */}
      {overallProgress >= 100 && onOpenTimeline && (
        <div 
          className="glass-card animate-pulse" 
          style={{ 
            padding: '24px', 
            borderRadius: '16px', 
            border: '2px solid #10b981', 
            backgroundColor: 'rgba(16, 185, 129, 0.1)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: '16px',
            flexWrap: 'wrap'
          }}
        >
          <div>
            <h3 style={{ margin: 0, fontSize: '18px', fontWeight: 800, color: '#10b981', display: 'flex', alignItems: 'center', gap: '8px' }}>
              ✓ All AI Processing Completed!
            </h3>
            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: '#cbd5e1' }}>
              Your video is ready for editing. Jump into the Timeline & Layers Studio to review, adjust subtitles, and fine-tune layers.
            </p>
          </div>

          <button
            onClick={onOpenTimeline}
            className="btn-primary"
            style={{ padding: '10px 24px', fontSize: '14px', fontWeight: 800, gap: '8px', background: 'linear-gradient(135deg, #10b981, #06b6d4)' }}
          >
            <Layers size={18} /> EDIT TIMELINE (CHỈNH SỬA VIDEO)
          </button>
        </div>
      )}

      {/* STAGE CARDS GRID */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
        {STAGE_ORDER.map(st => {
          const info = stageProgresses[st];
          const isRunning = info.status === 'RUNNING';
          const isDone = info.status === 'COMPLETED' || info.status === 'SKIPPED';
          const isFailed = info.status === 'FAILED';

          return (
            <div 
              key={st} 
              className="glass-card" 
              style={{ 
                padding: '20px', 
                borderColor: isRunning ? 'var(--cyan)' : isDone ? 'rgba(16, 185, 129, 0.4)' : isFailed ? 'var(--rose)' : 'var(--border-glass)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  {STAGE_ICONS[st]}
                  <div>
                    <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#fff' }}>{STAGE_LABELS[st]}</h4>
                    <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Mã bước: {st}</span>
                  </div>
                </div>

                <span className={`badge badge-${info.status.toLowerCase()}`}>
                  {isRunning && <Loader2 size={12} className="animate-spin" />}
                  {isDone ? 'Hoàn Thành' : info.status}
                </span>
              </div>

              {/* Progress bar inside card */}
              <div style={{ width: '100%', background: '#020617', height: '6px', borderRadius: '3px', overflow: 'hidden', marginBottom: '12px' }}>
                <div 
                  style={{ 
                    width: `${info.progress}%`, 
                    background: isDone ? '#10b981' : isFailed ? '#f43f5e' : '#06b6d4', 
                    height: '100%', 
                    transition: 'width 0.3s ease' 
                  }}
                ></div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                  {info.total > 0 ? `Tiến độ: ${info.current}/${info.total} (${info.progress}%)` : `Phần trăm: ${info.progress}%`}
                </span>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  {st === 'RENDER' && onOpenTimeline && (
                    <button 
                      className="btn-primary" 
                      onClick={onOpenTimeline}
                      style={{ padding: '4px 10px', fontSize: '11px', gap: '4px' }}
                    >
                      <Layers size={12} /> Chỉnh sửa trên Timeline
                    </button>
                  )}
                  <button 
                    className="btn-secondary" 
                    onClick={() => onRetryStage(st)}
                    style={{ padding: '4px 10px', fontSize: '11px' }}
                  >
                    <RefreshCw size={12} /> Chạy Lại
                  </button>
                </div>
              </div>

              {info.error && (
                <div style={{ marginTop: '10px', padding: '8px 10px', background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.3)', borderRadius: '6px', color: '#fb7185', fontSize: '11px' }}>
                  {info.error}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {errorDetails && (
        <div className="glass-panel" style={{ padding: '16px 20px', borderRadius: '12px', borderColor: 'var(--rose)', background: 'rgba(244, 63, 94, 0.15)' }}>
          <h4 style={{ margin: '0 0 6px 0', color: '#fb7185', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={18} /> Lỗi Trong Quá Trình Thực Thi
          </h4>
          <p style={{ margin: 0, fontSize: '13px', color: '#fca5a5' }}>{errorDetails}</p>
        </div>
      )}

    </div>
  );
};
