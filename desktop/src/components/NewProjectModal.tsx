import React, { useState, useEffect } from 'react';
import { Sparkles, FolderOpen, Loader2, RefreshCw, Languages, Info } from 'lucide-react';
import { open } from '@tauri-apps/api/dialog';

export interface TranslationStyleOption {
  id: string;
  name: string;
  description: string;
}

export const TRANSLATION_STYLES: TranslationStyleOption[] = [
  { id: 'general', name: 'General / Tự động', description: 'Dịch tiếng Việt tự nhiên, phù hợp hội thoại thông thường.' },
  { id: 'modern', name: 'Hiện đại', description: 'Tiếng Việt hiện đại, tự nhiên, phù hợp phim đô thị và đời thường.' },
  { id: 'ancient', name: 'Cổ trang', description: 'Phong cách tiếng Việt phù hợp phim cổ trang Trung Quốc, chú trọng địa vị và cách xưng hô.' },
  { id: 'time_travel', name: 'Xuyên không', description: 'Kết hợp ngôn ngữ hiện đại và cổ trang tùy theo thời đại của từng nhân vật.' },
  { id: 'xianxia', name: 'Tiên hiệp / Kiếm hiệp', description: 'Phù hợp tiên hiệp, kiếm hiệp, tu tiên và thế giới võ hiệp.' },
  { id: 'palace', name: 'Cung đấu', description: 'Phù hợp cung đấu, hoàng cung, quan hệ vua/chúa và tầng lớp quý tộc.' },
  { id: 'cartoon', name: 'Hoạt hình / Trẻ em', description: 'Tiếng Việt đơn giản, tự nhiên, dễ nghe, phù hợp hoạt hình.' },
  { id: 'custom', name: 'Tùy chỉnh', description: 'Cho phép người dùng nhập yêu cầu phong cách riêng.' }
];

interface NewProjectModalProps {
  isCreating: boolean;
  onCreateProject: (name: string, videoPath: string, style?: string, customStyle?: string) => Promise<void>;
}

export const NewProjectModal: React.FC<NewProjectModalProps> = ({
  isCreating,
  onCreateProject
}) => {
  const generateTimestampName = () => {
    const now = new Date();
    const YYYY = now.getFullYear();
    const MM = String(now.getMonth() + 1).padStart(2, '0');
    const DD = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    const ss = String(now.getSeconds()).padStart(2, '0');
    return `Project_${YYYY}-${MM}-${DD}_${hh}-${mm}-${ss}`;
  };

  const [projectName, setProjectName] = useState(generateTimestampName);
  const [videoPath, setVideoPath] = useState('');
  const [translationStyle, setTranslationStyle] = useState('general');
  const [customStyleText, setCustomStyleText] = useState('');

  // Automatically refresh name on mount
  useEffect(() => {
    setProjectName(generateTimestampName());
  }, []);

  const selectedStyleObj = TRANSLATION_STYLES.find(s => s.id === translationStyle) || TRANSLATION_STYLES[0];

  const handleSelectVideoFile = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{ name: 'Video Files', extensions: ['mp4', 'mkv', 'avi', 'mov'] }]
      });
      if (selected && typeof selected === 'string') {
        setVideoPath(selected);
      }
    } catch (err) {
      console.error('Select file error:', err);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!projectName.trim() || !videoPath) {
      alert('Vui lòng nhập tên dự án và chọn file video đầu vào!');
      return;
    }
    await onCreateProject(
      projectName.trim(),
      videoPath,
      translationStyle,
      translationStyle === 'custom' ? customStyleText : undefined
    );
  };

  return (
    <div style={{ padding: '40px', flexGrow: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '680px', borderRadius: '20px', padding: '36px', boxShadow: '0 20px 50px rgba(0,0,0,0.5)' }}>
        
        <div style={{ textAlign: 'center', marginBottom: '28px' }}>
          <h2 className="gradient-text" style={{ fontSize: '28px', margin: '0 0 10px 0' }}>Tạo Dự Án Lồng Tiếng Mới</h2>
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '14px' }}>Tự động tách âm thanh, dịch bằng Ollama AI và lồng tiếng với Piper TTS chuẩn xác.</p>
        </div>

        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, marginBottom: '8px', color: '#cbd5e1' }}>Tên Dự Án</label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                value={projectName}
                onChange={e => setProjectName(e.target.value)}
                placeholder="ví dụ: Video-Review-Game-01"
                style={{
                  flexGrow: 1,
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid var(--border-glass)',
                  borderRadius: '10px',
                  padding: '12px 16px',
                  color: '#fff',
                  fontSize: '14px',
                  outline: 'none'
                }}
              />
              <button 
                type="button" 
                className="btn-secondary" 
                onClick={() => setProjectName(generateTimestampName())}
                title="Tạo tên theo thời gian hiện tại"
                style={{ padding: '0 16px', gap: '6px' }}
              >
                <RefreshCw size={15} /> Tự động đặt tên
              </button>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, marginBottom: '8px', color: '#cbd5e1' }}>File Video Đầu Vào (MP4 / MKV / AVI)</label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                type="text"
                readOnly
                value={videoPath}
                placeholder="Chọn tệp video từ máy tính..."
                style={{
                  flexGrow: 1,
                  background: 'rgba(15, 23, 42, 0.8)',
                  border: '1px solid var(--border-glass)',
                  borderRadius: '10px',
                  padding: '12px 16px',
                  color: '#fff',
                  fontSize: '13px'
                }}
              />
              <button type="button" className="btn-secondary" onClick={handleSelectVideoFile}>
                <FolderOpen size={16} /> Chọn File
              </button>
            </div>
          </div>

          {/* TRANSLATION STYLE SELECTION */}
          <div>
            <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', fontWeight: 700, marginBottom: '8px', color: '#cbd5e1' }}>
              <Languages size={15} style={{ color: '#38bdf8' }} /> TRANSLATION STYLE (PHONG CÁCH DỊCH THUẬT)
            </label>
            <select
              value={translationStyle}
              onChange={e => setTranslationStyle(e.target.value)}
              style={{
                width: '100%',
                background: 'rgba(15, 23, 42, 0.9)',
                border: '1px solid var(--border-glass)',
                borderRadius: '10px',
                padding: '12px 16px',
                color: '#38bdf8',
                fontWeight: 600,
                fontSize: '14px',
                outline: 'none',
                cursor: 'pointer'
              }}
            >
              {TRANSLATION_STYLES.map(style => (
                <option key={style.id} value={style.id} style={{ background: '#0f172a', color: '#fff' }}>
                  {style.name}
                </option>
              ))}
            </select>

            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '8px', marginTop: '8px', padding: '10px 14px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.2)' }}>
              <Info size={16} style={{ color: '#38bdf8', flexShrink: 0, marginTop: '2px' }} />
              <span style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: '1.4' }}>
                {selectedStyleObj.description}
              </span>
            </div>
          </div>

          {/* CUSTOM TRANSLATION INSTRUCTIONS */}
          {translationStyle === 'custom' && (
            <div>
              <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, marginBottom: '8px', color: '#f59e0b' }}>
                CUSTOM TRANSLATION INSTRUCTIONS
              </label>
              <textarea
                value={customStyleText}
                onChange={e => setCustomStyleText(e.target.value)}
                placeholder="Nhập yêu cầu riêng (ví dụ: 'dịch tự nhiên như phim Việt Nam', 'ưu tiên văn phong hài hước', 'giữ xưng hô cổ trang')..."
                rows={3}
                style={{
                  width: '100%',
                  background: 'rgba(15, 23, 42, 0.9)',
                  border: '1px solid rgba(245, 158, 11, 0.4)',
                  borderRadius: '10px',
                  padding: '12px 16px',
                  color: '#fff',
                  fontSize: '13px',
                  outline: 'none',
                  resize: 'vertical'
                }}
              />
            </div>
          )}

          <button 
            type="submit" 
            className="btn-primary" 
            disabled={isCreating}
            style={{ width: '100%', justifyContent: 'center', padding: '14px', fontSize: '15px', marginTop: '10px' }}
          >
            {isCreating ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />} 
            {isCreating ? 'Đang Khởi Tạo...' : 'BẮT ĐẦU TẠO DỰ ÁN'}
          </button>
        </form>

      </div>
    </div>
  );
};
