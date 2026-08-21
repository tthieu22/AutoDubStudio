import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertTriangle, CheckCircle, Wand2, RefreshCw, Layers } from 'lucide-react';
import { PythonEngineService } from '../services/pythonEngine';

interface QualityControlProps {
  projectDir: string;
}

export const QualityControl: React.FC<QualityControlProps> = ({ projectDir }) => {
  const [qcReport, setQcReport] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isApplyingAutofit, setIsApplyingAutofit] = useState(false);

  useEffect(() => {
    runQC();
  }, [projectDir]);

  const runQC = async () => {
    setIsLoading(true);
    try {
      const res = await PythonEngineService.runQcCheck(projectDir);
      setQcReport(res);
    } catch (err) {
      console.error('QC execution error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApplyAutofit = async () => {
    setIsApplyingAutofit(true);
    try {
      await PythonEngineService.applyAutofitQc(projectDir);
      alert('Đã tự động căn chỉnh khoảng ngắt nghỉ và xử lý đè khớp thời gian thành công!');
      await runQC();
    } catch (err) {
      alert(`Auto-fit thất bại: ${err}`);
    } finally {
      setIsApplyingAutofit(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', height: '100%' }}>
      {/* HEADER */}
      <div className="glass-card" style={{ padding: '16px 20px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <ShieldCheck color="#10b981" size={22} />
          <div>
            <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#fff' }}>AUDIO SYNC & QUALITY CONTROL (QC) INSPECTOR</h3>
            <span style={{ fontSize: '12px', color: '#94a3b8' }}>Tự động kiểm tra lệch audio, missing segment, speech overrun & timestamp overlap</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '10px' }}>
          <button className="btn-secondary" onClick={runQC} disabled={isLoading}>
            <RefreshCw size={14} className={isLoading ? 'animate-spin' : ''} /> {isLoading ? 'Đang quét...' : 'Quét Lại (Inspect)'}
          </button>

          <button className="btn-primary" onClick={handleApplyAutofit} disabled={isApplyingAutofit || !qcReport || qcReport.issues?.length === 0}>
            <Wand2 size={15} /> {isApplyingAutofit ? 'Đang căn chỉnh...' : '[ Auto Fit ] Tự Động Sửa Lệch'}
          </button>
        </div>
      </div>

      {/* METRICS & STATS CARDS */}
      {qcReport && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px' }}>
          <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>TRẠNG THÁI KIỂM THỬ</span>
            <span style={{ fontSize: '18px', fontWeight: 800, color: qcReport.valid ? '#10b981' : '#f59e0b' }}>
              {qcReport.valid ? 'PASSED (HỢP LỆ)' : 'NEED ATTENTION'}
            </span>
          </div>

          <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>SỐ LƯỢNG CẢNH BÁO</span>
            <span style={{ fontSize: '18px', fontWeight: 800, color: qcReport.warning_count > 0 ? '#f59e0b' : '#38bdf8' }}>
              {qcReport.warning_count} Cảnh báo
            </span>
          </div>

          <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>TỶ LỆ LỜI THOẠI TRUNG BÌNH</span>
            <span style={{ fontSize: '18px', fontWeight: 800, color: '#fff' }}>
              {qcReport.stats?.avg_tts_duration_ratio || 1.0}x
            </span>
          </div>

          <div className="glass-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>LỆCH LỚN NHẤT</span>
            <span style={{ fontSize: '18px', fontWeight: 800, color: '#fb7185' }}>
              +{qcReport.stats?.max_duration_exceeded_sec || 0}s
            </span>
          </div>
        </div>
      )}

      {/* ISSUES LIST */}
      <div className="glass-card" style={{ padding: '20px', flexGrow: 1, display: 'flex', flexDirection: 'column', gap: '12px', overflowY: 'auto' }}>
        <h4 style={{ margin: 0, fontSize: '15px', color: '#fff', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Layers size={16} color="#38bdf8" /> DANH SÁCH CHI TIẾT CÁC ĐOẠN CẦN XỬ LÝ ({qcReport?.issues?.length || 0})
        </h4>

        {qcReport?.issues?.length === 0 ? (
          <div style={{ padding: '30px', textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px' }}>
            <CheckCircle size={36} color="#10b981" />
            <span style={{ fontSize: '14px', color: '#6ee7b7', fontWeight: 600 }}>Tất cả các đoạn phụ đề và audio lồng tiếng đều hoàn toàn khớp nhau! Không phát hiện lỗi.</span>
          </div>
        ) : (
          qcReport?.issues?.map((issue: any, idx: number) => (
            <div
              key={idx}
              style={{
                padding: '14px 16px',
                borderRadius: '8px',
                background: issue.severity === 'ERROR' ? 'rgba(239, 68, 68, 0.1)' : 'rgba(245, 158, 11, 0.1)',
                border: issue.severity === 'ERROR' ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <AlertTriangle size={18} color={issue.severity === 'ERROR' ? '#f87171' : '#fbbf24'} />
                <div>
                  <span style={{ fontSize: '13px', fontWeight: 700, color: '#fff' }}>
                    Segment #{issue.segment_id}: {issue.message}
                  </span>
                  <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginTop: '2px' }}>
                    Loại lỗi: {issue.type} • Đề xuất: {issue.action}
                  </span>
                </div>
              </div>

              <button className="btn-secondary" onClick={handleApplyAutofit} style={{ fontSize: '12px', padding: '6px 12px' }}>
                [{issue.action}]
              </button>
            </div>
          ))
        )}
      </div>
    </div>
  );
};
