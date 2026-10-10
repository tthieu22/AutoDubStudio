import { CompositionState, TimelineClip, Track } from './types';
import { INITIAL_TRACKS } from './editorStore';

import { DEFAULT_VIDEO_PROPS, VideoProps } from '../utils/videoDefaults';

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
    opacity?: number;
    rotation?: number;
    scale?: number;
    videoProps?: any;
    style?: Record<string, any>;
  }>;
  compositionWidth?: number;
  compositionHeight?: number;
}

/**
 * CompositionBuilder
 * Maps AI Pipeline outputs (STT subtitles, TTS audio, Video, Layers)
 * into a live, editable Multi-Track Timeline Composition Model.
 */
export class CompositionBuilder {
  static buildFromArtifacts(artifacts: ProjectArtifacts): CompositionState {
    const videoDuration = artifacts.videoDuration ?? 0;
    const clips: TimelineClip[] = [];
    const cW = artifacts.compositionWidth || 1920;
    const cH = artifacts.compositionHeight || 1080;

    // 1. VIDEO LAYER
    if (artifacts.sourceVideoPath || artifacts.videoDuration) {
      const savedVideo = artifacts.layers?.find((l) => l.type === 'video');
      const savedProps = savedVideo?.videoProps;

      const videoProps: VideoProps & { src: string } = {
        src: artifacts.sourceVideoPath || 'source/input.mp4',
        transform: {
          x: savedProps?.transform?.x ?? DEFAULT_VIDEO_PROPS.transform.x,
          y: savedProps?.transform?.y ?? DEFAULT_VIDEO_PROPS.transform.y,
          scale: savedProps?.transform?.scale ?? DEFAULT_VIDEO_PROPS.transform.scale,
          rotation: savedProps?.transform?.rotation ?? DEFAULT_VIDEO_PROPS.transform.rotation,
          flipX: savedProps?.transform?.flipX ?? DEFAULT_VIDEO_PROPS.transform.flipX,
          flipY: savedProps?.transform?.flipY ?? DEFAULT_VIDEO_PROPS.transform.flipY,
        },
        opacity: savedProps?.opacity ?? DEFAULT_VIDEO_PROPS.opacity,
        audio: {
          volume: savedProps?.audio?.volume ?? DEFAULT_VIDEO_PROPS.audio.volume,
          muted: savedProps?.audio?.muted ?? DEFAULT_VIDEO_PROPS.audio.muted,
          fadeIn: savedProps?.audio?.fadeIn ?? DEFAULT_VIDEO_PROPS.audio.fadeIn,
          fadeOut: savedProps?.audio?.fadeOut ?? DEFAULT_VIDEO_PROPS.audio.fadeOut,
        },
        color: {
          brightness: savedProps?.color?.brightness ?? DEFAULT_VIDEO_PROPS.color.brightness,
          contrast: savedProps?.color?.contrast ?? DEFAULT_VIDEO_PROPS.color.contrast,
          saturation: savedProps?.color?.saturation ?? DEFAULT_VIDEO_PROPS.color.saturation,
          exposure: savedProps?.color?.exposure ?? DEFAULT_VIDEO_PROPS.color.exposure,
          gamma: savedProps?.color?.gamma ?? DEFAULT_VIDEO_PROPS.color.gamma,
          hue: savedProps?.color?.hue ?? DEFAULT_VIDEO_PROPS.color.hue,
          temperature: savedProps?.color?.temperature ?? DEFAULT_VIDEO_PROPS.color.temperature,
          tint: savedProps?.color?.tint ?? DEFAULT_VIDEO_PROPS.color.tint,
        },
        filter: {
          preset: savedProps?.filter?.preset ?? DEFAULT_VIDEO_PROPS.filter.preset,
        },
        playback: {
          speed: savedProps?.playback?.speed ?? DEFAULT_VIDEO_PROPS.playback.speed,
        },
      };

      clips.push({
        id: savedVideo?.id || `clip-video-${artifacts.projectId || 'source'}`,
        name: 'Original Video',
        type: 'video',
        trackId: 'track-video-main',
        startTime: savedVideo?.start ?? 0,
        duration: videoDuration || (savedVideo?.duration ?? 60),
        visible: savedVideo?.visible !== false,
        locked: savedVideo?.locked || false,
        opacity: savedVideo?.opacity ?? 1,
        zIndex: 1,
        x: savedVideo ? (savedVideo.x / cW) * 100 : 50,
        y: savedVideo ? (savedVideo.y / cH) * 100 : 50,
        width: 100,
        height: 100,
        rotation: savedVideo?.rotation ?? 0,
        scaleX: savedVideo?.scale ?? 1,
        scaleY: savedVideo?.scale ?? 1,
        videoProps: videoProps,
      });
    }

    // 2. SUBTITLE & DUBBING SEGMENTS (Linked Clips)
    if (artifacts.segments && artifacts.segments.length > 0) {
      artifacts.segments.forEach((seg, idx) => {
        const padZero = (num: number | string, size: number) => {
          let s = String(num);
          while (s.length < size) s = '0' + s;
          return s;
        };
        const segId = !isNaN(Number(seg.id)) ? padZero(seg.id, 6) : seg.id;
        const defaultDuration = Math.max(0.2, seg.end - seg.start);

        // Find saved subtitle layer custom timings
        const savedSubLayer = artifacts.layers?.find(
          (l) => l.type === 'subtitle' && (l.id === `clip-sub-${seg.id}` || l.id === `clip-sub-${idx}`)
        );
        const startTime = savedSubLayer ? savedSubLayer.start : seg.start;
        const duration = savedSubLayer ? savedSubLayer.duration : defaultDuration;

        // Find saved audio layer custom properties (volume, mute)
        const savedAudioLayer = artifacts.layers?.find(
          (l) => l.type === 'audio' && (l.id === `clip-audio-seg-${seg.id}` || l.id === `clip-audio-seg-${idx}`)
        );
        const volume = savedAudioLayer ? (savedAudioLayer.opacity ?? 1.0) : 1.0;
        const muted = savedAudioLayer ? (savedAudioLayer.visible === false) : false;

        clips.push({
          id: `clip-sub-${seg.id || idx}`,
          segmentId: seg.id,
          name: `Sub & Voice #${idx + 1}: ${seg.text.substring(0, 16)}...`,
          type: 'subtitle',
          trackId: 'track-subtitle',
          startTime: startTime,
          duration: duration,
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
          audioProps: {
            src: `audio/synced/${segId}.wav`,
            volume: volume,
            muted: muted,
            solo: false,
            fadeIn: 0,
            fadeOut: 0,
          },
        });
      });
    }

    // 4. CUSTOM LAYERS (Title, Text, Image, Logo)
    if (artifacts.layers && artifacts.layers.length > 0) {
      const customLayers = artifacts.layers.filter(l => l.type !== 'subtitle' && l.type !== 'audio' && l.type !== 'video');
      customLayers.forEach((l, idx) => {
        // Skip corrupt duplicate video layers saved as custom layers
        if (l.id && l.id.startsWith('clip-video-')) {
          return;
        }
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
          x: (l.x / cW) * 100 || 50,
          y: (l.y / cH) * 100 || 20,
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

    const maxClipEnd = clips.length > 0
      ? Math.max(0, ...clips.map(c => c.startTime + c.duration))
      : 0;

    const timelineDuration = Math.max(
      videoDuration,
      maxClipEnd,
      60
    );

    return {
      id: artifacts.projectId || 'project-active',
      name: artifacts.projectName || 'Active Composition',
      width: cW,
      height: cH,
      fps: 30,
      duration: Math.ceil(timelineDuration),
      tracks: INITIAL_TRACKS,
      clips,
    };
  }
}
