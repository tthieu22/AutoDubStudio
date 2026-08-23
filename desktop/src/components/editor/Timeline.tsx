import React, { useRef, useEffect } from 'react';
import { CompositionState, EditorUiState, TimelineClip, Track } from '../../editor/state/types';
import { editorStore } from '../../editor/state/editorStore';
import { Play, Pause, Scissors, Copy, Trash2, ZoomIn, ZoomOut } from 'lucide-react';

interface TimelineProps {
  composition: CompositionState;
  uiState: EditorUiState;
  onPlayheadChange: (time: number) => void;
}

// 1. Memoized Track Sidebar Headers
const TrackSidebarHeaders = React.memo(({ tracks }: { tracks: Track[] }) => {
  return (
    <div className="track-sidebar">
      <div className="ruler-corner">Tracks & Layers</div>
      {tracks.map((track) => (
        <div key={track.id} className="editor-track-row-sidebar" style={{ height: `${track.height}px`, minHeight: `${track.height}px` }}>
          <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{track.name}</span>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: track.color }} />
        </div>
      ))}
    </div>
  );
});

// 2. Memoized Track Lanes & Clips Container
const TrackLanes = React.memo(({ 
  tracks, 
  clips, 
  pxPerSec, 
  selectedClipIds 
}: { 
  tracks: Track[]; 
  clips: TimelineClip[]; 
  pxPerSec: number; 
  selectedClipIds: string[] 
}) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column' }}>
      {tracks.map((track) => {
        const trackClips = clips.filter((c) => c.trackId === track.id);

        return (
          <div key={track.id} className="editor-track-lane" style={{ height: `${track.height}px`, minHeight: `${track.height}px` }}>
            {trackClips.map((clip) => {
              const isSelected = selectedClipIds.includes(clip.id);

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
        );
      })}
    </div>
  );
});

// 3. Isolated Playhead component to prevent track-lanes/clips re-render
const Playhead = ({ currentTime, pxPerSec }: { currentTime: number; pxPerSec: number }) => {
  return (
    <div
      className="editor-playhead-line"
      style={{
        transform: `translateX(${currentTime * pxPerSec}px)`,
        willChange: 'transform',
      }}
    >
      <div className="editor-playhead-handle" />
    </div>
  );
};

export const Timeline: React.FC<TimelineProps> = ({
  composition,
  uiState,
  onPlayheadChange,
}) => {
  const timelineViewportRef = useRef<HTMLDivElement>(null);
  const pxPerSec = uiState.zoomLevel;
  const isAutoScrollingRef = useRef<boolean>(false);
  const followPlayheadRef = useRef<boolean>(true);
  const scrollRafRef = useRef<number | null>(null);

  // Re-enable following the playhead when video starts playing
  useEffect(() => {
    if (uiState.isPlaying) {
      followPlayheadRef.current = true;
    }
  }, [uiState.isPlaying]);

  // Clean up RAF on unmount
  useEffect(() => {
    return () => {
      if (scrollRafRef.current !== null) {
        cancelAnimationFrame(scrollRafRef.current);
      }
    };
  }, []);

  // Handle auto-scroll when playhead leaves 20%-75% safe area
  useEffect(() => {
    const viewport = timelineViewportRef.current;
    if (!viewport || !followPlayheadRef.current) return;

    const playheadX = uiState.currentTime * pxPerSec;
    const viewportWidth = viewport.clientWidth;
    if (viewportWidth <= 0) return;

    const viewportLeft = viewport.scrollLeft;
    const safeLeft = viewportLeft + viewportWidth * 0.20;
    const safeRight = viewportLeft + viewportWidth * 0.75;

    let targetScrollLeft = -1;
    if (playheadX > safeRight) {
      targetScrollLeft = playheadX - viewportWidth * 0.60;
    } else if (playheadX < safeLeft) {
      targetScrollLeft = Math.max(0, playheadX - viewportWidth * 0.30);
    }

    if (targetScrollLeft !== -1 && Math.abs(viewport.scrollLeft - targetScrollLeft) > 5) {
      if (scrollRafRef.current !== null) {
        cancelAnimationFrame(scrollRafRef.current);
      }
      scrollRafRef.current = requestAnimationFrame(() => {
        isAutoScrollingRef.current = true;
        viewport.scrollLeft = targetScrollLeft;
        scrollRafRef.current = null;
        
        const timeout = setTimeout(() => {
          isAutoScrollingRef.current = false;
        }, 100);
        return () => clearTimeout(timeout);
      });
    }
  }, [uiState.currentTime, pxPerSec]);

  const handleScroll = () => {
    if (isAutoScrollingRef.current) return;
    // Manual scroll: disable auto-scroll temporarily
    followPlayheadRef.current = false;
  };

  const handleTimelineClick = (e: React.MouseEvent) => {
    const viewport = timelineViewportRef.current;
    if (!viewport) return;
    const rect = viewport.getBoundingClientRect();
    const clickX = e.clientX - rect.left + viewport.scrollLeft;
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

      {/* 2. TWO-COLUMN LAYOUT BODY */}
      <div className="timeline-body">
        {/* Track Sidebar Headers */}
        <TrackSidebarHeaders tracks={composition.tracks} />

        {/* Timeline Viewport */}
        <div 
          ref={timelineViewportRef}
          onScroll={handleScroll}
          onClick={handleTimelineClick}
          className="timeline-viewport"
        >
          <div className="timeline-content" style={{ width: `${composition.duration * pxPerSec}px` }}>
            {/* Time Ruler */}
            <div className="time-ruler">
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

            {/* Track Lanes */}
            <TrackLanes 
              tracks={composition.tracks} 
              clips={composition.clips} 
              pxPerSec={pxPerSec} 
              selectedClipIds={uiState.selectedClipIds} 
            />

            {/* Playhead */}
            <Playhead currentTime={uiState.currentTime} pxPerSec={pxPerSec} />
          </div>
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
