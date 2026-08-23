import React from 'react';
import { X, CheckCircle2, AlertTriangle, XCircle, ArrowRight, ShieldCheck } from 'lucide-react';
import { PreTtsValidationResult } from '../services/ttsValidator';

interface PreTtsValidationModalProps {
  isOpen: boolean;
  validationResult: PreTtsValidationResult | null;
  onClose: () => void;
  onConfirmProceed: () => void;
}

export const PreTtsValidationModal: React.FC<PreTtsValidationModalProps> = ({
  isOpen,
  validationResult,
  onClose,
  onConfirmProceed
}) => {
  if (!isOpen || !validationResult) return null;

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
        width: '560px',
        maxHeight: '85vh',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.6)'
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
            <ShieldCheck size={22} color={validationResult.canProceed ? "#10b981" : "#ef4444"} />
            <div>
              <h3 style={{ margin: 0, fontSize: '15px', fontWeight: 700, color: '#fff' }}>Kiểm Tra Trước Khi Tạo Giọng Đọc (PRE-TTS VALIDATION)</h3>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>Xác nhận toàn bộ bản dịch & thời lượng trước khi đưa vào TTS engine</span>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
            <X size={18} />
          </button>
        </div>

        {/* Body Checklist */}
        <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '12px', flex: 1, overflowY: 'auto' }}>
          {validationResult.checklist.map(item => (
            <div
              key={item.id}
              style={{
                display: 'flex',
                alignItems: 'start',
                gap: '12px',
                padding: '12px',
                borderRadius: '8px',
                background: item.passed ? 'rgba(16, 185, 129, 0.05)' : (item.severity === 'ERROR' ? 'rgba(239, 68, 68, 0.08)' : 'rgba(245, 158, 11, 0.08)'),
                border: '1px solid',
                borderColor: item.passed ? 'rgba(16, 185, 129, 0.2)' : (item.severity === 'ERROR' ? 'rgba(239, 68, 68, 0.3)' : 'rgba(245, 158, 11, 0.3)')
              }}
            >
              {item.passed ? (
                <CheckCircle2 size={18} color="#10b981" style={{ marginTop: '2px', flexShrink: 0 }} />
              ) : item.severity === 'ERROR' ? (
                <XCircle size={18} color="#ef4444" style={{ marginTop: '2px', flexShrink: 0 }} />
              ) : (
                <AlertTriangle size={18} color="#f59e0b" style={{ marginTop: '2px', flexShrink: 0 }} />
              )}
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 600, color: item.passed ? '#fff' : (item.severity === 'ERROR' ? '#fca5a5' : '#fcd34d') }}>
                  {item.label}
                </div>
                {item.details && (
                  <div style={{ fontSize: '11px', color: '#94a3b8', marginTop: '4px' }}>
                    {item.details}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div style={{
          padding: '16px 20px',
          borderTop: '1px solid rgba(255,255,255,0.08)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: '#0B0D10'
        }}>
          <div>
            {!validationResult.canProceed ? (
              <span style={{ fontSize: '11px', color: '#ef4444', fontWeight: 600 }}>⚠ Có lỗi nghiêm trọng cần khắc phục trước khi tiếp tục</span>
            ) : validationResult.warningCount > 0 ? (
              <span style={{ fontSize: '11px', color: '#f59e0b', fontWeight: 600 }}>⚠ Có {validationResult.warningCount} cảnh báo nhưng có thể tiếp tục</span>
            ) : (
              <span style={{ fontSize: '11px', color: '#10b981', fontWeight: 600 }}>✓ Toàn bộ kiểm tra đạt chuẩn</span>
            )}
          </div>

          <div style={{ display: 'flex', gap: '10px' }}>
            <button className="btn-secondary" onClick={onClose} style={{ padding: '8px 16px', fontSize: '12px' }}>
              Xem Lỗi / Hủy
            </button>
            <button
              className="btn-primary"
              disabled={!validationResult.canProceed}
              onClick={onConfirmProceed}
              style={{
                padding: '8px 20px',
                fontSize: '12px',
                background: validationResult.canProceed ? 'linear-gradient(135deg, #10b981, #06b6d4)' : '#334155',
                cursor: validationResult.canProceed ? 'pointer' : 'not-allowed',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              Tiến Hành TTS Casting <ArrowRight size={14} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
