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
  'TRANSLATE'
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
      {/* Left section empty to keep alignment or add spacing if needed */}
      <div></div>

      {/* COMPACT PIPELINE STEP TRACKER */}


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
