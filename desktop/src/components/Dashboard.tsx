import React from 'react';
import { 
  Play, Pause, RefreshCw, Square, CheckCircle2, Eye, 
  Activity, Cpu, HardDrive, Thermometer, Terminal, Sparkles, Lock, CheckCircle, XCircle
} from 'lucide-react';
import { PipelineStatus, StageName, StageProgressInfo, HardwareTelemetry, PipelineMode } from '../types/pipeline';

interface DashboardProps {
  projectName: string;
  mode: PipelineMode;
  status: PipelineStatus;
  overallProgress: number;
  stageProgresses: Partial<Record<StageName, StageProgressInfo>>;
  telemetry: HardwareTelemetry;
  logs: string[];
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onRetry: () => void;
  onCancel: () => void;
  onReview: () => void;
  onApproveGate?: () => void;
  onRejectGate?: () => void;
}

const STORY_STAGES: { key: StageName; label: string }[] = [
  { key: 'COLLECT', label: 'Collect' },
  { key: 'CLEAN', label: 'Clean' },
  { key: 'ANALYZE', label: 'Analyze' },
  { key: 'MEMORY', label: 'Memory' },
  { key: 'SCENE', label: 'Scene' },
  { key: 'IMAGE', label: 'Image' },
  { key: 'TTS', label: 'TTS' },
  { key: 'SUBTITLE', label: 'Subtitle' },
  { key: 'TIMELINE', label: 'Timeline' },
  { key: 'RENDER', label: 'Render' },
  { key: 'QA', label: 'QA' },
  { key: 'PUBLISH', label: 'Publish' },
];

const DUBBING_STAGES: { key: StageName; label: string }[] = [
  { key: 'EXTRACT', label: 'Extract' },
  { key: 'TRANSCRIBE', label: 'STT' },
  { key: 'TRANSLATE', label: 'Translate' },
  { key: 'TTS', label: 'TTS' },
  { key: 'SYNC', label: 'Sync' },
  { key: 'RENDER', label: 'Render' },
  { key: 'QA', label: 'QA' },
  { key: 'PUBLISH', label: 'Publish' },
];

export const Dashboard: React.FC<DashboardProps> = ({
  projectName,
  mode,
  status,
  overallProgress,
  stageProgresses,
  telemetry,
  logs,
  onStart,
  onPause,
  onResume,
  onRetry,
  onCancel,
  onReview,
  onApproveGate,
  onRejectGate,
}) => {
  const currentStages = mode === 'STORY' ? STORY_STAGES : DUBBING_STAGES;

  const getStageIcon = (stKey: StageName) => {
    const info = stageProgresses[stKey];
    const stStatus = info?.status || 'PENDING';

    if (stStatus === 'COMPLETED' || stStatus === 'APPROVED') {
      return <span style={{ color: '#10b981', fontWeight: 800 }}>✓</span>;
    }
    if (stStatus === 'RUNNING') {
      return <span style={{ color: '#06b6d4', fontWeight: 800 }}>▶</span>;
    }
    if (stStatus === 'REVIEW_REQUIRED') {
      return <span style={{ color: '#f59e0b', fontWeight: 800 }}>👁</span>;
    }
    if (stStatus === 'FAILED') {
      return <span style={{ color: '#ef4444', fontWeight: 800 }}>!</span>;
    }
    return <span style={{ color: '#475569' }}>○</span>;
  };

  const getStatusBadge = () => {
    let bg = 'rgba(71, 85, 105, 0.2)';
    let color = '#94a3b8';
    let text: string = status;

    if (status === 'RUNNING') {
      bg = 'rgba(6, 182, 212, 0.15)'; color = '#38bdf8'; text = 'RUNNING';
    } else if (status === 'PAUSED') {
      bg = 'rgba(245, 158, 11, 0.15)'; color = '#fbbf24'; text = 'PAUSED';
    } else if (status === 'REVIEW_REQUIRED') {
      bg = 'rgba(236, 72, 153, 0.2)'; color = '#f472b6'; text = 'REVIEW REQUIRED';
    } else if (status === 'COMPLETED') {
      bg = 'rgba(16, 185, 129, 0.15)'; color = '#34d399'; text = 'COMPLETED';
    } else if (status === 'FAILED') {
      bg = 'rgba(239, 68, 68, 0.15)'; color = '#f87171'; text = 'FAILED';
    }

    return (
      <span 
        style={{ 
          padding: '4px 10px', 
          borderRadius: '6px', 
          background: bg, 
          color, 
          fontSize: '11px', 
          fontWeight: 800, 
          letterSpacing: '0.5px' 
        }}
      >
        {text}
      </span>
    );
  };

  return (
    <div 
      style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        gap: '16px', 
        padding: '20px', 
        background: '#0B0D10', 
        color: '#f8fafc',
        borderRadius: '16px',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        fontFamily: 'Inter, system-ui, sans-serif'
      }}
    >
      {/* 1. HEADER CONTROL BAR */}
      <div 
        style={{ 
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center',
          paddingBottom: '14px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
        }}
      >
        <div>
          <span style={{ fontSize: '11px', color: '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>AutoDubStudio Control Center</span>
          <h2 style={{ margin: '2px 0 0 0', fontSize: '20px', fontWeight: 800, display: 'flex', alignItems: 'center', gap: '10px' }}>
            {projectName || 'MyStory'}
            <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '4px', background: 'rgba(99, 102, 241, 0.2)', color: '#818cf8', fontWeight: 700 }}>
              MODE: {mode}
            </span>
          </h2>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 600 }}>Status:</span>
          {getStatusBadge()}
        </div>
      </div>

      {/* 2. PIPELINE STAGE TRACKER GRID */}
      <div 
        style={{ 
          background: '#111318', 
          border: '1px solid rgba(255, 255, 255, 0.05)', 
          borderRadius: '12px', 
          padding: '16px 20px' 
        }}
      >
        <span style={{ fontSize: '11px', fontWeight: 800, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'block', marginBottom: '12px' }}>
          Pipeline Execution Trackers
        </span>
        
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
          {currentStages.map((st) => {
            const info = stageProgresses[st.key];
            const isRunning = info?.status === 'RUNNING';
            const isReview = info?.status === 'REVIEW_REQUIRED';

            return (
              <div 
                key={st.key}
                style={{ 
                  display: 'flex', 
                  alignItems: 'center', 
                  gap: '8px', 
                  padding: '8px 12px', 
                  borderRadius: '8px', 
                  background: isRunning ? 'rgba(6, 182, 212, 0.1)' : isReview ? 'rgba(245, 158, 11, 0.1)' : 'rgba(255, 255, 255, 0.02)',
                  border: isRunning ? '1px solid rgba(6, 182, 212, 0.4)' : '1px solid rgba(255, 255, 255, 0.05)',
                  fontSize: '13px',
                  fontWeight: 600
                }}
              >
                {getStageIcon(st.key)}
                <span style={{ flexGrow: 1, color: isRunning ? '#38bdf8' : '#e2e8f0' }}>{st.label}</span>
                {info && info.progress > 0 && (
                  <span style={{ fontSize: '10px', color: '#64748b' }}>{info.progress}%</span>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. PROGRESS BAR PANEL */}
      <div style={{ background: '#111318', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '12px', padding: '16px 20px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '13px' }}>
          <span style={{ fontWeight: 700, color: '#e2e8f0' }}>Total Progress</span>
          <span style={{ fontWeight: 800, color: '#38bdf8' }}>{overallProgress}%</span>
        </div>
        <div style={{ background: '#020617', height: '12px', borderRadius: '6px', overflow: 'hidden' }}>
          <div 
            style={{ 
              width: `${overallProgress}%`, 
              height: '100%', 
              background: 'linear-gradient(90deg, #6366f1, #06b6d4, #10b981)',
              transition: 'width 0.4s ease',
              borderRadius: '6px'
            }} 
          />
        </div>
      </div>

      {/* 4. HARDWARE TELEMETRY GAUGES (GTX 1650 Ti 4GB Target) */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '12px' }}>
        {/* GPU Utilization */}
        <div style={{ background: '#111318', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '10px', padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700 }}><Activity size={12} style={{ color: '#06b6d4' }} /> GPU</span>
            <span style={{ color: '#fff', fontWeight: 800 }}>{telemetry.gpu_util_percent}%</span>
          </div>
          <div style={{ background: '#020617', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${telemetry.gpu_util_percent}%`, height: '100%', background: '#06b6d4' }} />
          </div>
        </div>

        {/* VRAM Usage */}
        <div style={{ background: '#111318', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '10px', padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700 }}><HardDrive size={12} style={{ color: '#a855f7' }} /> VRAM</span>
            <span style={{ color: '#fff', fontWeight: 800 }}>{telemetry.vram_used_gb} / {telemetry.vram_total_gb} GB</span>
          </div>
          <div style={{ background: '#020617', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${telemetry.vram_percent}%`, height: '100%', background: '#a855f7' }} />
          </div>
        </div>

        {/* RAM Usage */}
        <div style={{ background: '#111318', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '10px', padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700 }}><Cpu size={12} style={{ color: '#10b981' }} /> RAM</span>
            <span style={{ color: '#fff', fontWeight: 800 }}>{telemetry.ram_used_gb} GB ({telemetry.ram_percent}%)</span>
          </div>
          <div style={{ background: '#020617', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${telemetry.ram_percent}%`, height: '100%', background: '#10b981' }} />
          </div>
        </div>

        {/* CPU & Temp */}
        <div style={{ background: '#111318', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '10px', padding: '12px 14px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#94a3b8', marginBottom: '6px' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700 }}><Thermometer size={12} style={{ color: '#f59e0b' }} /> CPU / Temp</span>
            <span style={{ color: '#fff', fontWeight: 800 }}>{telemetry.cpu_percent}% | {telemetry.temp_c}°C</span>
          </div>
          <div style={{ background: '#020617', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${telemetry.cpu_percent}%`, height: '100%', background: '#f59e0b' }} />
          </div>
        </div>
      </div>

      {/* 5. LOG STREAM FEED */}
      <div style={{ background: '#111318', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '12px', padding: '14px 16px' }}>
        <span style={{ fontSize: '11px', fontWeight: 800, color: '#06b6d4', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '8px' }}>
          <Terminal size={13} /> Live Log Stream
        </span>
        <div style={{ background: '#020617', borderRadius: '8px', padding: '12px', height: '110px', overflowY: 'auto', fontFamily: 'monospace', fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
          {logs.length === 0 ? (
            <span style={{ color: '#475569' }}>Logs will stream here in real-time...</span>
          ) : (
            logs.slice(-8).map((l, i) => (
              <div key={i} style={{ color: l.includes('ERROR') ? '#f87171' : l.includes('VRAM') ? '#c084fc' : '#cbd5e1' }}>
                {l}
              </div>
            ))
          )}
        </div>
      </div>

      {/* 6. REVIEW GATE MANDATORY CONTROL BANNER (Phase 33) */}
      {status === 'REVIEW_REQUIRED' && (
        <div style={{ background: 'rgba(245, 158, 11, 0.12)', border: '1px solid rgba(245, 158, 11, 0.4)', borderRadius: '12px', padding: '12px 16px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <Lock size={18} style={{ color: '#f59e0b' }} />
            <div>
              <span style={{ fontSize: '12px', fontWeight: 800, color: '#fcd34d' }}>🔒 REVIEW GATE MANDATORY: DỰ ÁN ĐANG CHỜ PHÊ DUYỆT (REVIEW REQUIRED)</span>
              <div style={{ fontSize: '11px', color: '#cbd5e1', marginTop: '2px' }}>
                Pipeline đã dừng an toàn tại Review Gate. Tiến trình Render bị <strong>KHÓA (LOCKED)</strong> cho tới khi bạn bấm <strong>[APPROVE]</strong>.
              </div>
            </div>
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button 
              onClick={onRejectGate}
              style={{ background: 'rgba(239, 68, 68, 0.2)', border: '1px solid #ef4444', color: '#f87171', padding: '6px 12px', borderRadius: '6px', fontSize: '11px', fontWeight: 700, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <XCircle size={13} /> [REJECT]
            </button>
            <button 
              onClick={onApproveGate}
              style={{ background: '#10b981', border: 'none', color: '#fff', padding: '6px 14px', borderRadius: '6px', fontSize: '11px', fontWeight: 800, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '4px' }}
            >
              <CheckCircle size={13} /> [APPROVE GATE ➔]
            </button>
          </div>
        </div>
      )}

      {/* 7. CONTROL ACTIONS BAR */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', paddingTop: '8px' }}>
        <button 
          onClick={onReview}
          style={{ 
            background: 'rgba(236, 72, 153, 0.15)', 
            border: '1px solid rgba(236, 72, 153, 0.4)', 
            color: '#f472b6', 
            padding: '8px 16px', 
            borderRadius: '8px', 
            fontSize: '12px', 
            fontWeight: 700, 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px', 
            cursor: 'pointer' 
          }}
        >
          <Eye size={14} /> [Review]
        </button>

        <button 
          onClick={onPause}
          disabled={status !== 'RUNNING'}
          style={{ 
            background: 'rgba(245, 158, 11, 0.15)', 
            border: '1px solid rgba(245, 158, 11, 0.4)', 
            color: '#fbbf24', 
            padding: '8px 16px', 
            borderRadius: '8px', 
            fontSize: '12px', 
            fontWeight: 700, 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px', 
            cursor: status === 'RUNNING' ? 'pointer' : 'not-allowed',
            opacity: status === 'RUNNING' ? 1 : 0.5 
          }}
        >
          <Pause size={14} /> [Pause]
        </button>

        <button 
          onClick={onResume}
          disabled={status !== 'PAUSED' && status !== 'CANCELLED' && status !== 'FAILED'}
          style={{ 
            background: 'rgba(16, 185, 129, 0.15)', 
            border: '1px solid rgba(16, 185, 129, 0.4)', 
            color: '#34d399', 
            padding: '8px 16px', 
            borderRadius: '8px', 
            fontSize: '12px', 
            fontWeight: 700, 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px', 
            cursor: 'pointer' 
          }}
        >
          <Play size={14} /> [Resume]
        </button>

        <button 
          onClick={onRetry}
          style={{ 
            background: 'rgba(99, 102, 241, 0.15)', 
            border: '1px solid rgba(99, 102, 241, 0.4)', 
            color: '#818cf8', 
            padding: '8px 16px', 
            borderRadius: '8px', 
            fontSize: '12px', 
            fontWeight: 700, 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px', 
            cursor: 'pointer' 
          }}
        >
          <RefreshCw size={14} /> [Retry]
        </button>

        <button 
          onClick={onCancel}
          style={{ 
            background: 'rgba(239, 68, 68, 0.15)', 
            border: '1px solid rgba(239, 68, 68, 0.4)', 
            color: '#f87171', 
            padding: '8px 16px', 
            borderRadius: '8px', 
            fontSize: '12px', 
            fontWeight: 700, 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px', 
            cursor: 'pointer' 
          }}
        >
          <Square size={14} /> [Cancel]
        </button>
      </div>
    </div>
  );
};
