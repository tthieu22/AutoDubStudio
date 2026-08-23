import React, { useState } from 'react';
import { X, Save, FileEdit, Search } from 'lucide-react';

interface BulkVietsubModalProps {
  isOpen: boolean;
  segments: any[];
  onClose: () => void;
  onSave: (updatedSegments: any[]) => void;
}

export const BulkVietsubModal: React.FC<BulkVietsubModalProps> = ({
  isOpen,
  segments,
  onClose,
  onSave
}) => {
  const [localSegments, setLocalSegments] = useState<any[]>(JSON.parse(JSON.stringify(segments)));
  const [searchQuery, setSearchQuery] = useState('');

  if (!isOpen) return null;

  const handleFieldChange = (id: number, field: string, value: string) => {
    setLocalSegments(prev => prev.map(s => {
      if (s.id === id) {
        const updated = { ...s, [field]: value };
        if (field === 'translated_text' && !s.tts_text_override) {
          // Keep tts_text in sync unless manual override
          updated.tts_text = value;
        }
        if (!updated.dirty) updated.dirty = {};
        updated.dirty.translation = true;
        if (!updated.tts) updated.tts = {};
        updated.tts.status = 'NEEDS_REGENERATION';
        return updated;
      }
      return s;
    }));
  };

  const handleSave = () => {
    onSave(localSegments);
    onClose();
  };

  const filteredSegments = localSegments.filter(s =>
    (s.text || s.original_text || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (s.translated_text || '').toLowerCase().includes(searchQuery.toLowerCase()) ||
    (s.tts_text || '').toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.8)',
      backdropFilter: 'blur(5px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999
    }}>
      <div style={{
        background: '#111318',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '12px',
        width: '90vw',
        maxWidth: '1200px',
        height: '85vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <FileEdit size={20} color="#10b981" />
            <div>
              <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#fff' }}>Chỉnh Sửa Toàn Bộ Transcript (Bulk Edit Vietsub & TTS Text)</h3>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>Xem và sửa trực tiếp danh sách tất cả câu thoại trước khi chạy TTS</span>
            </div>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ position: 'relative', width: '250px' }}>
              <Search size={14} style={{ position: 'absolute', left: '10px', top: '9px', color: '#64748b' }} />
              <input
                type="text"
                placeholder="Tìm kiếm segment..."
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0B0D10',
                  border: '1px solid rgba(255, 255, 255, 0.1)',
                  borderRadius: '6px',
                  padding: '6px 10px 6px 28px',
                  color: '#fff',
                  fontSize: '12px',
                  outline: 'none'
                }}
              />
            </div>
            <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content List */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '80px 1fr 1fr 1fr', fontSize: '11px', color: '#64748b', fontWeight: 700, paddingBottom: '10px', borderBottom: '1px solid rgba(255,255,255,0.05)', marginBottom: '10px' }}>
            <span>SEGMENT</span>
            <span>ORIGINAL TEXT (GỐC)</span>
            <span>VIETSUB TEXT (HIỂN THỊ)</span>
            <span>TTS TEXT (ĐỌC TTS)</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {filteredSegments.map(seg => (
              <div key={seg.id} style={{ display: 'grid', gridTemplateColumns: '80px 1fr 1fr 1fr', gap: '12px', alignItems: 'start', padding: '12px', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.05)', borderRadius: '8px' }}>
                <div>
                  <span style={{ fontSize: '12px', fontWeight: 700, color: '#6366f1' }}>#{seg.id.toString().padStart(3, '0')}</span>
                  <div style={{ fontSize: '10px', color: '#64748b', fontFamily: 'monospace', marginTop: '2px' }}>
                    {Number(seg.start || 0).toFixed(2)}s - {Number(seg.end || 0).toFixed(2)}s
                  </div>
                </div>

                <div style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: 1.5, background: '#0B0D10', padding: '8px', borderRadius: '4px', border: '1px solid rgba(255,255,255,0.03)' }}>
                  {seg.text || seg.original_text || '(Rỗng)'}
                </div>

                <textarea
                  value={seg.translated_text || ''}
                  onChange={e => handleFieldChange(seg.id, 'translated_text', e.target.value)}
                  placeholder="Nhập Vietsub..."
                  rows={2}
                  style={{
                    width: '100%',
                    background: '#0B0D10',
                    border: '1px solid rgba(99, 102, 241, 0.2)',
                    borderRadius: '4px',
                    color: '#fff',
                    padding: '8px',
                    fontSize: '12px',
                    resize: 'vertical',
                    outline: 'none'
                  }}
                />

                <textarea
                  value={seg.tts_text || seg.translated_text || ''}
                  onChange={e => {
                    seg.tts_text_override = true;
                    handleFieldChange(seg.id, 'tts_text', e.target.value);
                  }}
                  placeholder="Nhập văn bản đọc TTS..."
                  rows={2}
                  style={{
                    width: '100%',
                    background: '#0B0D10',
                    border: '1px solid rgba(16, 185, 129, 0.2)',
                    borderRadius: '4px',
                    color: '#38bdf8',
                    padding: '8px',
                    fontSize: '12px',
                    resize: 'vertical',
                    outline: 'none'
                  }}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ padding: '16px 24px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0B0D10' }}>
          <span style={{ fontSize: '12px', color: '#94a3b8' }}>Hiển thị {filteredSegments.length} / {localSegments.length} câu thoại</span>
          <div style={{ display: 'flex', gap: '12px' }}>
            <button className="btn-secondary" onClick={onClose} style={{ padding: '8px 16px', fontSize: '12px' }}>Hủy Bỏ</button>
            <button className="btn-primary" onClick={handleSave} style={{ padding: '8px 20px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Save size={14} /> Lưu Tất Cả Thay Đổi
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
