import React, { useState, useEffect } from 'react';
import { Sparkles, FolderOpen, Loader2, RefreshCw, Languages, Info } from 'lucide-react';
import { open } from '@tauri-apps/api/dialog';

export interface TranslationStyleOption {
  id: string;
  name: string;
  description: string;
}

const TRANSLATION_STYLES: TranslationStyleOption[] = [
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
  onCreateProject: (name: string, videoPath: string, style?: string, customStyle?: string, mode?: 'STORY' | 'DUBBING', storyText?: string) => Promise<void>;
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

  const [projectMode, setProjectMode] = useState<'DUBBING' | 'STORY'>('DUBBING');
  const [projectName, setProjectName] = useState(generateTimestampName);
  const [videoPath, setVideoPath] = useState('');
  const [storyText, setStoryText] = useState('');
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
        return;
      }
    } catch (err) {
      console.warn('Tauri dialog unavailable, falling back to manual input:', err);
    }

    const manualPath = prompt('Nhập đường dẫn file video (hoặc để mặc định):', videoPath || 'C:/Videos/sample_demo_video.mp4');
    if (manualPath) {
      setVideoPath(manualPath);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalProjectName = projectName.trim() || generateTimestampName();
    const finalMediaPath = videoPath.trim() || (projectMode === 'DUBBING' ? 'C:/Videos/sample_demo_video.mp4' : 'source/story.txt');

    await onCreateProject(
      finalProjectName,
      finalMediaPath,
      translationStyle,
      translationStyle === 'custom' ? customStyleText : undefined,
      projectMode,
      storyText
    );
  };

  return (
    <div style={{ padding: '40px', flexGrow: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '720px', borderRadius: '20px', padding: '36px', boxShadow: '0 20px 50px rgba(0,0,0,0.5)' }}>
        
        {/* MODE SELECTOR TABS */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '24px' }}>
          <button
            type="button"
            onClick={() => setProjectMode('DUBBING')}
            style={{
              padding: '14px',
              borderRadius: '12px',
              border: '2px solid',
              borderColor: projectMode === 'DUBBING' ? '#06b6d4' : 'rgba(255, 255, 255, 0.08)',
              background: projectMode === 'DUBBING' ? 'rgba(6, 182, 212, 0.12)' : '#0B0D10',
              color: projectMode === 'DUBBING' ? '#38bdf8' : '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease'
            }}
          >
            <span style={{ fontSize: '15px', fontWeight: 800 }}>🎬 DỊCH & LỒNG TIẾNG VIDEO</span>
            <span style={{ fontSize: '11px', opacity: 0.8 }}>Tách audio ➔ STT Whisper ➔ Dịch Qwen AI ➔ Piper TTS ➔ Render</span>
          </button>

          <button
            type="button"
            onClick={() => setProjectMode('STORY')}
            style={{
              padding: '14px',
              borderRadius: '12px',
              border: '2px solid',
              borderColor: projectMode === 'STORY' ? '#a855f7' : 'rgba(255, 255, 255, 0.08)',
              background: projectMode === 'STORY' ? 'rgba(168, 85, 247, 0.12)' : '#0B0D10',
              color: projectMode === 'STORY' ? '#c084fc' : '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              gap: '6px',
              transition: 'all 0.2s ease'
            }}
          >
            <span style={{ fontSize: '15px', fontWeight: 800 }}>📖 TẠO VIDEO TRUYỆN (STORY)</span>
            <span style={{ fontSize: '11px', opacity: 0.8 }}>Làm sạch văn bản ➔ Phân cảnh ➔ Tạo ảnh SD 1.5 ➔ Piper TTS ➔ Render</span>
          </button>
        </div>

        <div style={{ textAlign: 'center', marginBottom: '24px' }}>
          <h2 className="gradient-text" style={{ fontSize: '24px', margin: '0 0 6px 0' }}>
            {projectMode === 'DUBBING' ? 'Tạo Dự Án Lồng Tiếng Video Mới' : 'Tạo Dự Án Phim Truyện AI Mới'}
          </h2>
          <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '13px' }}>
            {projectMode === 'DUBBING' 
              ? 'Tự động tách âm thanh, dịch tiếng Việt AI và lồng tiếng Piper TTS chuẩn xác.'
              : 'Tự động phân tích kịch bản truyện, tạo ảnh Stable Diffusion và tổng hợp giọng đọc AI.'}
          </p>
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



          {/* DUBBING MODE FIELDS */}
          {projectMode === 'DUBBING' && (
            <>
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
            </>
          )}

          {/* STORY MODE FIELDS */}
          {projectMode === 'STORY' && (
            <>
              <div>
                <label style={{ display: 'block', fontSize: '13px', fontWeight: 700, marginBottom: '8px', color: '#c084fc' }}>
                  📖 Nội Dung / Kịch Bản Truyện
                </label>
                <textarea
                  value={storyText}
                  onChange={e => setStoryText(e.target.value)}
                  rows={4}
                  placeholder="Dán nội dung chương truyện hoặc kịch bản vào đây (Hoặc dùng Import Truyện từ Web / File sau khi tạo dự án)..."
                  style={{
                    width: '100%',
                    background: 'rgba(15, 23, 42, 0.8)',
                    border: '1px solid var(--border-glass)',
                    borderRadius: '10px',
                    padding: '12px 16px',
                    color: '#fff',
                    fontSize: '13px',
                    outline: 'none',
                    resize: 'none'
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, marginBottom: '6px', color: '#cbd5e1' }}>
                    🎨 Mô Hình AI Tạo Ảnh
                  </label>
                  <select
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid var(--border-glass)',
                      borderRadius: '8px',
                      padding: '10px',
                      color: '#fff',
                      fontSize: '12px'
                    }}
                  >
                    <option value="SD 1.5 - Realistic Vision">SD 1.5 - Realistic Vision v5.1</option>
                    <option value="Anime Anything V5">Anime Anything V5</option>
                    <option value="SDXL Turbo">SDXL Turbo (4-Step Fast)</option>
                  </select>
                </div>

                <div>
                  <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, marginBottom: '6px', color: '#cbd5e1' }}>
                    🔊 Giọng Đọc TTS
                  </label>
                  <select
                    style={{
                      width: '100%',
                      background: 'rgba(15, 23, 42, 0.9)',
                      border: '1px solid var(--border-glass)',
                      borderRadius: '8px',
                      padding: '10px',
                      color: '#fff',
                      fontSize: '12px'
                    }}
                  >
                    <option value="vi_VN-vais1000-medium">vi_VN-vais1000-medium (Giọng Nam Chuẩn)</option>
                    <option value="vi_female_soft">vi_female_soft (Giọng Nữ Nhẹ Nhàng)</option>
                    <option value="vi_male_hero">vi_male_hero (Giọng Truyện Hero)</option>
                  </select>
                </div>
              </div>
            </>
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
