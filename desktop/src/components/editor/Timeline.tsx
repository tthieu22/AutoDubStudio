import React, { useRef } from 'react';
import { CompositionState, EditorUiState, TimelineClip } from '../../editor/state/types';
import { editorStore } from '../../editor/state/editorStore';
import { Play, Pause, Scissors, Copy, Trash2, ZoomIn, ZoomOut, Magnet } from 'lucide-react';

interface TimelineProps {
  composition: CompositionState;
  uiState: EditorUiState;
  onPlayheadChange: (time: number) => void;
}

export const Timeline: React.FC<TimelineProps> = ({
  composition,
  uiState,
  onPlayheadChange,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const pxPerSec = uiState.zoomLevel;

  const handleTimelineClick = (e: React.MouseEvent) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const clickX = e.clientX - rect.left - 160; // 160px track header offset
    if (clickX < 0) return;
    const time = Math.max(0, Math.min(composition.duration, clickX / pxPerSec));
    onPlayheadChange(Math.round(time * 100) / 100);
  };

  return (
    <div className="editor-timeline-panel" style={{ height: '100%' }}>
      {/* 1. TIMELINE TOOLBAR */}
      <div className="editor-timeline-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <button
            onClick={() => editorStore.setUiState({ isPlaying: !uiState.isPlaying })}
            className="btn-primary"
            style={{ padding: '4px 10px', fontSize: '11px', gap: '4px' }}
            title="Phát / Tạm dừng (Space)"
          >
            {uiState.isPlaying ? <Pause size={13} /> : <Play size={13} />}
            <span>{uiState.isPlaying ? 'Pause' : 'Play'}</span>
          </button>

          <span style={{ fontFamily: 'monospace', color: '#38bdf8', fontWeight: 700, fontSize: '12px', marginLeft: '6px' }}>
            {formatTime(uiState.currentTime)} / {formatTime(composition.duration)}
          </span>

          <div style={{ height: '14px', width: '1px', backgroundColor: 'rgba(255, 255, 255, 0.1)', margin: '0 4px' }} />

          <button
            onClick={() => {
              if (uiState.selectedClipIds.length > 0) {
                editorStore.splitClipAtPlayhead(uiState.selectedClipIds[0]);
              }
            }}
            disabled={uiState.selectedClipIds.length === 0}
            className="editor-nav-btn"
            style={{ width: 'auto', padding: '0 8px', height: '26px', fontSize: '11px', gap: '4px', opacity: uiState.selectedClipIds.length > 0 ? 1 : 0.4 }}
            title="Cắt clip tại vị trí con trỏ (B)"
          >
            <Scissors size={13} />
            <span>Split (B)</span>
          </button>

          <button
            onClick={() => editorStore.duplicateSelectedClips()}
            disabled={uiState.selectedClipIds.length === 0}
            className="editor-nav-btn"
            style={{ width: 'auto', padding: '0 8px', height: '26px', fontSize: '11px', gap: '4px', opacity: uiState.selectedClipIds.length > 0 ? 1 : 0.4 }}
            title="Nhân đôi clip (Ctrl+D)"
          >
            <Copy size={13} />
            <span>Duplicate</span>
          </button>

          <button
            onClick={() => editorStore.deleteSelectedClips()}
            disabled={uiState.selectedClipIds.length === 0}
            className="editor-nav-btn"
            style={{ width: 'auto', padding: '0 8px', height: '26px', fontSize: '11px', gap: '4px', color: '#fb7185', opacity: uiState.selectedClipIds.length > 0 ? 1 : 0.4 }}
            title="Xóa clip (Delete)"
          >
            <Trash2 size={13} />
            <span>Delete</span>
          </button>
        </div>

        {/* ZOOM CONTROLS */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={() => editorStore.setUiState({ zoomLevel: Math.max(15, pxPerSec - 10) })}
            className="editor-nav-btn"
            style={{ width: '26px', height: '26px' }}
            title="Thu nhỏ Timeline"
          >
            <ZoomOut size={13} />
          </button>
          <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8', width: '50px', textAlign: 'center' }}>
            {pxPerSec}px/s
          </span>
          <button
            onClick={() => editorStore.setUiState({ zoomLevel: Math.min(150, pxPerSec + 10) })}
            className="editor-nav-btn"
            style={{ width: '26px', height: '26px' }}
            title="Phóng to Timeline"
          >
            <ZoomIn size={13} />
          </button>
        </div>
      </div>

      {/* 2. RULER & TRACKS CONTAINER */}
      <div 
        ref={containerRef}
        onClick={handleTimelineClick}
        className="editor-timeline-body"
      >
        {/* RULER HEADER */}
        <div style={{ display: 'flex', height: '26px', minHeight: '26px', backgroundColor: '#131926', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', position: 'sticky', top: 0, zIndex: 15 }}>
          <div style={{ width: '160px', minWidth: '160px', backgroundColor: '#0f1420', borderRight: '1px solid rgba(255, 255, 255, 0.08)', padding: '0 12px', display: 'flex', alignItems: 'center', fontSize: '10px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', position: 'sticky', left: 0, zIndex: 20 }}>
            Tracks & Layers
          </div>
          <div style={{ flex: 1, position: 'relative', height: '100%', display: 'flex', alignItems: 'center' }}>
            {Array.from({ length: Math.ceil(composition.duration) }).map((_, i) => (
              <div
                key={i}
                style={{
                  position: 'absolute',
                  left: `${i * pxPerSec}px`,
                  top: 0,
                  bottom: 0,
                  borderLeft: '1px solid rgba(255, 255, 255, 0.08)',
                  paddingLeft: '4px',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                {i % 5 === 0 && (
                  <span style={{ fontSize: '9px', fontFamily: 'monospace', color: '#64748b' }}>
                    {formatTime(i)}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* PLAYHEAD VERTICAL LINE */}
        <div
          className="editor-playhead-line"
          style={{ left: `${160 + uiState.currentTime * pxPerSec}px` }}
        >
          <div className="editor-playhead-handle" />
        </div>

        {/* TRACK LIST */}
        <div style={{ display: 'flex', flexDirection: 'column' }}>
          {composition.tracks.map((track) => {
            const trackClips = composition.clips.filter((c) => c.trackId === track.id);

            return (
              <div key={track.id} className="editor-track-row">
                {/* TRACK HEADER */}
                <div className="editor-track-header">
                  <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{track.name}</span>
                  <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: track.color }} />
                </div>

                {/* TRACK CLIPS CONTAINER */}
                <div className="editor-track-lane">
                  {trackClips.map((clip) => {
                    const isSelected = uiState.selectedClipIds.includes(clip.id);

                    return (
                      <div
                        key={clip.id}
                        onClick={(e) => {
                          e.stopPropagation();
                          editorStore.selectClip(clip.id, e.ctrlKey || e.shiftKey);
                        }}
                        style={{
                          left: `${clip.startTime * pxPerSec}px`,
                          width: `${clip.duration * pxPerSec}px`,
                          backgroundColor: track.color,
                        }}
                        className={`editor-clip ${isSelected ? 'selected' : ''}`}
                      >
                        <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                          {clip.name}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  const ms = Math.floor((seconds % 1) * 10);
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}.${ms}`;
}
