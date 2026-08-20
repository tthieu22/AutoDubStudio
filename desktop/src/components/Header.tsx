import React from 'react';
import { Play, Square, FolderOpen, Loader2 } from 'lucide-react';
import { PipelineStatus } from '../types/pipeline';

interface HeaderProps {
  selectedProjectDir: string;
  pipelineStatus: PipelineStatus;
  onStartPipeline: (force?: boolean) => void;
  onCancelPipeline: () => void;
  onOpenOutputFolder: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  selectedProjectDir,
  pipelineStatus,
  onStartPipeline,
  onCancelPipeline,
  onOpenOutputFolder
}) => {
  const projectName = selectedProjectDir.split('/').pop()?.split('\\').pop() || selectedProjectDir;

  return (
    <div style={{ padding: '16px 24px', background: 'rgba(15, 23, 42, 0.8)', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <h2 style={{ fontSize: '20px', fontWeight: 800, margin: 0, color: '#fff' }}>
            {projectName}
          </h2>
          <span className={`badge badge-${pipelineStatus.toLowerCase()}`}>
            {pipelineStatus === 'RUNNING' && <Loader2 size={12} className="animate-spin" />}
            {pipelineStatus}
          </span>
        </div>
        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{selectedProjectDir}</span>
      </div>

      {/* ACTION TOOLBAR */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        {pipelineStatus === 'RUNNING' ? (
          <button className="btn-secondary" onClick={onCancelPipeline} style={{ borderColor: 'var(--rose)', color: '#fb7185' }}>
            <Square size={14} /> Hủy Tiến Trình
          </button>
        ) : (
          <button className="btn-primary" onClick={() => onStartPipeline(true)}>
            <Play size={15} /> CHẠY LỒNG TIẾNG AUTOMATION
          </button>
        )}

        <button className="btn-secondary" onClick={onOpenOutputFolder}>
          <FolderOpen size={14} /> Mở Thư Mục Xuất
        </button>
      </div>
    </div>
  );
};
