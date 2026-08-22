import React, { useState, useEffect } from 'react';
import { Sparkles, FolderOpen, Loader2, RefreshCw } from 'lucide-react';
import { open } from '@tauri-apps/api/dialog';

interface NewProjectModalProps {
  isCreating: boolean;
  onCreateProject: (name: string, videoPath: string) => Promise<void>;
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

  // Automatically refresh name on mount
  useEffect(() => {
    setProjectName(generateTimestampName());
  }, []);

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
    await onCreateProject(projectName.trim(), videoPath);
  };

  return (
    <div style={{ padding: '40px', flexGrow: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '650px', borderRadius: '20px', padding: '36px', boxShadow: '0 20px 50px rgba(0,0,0,0.5)' }}>
        
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
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
