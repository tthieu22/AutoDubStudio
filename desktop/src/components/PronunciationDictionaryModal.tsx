import React, { useState } from 'react';
import { X, Plus, Trash2, BookOpen, Sparkles, Loader2, Zap, Check } from 'lucide-react';
import { DictionaryEntry, PronunciationDictionaryService } from '../services/pronunciationDictionary';

interface PronunciationDictionaryModalProps {
  isOpen: boolean;
  entries: DictionaryEntry[];
  subtitles?: any[];
  onClose: () => void;
  onSave: (entries: DictionaryEntry[]) => void;
  onApplyToSubtitles?: (updatedEntries: DictionaryEntry[], targetMode: 'tts' | 'both') => void;
}

export const PronunciationDictionaryModal: React.FC<PronunciationDictionaryModalProps> = ({
  isOpen,
  entries,
  subtitles = [],
  onClose,
  onSave,
  onApplyToSubtitles
}) => {
  const [localEntries, setLocalEntries] = useState<DictionaryEntry[]>(entries);
  const [newWord, setNewWord] = useState('');
  const [newPronunciation, setNewPronunciation] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAiScanning, setIsAiScanning] = useState(false);
  const [aiStatusMessage, setAiStatusMessage] = useState<string | null>(null);
  const [appliedNotice, setAppliedNotice] = useState<string | null>(null);

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

  const handleAiScan = async () => {
    if (subtitles.length === 0) {
      setAiStatusMessage('Không tìm thấy phụ đề nào trong dự án để quét.');
      return;
    }

    setIsAiScanning(true);
    setAiStatusMessage('Đang quét từ tiếng Anh & tên riêng trong phụ đề...');

    try {
      const foreignWords = PronunciationDictionaryService.extractForeignWords(subtitles, localEntries);

      if (foreignWords.length === 0) {
        setAiStatusMessage('✓ Tất cả từ tiếng Anh / tên riêng đã có trong từ điển.');
        setIsAiScanning(false);
        return;
      }

      setAiStatusMessage(`AI (Qwen 2.5) đang sinh phiên âm tiếng Việt cho ${foreignWords.length} từ: ${foreignWords.slice(0, 4).join(', ')}...`);

      const aiPhonetics = await PronunciationDictionaryService.generatePhoneticsWithAi(foreignWords);
      const newEntriesToAdd: DictionaryEntry[] = [];

      Object.entries(aiPhonetics).forEach(([word, pron]) => {
        if (!localEntries.some(e => e.word.toLowerCase() === word.toLowerCase())) {
          newEntriesToAdd.push({
            id: `ai-${Date.now()}-${Math.random().toString(36).substring(7)}`,
            word,
            pronunciation: pron,
            language: 'vi',
            source: 'project',
            enabled: true
          });
        }
      });

      if (newEntriesToAdd.length > 0) {
        const merged = [...newEntriesToAdd, ...localEntries];
        setLocalEntries(merged);
        setAiStatusMessage(`✓ Đã thêm thành công ${newEntriesToAdd.length} từ phiên âm mới từ AI!`);
      } else {
        setAiStatusMessage('✓ Không có từ mới cần thêm.');
      }
    } catch (err) {
      setAiStatusMessage('Lỗi khi AI quét từ điển. Đã dùng bộ quy tắc dự phòng.');
    } finally {
      setIsAiScanning(false);
    }
  };

  const handleApplyBulk = (targetMode: 'tts' | 'both') => {
    onSave(localEntries);
    if (onApplyToSubtitles) {
      onApplyToSubtitles(localEntries, targetMode);
      setAppliedNotice(`✓ Đã áp dụng thay thế vào ${targetMode === 'both' ? 'VIETSUB & TTS TEXT' : 'TTS TEXT'} của ${subtitles.length} phụ đề!`);
      setTimeout(() => {
        setAppliedNotice(null);
        onClose();
      }, 1200);
    } else {
      onClose();
    }
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
        width: '720px',
        maxHeight: '88vh',
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
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>Phiên âm tiếng Anh, tên riêng & chuẩn hóa giọng đọc TTS tiếng Việt</span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        {/* AI Auto Scanner Banner */}
        <div style={{
          padding: '12px 20px',
          background: 'linear-gradient(90deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%)',
          borderBottom: '1px solid rgba(99, 102, 241, 0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} color="#c084fc" />
            <div>
              <div style={{ fontSize: '12px', fontWeight: 700, color: '#e9d5ff' }}>Tự Động Quét & Sinh Từ Điển Với AI (Qwen 2.5)</div>
              <div style={{ fontSize: '11px', color: '#cbd5e1' }}>
                {aiStatusMessage || `Tự động quét ${subtitles.length} phụ đề tìm các từ tiếng Anh / Tên riêng chưa có và sinh phiên âm chuẩn.`}
              </div>
            </div>
          </div>

          <button
            onClick={handleAiScan}
            disabled={isAiScanning}
            style={{
              padding: '6px 14px',
              fontSize: '12px',
              fontWeight: 700,
              background: isAiScanning ? '#475569' : 'linear-gradient(135deg, #6366f1 0%, #a855f7 100%)',
              color: '#fff',
              border: 'none',
              borderRadius: '6px',
              cursor: isAiScanning ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              flexShrink: 0
            }}
          >
            {isAiScanning ? <Loader2 size={13} className="spin" /> : <Sparkles size={13} />}
            {isAiScanning ? 'Đang Quét AI...' : 'Tự Động Quét AI'}
          </button>
        </div>

        {/* Search & Manual Add Bar */}
        <div style={{ padding: '12px 20px', background: '#0B0D10', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', display: 'flex', gap: '8px', alignItems: 'center' }}>
          <input
            type="text"
            placeholder="Tìm kiếm từ..."
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            style={{ width: '140px', background: '#111318', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 10px', borderRadius: '6px', fontSize: '12px' }}
          />
          <input
            type="text"
            placeholder="Từ gốc (Ví dụ: Peppa, OK, KFC)"
            value={newWord}
            onChange={e => setNewWord(e.target.value)}
            style={{ flex: 1, background: '#111318', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 10px', borderRadius: '6px', fontSize: '12px' }}
          />
          <input
            type="text"
            placeholder="Phiên âm (Ví dụ: Pép-pa, ô kê)"
            value={newPronunciation}
            onChange={e => setNewPronunciation(e.target.value)}
            style={{ flex: 1, background: '#111318', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '6px 10px', borderRadius: '6px', fontSize: '12px' }}
          />
          <button className="btn-primary" onClick={handleAddEntry} style={{ padding: '6px 12px', fontSize: '12px', display: 'flex', alignItems: 'center', gap: '4px', whiteSpace: 'nowrap' }}>
            <Plus size={14} /> Thêm
          </button>
        </div>

        {/* Entries Table */}
        <div style={{ flex: 1, overflowY: 'auto', padding: '14px 20px' }}>
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
                <span style={{ color: '#38bdf8', fontFamily: 'monospace', fontWeight: 600 }}>{entry.pronunciation}</span>
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

        {/* Footer with Bulk Replacement Actions */}
        <div style={{ padding: '12px 20px', borderTop: '1px solid rgba(255,255,255,0.08)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#0B0D10' }}>
          <div>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Tổng số <strong>{localEntries.length}</strong> từ phiên âm</span>
            {appliedNotice && (
              <span style={{ marginLeft: '12px', fontSize: '11px', color: '#34d399', fontWeight: 700 }}>
                {appliedNotice}
              </span>
            )}
          </div>
          <div style={{ display: 'flex', gap: '8px' }}>
            <button className="btn-secondary" onClick={onClose} style={{ padding: '6px 12px', fontSize: '12px' }}>Đóng</button>
            <button
              onClick={() => handleApplyBulk('tts')}
              style={{
                padding: '6px 14px',
                fontSize: '12px',
                fontWeight: 700,
                background: 'rgba(56, 189, 248, 0.15)',
                color: '#38bdf8',
                border: '1px solid rgba(56, 189, 248, 0.4)',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Zap size={13} /> Áp Dụng Vào TTS TEXT
            </button>
            <button
              onClick={() => handleApplyBulk('both')}
              style={{
                padding: '6px 16px',
                fontSize: '12px',
                fontWeight: 700,
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                color: '#fff',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}
            >
              <Check size={14} /> Thay Thế Toàn Bộ (Vietsub & TTS)
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
