import React, { useRef, useEffect } from 'react';
import { Terminal } from 'lucide-react';

interface ConsoleLogsProps {
  logs: string[];
  onClearLogs: () => void;
}

export const ConsoleLogs: React.FC<ConsoleLogsProps> = ({ logs, onClearLogs }) => {
  const logEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  return (
    <div className="glass-panel" style={{ height: '100%', borderRadius: '16px', padding: '20px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--cyan)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Terminal size={15} /> LIVE EXECUTION LOG STREAM
        </span>
        <button className="btn-secondary" onClick={onClearLogs} style={{ padding: '4px 10px', fontSize: '11px' }}>
          Xóa Log
        </button>
      </div>

      <div style={{ flexGrow: 1, background: '#020617', borderRadius: '10px', padding: '16px', overflowY: 'auto', fontFamily: 'monospace', fontSize: '12px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
        {logs.length === 0 ? (
          <span style={{ color: '#64748b' }}>Đang chờ luồng dữ liệu log...</span>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} style={{ color: log.includes('ERROR') ? '#fb7185' : log.includes('WARNING') ? '#f59e0b' : '#cbd5e1' }}>
              {log}
            </div>
          ))
        )}
        <div ref={logEndRef}></div>
      </div>
    </div>
  );
};
