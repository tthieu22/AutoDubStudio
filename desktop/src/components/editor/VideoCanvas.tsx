import React, { useRef, useState } from 'react';
import { CompositionState, TimelineClip } from '../../editor/state/types';
import { editorStore } from '../../editor/state/editorStore';

interface VideoCanvasProps {
  composition: CompositionState;
  selectedClipIds: string[];
  showSafeArea: boolean;
  currentTime: number;
}

export const VideoCanvas: React.FC<VideoCanvasProps> = ({
  composition,
  selectedClipIds,
  showSafeArea,
  currentTime,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragStartPos, setDragStartPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [clipStartPos, setClipStartPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  // Active visible clips at playhead time
  const visibleClips = composition.clips.filter((c) => {
    return c.visible && currentTime >= c.startTime && currentTime <= c.startTime + c.duration;
  });

  const handlePointerDown = (e: React.PointerEvent, clip: TimelineClip) => {
    if (clip.locked) return;
    e.stopPropagation();
    editorStore.selectClip(clip.id, e.ctrlKey || e.shiftKey);
    setDraggingId(clip.id);
    setDragStartPos({ x: e.clientX, y: e.clientY });
    setClipStartPos({ x: clip.x, y: clip.y });
    (e.target as HTMLElement).setPointerCapture(e.pointerId);
  };

  const handlePointerMove = (e: React.PointerEvent, clip: TimelineClip) => {
    if (draggingId !== clip.id || !containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const dxPx = e.clientX - dragStartPos.x;
    const dyPx = e.clientY - dragStartPos.y;

    const dxPercent = (dxPx / rect.width) * 100;
    const dyPercent = (dyPx / rect.height) * 100;

    const newX = Math.round((clipStartPos.x + dxPercent) * 10) / 10;
    const newY = Math.round((clipStartPos.y + dyPercent) * 10) / 10;

    editorStore.updateClip(clip.id, { x: newX, y: newY }, false);
  };

  const handlePointerUp = (e: React.PointerEvent, clip: TimelineClip) => {
    if (draggingId === clip.id) {
      setDraggingId(null);
      // Record history step after drag complete
      editorStore.updateClip(clip.id, { x: clip.x, y: clip.y }, true);
    }
  };

  return (
    <div 
      ref={containerRef}
      onClick={() => editorStore.clearSelection()}
      className="editor-canvas-screen"
      style={{ position: 'relative', width: '100%', height: '100%', maxWidth: '960px', aspectRatio: '16/9' }}
    >
      {/* 1. SAFE AREA GUIDES OVERLAY */}
      {showSafeArea && (
        <div 
          style={{
            position: 'absolute',
            inset: 0,
            pointerEvents: 'none',
            zIndex: 30,
            border: '1px solid rgba(99, 102, 241, 0.2)'
          }}
        >
          {/* Action Safe (90%) */}
          <div 
            style={{
              position: 'absolute',
              inset: '5%',
              border: '1px dashed rgba(6, 182, 212, 0.35)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            {/* Title Safe (80%) */}
            <div 
              style={{
                position: 'absolute',
                inset: '5%',
                border: '1px dashed rgba(245, 158, 11, 0.35)'
              }}
            />
          </div>
          {/* Center Crosshair */}
          <div style={{ position: 'absolute', top: '50%', left: 0, right: 0, height: '1px', backgroundColor: 'rgba(255, 255, 255, 0.15)' }} />
          <div style={{ position: 'absolute', left: '50%', top: 0, bottom: 0, width: '1px', backgroundColor: 'rgba(255, 255, 255, 0.15)' }} />
        </div>
      )}

      {/* 2. RENDER VISIBLE CLIPS ON CANVAS */}
      {visibleClips.map((clip) => {
        const isSelected = selectedClipIds.includes(clip.id);

        return (
          <div
            key={clip.id}
            onPointerDown={(e) => handlePointerDown(e, clip)}
            onPointerMove={(e) => handlePointerMove(e, clip)}
            onPointerUp={(e) => handlePointerUp(e, clip)}
            style={{
              position: 'absolute',
              left: `${clip.x}%`,
              top: `${clip.y}%`,
              width: `${clip.width}%`,
              height: `${clip.height}%`,
              transform: `translate(-50%, -50%) rotate(${clip.rotation}deg)`,
              opacity: clip.opacity,
              zIndex: clip.zIndex,
              cursor: 'grab',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              userSelect: 'none',
            }}
          >
            {/* TEXT LAYER */}
            {clip.type === 'text' && clip.textProps && (
              <div 
                style={{
                  fontFamily: clip.textProps.fontFamily,
                  fontSize: `${clip.textProps.fontSize}px`,
                  fontWeight: clip.textProps.fontWeight,
                  color: clip.textProps.color,
                  textAlign: clip.textProps.textAlign,
                  textShadow: '0 2px 8px rgba(0,0,0,0.8)',
                  width: '100%',
                  height: '100%',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {clip.textProps.content}
              </div>
            )}

            {/* SUBTITLE LAYER */}
            {clip.type === 'subtitle' && clip.subtitleProps && (
              <div 
                style={{
                  fontFamily: clip.subtitleProps.fontFamily,
                  fontSize: `${clip.subtitleProps.fontSize}px`,
                  color: clip.subtitleProps.color,
                  backgroundColor: clip.subtitleProps.backgroundColor,
                  padding: '8px 16px',
                  borderRadius: '6px',
                  fontWeight: 600,
                  textAlign: 'center',
                  boxShadow: '0 4px 12px rgba(0,0,0,0.6)'
                }}
              >
                {clip.subtitleProps.text}
              </div>
            )}

            {/* SELECTION BOUNDING BOX & HANDLES */}
            {isSelected && (
              <div 
                style={{
                  position: 'absolute',
                  inset: 0,
                  border: '2px solid #6366f1',
                  pointerEvents: 'none',
                  borderRadius: '2px'
                }}
              >
                {/* 4 Corner Resize Handles */}
                <div style={{ position: 'absolute', top: '-4px', left: '-4px', width: '8px', height: '8px', backgroundColor: '#6366f1', border: '1px solid #fff', borderRadius: '50%' }} />
                <div style={{ position: 'absolute', top: '-4px', right: '-4px', width: '8px', height: '8px', backgroundColor: '#6366f1', border: '1px solid #fff', borderRadius: '50%' }} />
                <div style={{ position: 'absolute', bottom: '-4px', left: '-4px', width: '8px', height: '8px', backgroundColor: '#6366f1', border: '1px solid #fff', borderRadius: '50%' }} />
                <div style={{ position: 'absolute', bottom: '-4px', right: '-4px', width: '8px', height: '8px', backgroundColor: '#6366f1', border: '1px solid #fff', borderRadius: '50%' }} />
                {/* Rotation Handle */}
                <div style={{ position: 'absolute', top: '-20px', left: '50%', transform: 'translateX(-50%)', width: '8px', height: '8px', backgroundColor: '#06b6d4', border: '1px solid #fff', borderRadius: '50%' }} />
              </div>
            )}
          </div>
        );
      })}

      {visibleClips.length === 0 && (
        <div style={{ color: '#475569', fontSize: '12px', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '2px', pointerEvents: 'none' }}>
          Canvas Preview (Khung hình 1920 × 1080)
        </div>
      )}
    </div>
  );
};
