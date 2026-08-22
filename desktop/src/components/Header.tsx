import React from 'react';
import { Play, Square, FolderOpen, Loader2, Sparkles, AlertTriangle } from 'lucide-react';
import { PipelineStatus, StageName, StageProgressInfo, StageStatus } from '../types/pipeline';

interface HeaderProps {
  selectedProjectDir: string;
  pipelineStatus: PipelineStatus;
  stageProgresses: Record<StageName, StageProgressInfo>;
  onStartPipeline: (force?: boolean) => void;
  onCancelPipeline: () => void;
  onOpenOutputFolder: () => void;
  activeTab: string;
  setActiveTab: (tab: any) => void;
}

const STAGE_ORDER: StageName[] = [
  'EXTRACT',
  'TRANSCRIBE',
  'TRANSLATE',
  'TTS',
  'SYNC',
  'RENDER'
];

const STAGE_SHORT_LABELS: Record<StageName, string> = {
  EXTRACT: 'EXTRACT',
  TRANSCRIBE: 'STT',
  TRANSLATE: 'TRANSLATE',
  TTS: 'TTS',
  SYNC: 'SYNC',
  RENDER: 'RENDER'
};

export const Header: React.FC<HeaderProps> = ({
  selectedProjectDir,
  pipelineStatus,
  stageProgresses,
  onStartPipeline,
  onCancelPipeline,
  onOpenOutputFolder,
  activeTab,
  setActiveTab
}) => {
  const projectName = selectedProjectDir.split('/').pop()?.split('\\').pop() || selectedProjectDir;

  const renderStageIndicator = (st: StageName, status: StageStatus) => {
    let color = '#64748b';
    let label = STAGE_SHORT_LABELS[st];
    let icon = '○';

    if (status === 'COMPLETED' || status === 'SKIPPED') {
      color = '#10b981';
      icon = '✓';
    } else if (status === 'RUNNING') {
      color = '#06b6d4';
      icon = '●';
    } else if (status === 'FAILED') {
      color = '#ef4444';
      icon = '!';
    }

    return (
      <span 
        key={st} 
        onClick={() => setActiveTab('pipeline')}
        style={{ 
          color, 
          fontSize: '11px', 
          fontWeight: 700, 
          display: 'flex', 
          alignItems: 'center', 
          gap: '4px',
          cursor: 'pointer',
          padding: '2px 6px',
          borderRadius: '4px',
          background: status === 'RUNNING' ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
          transition: 'all 0.15s ease'
        }}
        title={`${st}: ${status}`}
      >
        <span style={{ fontSize: status === 'RUNNING' ? '12px' : '10px' }}>{icon}</span>
        {label}
      </span>
    );
  };

  return (
    <div 
      style={{ 
        height: '52px', 
        padding: '0 20px', 
        background: '#111318', 
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)', 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        flexShrink: 0
      }}
    >
      {/* BRAND & PROJECT INFO */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div style={{ width: '24px', height: '24px', borderRadius: '6px', background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Sparkles size={14} color="#fff" />
          </div>
          <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 800, fontSize: '14px', letterSpacing: '0.5px' }}>AutoDub Studio</span>
          <span style={{ fontSize: '10px', color: '#64748b', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: '4px' }}>PRO</span>
        </div>
        <div style={{ width: '1px', height: '20px', background: 'rgba(255,255,255,0.1)' }} />
        <div>
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#fff' }}>{projectName}</span>
        </div>
      </div>

      {/* COMPACT PIPELINE STEP TRACKER */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '4px', background: '#0B0D10', padding: '4px 8px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.03)' }}>
        {STAGE_ORDER.map((st, idx) => {
          const info = stageProgresses[st] || { status: 'PENDING' };
          return (
            <React.Fragment key={st}>
              {renderStageIndicator(st, info.status)}
              {idx < STAGE_ORDER.length - 1 && (
                <span style={{ color: 'rgba(255,255,255,0.15)', fontSize: '10px' }}>➔</span>
              )}
            </React.Fragment>
          );
        })}
      </div>

      {/* ACTIONS TOOLBAR */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        {pipelineStatus === 'RUNNING' ? (
          <button 
            className="btn-secondary" 
            onClick={onCancelPipeline} 
            style={{ 
              borderColor: 'rgba(239, 68, 68, 0.4)', 
              color: '#ef4444', 
              padding: '6px 12px', 
              fontSize: '12px', 
              background: 'rgba(239, 68, 68, 0.08)' 
            }}
          >
            <Square size={13} /> Cancel Pipeline
          </button>
        ) : (
          <button 
            className="btn-primary" 
            onClick={() => onStartPipeline(true)}
            style={{ padding: '6px 14px', fontSize: '12px' }}
          >
            <Play size={13} /> RUN DUBBING
          </button>
        )}

        <button 
          className="btn-secondary" 
          onClick={onOpenOutputFolder}
          style={{ padding: '6px 12px', fontSize: '12px' }}
        >
          <FolderOpen size={13} /> Output Directory
        </button>
      </div>
    </div>
  );
};
