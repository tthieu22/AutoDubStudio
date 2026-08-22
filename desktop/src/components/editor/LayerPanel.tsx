import React from 'react';
import { CompositionState } from '../../editor/state/types';
import { editorStore } from '../../editor/state/editorStore';
import { Eye, EyeOff, Lock, Unlock, Layers, Trash2 } from 'lucide-react';

interface LayerPanelProps {
  composition: CompositionState;
  selectedClipIds: string[];
}

export const LayerPanel: React.FC<LayerPanelProps> = ({ composition, selectedClipIds }) => {
  const sortedClips = [...composition.clips].sort((a, b) => b.zIndex - a.zIndex);

  return (
    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} color="#818cf8" />
          <h3 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#f1f5f9', margin: 0 }}>
            Layer Hierarchy
          </h3>
        </div>
        <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#64748b' }}>{sortedClips.length} layers</span>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {sortedClips.map((clip) => {
          const isSelected = selectedClipIds.includes(clip.id);

          return (
            <div
              key={clip.id}
              onClick={(e) => editorStore.selectClip(clip.id, e.ctrlKey || e.shiftKey)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '8px 10px',
                borderRadius: '6px',
                border: isSelected ? '1px solid #6366f1' : '1px solid rgba(255, 255, 255, 0.06)',
                backgroundColor: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(15, 23, 42, 0.6)',
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', overflow: 'hidden' }}>
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#06b6d4', flexShrink: 0 }} />
                <span style={{ fontSize: '12px', fontWeight: 600, color: '#f8fafc', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {clip.name}
                </span>
                <span style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase' }}>({clip.type})</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    editorStore.updateClip(clip.id, { visible: !clip.visible }, true);
                  }}
                  className="editor-nav-btn"
                  style={{ width: '24px', height: '24px' }}
                  title={clip.visible ? 'Ẩn layer' : 'Hiện layer'}
                >
                  {clip.visible ? <Eye size={13} /> : <EyeOff size={13} color="#f43f5e" />}
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    editorStore.updateClip(clip.id, { locked: !clip.locked }, true);
                  }}
                  className="editor-nav-btn"
                  style={{ width: '24px', height: '24px' }}
                  title={clip.locked ? 'Mở khóa layer' : 'Khóa layer'}
                >
                  {clip.locked ? <Lock size={13} color="#f59e0b" /> : <Unlock size={13} />}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
