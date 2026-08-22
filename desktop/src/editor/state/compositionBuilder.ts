import { CompositionState, TimelineClip, Track } from './types';
import { INITIAL_TRACKS } from './editorStore';

export interface ProjectArtifacts {
  projectId: string;
  projectName: string;
  videoDuration?: number;
  sourceVideoPath?: string;
  segments?: Array<{
    id: number | string;
    start: number;
    end: number;
    text: string;
    speaker?: string;
  }>;
  dubbedAudioPath?: string;
  dubbedAudioDuration?: number;
  layers?: Array<{
    id: string;
    type: string;
    text?: string;
    x: number;
    y: number;
    start: number;
    duration: number;
    visible?: boolean;
    locked?: boolean;
    style?: Record<string, any>;
  }>;
}

/**
 * CompositionBuilder
 * Maps AI Pipeline outputs (STT subtitles, TTS audio, Video, Layers)
 * into a live, editable Multi-Track Timeline Composition Model.
 */
export class CompositionBuilder {
  static buildFromArtifacts(artifacts: ProjectArtifacts): CompositionState {
    const duration = Math.max(
      60,
      artifacts.videoDuration || 0,
      artifacts.dubbedAudioDuration || 0,
      artifacts.segments && artifacts.segments.length > 0 
        ? Math.max(...artifacts.segments.map(s => s.end)) + 5 
        : 0
    );

    const clips: TimelineClip[] = [];

    // 1. VIDEO LAYER
    if (artifacts.sourceVideoPath || artifacts.videoDuration) {
      clips.push({
        id: `clip-video-${artifacts.projectId || 'source'}`,
        name: 'Original Video',
        type: 'video',
        trackId: 'track-video',
        startTime: 0,
        duration: artifacts.videoDuration || duration,
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
        videoProps: {
          src: artifacts.sourceVideoPath || 'source/input.mp4',
          volume: 1,
          muted: false,
          playbackRate: 1,
        },
      });
    }

    // 2. DUB AUDIO LAYER (from TTS & Audio Sync)
    if (artifacts.dubbedAudioPath || artifacts.dubbedAudioDuration) {
      clips.push({
        id: `clip-audio-dubbed`,
        name: 'AI Dubbed Audio',
        type: 'audio',
        trackId: 'track-audio',
        startTime: 0,
        duration: artifacts.dubbedAudioDuration || duration,
        visible: true,
        locked: false,
        opacity: 1,
        zIndex: 2,
        x: 0,
        y: 0,
        width: 0,
        height: 0,
        rotation: 0,
        scaleX: 1,
        scaleY: 1,
        audioProps: {
          src: artifacts.dubbedAudioPath || 'audio/dubbed_synchronized.wav',
          volume: 1,
          muted: false,
          solo: false,
          fadeIn: 0,
          fadeOut: 0,
        },
      });
    }

    // 3. SUBTITLE SEGMENTS (from STT & Translation)
    if (artifacts.segments && artifacts.segments.length > 0) {
      artifacts.segments.forEach((seg, idx) => {
        const segDuration = Math.max(0.2, seg.end - seg.start);
        clips.push({
          id: `clip-sub-${seg.id || idx}`,
          name: `Sub #${idx + 1}: ${seg.text.substring(0, 16)}...`,
          type: 'subtitle',
          trackId: 'track-subtitle',
          startTime: seg.start,
          duration: segDuration,
          visible: true,
          locked: false,
          opacity: 1,
          zIndex: 5,
          x: 50,
          y: 85,
          width: 70,
          height: 12,
          rotation: 0,
          scaleX: 1,
          scaleY: 1,
          subtitleProps: {
            text: seg.text,
            speaker: seg.speaker || 'Speaker',
            fontFamily: 'Plus Jakarta Sans',
            fontSize: 24,
            color: '#ffffff',
            backgroundColor: 'rgba(0, 0, 0, 0.75)',
          },
        });
      });
    }

    // 4. CUSTOM LAYERS (Title, Text, Image, Logo)
    if (artifacts.layers && artifacts.layers.length > 0) {
      artifacts.layers.forEach((l, idx) => {
        const isLogo = l.type === 'logo' || l.type === 'image';
        clips.push({
          id: l.id || `clip-layer-${idx}`,
          name: l.text || `Layer ${idx + 1}`,
          type: (isLogo ? 'image' : 'text') as any,
          trackId: isLogo ? 'track-image' : 'track-text',
          startTime: l.start || 0,
          duration: l.duration || 10,
          visible: l.visible !== false,
          locked: l.locked || false,
          opacity: 1,
          zIndex: 10 + idx,
          x: (l.x / 1920) * 100 || 50,
          y: (l.y / 1080) * 100 || 20,
          width: isLogo ? 15 : 40,
          height: isLogo ? 15 : 12,
          rotation: 0,
          scaleX: 1,
          scaleY: 1,
          textProps: !isLogo ? {
            content: l.text || 'Custom Text',
            fontFamily: 'Outfit',
            fontSize: l.style?.font_size || 40,
            fontWeight: 'bold',
            color: l.style?.color || '#38bdf8',
            textAlign: 'center',
          } : undefined,
          imageProps: isLogo ? {
            src: 'logo.png',
            aspectRatio: 1,
          } : undefined,
        });
      });
    }

    return {
      id: artifacts.projectId || 'project-active',
      name: artifacts.projectName || 'Active Composition',
      width: 1920,
      height: 1080,
      fps: 30,
      duration: Math.ceil(duration),
      tracks: INITIAL_TRACKS,
      clips,
    };
  }
}
