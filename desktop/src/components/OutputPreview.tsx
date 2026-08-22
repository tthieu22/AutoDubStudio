import React from 'react';
import { FolderOpen, Film, Video } from 'lucide-react';
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
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', maxWidth: '800px', margin: '0 auto', height: '100%', justifyContent: 'center' }}>
      {/* Video Viewport Frame */}
      <div 
        style={{ 
          width: '100%', 
          borderRadius: '10px', 
          overflow: 'hidden', 
          background: '#0B0D10', 
          border: '1px solid rgba(255, 255, 255, 0.05)',
          boxShadow: '0 10px 30px rgba(0,0,0,0.5)',
          padding: '8px'
        }}
      >
        <video 
          key={selectedProjectDir}
          src={videoSrc}
          controls
          style={{ width: '100%', borderRadius: '6px', display: 'block', maxHeight: '420px' }}
        />
      </div>

      {/* Asset Meta Info Card */}
      <div 
        style={{ 
          width: '100%', 
          padding: '16px 20px', 
          background: '#111318', 
          border: '1px solid rgba(255, 255, 255, 0.05)',
          borderRadius: '10px',
          display: 'flex', 
          justifyContent: 'space-between', 
          alignItems: 'center' 
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{ width: '32px', height: '32px', borderRadius: '6px', background: 'rgba(99, 102, 241, 0.08)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(99, 102, 241, 0.15)' }}>
            <Video size={16} color="#6366f1" />
          </div>
          <div>
            <h4 style={{ margin: '0 0 2px 0', fontSize: '13px', fontWeight: 700, color: '#fff' }}>final.mp4 (Rendered Output)</h4>
            <span style={{ fontSize: '11px', color: '#94a3b8', fontFamily: 'monospace' }}>{selectedProjectDir}/output/final.mp4</span>
          </div>
        </div>

        <button className="btn-primary" onClick={onOpenOutputFolder} style={{ padding: '8px 16px', fontSize: '12px' }}>
          <FolderOpen size={14} /> Open Directory
        </button>
      </div>
    </div>
  );
};
