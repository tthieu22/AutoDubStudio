import React from 'react';
import { FolderOpen } from 'lucide-react';
import { convertFileSrc } from '@tauri-apps/api/tauri';

interface OutputPreviewProps {
  selectedProjectDir: string;
  onOpenOutputFolder: () => void;
}

export const OutputPreview: React.FC<OutputPreviewProps> = ({
  selectedProjectDir,
  onOpenOutputFolder
}) => {
  const isTauri = typeof (window as any).__TAURI_IPC__ === 'function';
  const videoSrc = selectedProjectDir
    ? isTauri
      ? convertFileSrc(`${selectedProjectDir.replace(/\\/g, '/')}/output/final.mp4`)
      : 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4'
    : undefined;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <div className="glass-panel" style={{ width: '100%', borderRadius: '16px', overflow: 'hidden', padding: '16px', border: '1px solid var(--border-glass-bright)' }}>
        <video 
          key={selectedProjectDir}
          src={videoSrc}
          controls
          style={{ width: '100%', borderRadius: '10px', display: 'block' }}
        />
      </div>

      <div className="glass-card" style={{ width: '100%', padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h4 style={{ margin: '0 0 4px 0', fontSize: '14px' }}>Video Thành Phẩm final.mp4</h4>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{selectedProjectDir}/output/final.mp4</span>
        </div>

        <button className="btn-primary" onClick={onOpenOutputFolder}>
          <FolderOpen size={16} /> Mở Thư Mục Xuất
        </button>
      </div>
    </div>
  );
};
