import React from 'react';
import { Upload, Film, Music, Type } from 'lucide-react';
import { editorStore } from '../../editor/state/editorStore';

export const MediaPanel: React.FC = () => {
  return (
    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '10px' }}>
        <h3 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#f1f5f9', margin: 0 }}>
          Media Assets
        </h3>
        <button
          onClick={() => {
            const name = prompt('Nhập tên file hình ảnh hoặc URL logo:', 'brand_logo.png');
            if (name) {
              editorStore.addClip({
                id: `img-${Date.now()}`,
                name: 'Brand Logo',
                type: 'image',
                trackId: 'track-image',
                startTime: editorStore.getUiState().currentTime,
                duration: 10,
                visible: true,
                locked: false,
                opacity: 0.9,
                zIndex: 15,
                x: 85,
                y: 15,
                width: 15,
                height: 15,
                rotation: 0,
                scaleX: 1,
                scaleY: 1,
                imageProps: { src: name, aspectRatio: 1 },
              });
            }
          }}
          className="btn-primary"
          style={{ padding: '4px 10px', fontSize: '11px', gap: '4px' }}
        >
          <Upload size={13} /> + Import Media
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <div 
          onClick={() => {
            editorStore.addClip({
              id: `vid-${Date.now()}`,
              name: 'Main Video Clip',
              type: 'video',
              trackId: 'track-video',
              startTime: 0,
              duration: 60,
              visible: true,
              locked: false,
              opacity: 1,
              zIndex: 1,
              x: 50,
              y: 50,
              width: 100,
              height: 100,
              rotation: 0,
              scaleX: 1,
              scaleY: 1,
            });
          }}
          style={{
            padding: '16px 12px',
            backgroundColor: 'rgba(15, 23, 42, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.15s ease'
          }}
          className="glass-card"
        >
          <Film size={24} color="#60a5fa" />
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#cbd5e1' }}>+ Video Clip</span>
        </div>

        <div 
          onClick={() => {
            editorStore.addClip({
              id: `audio-${Date.now()}`,
              name: 'Dubbed Voice',
              type: 'audio',
              trackId: 'track-audio',
              startTime: 0,
              duration: 30,
              visible: true,
              locked: false,
              opacity: 1,
              zIndex: 1,
              x: 0,
              y: 0,
              width: 0,
              height: 0,
              rotation: 0,
              scaleX: 1,
              scaleY: 1,
            });
          }}
          style={{
            padding: '16px 12px',
            backgroundColor: 'rgba(15, 23, 42, 0.7)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '8px',
            cursor: 'pointer',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '8px',
            transition: 'all 0.15s ease'
          }}
          className="glass-card"
        >
          <Music size={24} color="#34d399" />
          <span style={{ fontSize: '11px', fontWeight: 600, color: '#cbd5e1' }}>+ Audio Voice</span>
        </div>
      </div>
    </div>
  );
};
