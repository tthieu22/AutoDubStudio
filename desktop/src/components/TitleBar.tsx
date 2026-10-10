import React from 'react';
import { Minus, Square, X } from 'lucide-react';
import { appWindow } from '@tauri-apps/api/window';
import { StageName, StageProgressInfo, StageStatus } from '../types/pipeline';

interface TitleBarProps {
  selectedProjectDir?: string | null;
  stageProgresses?: Partial<Record<StageName, StageProgressInfo>>;
}

const STAGE_ORDER: StageName[] = ['EXTRACT', 'TRANSCRIBE', 'TRANSLATE', 'TTS', 'SYNC', 'RENDER'];

const STAGE_SHORT_LABELS: Partial<Record<StageName, string>> = {
  EXTRACT: 'EXTRACT',
  TRANSCRIBE: 'STT',
  TRANSLATE: 'TRANSLATE',
  TTS: 'TTS',
  SYNC: 'SYNC',
  RENDER: 'RENDER'
};

export const TitleBar: React.FC<TitleBarProps> = ({ selectedProjectDir, stageProgresses = {} as any }) => {
  const isTauri = typeof (window as any).__TAURI_IPC__ === 'function';

  if (!isTauri) return null;

  const projectName = selectedProjectDir 
    ? selectedProjectDir.split('/').pop()?.split('\\').pop() 
    : null;

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
        style={{ 
          color, 
          fontSize: '9px', 
          fontWeight: 700, 
          display: 'flex', 
          alignItems: 'center', 
          gap: '3px',
          padding: '2px 4px',
          borderRadius: '3px',
          background: status === 'RUNNING' ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
        }}
        title={`${st}: ${status}`}
      >
        <span style={{ fontSize: status === 'RUNNING' ? '10px' : '8px' }}>{icon}</span>
        {label}
      </span>
    );
  };

  const handleMinimize = () => {
    appWindow.minimize();
  };

  const handleMaximize = () => {
    appWindow.toggleMaximize();
  };

  const handleClose = () => {
    appWindow.close();
  };

  return (
    <div 
      data-tauri-drag-region 
      style={{
        height: '32px',
        background: '#0B0D10',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '0 12px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
        userSelect: 'none',
        flexShrink: 0,
        zIndex: 9999
      }}
    >
      <style>{`
        .titlebar-btn {
          background: transparent;
          border: none;
          color: #64748b;
          width: 28px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          border-radius: 4px;
          outline: none;
          transition: all 0.1s ease;
        }
        .titlebar-btn:hover {
          background: rgba(255, 255, 255, 0.08);
          color: #fff;
        }
        .titlebar-btn-close {
          background: transparent;
          border: none;
          color: #64748b;
          width: 28px;
          height: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          border-radius: 4px;
          outline: none;
          transition: all 0.1s ease;
        }
        .titlebar-btn-close:hover {
          background: #ef4444;
          color: #fff;
        }
      `}</style>
      <div data-tauri-drag-region style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <span data-tauri-drag-region style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 600 }}>
          AutoDub Studio{projectName ? ` - ${projectName}` : ''}
        </span>
      </div>

      {/* COMPACT PIPELINE STEP TRACKER */}
      {selectedProjectDir && (
        <div 
          data-tauri-drag-region 
          style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: '6px', 
            background: 'rgba(255,255,255,0.02)', 
            padding: '3px 10px', 
            borderRadius: '6px', 
            border: '1px solid rgba(255,255,255,0.05)',
            position: 'absolute',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 10000
          }}
        >
          {STAGE_ORDER.map((st, idx) => {
            const info = stageProgresses[st] || { status: 'PENDING' };
            return (
              <React.Fragment key={st}>
                {renderStageIndicator(st, info.status)}
                {idx < STAGE_ORDER.length - 1 && (
                  <span style={{ color: 'rgba(255,255,255,0.15)', fontSize: '9px' }}>➔</span>
                )}
              </React.Fragment>
            );
          })}
        </div>
      )}

      <div style={{ display: 'flex', gap: '2px' }}>
        <button 
          onClick={handleMinimize}
          className="titlebar-btn"
          title="Minimize"
        >
          <Minus size={12} />
        </button>
        <button 
          onClick={handleMaximize}
          className="titlebar-btn"
          title="Maximize"
        >
          <Square size={10} />
        </button>
        <button 
          onClick={handleClose}
          className="titlebar-btn-close"
          title="Close"
        >
          <X size={12} />
        </button>
      </div>
    </div>
  );
};
