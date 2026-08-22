export type LayerType = 'video' | 'audio' | 'subtitle' | 'text' | 'image' | 'logo';

export interface BaseLayer {
  id: string;
  name: string;
  type: LayerType;
  trackId: string;
  startTime: number; // in seconds
  duration: number;  // in seconds
  visible: boolean;
  locked: boolean;
  opacity: number;   // 0 to 1
  zIndex: number;
  x: number;         // percentage or px
  y: number;
  width: number;
  height: number;
  rotation: number;
  scaleX: number;
  scaleY: number;
}

export interface TransformProps {
  x: number;      // canvas percentage or px (center aligned default)
  y: number;
  width: number;
  height: number;
  rotation: number; // degrees
  scaleX: number;
  scaleY: number;
}

export interface TextLayerProps extends TransformProps {
  content: string;
  fontFamily: string;
  fontSize: number;
  fontWeight: string;
  color: string;
  strokeColor?: string;
  strokeWidth?: number;
  shadowColor?: string;
  shadowBlur?: number;
  textAlign: 'left' | 'center' | 'right';
}

export interface SubtitleLayerProps extends TransformProps {
  text: string;
  speaker?: string;
  fontFamily: string;
  fontSize: number;
  color: string;
  backgroundColor?: string;
}

export interface ImageLayerProps extends TransformProps {
  src: string;
  aspectRatio: number;
  cropTop?: number;
  cropBottom?: number;
  cropLeft?: number;
  cropRight?: number;
}

export interface VideoLayerProps extends TransformProps {
  src: string;
  volume: number;
  muted: boolean;
  playbackRate: number;
}

export interface AudioLayerProps {
  src: string;
  volume: number;
  muted: boolean;
  solo: boolean;
  fadeIn: number;
  fadeOut: number;
}

export type TrackType = LayerType;

export interface Track {
  id: string;
  name: string;
  type: TrackType;
  muted: boolean;
  locked: boolean;
  height: number;
  color: string;
}

export type TimelineClip = BaseLayer & {
  textProps?: Partial<TextLayerProps>;
  subtitleProps?: Partial<SubtitleLayerProps>;
  imageProps?: Partial<ImageLayerProps>;
  videoProps?: Partial<VideoLayerProps>;
  audioProps?: Partial<AudioLayerProps>;
};

export interface CompositionState {
  id: string;
  name: string;
  width: number;
  height: number;
  fps: number;
  duration: number;
  tracks: Track[];
  clips: TimelineClip[];
}

export interface SnappingSettings {
  enabled: boolean;
  snapToPlayhead: boolean;
  snapToClipEdges: boolean;
  snapToGrid: boolean;
  thresholdPx: number;
}

export interface EditorUiState {
  currentTime: number;
  isPlaying: boolean;
  zoomLevel: number; // px per second
  selectedClipIds: string[];
  activeLeftTab: 'media' | 'audio' | 'text' | 'titles' | 'subtitles' | 'images' | 'elements' | 'ai';
  showSafeArea: boolean;
  snapping: SnappingSettings;
  splitMode: boolean;
  isSaving: boolean;
  lastSavedAt: string | null;
}
