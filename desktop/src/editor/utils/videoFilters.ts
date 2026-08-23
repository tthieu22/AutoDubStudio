import React from 'react';
import { VideoProps, VideoFilterPreset } from './videoDefaults';

export function getCSSFilterString(props: VideoProps): string {
  const filters: string[] = [];

  // Color adjustments
  const brightness = props.color.brightness ?? 0;
  const exposure = props.color.exposure ?? 0;
  // Combine brightness and exposure for CSS
  const combinedBrightness = (1 + brightness / 100) * (1 + exposure / 100);
  if (combinedBrightness !== 1) {
    filters.push(`brightness(${combinedBrightness.toFixed(2)})`);
  }

  const contrast = props.color.contrast ?? 0;
  if (contrast !== 0) {
    filters.push(`contrast(${(1 + contrast / 100).toFixed(2)})`);
  }

  const saturation = props.color.saturation ?? 0;
  if (saturation !== 0) {
    filters.push(`saturate(${(1 + saturation / 100).toFixed(2)})`);
  }

  const hue = props.color.hue ?? 0;
  if (hue !== 0) {
    filters.push(`hue-rotate(${hue}deg)`);
  }

  // Presets mapping
  const preset: VideoFilterPreset = props.filter.preset ?? 'none';
  switch (preset) {
    case 'warm':
      filters.push('sepia(0.3) saturate(1.2) hue-rotate(-10deg)');
      break;
    case 'cool':
      filters.push('saturate(0.9) hue-rotate(10deg) brightness(1.05)');
      break;
    case 'cinematic':
      filters.push('contrast(1.25) saturate(0.85) brightness(0.95)');
      break;
    case 'grayscale':
      filters.push('grayscale(1.0)');
      break;
    case 'vintage':
      filters.push('sepia(0.4) contrast(0.9) saturate(0.8)');
      break;
    case 'high-contrast':
      filters.push('contrast(1.5)');
      break;
    case 'low-contrast':
      filters.push('contrast(0.7) brightness(1.1)');
      break;
    default:
      break;
  }

  // Temperature / Tint approximations
  const temp = props.color.temperature ?? 0;
  if (temp > 0) {
    filters.push(`sepia(${(temp / 200).toFixed(2)}) hue-rotate(${-(temp / 10).toFixed(1)}deg)`);
  } else if (temp < 0) {
    filters.push(`hue-rotate(${-(temp / 10).toFixed(1)}deg)`);
  }

  const tint = props.color.tint ?? 0;
  if (tint !== 0) {
    // Tint can be approximated via hue-rotate
    filters.push(`hue-rotate(${(tint / 2).toFixed(1)}deg)`);
  }

  return filters.join(' ');
}

export function getCSSStyle(props: VideoProps): React.CSSProperties {
  const filterStr = getCSSFilterString(props);
  
  const scaleVal = props.transform.scale ?? 1;
  const flipXVal = props.transform.flipX ? -1 : 1;
  const flipYVal = props.transform.flipY ? -1 : 1;
  const rotateVal = props.transform.rotation ?? 0;
  const posX = props.transform.x ?? 0;
  const posY = props.transform.y ?? 0;

  return {
    filter: filterStr || undefined,
    opacity: props.opacity ?? 1,
    transform: `translate(${posX}px, ${posY}px) rotate(${rotateVal}deg) scale(${scaleVal}) scaleX(${flipXVal}) scaleY(${flipYVal})`,
  };
}
