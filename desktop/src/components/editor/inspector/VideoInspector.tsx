import React, { useState } from 'react';
import { TimelineClip } from '../../../editor/state/types';
import { editorStore } from '../../../editor/state/editorStore';
import { DEFAULT_VIDEO_PROPS, VideoProps, VideoFilterPreset } from '../../../editor/utils/videoDefaults';
import { RotateCcw, Volume2, Sliders, Maximize, Palette, Filter, Gauge, Check } from 'lucide-react';

interface VideoInspectorProps {
  selectedClip: TimelineClip;
}

export const VideoInspector: React.FC<VideoInspectorProps> = ({ selectedClip }) => {
  const [openSections, setOpenSections] = useState({
    transform: true,
    opacity: true,
    audio: true,
    color: true,
    filter: true,
    playback: true,
  });

  const props = selectedClip.videoProps || DEFAULT_VIDEO_PROPS;

  const toggleSection = (section: keyof typeof openSections) => {
    setOpenSections(prev => ({ ...prev, [section]: !prev[section] }));
  };

  const updateProp = (section: keyof VideoProps, key: string, value: any, commitHistory = false) => {
    const currentProps = selectedClip.videoProps || DEFAULT_VIDEO_PROPS;
    const sectionProps = (currentProps as any)[section];
    const newVideoProps = {
      ...currentProps,
      [section]: {
        ...sectionProps,
        [key]: value,
      },
    };

    const updates: any = { videoProps: newVideoProps };
    if (section === 'transform') {
      if (key === 'rotation') updates.rotation = value;
      if (key === 'scale') {
        updates.scaleX = value;
        updates.scaleY = value;
      }
      if (key === 'x') updates.x = value;
      if (key === 'y') updates.y = value;
    }
    editorStore.updateClip(selectedClip.id, updates, commitHistory);
  };

  const updateOpacity = (value: number, commitHistory = false) => {
    const currentProps = selectedClip.videoProps || DEFAULT_VIDEO_PROPS;
    editorStore.updateClip(
      selectedClip.id,
      {
        opacity: value,
        videoProps: {
          ...currentProps,
          opacity: value,
        },
      },
      commitHistory
    );
  };

  const videoSrc = selectedClip.videoProps?.src || '';

  // Reset helpers
  const resetProperty = (section: keyof VideoProps, key: string) => {
    const defaultVal = (DEFAULT_VIDEO_PROPS as any)[section][key];
    updateProp(section, key, defaultVal, true);
  };

  const resetSection = (section: keyof VideoProps) => {
    const currentProps = selectedClip.videoProps || DEFAULT_VIDEO_PROPS;
    const defaultVal = DEFAULT_VIDEO_PROPS[section];
    const newVideoProps = {
      ...currentProps,
      [section]: typeof defaultVal === 'object' && defaultVal !== null ? { ...defaultVal } : defaultVal,
    };
    const updates: any = { videoProps: newVideoProps };
    if (section === 'transform') {
      updates.rotation = DEFAULT_VIDEO_PROPS.transform.rotation;
      updates.scaleX = DEFAULT_VIDEO_PROPS.transform.scale;
      updates.scaleY = DEFAULT_VIDEO_PROPS.transform.scale;
      updates.x = DEFAULT_VIDEO_PROPS.transform.x;
      updates.y = DEFAULT_VIDEO_PROPS.transform.y;
    }
    editorStore.updateClip(selectedClip.id, updates, true);
  };

  const resetAll = () => {
    editorStore.updateClip(
      selectedClip.id,
      {
        opacity: DEFAULT_VIDEO_PROPS.opacity,
        rotation: DEFAULT_VIDEO_PROPS.transform.rotation,
        scaleX: DEFAULT_VIDEO_PROPS.transform.scale,
        scaleY: DEFAULT_VIDEO_PROPS.transform.scale,
        x: DEFAULT_VIDEO_PROPS.transform.x,
        y: DEFAULT_VIDEO_PROPS.transform.y,
        videoProps: {
          ...DEFAULT_VIDEO_PROPS,
          src: videoSrc, // Preserve video source
        },
      },
      true
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
      
      {/* SOURCE INFO */}
      <div style={{ backgroundColor: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '6px', border: '1px solid rgba(255,255,255,0.06)', fontSize: '11px' }}>
        <div style={{ color: '#94a3b8', fontWeight: 600, marginBottom: '4px' }}>SOURCE</div>
        <div style={{ textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap', color: '#f1f5f9' }} title={videoSrc}>
          {videoSrc.split('/').pop() || 'video.mp4'}
        </div>
        <div style={{ color: '#64748b', marginTop: '2px' }}>Duration: {selectedClip.duration.toFixed(2)}s</div>
      </div>

      {/* TRANSFORM SECTION */}
      <div style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', overflow: 'hidden' }}>
        <div 
          onClick={() => toggleSection('transform')}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.04)', cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Maximize size={13} /> Transform
          </span>
          <button 
            onClick={(e) => { e.stopPropagation(); resetSection('transform'); }} 
            style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}
            title="Reset Transform"
          >
            <RotateCcw size={12} />
          </button>
        </div>
        {openSections.transform && (
          <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {/* Position X */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="editor-label">Position X</label>
                <button onClick={() => resetProperty('transform', 'x')} style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}><RotateCcw size={10} /></button>
              </div>
              <input 
                type="number" 
                value={props.transform.x} 
                onChange={(e) => updateProp('transform', 'x', Number(e.target.value), true)}
                className="editor-input"
              />
            </div>
            {/* Position Y */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="editor-label">Position Y</label>
                <button onClick={() => resetProperty('transform', 'y')} style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}><RotateCcw size={10} /></button>
              </div>
              <input 
                type="number" 
                value={props.transform.y} 
                onChange={(e) => updateProp('transform', 'y', Number(e.target.value), true)}
                className="editor-input"
              />
            </div>
            {/* Scale */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="editor-label">Scale ({(props.transform.scale * 100).toFixed(0)}%)</label>
                <button onClick={() => resetProperty('transform', 'scale')} style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}><RotateCcw size={10} /></button>
              </div>
              <input 
                type="range" 
                min="0.1" 
                max="3" 
                step="0.05"
                value={props.transform.scale}
                onChange={(e) => updateProp('transform', 'scale', Number(e.target.value), false)}
                onPointerUp={(e) => updateProp('transform', 'scale', Number((e.target as HTMLInputElement).value), true)}
                style={{ width: '100%', accentColor: '#6366f1' }}
              />
            </div>
            {/* Rotation */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="editor-label">Rotation ({props.transform.rotation}°)</label>
                <button onClick={() => resetProperty('transform', 'rotation')} style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}><RotateCcw size={10} /></button>
              </div>
              <input 
                type="range" 
                min="-180" 
                max="180" 
                step="1"
                value={props.transform.rotation}
                onChange={(e) => updateProp('transform', 'rotation', Number(e.target.value), false)}
                onPointerUp={(e) => updateProp('transform', 'rotation', Number((e.target as HTMLInputElement).value), true)}
                style={{ width: '100%', accentColor: '#6366f1' }}
              />
            </div>
            {/* Flips */}
            <div style={{ display: 'flex', gap: '16px', marginTop: '4px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#cbd5e1', cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  checked={props.transform.flipX}
                  onChange={(e) => updateProp('transform', 'flipX', e.target.checked, true)}
                />
                Flip Horizontal
              </label>
              <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#cbd5e1', cursor: 'pointer' }}>
                <input 
                  type="checkbox" 
                  checked={props.transform.flipY}
                  onChange={(e) => updateProp('transform', 'flipY', e.target.checked, true)}
                />
                Flip Vertical
              </label>
            </div>
          </div>
        )}
      </div>

      {/* OPACITY SECTION */}
      <div style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', overflow: 'hidden' }}>
        <div 
          onClick={() => toggleSection('opacity')}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.04)', cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Sliders size={13} /> Opacity
          </span>
          <button 
            onClick={(e) => { e.stopPropagation(); updateOpacity(1, true); }} 
            style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}
            title="Reset Opacity"
          >
            <RotateCcw size={12} />
          </button>
        </div>
        {openSections.opacity && (
          <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="editor-label">Opacity ({(props.opacity * 100).toFixed(0)}%)</label>
            </div>
            <input 
              type="range" 
              min="0" 
              max="1" 
              step="0.05"
              value={props.opacity}
              onChange={(e) => updateOpacity(Number(e.target.value), false)}
              onPointerUp={(e) => updateOpacity(Number((e.target as HTMLInputElement).value), true)}
              style={{ width: '100%', accentColor: '#6366f1' }}
            />
          </div>
        )}
      </div>

      {/* AUDIO SECTION */}
      <div style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', overflow: 'hidden' }}>
        <div 
          onClick={() => toggleSection('audio')}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.04)', cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Volume2 size={13} /> Audio Settings
          </span>
          <button 
            onClick={(e) => { e.stopPropagation(); resetSection('audio'); }} 
            style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}
            title="Reset Audio"
          >
            <RotateCcw size={12} />
          </button>
        </div>
        {openSections.audio && (
          <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {/* Volume */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="editor-label">Volume ({(props.audio.volume * 100).toFixed(0)}%)</label>
                <button onClick={() => resetProperty('audio', 'volume')} style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}><RotateCcw size={10} /></button>
              </div>
              <input 
                type="range" 
                min="0" 
                max="2" 
                step="0.05"
                value={props.audio.volume}
                onChange={(e) => updateProp('audio', 'volume', Number(e.target.value), false)}
                onPointerUp={(e) => updateProp('audio', 'volume', Number((e.target as HTMLInputElement).value), true)}
                style={{ width: '100%', accentColor: '#6366f1' }}
              />
            </div>
            {/* Muted */}
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#cbd5e1', cursor: 'pointer', margin: '4px 0' }}>
              <input 
                type="checkbox" 
                checked={props.audio.muted}
                onChange={(e) => updateProp('audio', 'muted', e.target.checked, true)}
              />
              🔇 Mute Video Audio
            </label>
            {/* Fade In / Fade Out */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
              <div>
                <label className="editor-label">Fade In (s)</label>
                <input 
                  type="number" 
                  step="0.1"
                  min="0"
                  value={props.audio.fadeIn}
                  onChange={(e) => updateProp('audio', 'fadeIn', Number(e.target.value), true)}
                  className="editor-input"
                />
              </div>
              <div>
                <label className="editor-label">Fade Out (s)</label>
                <input 
                  type="number" 
                  step="0.1"
                  min="0"
                  value={props.audio.fadeOut}
                  onChange={(e) => updateProp('audio', 'fadeOut', Number(e.target.value), true)}
                  className="editor-input"
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* COLOR ADJUSTMENTS SECTION */}
      <div style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', overflow: 'hidden' }}>
        <div 
          onClick={() => toggleSection('color')}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.04)', cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Palette size={13} /> Color Adjustments
          </span>
          <button 
            onClick={(e) => { e.stopPropagation(); resetSection('color'); }} 
            style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}
            title="Reset Color Adjustments"
          >
            <RotateCcw size={12} />
          </button>
        </div>
        {openSections.color && (
          <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {/* Helper Slider Renderer */}
            {[
              { label: 'Brightness', field: 'brightness', min: -100, max: 100, step: 1 },
              { label: 'Contrast', field: 'contrast', min: -100, max: 100, step: 1 },
              { label: 'Saturation', field: 'saturation', min: -100, max: 100, step: 1 },
              { label: 'Exposure', field: 'exposure', min: -100, max: 100, step: 1 },
              { label: 'Gamma', field: 'gamma', min: 0.1, max: 5.0, step: 0.1 },
              { label: 'Hue', field: 'hue', min: -180, max: 180, step: 1 },
              { label: 'Temperature', field: 'temperature', min: -100, max: 100, step: 1 },
              { label: 'Tint', field: 'tint', min: -100, max: 100, step: 1 },
            ].map(({ label, field, min, max, step }) => {
              const val = (props.color as any)[field] ?? (field === 'gamma' ? 1.0 : 0);
              return (
                <div key={field} style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <label className="editor-label">{label} ({val > 0 && field !== 'gamma' ? `+${val}` : val})</label>
                    <button onClick={() => resetProperty('color', field)} style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}><RotateCcw size={10} /></button>
                  </div>
                  <input 
                    type="range" 
                    min={min} 
                    max={max} 
                    step={step}
                    value={val}
                    onChange={(e) => updateProp('color', field, Number(e.target.value), false)}
                    onPointerUp={(e) => updateProp('color', field, Number((e.target as HTMLInputElement).value), true)}
                    style={{ width: '100%', accentColor: '#6366f1' }}
                  />
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* FILTERS PRESETS */}
      <div style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', overflow: 'hidden' }}>
        <div 
          onClick={() => toggleSection('filter')}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.04)', cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Filter size={13} /> Filters
          </span>
          <button 
            onClick={(e) => { e.stopPropagation(); resetSection('filter'); }} 
            style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}
            title="Reset Filters"
          >
            <RotateCcw size={12} />
          </button>
        </div>
        {openSections.filter && (
          <div style={{ padding: '12px' }}>
            <label className="editor-label">Filter Preset</label>
            <select
              value={props.filter.preset}
              onChange={(e) => updateProp('filter', 'preset', e.target.value, true)}
              className="editor-input"
              style={{ marginTop: '4px' }}
            >
              <option value="none">None</option>
              <option value="warm">Warm</option>
              <option value="cool">Cool</option>
              <option value="cinematic">Cinematic</option>
              <option value="grayscale">Grayscale</option>
              <option value="vintage">Vintage</option>
              <option value="high-contrast">High Contrast</option>
              <option value="low-contrast">Low Contrast</option>
            </select>
          </div>
        )}
      </div>

      {/* PLAYBACK SPEED */}
      <div style={{ border: '1px solid rgba(255,255,255,0.08)', borderRadius: '6px', overflow: 'hidden' }}>
        <div 
          onClick={() => toggleSection('playback')}
          style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 12px', background: 'rgba(255,255,255,0.04)', cursor: 'pointer', userSelect: 'none' }}
        >
          <span style={{ fontSize: '12px', fontWeight: 600, color: '#f1f5f9', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Gauge size={13} /> Playback Speed
          </span>
          <button 
            onClick={(e) => { e.stopPropagation(); resetSection('playback'); }} 
            style={{ border: 'none', background: 'none', color: '#64748b', cursor: 'pointer' }}
            title="Reset Playback Speed"
          >
            <RotateCcw size={12} />
          </button>
        </div>
        {openSections.playback && (
          <div style={{ padding: '12px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <label className="editor-label">Speed ({props.playback.speed.toFixed(2)}x)</label>
            </div>
            <input 
              type="range" 
              min="0.25" 
              max="4.0" 
              step="0.05"
              value={props.playback.speed}
              onChange={(e) => updateProp('playback', 'speed', Number(e.target.value), false)}
              onPointerUp={(e) => updateProp('playback', 'speed', Number((e.target as HTMLInputElement).value), true)}
              style={{ width: '100%', accentColor: '#6366f1' }}
            />
          </div>
        )}
      </div>

      {/* RESET ALL PROPERTIES BUTTON */}
      <button
        onClick={resetAll}
        className="btn-secondary"
        style={{
          width: '100%',
          justifyContent: 'center',
          padding: '10px',
          fontSize: '12px',
          fontWeight: 700,
          color: '#f43f5e',
          borderColor: 'rgba(244, 63, 94, 0.2)',
          backgroundColor: 'rgba(244, 63, 94, 0.05)',
          borderRadius: '8px',
          cursor: 'pointer',
          marginTop: '8px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}
      >
        <RotateCcw size={14} />
        <span>RESET ALL PROPERTIES</span>
      </button>

    </div>
  );
};
