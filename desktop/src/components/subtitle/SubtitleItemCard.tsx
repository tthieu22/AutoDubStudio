import React from 'react';
import { TtsValidatorService } from '../../services/ttsValidator';

interface SubtitleItemCardProps {
  seg: any;
  isSelected: boolean;
  isBatchSelected: boolean;
  onSelectSegment: (id: number) => void;
  onToggleRowSelect: (id: number, e: React.MouseEvent) => void;
  onFieldChange: (id: number, field: string, value: any) => void;
}

export const SubtitleItemCard: React.FC<SubtitleItemCardProps> = ({
  seg,
  isSelected,
  isBatchSelected,
  onSelectSegment,
  onToggleRowSelect,
  onFieldChange,
}) => {
  const timingVal = TtsValidatorService.validateSegmentTiming(seg);

  return (
    <div
      onClick={() => onSelectSegment(seg.id)}
      style={{
        display: 'grid',
        gridTemplateColumns: '30px 70px 100px 70px 1fr 1fr 1fr 60px 110px',
        alignItems: 'center',
        padding: '8px',
        borderRadius: '6px',
        background: isSelected ? 'rgba(99, 102, 241, 0.12)' : (isBatchSelected ? 'rgba(99, 102, 241, 0.05)' : 'transparent'),
        border: '1px solid',
        borderColor: isSelected ? '#6366f1' : (timingVal.fitsTimeline ? 'transparent' : 'rgba(239, 68, 68, 0.3)'),
        cursor: 'pointer',
        transition: 'all 0.15s ease',
        gap: '8px'
      }}
    >
      <input
        type="checkbox"
        checked={isBatchSelected}
        onClick={(e) => onToggleRowSelect(seg.id, e)}
        onChange={() => { }}
        style={{ cursor: 'pointer' }}
      />

      <span style={{ fontSize: '11px', fontWeight: 700, color: isSelected ? '#6366f1' : '#94a3b8' }}>
        #{seg.id.toString().padStart(3, '0')}
      </span>

      <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#cbd5e1' }}>
        {Number(seg.start).toFixed(2)}s - {Number(seg.end).toFixed(2)}s
      </span>

      <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8' }}>
        {timingVal.segmentDuration.toFixed(2)}s
      </span>

      <div style={{ fontSize: '12px', color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
        {seg.text || seg.original_text || '(Rỗng)'}
      </div>

      <input
        type="text"
        value={seg.translated_text || ''}
        onChange={(e) => onFieldChange(seg.id, 'translated_text', e.target.value)}
        style={{
          background: isSelected ? '#0B0D10' : 'rgba(255,255,255,0.02)',
          border: '1px solid rgba(255,255,255,0.05)',
          color: '#fff',
          padding: '4px 8px',
          borderRadius: '4px',
          fontSize: '12px',
          outline: 'none',
          width: '100%'
        }}
        placeholder="Vietsub..."
      />

      <div style={{ position: 'relative', width: '100%' }}>
        <input
          type="text"
          value={seg.tts_text || seg.translated_text || ''}
          onChange={(e) => onFieldChange(seg.id, 'tts_text', e.target.value)}
          style={{
            background: isSelected ? '#0B0D10' : 'rgba(255,255,255,0.02)',
            border: '1px solid rgba(16,185,129,0.2)',
            color: '#38bdf8',
            padding: '4px 8px',
            paddingRight: seg.tts_text_override ? '50px' : '8px',
            borderRadius: '4px',
            fontSize: '12px',
            outline: 'none',
            width: '100%'
          }}
          placeholder="TTS Text..."
        />
        {seg.tts_text_override && (
          <span style={{ position: 'absolute', right: '4px', top: '5px', fontSize: '9px', fontWeight: 800, color: '#f59e0b', background: 'rgba(245, 158, 11, 0.15)', padding: '1px 4px', borderRadius: '3px' }}>
            MANUAL
          </span>
        )}
      </div>

      <span style={{ fontSize: '11px', fontWeight: 700, color: '#f59e0b', textAlign: 'center' }}>
        {Number(seg.speed || 1.0).toFixed(2)}x
      </span>

      <div>
        {!timingVal.fitsTimeline ? (
          <span style={{ color: '#ef4444', fontSize: '10px', fontWeight: 700 }}>⚠ Overflow (+{timingVal.overflow}s)</span>
        ) : seg.tts?.status === 'NEEDS_REGENERATION' ? (
          <span style={{ color: '#f59e0b', fontSize: '10px', fontWeight: 700 }}>⚠ Needs Regen</span>
        ) : seg.translated_text ? (
          <span style={{ color: '#10b981', fontSize: '10px', fontWeight: 700 }}>✓ Ready</span>
        ) : (
          <span style={{ color: '#64748b', fontSize: '10px', fontWeight: 700 }}>Not Generated</span>
        )}
      </div>
    </div>
  );
};
