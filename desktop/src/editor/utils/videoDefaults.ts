export type VideoFilterPreset = 'none' | 'warm' | 'cool' | 'cinematic' | 'grayscale' | 'vintage' | 'high-contrast' | 'low-contrast';

export interface VideoProps {
  transform: {
    x: number;
    y: number;
    scale: number;
    rotation: number;
    flipX: boolean;
    flipY: boolean;
  };
  opacity: number;
  audio: {
    volume: number;
    muted: boolean;
    fadeIn: number;
    fadeOut: number;
  };
  color: {
    brightness: number;  // -100 to +100
    contrast: number;    // -100 to +100
    saturation: number;  // -100 to +100
    exposure: number;    // -100 to +100
    gamma: number;       // 0.1 to 10 (default 1.0)
    hue: number;         // -180 to +180
    temperature: number; // -100 to +100
    tint: number;        // -100 to +100
  };
  filter: {
    preset: VideoFilterPreset;
  };
  playback: {
    speed: number;       // 0.25 to 4.0
  };
}

export const DEFAULT_VIDEO_PROPS: VideoProps = {
  transform: {
    x: 0,
    y: 0,
    scale: 1,
    rotation: 0,
    flipX: false,
    flipY: false,
  },
  opacity: 1,
  audio: {
    volume: 1,
    muted: false,
    fadeIn: 0,
    fadeOut: 0,
  },
  color: {
    brightness: 0,
    contrast: 0,
    saturation: 0,
    exposure: 0,
    gamma: 1.0,
    hue: 0,
    temperature: 0,
    tint: 0,
  },
  filter: {
    preset: 'none',
  },
  playback: {
    speed: 1.0,
  },
};
