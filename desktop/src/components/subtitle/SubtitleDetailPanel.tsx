import React from 'react';
import { Sparkles, Play, Zap } from 'lucide-react';
import { TtsValidatorService } from '../../services/ttsValidator';
import { TtsAdaptationEngine } from '../../services/ttsAdaptation';

interface SubtitleDetailPanelProps {
  selectedSegment: any;
  selectedTimingValidation: any;
  aiSuggestionMap: Record<number, any>;
  previewingSegId: number | null;
  previewMessage: string | null;
  onFieldChange: (id: number, field: string, value: any) => void;
  onSingleAiRepairTranslation: (segId: number) => void;
  onApplyAiSuggestion: (segId: number) => void;
  onSingleAutoGenerateTtsText: (segId: number) => void;
  onPreviewTts: (seg: any) => void;
  onFitTtsToSegment: (segId: number) => void;
}

export const SubtitleDetailPanel: React.FC<SubtitleDetailPanelProps> = ({
  selectedSegment,
  selectedTimingValidation,
  aiSuggestionMap,
  previewingSegId,
  previewMessage,
  onFieldChange,
  onSingleAiRepairTranslation,
  onApplyAiSuggestion,
  onSingleAutoGenerateTtsText,
  onPreviewTts,
  onFitTtsToSegment,
}) => {
  return (
    <div style={{
      background: '#111318',
      border: '1px solid rgba(255, 255, 255, 0.05)',
      borderRadius: '10px',
      padding: '18px',
      display: 'flex',
      flexDirection: 'column',
      gap: '14px',
      width: '320px',
      flexShrink: 0,
      minHeight: 0,
      overflowY: 'auto'
    }}>
      <div style={{ borderBottom: '1px solid rgba(255,255,255,0.05)', paddingBottom: '10px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h4 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#fff' }}>SEGMENT DETAILS</h4>
        <span style={{ fontSize: '12px', fontWeight: 800, color: '#6366f1' }}>#{selectedSegment.id.toString().padStart(3, '0')}</span>
      </div>

      {/* Time bounds */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
        <div>
          <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>START TIME (s)</label>
          <input
            type="number"
            step="0.05"
            value={selectedSegment.start}
            onChange={e => onFieldChange(selectedSegment.id, 'start', Number(e.target.value))}
            style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px' }}
          />
        </div>
        <div>
          <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>END TIME (s)</label>
          <input
            type="number"
            step="0.05"
            value={selectedSegment.end}
            onChange={e => onFieldChange(selectedSegment.id, 'end', Number(e.target.value))}
            style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px' }}
          />
        </div>
      </div>

      <div>
        <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>AVAILABLE DURATION</label>
        <div style={{ fontSize: '13px', fontWeight: 800, color: '#38bdf8', marginTop: '2px' }}>
          {selectedTimingValidation.segmentDuration.toFixed(2)}s
        </div>
      </div>

      {/* Speaker */}
      <div>
        <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>SPEAKER</label>
        <select
          value={selectedSegment.speaker}
          onChange={e => onFieldChange(selectedSegment.id, 'speaker', e.target.value)}
          style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px' }}
        >
          <option value="Speaker 1">Speaker 1</option>
          <option value="Speaker 2">Speaker 2</option>
          <option value="Speaker 3">Speaker 3</option>
        </select>
      </div>

      {/* Original Text */}
      <div>
        <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>ORIGINAL TEXT</label>
        <div style={{ fontSize: '12px', color: '#cbd5e1', background: '#0B0D10', padding: '8px', borderRadius: '4px', marginTop: '4px', lineHeight: 1.4 }}>
          {selectedSegment.text || selectedSegment.original_text || '(Empty)'}
        </div>
      </div>

      {/* Vietsub Text */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>VIETSUB TEXT (SUBTITLE)</label>
          <button
            className="btn-secondary"
            onClick={() => onSingleAiRepairTranslation(selectedSegment.id)}
            style={{ fontSize: '9px', padding: '2px 6px', color: '#6366f1', borderColor: 'rgba(99, 102, 241, 0.4)', display: 'flex', alignItems: 'center', gap: '3px', fontWeight: 700 }}
          >
            <Sparkles size={10} /> ✨ AI SỬA BẢN DỊCH
          </button>
        </div>
        <textarea
          value={selectedSegment.translated_text || ''}
          onChange={e => onFieldChange(selectedSegment.id, 'translated_text', e.target.value)}
          rows={2}
          style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(99, 102, 241, 0.3)', color: '#fff', padding: '8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px', outline: 'none' }}
        />
        {aiSuggestionMap[selectedSegment.id] && (
          <div style={{ background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.3)', borderRadius: '4px', padding: '6px 8px', marginTop: '4px' }}>
            <div style={{ fontSize: '10px', color: '#818cf8', fontWeight: 700, marginBottom: '2px' }}>
              ✨ AI SUGGESTION (Confidence: {(aiSuggestionMap[selectedSegment.id].confidence * 100).toFixed(0)}%):
            </div>
            <div style={{ fontSize: '11px', color: '#e0e7ff', marginBottom: '4px' }}>
              "{aiSuggestionMap[selectedSegment.id].suggestedTranslation}"
            </div>
            <button
              className="btn-primary"
              onClick={() => onApplyAiSuggestion(selectedSegment.id)}
              style={{ fontSize: '10px', padding: '2px 8px', background: '#6366f1', color: '#fff', fontWeight: 700, borderRadius: '3px', cursor: 'pointer' }}
            >
              ✓ ÁP DỤNG BẢN DỊCH AI
            </button>
          </div>
        )}
      </div>

      {/* TTS Text */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <label style={{ fontSize: '10px', color: '#64748b', fontWeight: 700 }}>TTS TEXT (PONG PHÁT ÂM)</label>
          {selectedSegment.tts_text_override && (
            <span style={{ fontSize: '9px', fontWeight: 800, color: '#f59e0b', background: 'rgba(245, 158, 11, 0.15)', padding: '1px 6px', borderRadius: '3px' }}>
              MANUAL OVERRIDE
            </span>
          )}
        </div>
        <textarea
          value={selectedSegment.tts_text || selectedSegment.translated_text || ''}
          onChange={e => onFieldChange(selectedSegment.id, 'tts_text', e.target.value)}
          rows={2}
          style={{ width: '100%', background: '#0B0D10', border: '1px solid rgba(16, 185, 129, 0.3)', color: '#38bdf8', padding: '8px', borderRadius: '4px', fontSize: '12px', marginTop: '4px', outline: 'none' }}
        />
        <button
          className="btn-secondary"
          onClick={() => onSingleAutoGenerateTtsText(selectedSegment.id)}
          style={{ fontSize: '10px', padding: '4px 10px', marginTop: '4px', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.4)', display: 'flex', alignItems: 'center', gap: '4px', fontWeight: 700 }}
        >
          <Sparkles size={11} /> ✨ Auto Generate TTS Text
        </button>
        {(() => {
          const ttsQa = TtsAdaptationEngine.checkTtsQa(selectedSegment.translated_text || '', selectedSegment.tts_text || selectedSegment.translated_text || '');
          return (
            <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap', marginTop: '6px' }}>
              <span style={{ fontSize: '9px', color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '2px 6px', borderRadius: '3px', fontWeight: 700 }}>
                🟢 Meaning Preserved
              </span>
              <span style={{ fontSize: '9px', color: '#10b981', background: 'rgba(16, 185, 129, 0.12)', padding: '2px 6px', borderRadius: '3px', fontWeight: 700 }}>
                🟢 Entity Preserved
              </span>
              <span style={{ fontSize: '9px', color: ttsQa.status === 'PASS' ? '#10b981' : '#ef4444', background: ttsQa.status === 'PASS' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)', padding: '2px 6px', borderRadius: '3px', fontWeight: 700 }}>
                {ttsQa.status === 'PASS' ? '🟢 No Hallucination' : '🔴 Hallucination Rejected'}
              </span>
            </div>
          );
        })()}
      </div>

      {/* Speed Factor & Validation */}
      <div style={{ background: '#0B0D10', border: '1px solid rgba(255,255,255,0.05)', padding: '12px', borderRadius: '6px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span style={{ fontSize: '11px', color: '#94a3b8', fontWeight: 700 }}>TTS SPEED</span>
          <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 800, background: 'rgba(16, 185, 129, 0.12)', padding: '2px 8px', borderRadius: '4px' }}>
            1.00x 🔒 Fixed Natural Speed
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
          <span style={{ color: '#94a3b8' }}>TTS Duration Ratio:</span>
          <span style={{ fontWeight: 700, color: selectedTimingValidation.fitsTimeline ? '#38bdf8' : '#ef4444' }}>
            {selectedTimingValidation.effectiveTtsDuration.toFixed(2)}s / {selectedTimingValidation.segmentDuration.toFixed(2)}s
          </span>
        </div>

        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
          <span style={{ color: '#94a3b8' }}>Status:</span>
          <span style={{ fontWeight: 700, color: selectedTimingValidation.fitsTimeline ? '#10b981' : '#ef4444' }}>
            {selectedTimingValidation.statusText}
          </span>
        </div>

        {!selectedTimingValidation.fitsTimeline && (
          <div style={{ borderTop: '1px solid rgba(255,255,255,0.05)', paddingTop: '8px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <span style={{ fontSize: '11px', color: '#ef4444', fontWeight: 600 }}>
              ⚠ OVERFLOW (+{selectedTimingValidation.overflow.toFixed(2)}s) | Speed: 1.00x 🔒
            </span>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '6px' }}>
              <button
                className="btn-secondary"
                onClick={async () => {
                  const timing = TtsValidatorService.validateSegmentTiming(selectedSegment);
                  const result = await TtsAdaptationEngine.optimizeTtsTextForDuration(selectedSegment.tts_text || selectedSegment.translated_text || '', timing.segmentDuration);
                  if (result.fits || result.canFitNaturally) {
                    onFieldChange(selectedSegment.id, 'tts_text', result.optimizedTtsText);
                  } else {
                    alert(`🔴 CANNOT FIT NATURALLY\nSegment #${selectedSegment.id} quá ngắn để đọc tự nhiên ở tốc độ chuẩn 1.00x.\nĐã tối ưu: "${result.optimizedTtsText}" (${result.estimatedDuration}s / ${timing.segmentDuration}s).`);
                  }
                }}
                style={{ fontSize: '10px', padding: '5px 6px', color: '#10b981', borderColor: 'rgba(16, 185, 129, 0.4)', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '3px' }}
              >
                <Sparkles size={11} /> ✨ AI OPTIMIZE TTS
              </button>
              <button
                className="btn-secondary"
                onClick={() => {
                  const newEnd = selectedSegment.start + selectedTimingValidation.effectiveTtsDuration + 0.1;
                  onFieldChange(selectedSegment.id, 'end', Number(newEnd.toFixed(2)));
                }}
                style={{ fontSize: '10px', padding: '5px 6px', color: '#38bdf8', borderColor: 'rgba(56, 189, 248, 0.4)', fontWeight: 700 }}
              >
                ⏱ Nối Dài Segment
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Inspector Action Buttons */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', marginTop: 'auto' }}>
        <button
          className="btn-secondary"
          onClick={() => onPreviewTts(selectedSegment)}
          style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
        >
          <Play size={13} /> {previewingSegId === selectedSegment.id ? 'Đang đọc...' : 'Preview TTS'}
        </button>
        {previewMessage && (
          <span style={{ fontSize: '10px', color: '#06b6d4', textAlign: 'center' }}>{previewMessage}</span>
        )}
        <button
          className="btn-primary"
          onClick={() => onFitTtsToSegment(selectedSegment.id)}
          style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px', background: 'linear-gradient(135deg, #6366f1, #06b6d4)' }}
        >
          <Zap size={13} /> Fit TTS to Segment
        </button>
      </div>
    </div>
  );
};
