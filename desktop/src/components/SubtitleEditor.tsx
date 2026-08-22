import React, { useState, useEffect } from 'react';
import { Play, Pause, Save, RotateCcw, Clock, User, Volume2, Sparkles, AlertCircle } from 'lucide-react';
import { PythonEngineService } from '../services/pythonEngine';
import { editorStore } from '../editor/state/editorStore';

interface SubtitleEditorProps {
  projectDir: string;
}

export const SubtitleEditor: React.FC<SubtitleEditorProps> = ({ projectDir }) => {
  const [subtitles, setSubtitles] = useState<any[]>([]);
  const [selectedSegId, setSelectedSegId] = useState<number | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [hasChanges, setHasChanges] = useState(false);

  useEffect(() => {
    loadSubtitles();
  }, [projectDir]);

  const loadSubtitles = async () => {
    try {
      const data = await PythonEngineService.readSubtitles(projectDir);
      setSubtitles(data);
      if (data.length > 0) setSelectedSegId(data[0].id);
      setHasChanges(false);
    } catch (err) {
      console.error('Failed to load subtitles:', err);
    }
  };

  const handleFieldChange = (id: number, field: string, value: any) => {
    const updated = subtitles.map(s => {
      if (s.id === id) {
        return { ...s, [field]: value };
      }
      return s;
    });
    setSubtitles(updated);
    setHasChanges(true);

    // Sync directly to timeline subtitle clip
    const currentComp = editorStore.getComposition();
    const clipId = `clip-sub-${id}`;
    const targetClip = currentComp.clips.find(c => c.id === clipId);
    if (targetClip) {
      if (field === 'translated_text' || field === 'text') {
        editorStore.updateClip(clipId, {
          name: `Sub #${id}: ${(value || '').substring(0, 16)}...`,
          subtitleProps: { ...targetClip.subtitleProps, text: value }
        });
      } else if (field === 'start') {
        editorStore.updateClip(clipId, { startTime: Number(value) });
      } else if (field === 'end') {
        editorStore.updateClip(clipId, { duration: Math.max(0.2, Number(value) - targetClip.startTime) });
      }
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await PythonEngineService.writeSubtitles(projectDir, subtitles);
      setHasChanges(false);
    } catch (err) {
      alert(`Lưu thất bại: ${err}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
      {/* TOOLBAR */}
      <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Sparkles color="#38bdf8" size={20} />
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#fff' }}>INTERACTIVE SUBTITLE & TRANSCRIPT EDITOR</h3>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Sửa nội dung thoại, điều chỉnh timestamp & tốc độ đọc trước khi chạy TTS</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-secondary" onClick={loadSubtitles} disabled={isSaving}>
            <RotateCcw size={14} /> Khôi Phục
          </button>
          <button className="btn-primary" onClick={handleSave} disabled={isSaving || !hasChanges}>
            <Save size={15} /> {isSaving ? 'Đang lưu...' : 'Lưu Phụ Đề (Save)'}
          </button>
        </div>
      </div>

      {/* MAIN CONTAINER: SEGMENTS LIST & DETAILS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '20px', flexGrow: 1, minHeight: 0 }}>
        {/* SEGMENTS TABLE / LIST */}
        <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px', overflowY: 'auto' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#94a3b8', fontWeight: 600, borderBottom: '1px solid var(--border-glass)', paddingBottom: '8px' }}>
            <span>SEGMENT ({subtitles.length})</span>
            <span>TIME BOUNDS</span>
          </div>

          {subtitles.map(seg => {
            const isSelected = selectedSegId === seg.id;
            const duration = (seg.end - seg.start).toFixed(2);
            return (
              <div
                key={seg.id}
                onClick={() => setSelectedSegId(seg.id)}
                style={{
                  padding: '12px',
                  borderRadius: '8px',
                  background: isSelected ? 'rgba(99, 102, 241, 0.15)' : 'rgba(15, 23, 42, 0.4)',
                  border: isSelected ? '1px solid var(--primary)' : '1px solid rgba(255, 255, 255, 0.05)',
                  cursor: 'pointer',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '8px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span className="badge badge-completed" style={{ fontSize: '11px' }}>
                    #{seg.id} • {seg.speaker || 'Speaker 1'}
                  </span>
                  <span style={{ fontSize: '11px', color: '#38bdf8', fontFamily: 'monospace' }}>
                    {seg.start.toFixed(2)}s ➔ {seg.end.toFixed(2)}s ({duration}s)
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
                  <span style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic' }}>
                    En: {seg.text || seg.original_text || '(Gốc)'}
                  </span>
                  <input
                    type="text"
                    value={seg.translated_text || ''}
                    onChange={(e) => handleFieldChange(seg.id, 'translated_text', e.target.value)}
                    style={{
                      width: '100%',
                      background: 'rgba(2, 6, 23, 0.8)',
                      border: '1px solid var(--border-glass)',
                      color: '#fff',
                      padding: '8px 10px',
                      borderRadius: '6px',
                      fontSize: '13px',
                      fontWeight: 600
                    }}
                    placeholder="Nhập bản dịch tiếng Việt..."
                  />
                </div>
              </div>
            );
          })}
        </div>

        {/* SIDE INSPECTOR FOR SELECTED SEGMENT */}
        <div className="glass-card" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
          <h4 style={{ margin: 0, fontSize: '15px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={16} color="#38bdf8" /> CHI TIẾT THÔNG SỐ SEGMENT #{selectedSegId || '-'}
          </h4>

          {selectedSegId ? (() => {
            const activeSeg = subtitles.find(s => s.id === selectedSegId) || {};
            return (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>GIỜ BẮT ĐẦU (START TIME SEC)</label>
                  <input
                    type="number"
                    step="0.05"
                    value={activeSeg.start || 0}
                    onChange={(e) => handleFieldChange(activeSeg.id, 'start', parseFloat(e.target.value))}
                    style={{ width: '100%', background: '#0f172a', border: '1px solid var(--border-glass)', color: '#fff', padding: '8px', borderRadius: '6px' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>GIỜ KẾT THÚC (END TIME SEC)</label>
                  <input
                    type="number"
                    step="0.05"
                    value={activeSeg.end || 0}
                    onChange={(e) => handleFieldChange(activeSeg.id, 'end', parseFloat(e.target.value))}
                    style={{ width: '100%', background: '#0f172a', border: '1px solid var(--border-glass)', color: '#fff', padding: '8px', borderRadius: '6px' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>NGƯỜI NÓI (SPEAKER TAG)</label>
                  <input
                    type="text"
                    value={activeSeg.speaker || 'Speaker 1'}
                    onChange={(e) => handleFieldChange(activeSeg.id, 'speaker', e.target.value)}
                    style={{ width: '100%', background: '#0f172a', border: '1px solid var(--border-glass)', color: '#fff', padding: '8px', borderRadius: '6px' }}
                  />
                </div>

                <div>
                  <label style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginBottom: '4px' }}>TỐC ĐỘ ĐỌC MONG MUỐN (SPEED FACTOR)</label>
                  <select
                    value={activeSeg.speed || 1.0}
                    onChange={(e) => handleFieldChange(activeSeg.id, 'speed', parseFloat(e.target.value))}
                    style={{ width: '100%', background: '#0f172a', border: '1px solid var(--border-glass)', color: '#fff', padding: '8px', borderRadius: '6px' }}
                  >
                    <option value={0.90}>0.90x (Đọc chậm tự nhiên)</option>
                    <option value={0.95}>0.95x (Thuyết minh tiêu chuẩn)</option>
                    <option value={1.00}>1.00x (Tốc độ mặc định)</option>
                    <option value={1.05}>1.05x (Đọc nhanh tự nhiên)</option>
                    <option value={1.10}>1.10x (Đọc rất nhanh)</option>
                  </select>
                </div>
              </div>
            );
          })() : (
            <span style={{ fontSize: '13px', color: '#64748b' }}>Chọn một câu trong danh sách để điều chỉnh</span>
          )}
        </div>
      </div>
    </div>
  );
};
