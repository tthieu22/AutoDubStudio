import React, { useRef, useState, useEffect } from 'react';
import { convertFileSrc } from '@tauri-apps/api/tauri';
import { CompositionState, TimelineClip } from '../../editor/state/types';
import { editorStore } from '../../editor/state/editorStore';
import { DEFAULT_VIDEO_PROPS } from '../../editor/utils/videoDefaults';
import { getCSSStyle } from '../../editor/utils/videoFilters';

interface VideoCanvasProps {
  composition: CompositionState;
  selectedClipIds: string[];
  showSafeArea: boolean;
  currentTime: number;
  isPlaying: boolean;
}

export const VideoCanvas: React.FC<VideoCanvasProps> = ({
  composition,
  selectedClipIds,
  showSafeArea,
  currentTime,
  isPlaying,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const isSeekingRef = useRef<boolean>(false);
  const [videoError, setVideoError] = useState<string | null>(null);

  const [draggingId, setDraggingId] = useState<string | null>(null);
  const [dragStartPos, setDragStartPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [clipStartPos, setClipStartPos] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  const isTauri = typeof (window as any).__TAURI_IPC__ === 'function';

  // Resolve source video path
  const videoClip = composition.clips.find((c) => c.type === 'video');
  const sourceVideoPath = videoClip?.videoProps?.src || '';
  const projectDir = composition.id;

  const absoluteVideoPath = sourceVideoPath.includes(':') || sourceVideoPath.startsWith('/')
    ? sourceVideoPath
    : projectDir && sourceVideoPath
      ? `${projectDir}/${sourceVideoPath}`
      : '';

  const videoSrc = isTauri && absoluteVideoPath
    ? convertFileSrc(absoluteVideoPath.replace(/\\/g, '/'))
    : 'https://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ForBiggerBlazes.mp4';

  const rawProps = videoClip?.videoProps;
  const videoProps = {
    ...DEFAULT_VIDEO_PROPS,
    ...rawProps,
    transform: { ...DEFAULT_VIDEO_PROPS.transform, ...(rawProps?.transform || {}) },
    audio: { ...DEFAULT_VIDEO_PROPS.audio, ...(rawProps?.audio || {}) },
    color: { ...DEFAULT_VIDEO_PROPS.color, ...(rawProps?.color || {}) },
    filter: { ...DEFAULT_VIDEO_PROPS.filter, ...(rawProps?.filter || {}) },
    playback: { ...DEFAULT_VIDEO_PROPS.playback, ...(rawProps?.playback || {}) }
  };
  const cssStyles = getCSSStyle(videoProps);

  // Sync original video properties (volume, muted, speed) to video DOM element
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    const audioProps = videoProps.audio || DEFAULT_VIDEO_PROPS.audio;
    const playbackProps = videoProps.playback || DEFAULT_VIDEO_PROPS.playback;

    const vol = typeof audioProps.volume === 'number' ? audioProps.volume : 1.0;
    video.volume = Math.max(0, Math.min(1.0, vol)); // Clamp to HTML5 max of 1.0
    video.muted = !!audioProps.muted;

    const speed = typeof playbackProps.speed === 'number' ? playbackProps.speed : 1.0;
    video.playbackRate = speed;
  }, [videoProps.audio, videoProps.playback]);

  // 1. Sync isPlaying -> video.play() / video.pause() & requestAnimationFrame loop
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    let rafId: number;

    const updateLoop = () => {
      if (video && !isSeekingRef.current && !video.paused) {
        editorStore.setUiState({ currentTime: video.currentTime });
      }
      rafId = requestAnimationFrame(updateLoop);
    };

    if (isPlaying) {
      video.play()
        .then(() => {
          rafId = requestAnimationFrame(updateLoop);
        })
        .catch((err) => {
          console.warn("HTML5 video autoplay/play failed:", err);
          editorStore.setUiState({ isPlaying: false });
        });
    } else {
      video.pause();
    }

    return () => {
      if (rafId) {
        cancelAnimationFrame(rafId);
      }
    };
  }, [isPlaying]);

  // 2. Sync currentTime -> video.currentTime (with Threshold & Seek Guard)
  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;

    if (Math.abs(video.currentTime - currentTime) > 0.15) {
      isSeekingRef.current = true;
      video.currentTime = currentTime;
      const timeout = setTimeout(() => {
        isSeekingRef.current = false;
      }, 50);
      return () => clearTimeout(timeout);
    }
  }, [currentTime]);

  // 3. Sync video.currentTime -> currentTime during playback
  const handleTimeUpdate = () => {
    const video = videoRef.current;
    if (!video || isSeekingRef.current) return;

    if (isPlaying) {
      editorStore.setUiState({ currentTime: video.currentTime });
    }
  };

  // 4. loadedmetadata -> update canonical duration
  const handleLoadedMetadata = () => {
    const video = videoRef.current;
    if (!video) return;

    const dur = video.duration;
    if (isFinite(dur) && !isNaN(dur) && dur > 0) {
      const newComp = { ...editorStore.getComposition(), duration: dur };
      editorStore.setComposition(newComp, false);
    }
  };

  // 5. ended -> stop playback and remain at end
  const handleEnded = () => {
    const video = videoRef.current;
    if (!video) return;
    editorStore.setUiState({ isPlaying: false, currentTime: video.duration });
  };

  // 6. error handler
  const handleVideoError = () => {
    if (isTauri) {
      setVideoError("Unable to load source video");
    } else {
      console.warn("Fallback video failed to load, ignoring on web mockup.");
    }
  };

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
      editorStore.updateClip(clip.id, { x: clip.x, y: clip.y }, true);
    }
  };

  return (
    <div 
      ref={containerRef}
      onClick={() => editorStore.clearSelection()}
      className="editor-canvas-screen"
      style={{ position: 'relative', width: '100%', height: '100%', maxWidth: '960px', aspectRatio: '16/9', overflow: 'hidden', background: '#000', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
    >
      {/* HTML5 VIDEO PLAYER PREVIEW */}
      {!videoError && (sourceVideoPath || !isTauri) ? (
        <video
          ref={videoRef}
          src={videoSrc}
          onTimeUpdate={handleTimeUpdate}
          onLoadedMetadata={handleLoadedMetadata}
          onEnded={handleEnded}
          onError={handleVideoError}
          preload="metadata"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            width: '100%',
            height: '100%',
            objectFit: 'contain',
            pointerEvents: 'none',
            zIndex: 0,
            ...cssStyles,
          }}
        />
      ) : (
        <div style={{ color: '#ef4444', fontSize: '14px', zIndex: 1, textAlign: 'center', pointerEvents: 'none', fontWeight: 600 }}>
          {videoError || "No source video available"}
        </div>
      )}

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
        const isVideo = clip.type === 'video';

        return (
          <div
            key={clip.id}
            onPointerDown={(e) => handlePointerDown(e, clip)}
            onPointerMove={(e) => handlePointerMove(e, clip)}
            onPointerUp={(e) => handlePointerUp(e, clip)}
            style={isVideo ? {
              position: 'absolute',
              left: 0,
              top: 0,
              width: '100%',
              height: '100%',
              opacity: clip.opacity,
              zIndex: clip.zIndex,
              cursor: 'grab',
              userSelect: 'none',
              ...cssStyles,
            } : {
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
                <div style={{ position: 'absolute', top: '-4px', left: '-4px', width: '8px', height: '8px', backgroundColor: '#6366f1', border: '1px solid #fff', borderRadius: '50%' }} />
                <div style={{ position: 'absolute', top: '-4px', right: '-4px', width: '8px', height: '8px', backgroundColor: '#6366f1', border: '1px solid #fff', borderRadius: '50%' }} />
                <div style={{ position: 'absolute', bottom: '-4px', left: '-4px', width: '8px', height: '8px', backgroundColor: '#6366f1', border: '1px solid #fff', borderRadius: '50%' }} />
                <div style={{ position: 'absolute', bottom: '-4px', right: '-4px', width: '8px', height: '8px', backgroundColor: '#6366f1', border: '1px solid #fff', borderRadius: '50%' }} />
                <div style={{ position: 'absolute', top: '-20px', left: '50%', transform: 'translateX(-50%)', width: '8px', height: '8px', backgroundColor: '#06b6d4', border: '1px solid #fff', borderRadius: '50%' }} />
              </div>
            )}
          </div>
        );
      })}

      {visibleClips.length === 0 && !sourceVideoPath && isTauri && (
        <div style={{ color: '#475569', fontSize: '12px', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '2px', pointerEvents: 'none' }}>
          Canvas Preview (Khung hình 1920 × 1080)
        </div>
      )}
    </div>
  );
};
