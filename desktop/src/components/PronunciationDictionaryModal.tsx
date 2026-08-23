import React, { useState } from 'react';
import { X, Plus, Trash2, BookOpen, Check, Download, Upload } from 'lucide-react';
import { DictionaryEntry } from '../services/pronunciationDictionary';

interface PronunciationDictionaryModalProps {
  isOpen: boolean;
  entries: DictionaryEntry[];
  onClose: () => void;
  onSave: (entries: DictionaryEntry[]) => void;
}

export const PronunciationDictionaryModal: React.FC<PronunciationDictionaryModalProps> = ({
  isOpen,
  entries,
  onClose,
  onSave
}) => {
  const [localEntries, setLocalEntries] = useState<DictionaryEntry[]>(entries);
  const [newWord, setNewWord] = useState('');
  const [newPronunciation, setNewPronunciation] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  if (!isOpen) return null;

  const handleAddEntry = () => {
    if (!newWord.trim() || !newPronunciation.trim()) return;
    const newEntry: DictionaryEntry = {
      id: `proj-${Date.now()}-${Math.random().toString(36).substring(7)}`,
      word: newWord.trim(),
      pronunciation: newPronunciation.trim(),
      language: 'vi',
      source: 'project',
      enabled: true
    };
    setLocalEntries([newEntry, ...localEntries]);
    setNewWord('');
    setNewPronunciation('');
  };

  const handleToggleEntry = (id: string) => {
    setLocalEntries(localEntries.map(e => e.id === id ? { ...e, enabled: !e.enabled } : e));
  };

  const handleDeleteEntry = (id: string) => {
    setLocalEntries(localEntries.filter(e => e.id !== id));
  };

  const handleSaveAll = () => {
    onSave(localEntries);
    onClose();
  };

  const filteredEntries = localEntries.filter(e =>
    e.word.toLowerCase().includes(searchQuery.toLowerCase()) ||
    e.pronunciation.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0, 0, 0, 0.75)',
      backdropFilter: 'blur(4px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999
    }}>
      <div style={{
        background: '#111318',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '12px',
        width: '650px',
        maxHeight: '85vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
      }}>
        {/* Header */}
        <div style={{
          padding: '16px 20px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <BookOpen size={20} color="#6366f1" />
            <div>
              <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#fff' }}>Từ Điển Phát Âm (Pronunciation Dictionary)</h3>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>Phiên âm danh từ riêng, từ tiếng Anh & chuẩn hóa cách đọc TTS tiếng Việt</span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        {/* Add Entry Bar */}
        <div style={{ padding: '16px 20px', background: '#0B0D10', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', display: 'flex', gap: '10px' }}>
          <input
            type="text"
            placeholder="Từ / Tên gốc (Ví dụ: Peppa)"
            value={newWord}
            onChange={e => setNewWord(e.target.value)}
            style={{ flex: 1, background: '#111318', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 12px', borderRadius: '6px', fontSize: '12px' }}
          />
          <input
            type="text"
            placeholder="Phiên âm đọc (Ví dụ: Bép-pa)"
            value={newPronunciation}
            onChange={e => setNewPronunciation(e.target.value)}
            style={{ flex: 1, background: '#111318', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 12px', borderRadius: '6px', fontSize: '12px' }}
          />
          <button className="btn-primary" onClick={handleAddEntry} style={{ padding: '6px 14px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Plus size={14} /> Thêm Từ
          </button>
        </div>

        {/* Entries Table */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '16px 20px' }}>
          <div style={{ display: 'grid', gridTemplateColumns: '40px 1fr 1fr 90px 60px', fontSize: '11px', color: '#64748b', fontWeight: 700, paddingBottom: '8px', borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
            <span>BẬT</span>
            <span>TỪ GỐC (WORD)</span>
            <span>PHIÊN ÂM (PRONUNCIATION)</span>
            <span>NGUỒN</span>
            <span>XÓA</span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', marginTop: '8px' }}>
            {filteredEntries.map(entry => (
              <div key={entry.id} style={{ display: 'grid', gridTemplateColumns: '40px 1fr 1fr 90px 60px', alignItems: 'center', padding: '8px', background: 'rgba(255,255,255,0.02)', borderRadius: '6px', fontSize: '12px' }}>
                <input
                  type="checkbox"
                  checked={entry.enabled}
                  onChange={() => handleToggleEntry(entry.id)}
                  style={{ cursor: 'pointer' }}
                />
                <span style={{ fontWeight: 600, color: '#fff' }}>{entry.word}</span>
                <span style={{ color: '#38bdf8', fontFamily: 'monospace' }}>{entry.pronunciation}</span>
                <span style={{ fontSize: '10px', color: entry.source === 'project' ? '#a855f7' : '#64748b', textTransform: 'uppercase', fontWeight: 700 }}>
                  {entry.source}
                </span>
                <button
                  onClick={() => handleDeleteEntry(entry.id)}
                  style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer' }}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0B0D10' }}>
          <span style={{ fontSize: '11px', color: '#64748b' }}>Tổng số {localEntries.length} từ phiên âm</span>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn-secondary" onClick={onClose} style={{ padding: '6px 14px', fontSize: '12px' }}>Đóng</button>
            <button className="btn-primary" onClick={handleSaveAll} style={{ padding: '6px 16px', fontSize: '12px' }}>Lưu Từ Điển</button>
          </div>
        </div>
      </div>
    </div>
  );
};
