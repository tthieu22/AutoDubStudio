import React from 'react';
import { Cpu, Zap, Info, ShieldCheck, HelpCircle } from 'lucide-react';

interface SystemSettingsProps {
  settings: {
    whisperModel: string;
    translationModel: string;
    translationBatchSize?: number;
    ttsVoice: string;
    encoder: string;
  };
  onSettingsChange: (newSettings: any) => void;
}

export const SystemSettings: React.FC<SystemSettingsProps> = ({
  settings,
  onSettingsChange
}) => {
  return (
    <div className="glass-panel" style={{ maxWidth: '850px', margin: '0 auto', borderRadius: '20px', padding: '32px' }}>
      
      <div style={{ marginBottom: '24px', borderBottom: '1px solid var(--border-glass)', paddingBottom: '16px' }}>
        <h3 className="gradient-text" style={{ margin: '0 0 6px 0', fontSize: '22px' }}>Cấu Hình Hệ Thống AI Engine & Bộ Xuất Video</h3>
        <p style={{ margin: 0, color: 'var(--text-muted)', fontSize: '13px' }}>
          Tùy chỉnh thông số phần cứng, mô hình AI dịch thuật và công nghệ tăng tốc phần cứng card đồ họa (GPU).
        </p>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
        
        {/* 1. VIDEO ENCODER CONFIGURATION (EXPLAINED IN DETAIL) */}
        <div className="glass-card" style={{ padding: '20px', borderColor: 'var(--border-glass-bright)', background: 'rgba(15, 23, 42, 0.7)' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <label style={{ fontSize: '14px', fontWeight: 800, color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Zap size={18} className="text-amber-400" /> BỘ MÃ HÓA VIDEO (VIDEO ENCODER)
            </label>
            <span className="badge badge-completed">TĂNG TỐC PHẦN CỨNG</span>
          </div>

          <select 
            value={settings.encoder} 
            onChange={e => onSettingsChange({ ...settings, encoder: e.target.value })}
            style={{ 
              width: '100%', 
              background: '#020617', 
              border: '1px solid var(--border-glass-bright)', 
              borderRadius: '10px', 
              padding: '12px 16px', 
              color: '#fff', 
              fontSize: '14px',
              fontWeight: 600,
              outline: 'none',
              marginBottom: '14px'
            }}
          >
            <option value="NVENC">NVIDIA NVENC (Tăng tốc phần cứng bằng Card đồ họa GPU - Khuyên Dùng)</option>
            <option value="CPU">CPU Software (Mã hóa bằng vi xử lý CPU - Chạy trên mọi máy)</option>
          </select>

          {/* Detailed visual explanation box */}
          <div style={{ background: 'rgba(2, 6, 23, 0.9)', border: '1px solid rgba(99, 102, 241, 0.25)', borderRadius: '10px', padding: '14px', fontSize: '12px', lineHeight: 1.6 }}>
            {settings.encoder === 'NVENC' ? (
              <div>
                <div style={{ fontWeight: 700, color: '#38bdf8', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Chế độ Card Đồ Họa NVIDIA NVENC (Khuyên Dùng Cho Máy Có Card Rời NVIDIA):
                </div>
                <div style={{ color: 'var(--text-muted)' }}>
                  Sử dụng bộ mã hóa phần cứng tích hợp trực tiếp trên GPU NVIDIA. Giảm 90% tải CPU, render video siêu nhanh, xem mượt mà không giật giật.
                </div>
              </div>
            ) : (
              <div>
                <div style={{ fontWeight: 700, color: '#f59e0b', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                  Chế độ Vi Xử Lý CPU (Software Encoder x264):
                </div>
                <div style={{ color: 'var(--text-muted)' }}>
                  Sử dụng vi xử lý CPU để mã hóa video. Tương thích tuyệt đối trên 100% thiết bị nhưng sẽ làm tăng tải CPU khi xuất video.
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 2. WHISPER STT MODEL */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <label style={{ fontSize: '14px', fontWeight: 800, color: '#fff' }}>🎙️ Mô Hình Nhận Dạng Giọng Nói (Whisper STT)</label>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Tách lời thoại từ video gốc</span>
          </div>

          <select 
            value={settings.whisperModel} 
            onChange={e => onSettingsChange({ ...settings, whisperModel: e.target.value })}
            style={{ width: '100%', background: '#020617', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px 16px', color: '#fff', fontSize: '14px', outline: 'none' }}
          >
            <option value="small">Whisper Small (Khuyên dùng - Cân bằng tốc độ & độ chính xác cao)</option>
            <option value="base">Whisper Base (Tốc độ xử lý nhanh cho máy cấu hình nhẹ)</option>
            <option value="medium">Whisper Medium (Độ chính xác cao cho âm thanh khó nghe)</option>
            <option value="large-v3">Whisper Large-v3 (Độ chính xác tuyệt đối)</option>
          </select>
        </div>

        {/* 3. GPU TRANSLATION MODEL */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <label style={{ fontSize: '14px', fontWeight: 800, color: '#fff' }}>⚡ Mô Hình Dịch Thuật GPU (Chinese → Vietnamese)</label>
              <span style={{ fontSize: '11px', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.4)', borderRadius: '4px', padding: '2px 6px', fontWeight: 700 }}>
                100% GPU CUDA
              </span>
            </div>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>GTX 1650 Ti (4GB)</span>
          </div>

          <select 
            value={settings.translationModel || "hachimi-60m"} 
            onChange={e => onSettingsChange({ ...settings, translationModel: e.target.value })}
            style={{ width: '100%', background: '#020617', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px 16px', color: '#fff', fontSize: '14px', outline: 'none', marginBottom: '14px' }}
          >
            <option value="hachimi-60m">🟢 HachimiMT-60 (Siêu Tốc - GPU FP16, ~260MB VRAM) [Khuyên Dùng Mặc Định]</option>
            <option value="qwen2.5:3b">🔵 Qwen2.5:3B (Chuyên Sâu - GPU Ollama, ~2.1GB VRAM)</option>
          </select>

          <div style={{ marginBottom: '14px', padding: '10px 12px', background: 'rgba(15, 23, 42, 0.6)', borderRadius: '8px', border: '1px solid rgba(255, 255, 255, 0.05)' }}>
            <div style={{ fontSize: '12px', fontWeight: 700, color: '#93c5fd', marginBottom: '4px' }}>Chế độ thực thi phần cứng (Hardware Execution):</div>
            <div style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: 1.5 }}>
              🔒 <strong>Khóa độc quyền 1 Model:</strong> Hệ thống tự động giải phóng VRAM ngay sau khi dịch xong trước khi nạp TTS / STT để bảo vệ tối đa 4GB VRAM.
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '6px' }}>
            <label style={{ fontSize: '13px', fontWeight: 700, color: '#cbd5e1' }}>📦 Kích Thước Batch Phụ Đề (Batch Size)</label>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Số câu dịch song song trên GPU</span>
          </div>
          <select 
            value={settings.translationBatchSize || 20} 
            onChange={e => onSettingsChange({ ...settings, translationBatchSize: Number(e.target.value) })}
            style={{ width: '100%', background: '#020617', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '10px 14px', color: '#fff', fontSize: '13px', outline: 'none' }}
          >
            <option value={5}>5 câu / batch</option>
            <option value={10}>10 câu / batch (Nhanh)</option>
            <option value={20}>20 câu / batch (Mặc định tối ưu GPU GTX 1650 Ti)</option>
            <option value={50}>50 câu / batch (Tối đa - Siêu tốc)</option>
          </select>
        </div>

        {/* 4. PIPER TTS VOICE */}
        <div className="glass-card" style={{ padding: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '10px' }}>
            <label style={{ fontSize: '14px', fontWeight: 800, color: '#fff' }}>🗣️ Giọng Đọc Lồng Tiếng (Piper Local TTS)</label>
            <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Tổng hợp giọng đọc offline</span>
          </div>

          <select 
            value={settings.ttsVoice} 
            onChange={e => onSettingsChange({ ...settings, ttsVoice: e.target.value })}
            style={{ width: '100%', background: '#020617', border: '1px solid var(--border-glass)', borderRadius: '10px', padding: '12px 16px', color: '#fff', fontSize: '14px', outline: 'none' }}
          >
            <option value="vi_VN-vais1000-medium">vi_VN-vais1000-medium (Giọng đọc Tiếng Việt chuẩn truyền cảm - Khuyên dùng)</option>
            <option value="vi_VN-viss-low">vi_VN-viss-low (Tốc độ sinh âm thanh siêu nhanh)</option>
          </select>
        </div>

      </div>
    </div>
  );
};
