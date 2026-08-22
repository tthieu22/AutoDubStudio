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
      alert('Autofit alignment completed successfully!');
      await runQC();
    } catch (err) {
      alert(`Autofit failed: ${err}`);
    } finally {
      setIsApplyingAutofit(false);
    }
  };

  const getHealthScore = () => {
    if (!qcReport) return 100;
    const warnings = qcReport.warning_count || 0;
    const score = Math.max(0, 100 - warnings * 5);
    return score;
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', height: '100%', overflow: 'hidden' }}>
      {/* 1. CONTROL HEADER */}
      <div 
        style={{ 
          background: '#111318', 
          border: '1px solid rgba(255, 255, 255, 0.05)', 
          borderRadius: '10px', 
          padding: '12px 20px', 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          flexShrink: 0
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <ShieldCheck color="#10b981" size={18} />
          <div>
            <h3 style={{ margin: 0, fontSize: '14px', fontWeight: 700, color: '#fff' }}>Audio & Timing Quality Control</h3>
            <span style={{ fontSize: '11px', color: '#94a3b8' }}>Analyze segment alignments, speech overruns, and overlap constraints</span>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="btn-secondary" onClick={runQC} disabled={isLoading} style={{ padding: '6px 12px', fontSize: '12px' }}>
            <RefreshCw size={12} className={isLoading ? 'animate-spin' : ''} /> Analyze Timeline
          </button>
          <button 
            className="btn-primary" 
            onClick={handleApplyAutofit} 
            disabled={isApplyingAutofit || !qcReport || qcReport.issues?.length === 0}
            style={{ padding: '6px 14px', fontSize: '12px', background: 'linear-gradient(135deg, #10b981, #06b6d4)' }}
          >
            <Wand2 size={13} /> {isApplyingAutofit ? 'Aligning...' : 'Auto-Fit Segments'}
          </button>
        </div>
      </div>

      {/* 2. DUAL LAYOUT: SUMMARY & DIAGNOSTICS */}
      {qcReport && (
        <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', gap: '16px', flexGrow: 1, minHeight: 0, overflow: 'hidden' }}>
          {/* STATS & METRICS PANEL */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{ background: '#111318', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '10px', padding: '16px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontSize: '11px', color: '#64748b', fontWeight: 700 }}>HEALTH SCORE</span>
              <span style={{ fontSize: '36px', fontWeight: 800, color: getHealthScore() > 80 ? '#10b981' : '#f59e0b' }}>
                {getHealthScore()}%
              </span>
              <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                {qcReport.valid ? 'All segments valid' : 'Timeline needs adjustment'}
              </span>
            </div>

            <div style={{ background: '#111318', border: '1px solid rgba(255, 255, 255, 0.05)', borderRadius: '10px', padding: '14px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <span style={{ fontSize: '10px', fontWeight: 800, color: '#64748b' }}>DIAGNOSTIC METRICS</span>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', borderBottom: '1px solid rgba(255,255,255,0.03)', paddingBottom: '6px' }}>
                <span style={{ color: '#94a3b8' }}>Total Warnings</span>
                <span style={{ color: '#fff', fontWeight: 700 }}>{qcReport.warning_count}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', borderBottom: '1px solid rgba(255,255,255,0.03)', paddingBottom: '6px' }}>
                <span style={{ color: '#94a3b8' }}>Avg Speed Ratio</span>
                <span style={{ color: '#fff', fontWeight: 700 }}>{qcReport.stats?.avg_tts_duration_ratio || '1.0'}x</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px' }}>
                <span style={{ color: '#94a3b8' }}>Max Overrun</span>
                <span style={{ color: '#ef4444', fontWeight: 700 }}>+{qcReport.stats?.max_duration_exceeded_sec || 0}s</span>
              </div>
            </div>
          </div>

          {/* DIAGNOSTIC DETAILED LIST */}
          <div 
            style={{ 
              background: '#111318', 
              border: '1px solid rgba(255, 255, 255, 0.05)', 
              borderRadius: '10px', 
              padding: '20px', 
              display: 'flex', 
              flexDirection: 'column', 
              gap: '12px',
              overflowY: 'auto' 
            }}
          >
            <span style={{ fontSize: '10px', fontWeight: 800, color: '#6366f1', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Detailed Diagnoses
            </span>

            {qcReport.issues?.length === 0 ? (
              <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '10px' }}>
                <CheckCircle size={32} color="#10b981" />
                <span style={{ fontSize: '13px', color: '#10b981', fontWeight: 700 }}>All segments are perfectly synchronized!</span>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {qcReport.issues?.map((issue: any, idx: number) => (
                  <div
                    key={idx}
                    style={{
                      padding: '12px 14px',
                      borderRadius: '6px',
                      background: 'rgba(255, 255, 255, 0.01)',
                      border: '1px solid',
                      borderColor: issue.severity === 'ERROR' ? 'rgba(239, 68, 68, 0.15)' : 'rgba(245, 158, 11, 0.15)',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      gap: '16px'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <AlertTriangle size={16} color={issue.severity === 'ERROR' ? '#ef4444' : '#f59e0b'} style={{ flexShrink: 0 }} />
                      <div>
                        <span style={{ fontSize: '12px', fontWeight: 700, color: '#fff' }}>
                          Segment #{issue.segment_id}: {issue.message}
                        </span>
                        <span style={{ fontSize: '11px', color: '#94a3b8', display: 'block', marginTop: '2px' }}>
                          Recommendation: {issue.action}
                        </span>
                      </div>
                    </div>

                    <button 
                      className="btn-secondary" 
                      onClick={handleApplyAutofit}
                      style={{ fontSize: '11px', padding: '4px 8px' }}
                    >
                      Fix Segment
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
