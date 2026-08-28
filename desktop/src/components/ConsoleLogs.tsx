import React, { useRef, useEffect, useState } from 'react';
import { Terminal, Copy, Check, Trash2 } from 'lucide-react';

interface ConsoleLogsProps {
  logs: string[];
  onClearLogs: () => void;
}

export const ConsoleLogs: React.FC<ConsoleLogsProps> = ({ logs, onClearLogs }) => {
  const logEndRef = useRef<HTMLDivElement | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  const handleCopyLogs = () => {
    if (logs.length === 0) return;
    navigator.clipboard.writeText(logs.join('\n'));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="glass-panel" style={{ height: '100%', borderRadius: '16px', padding: '20px', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
        <span style={{ fontSize: '13px', fontWeight: 700, color: 'var(--cyan)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <Terminal size={15} /> LIVE EXECUTION LOG STREAM
        </span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          {logs.length > 0 && (
            <button
              className="btn-secondary"
              onClick={handleCopyLogs}
              style={{ padding: '4px 10px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}
              title="Sao chép toàn bộ log"
            >
              {copied ? <Check size={12} style={{ color: '#34d399' }} /> : <Copy size={12} />}
              <span>{copied ? 'Đã sao chép!' : 'Sao Chép Log'}</span>
            </button>
          )}
          <button className="btn-secondary" onClick={onClearLogs} style={{ padding: '4px 10px', fontSize: '11px', display: 'flex', alignItems: 'center', gap: '4px' }}>
            <Trash2 size={12} /> Xóa Log
          </button>
        </div>
      </div>

      <div
        className="select-text cursor-text"
        style={{
          flexGrow: 1,
          background: '#020617',
          borderRadius: '10px',
          padding: '16px',
          overflowY: 'auto',
          fontFamily: 'monospace',
          fontSize: '12px',
          display: 'flex',
          flexDirection: 'column',
          gap: '6px',
          userSelect: 'text',
          WebkitUserSelect: 'text'
        }}
      >
        {logs.length === 0 ? (
          <span style={{ color: '#64748b', userSelect: 'none' }}>Đang chờ luồng dữ liệu log...</span>
        ) : (
          logs.map((log, idx) => (
            <div key={idx} style={{ color: log.includes('ERROR') ? '#fb7185' : log.includes('WARNING') ? '#f59e0b' : '#cbd5e1', userSelect: 'text', WebkitUserSelect: 'text' }}>
              {log}
            </div>
          ))
        )}
        <div ref={logEndRef}></div>
      </div>
    </div>
  );
};
