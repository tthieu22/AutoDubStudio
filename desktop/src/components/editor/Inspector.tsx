import React, { useState } from 'react';
import { CompositionState, TimelineClip } from '../../editor/state/types';
import { editorStore } from '../../editor/state/editorStore';
import { PythonEngineService } from '../../services/pythonEngine';
import { Sliders, Eye, EyeOff, Lock, Unlock, Zap, Volume2, Check, RefreshCw } from 'lucide-react';

interface InspectorProps {
  composition: CompositionState;
  selectedClipIds: string[];
}

export const Inspector: React.FC<InspectorProps> = ({ composition, selectedClipIds }) => {
  const [isGeneratingVoice, setIsGeneratingVoice] = useState(false);
  const [voiceSuccess, setVoiceSuccess] = useState(false);

  if (selectedClipIds.length === 0) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', padding: '24px', textAlign: 'center', color: '#64748b' }}>
        <Sliders size={32} style={{ marginBottom: '8px', opacity: 0.5 }} />
        <p style={{ fontSize: '12px', margin: 0, lineHeight: 1.4 }}>
          Chọn một Layer hoặc Clip trên Canvas/Timeline để chỉnh sửa thuộc tính.
        </p>
      </div>
    );
  }

  const selectedClip = composition.clips.find((c) => c.id === selectedClipIds[0]);
  if (!selectedClip) return null;

  const handleGenerateSegmentVoice = async () => {
    if (!selectedClip.subtitleProps) return;
    setIsGeneratingVoice(true);
    setVoiceSuccess(false);

    try {
      const segId = selectedClip.id.replace('clip-sub-', '');
      await PythonEngineService.synthesizeSegmentVoice(
        composition.id || 'active-project',
        segId,
        selectedClip.subtitleProps.text || '',
        'vi_VN-vais1000-medium'
      );
      setVoiceSuccess(true);
      setTimeout(() => setVoiceSuccess(false), 3000);
    } catch (err) {
      alert(`Lỗi tạo giọng: ${err}`);
    } finally {
      setIsGeneratingVoice(false);
    }
  };

  return (
    <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px', overflowY: 'auto' }}>
      {/* HEADER */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '10px' }}>
        <span style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#f1f5f9' }}>
          {selectedClip.type} Properties
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
          <button
            onClick={() => editorStore.updateClip(selectedClip.id, { visible: !selectedClip.visible }, true)}
            className="editor-nav-btn"
            style={{ width: '26px', height: '26px' }}
            title={selectedClip.visible ? 'Ẩn layer' : 'Hiện layer'}
          >
            {selectedClip.visible ? <Eye size={14} /> : <EyeOff size={14} color="#f43f5e" />}
          </button>
          <button
            onClick={() => editorStore.updateClip(selectedClip.id, { locked: !selectedClip.locked }, true)}
            className="editor-nav-btn"
            style={{ width: '26px', height: '26px' }}
            title={selectedClip.locked ? 'Mở khóa' : 'Khóa'}
          >
            {selectedClip.locked ? <Lock size={14} color="#f59e0b" /> : <Unlock size={14} />}
          </button>
        </div>
      </div>

      {/* SUBTITLE CONTENT & SEGMENT-LEVEL PROCESSING */}
      {selectedClip.type === 'subtitle' && selectedClip.subtitleProps && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label className="editor-label">Câu Phụ Đề (Editable Subtitle)</label>
            <textarea
              value={selectedClip.subtitleProps.text}
              onChange={(e) => {
                editorStore.updateClip(selectedClip.id, {
                  name: `Sub: ${e.target.value.substring(0, 16)}...`,
                  subtitleProps: { ...selectedClip.subtitleProps, text: e.target.value },
                });
              }}
              rows={3}
              className="editor-input"
              style={{ resize: 'none', lineHeight: 1.4 }}
            />
          </div>

          {/* SEGMENT TTS GENERATION ACTION */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', backgroundColor: 'rgba(99, 102, 241, 0.1)', padding: '10px', borderRadius: '8px', border: '1px solid rgba(99, 102, 241, 0.25)' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#818cf8', display: 'flex', alignItems: 'center', gap: '4px' }}>
                <Volume2 size={13} /> Segment-Level TTS
              </span>
              {voiceSuccess && <span style={{ fontSize: '10px', color: '#10b981', fontWeight: 600 }}>✓ Voice Updated</span>}
            </div>

            <button
              onClick={handleGenerateSegmentVoice}
              disabled={isGeneratingVoice}
              className="btn-primary"
              style={{ width: '100%', justifyContent: 'center', padding: '6px', fontSize: '11px', gap: '6px' }}
            >
              {isGeneratingVoice ? <RefreshCw size={12} className="animate-spin" /> : <Zap size={12} />}
              <span>{isGeneratingVoice ? 'Đang tạo lại Voice...' : '🔊 Tạo lại Voice cho câu này'}</span>
            </button>
          </div>

          {/* FONT & STYLING */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <div>
              <label className="editor-label">Font Chữ</label>
              <select
                value={selectedClip.subtitleProps.fontFamily}
                onChange={(e) => {
                  editorStore.updateClip(selectedClip.id, {
                    subtitleProps: { ...selectedClip.subtitleProps, fontFamily: e.target.value },
                  });
                }}
                className="editor-input"
              >
                <option value="Plus Jakarta Sans">Plus Jakarta Sans</option>
                <option value="Outfit">Outfit</option>
                <option value="Roboto">Roboto</option>
                <option value="Inter">Inter</option>
              </select>
            </div>

            <div>
              <label className="editor-label">Cỡ Chữ (px)</label>
              <input
                type="number"
                value={selectedClip.subtitleProps.fontSize}
                onChange={(e) => {
                  editorStore.updateClip(selectedClip.id, {
                    subtitleProps: { ...selectedClip.subtitleProps, fontSize: Number(e.target.value) },
                  });
                }}
                className="editor-input"
              />
            </div>
          </div>

          <div>
            <label className="editor-label">Màu Sắc</label>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <input
                type="color"
                value={selectedClip.subtitleProps.color}
                onChange={(e) => {
                  editorStore.updateClip(selectedClip.id, {
                    subtitleProps: { ...selectedClip.subtitleProps, color: e.target.value },
                  });
                }}
                style={{ width: '32px', height: '32px', border: 'none', background: 'transparent', cursor: 'pointer' }}
              />
              <span style={{ fontSize: '11px', fontFamily: 'monospace', color: '#94a3b8' }}>
                {selectedClip.subtitleProps.color}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* TEXT CONTENT INSPECTOR */}
      {selectedClip.type === 'text' && selectedClip.textProps && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div>
            <label className="editor-label">Nội Dung Văn Bản</label>
            <textarea
              value={selectedClip.textProps.content}
              onChange={(e) => {
                editorStore.updateClip(selectedClip.id, {
                  textProps: { ...selectedClip.textProps, content: e.target.value },
                });
              }}
              rows={2}
              className="editor-input"
              style={{ resize: 'none' }}
            />
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
            <div>
              <label className="editor-label">Font Chữ</label>
              <select
                value={selectedClip.textProps.fontFamily}
                onChange={(e) => {
                  editorStore.updateClip(selectedClip.id, {
                    textProps: { ...selectedClip.textProps, fontFamily: e.target.value },
                  });
                }}
                className="editor-input"
              >
                <option value="Outfit">Outfit</option>
                <option value="Plus Jakarta Sans">Plus Jakarta Sans</option>
                <option value="Roboto">Roboto</option>
                <option value="Inter">Inter</option>
              </select>
            </div>

            <div>
              <label className="editor-label">Cỡ Chữ (px)</label>
              <input
                type="number"
                value={selectedClip.textProps.fontSize}
                onChange={(e) => {
                  editorStore.updateClip(selectedClip.id, {
                    textProps: { ...selectedClip.textProps, fontSize: Number(e.target.value) },
                  });
                }}
                className="editor-input"
              />
            </div>
          </div>
        </div>
      )}

      {/* TRANSFORM & POSITION CONTROLS */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', paddingTop: '10px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
        <span style={{ fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#94a3b8' }}>
          Transform & Timestamps
        </span>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <div>
            <label className="editor-label">Vị trí X (%)</label>
            <input
              type="number"
              value={selectedClip.x}
              onChange={(e) => editorStore.updateClip(selectedClip.id, { x: Number(e.target.value) })}
              className="editor-input"
            />
          </div>
          <div>
            <label className="editor-label">Vị trí Y (%)</label>
            <input
              type="number"
              value={selectedClip.y}
              onChange={(e) => editorStore.updateClip(selectedClip.id, { y: Number(e.target.value) })}
              className="editor-input"
            />
          </div>
          <div>
            <label className="editor-label">Bắt đầu (s)</label>
            <input
              type="number"
              step="0.1"
              value={selectedClip.startTime}
              onChange={(e) => editorStore.updateClip(selectedClip.id, { startTime: Number(e.target.value) })}
              className="editor-input"
            />
          </div>
          <div>
            <label className="editor-label">Thời lượng (s)</label>
            <input
              type="number"
              step="0.1"
              value={selectedClip.duration}
              onChange={(e) => editorStore.updateClip(selectedClip.id, { duration: Number(e.target.value) })}
              className="editor-input"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
