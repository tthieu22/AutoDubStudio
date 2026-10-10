import React from 'react';
import { X, Keyboard } from 'lucide-react';

interface ShortcutsModalProps {
  onClose: () => void;
}

export const ShortcutsModal: React.FC<ShortcutsModalProps> = ({ onClose }) => {
  const shortcuts = [
    { key: 'Space', desc: 'Phát / Tạm dừng Video Preview' },
    { key: 'Ctrl + Z', desc: 'Hoàn tác (Undo)' },
    { key: 'Ctrl + Shift + Z', desc: 'Làm lại (Redo)' },
    { key: 'Ctrl + S', desc: 'Lưu trạng thái dự án' },
    { key: 'Ctrl + D', desc: 'Nhân bản Clip/Layer đã chọn' },
    { key: 'Delete / Backspace', desc: 'Xóa Clip/Layer đã chọn' },
    { key: 'B', desc: 'Cắt Clip tại vị trí con trỏ phát' },
    { key: 'Shift + ?', desc: 'Mở bảng phím tắt này' },
  ];

  return (
    <div 
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(5, 7, 12, 0.85)',
        backdropFilter: 'blur(12px)',
        zIndex: 99999,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '16px'
      }}
    >
      <div 
        style={{
          background: 'linear-gradient(145deg, #11131c 0%, #07090e 100%)',
          border: '1px solid rgba(99, 102, 241, 0.2)',
          borderRadius: '16px',
          width: '100%',
          maxWidth: '480px',
          overflow: 'hidden',
          boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 50px rgba(99, 102, 241, 0.1)',
          display: 'flex',
          flexDirection: 'column'
        }}
      >
        {/* Header */}
        <div 
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            padding: '20px 24px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
            background: 'rgba(255, 255, 255, 0.01)'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '32px', height: '32px', borderRadius: '8px', background: 'rgba(99, 102, 241, 0.1)', display: 'flex', alignItems: 'center', justifyContent: 'center', border: '1px solid rgba(99, 102, 241, 0.2)' }}>
              <Keyboard size={18} color="#6366f1" />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 800, color: '#fff', letterSpacing: '0.5px' }}>
                Bảng Phím Tắt Trợ Giúp
              </h3>
              <span style={{ fontSize: '11px', color: '#64748b' }}>Tăng tốc thao tác biên tập video của bạn</span>
            </div>
          </div>
          <button 
            onClick={onClose} 
            style={{
              background: 'transparent',
              border: 'none',
              color: '#94a3b8',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '28px',
              height: '28px',
              borderRadius: '50%',
              backgroundColor: 'rgba(255, 255, 255, 0.03)',
              transition: 'all 0.15s'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(239, 68, 68, 0.1)';
              e.currentTarget.style.color = '#ef4444';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.backgroundColor = 'rgba(255, 255, 255, 0.03)';
              e.currentTarget.style.color = '#94a3b8';
            }}
          >
            <X size={16} />
          </button>
        </div>

        {/* List */}
        <div style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '12px', maxHeight: '55vh', overflowY: 'auto' }}>
          {shortcuts.map((s, i) => (
            <div 
              key={i} 
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                paddingBottom: '10px',
                borderBottom: '1px solid rgba(255, 255, 255, 0.03)'
              }}
            >
              <span style={{ fontSize: '13px', color: '#cbd5e1', fontWeight: 500 }}>{s.desc}</span>
              <kbd 
                style={{
                  padding: '4px 10px',
                  background: 'linear-gradient(180deg, #1e293b 0%, #0f172a 100%)',
                  border: '1px solid rgba(255, 255, 255, 0.08)',
                  borderBottom: '2px solid rgba(255, 255, 255, 0.2)',
                  borderRadius: '6px',
                  fontFamily: 'Consolas, Monaco, "Andale Mono", monospace',
                  fontSize: '11px',
                  color: '#38bdf8',
                  fontWeight: 600,
                  boxShadow: 'inset 0 1px 0 rgba(255, 255, 255, 0.05), 0 2px 4px rgba(0,0,0,0.4)',
                  letterSpacing: '0.3px'
                }}
              >
                {s.key}
              </kbd>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
