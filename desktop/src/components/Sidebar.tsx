import React from 'react';
import { Sparkles, PlusCircle, RefreshCw, FileVideo, Activity } from 'lucide-react';

interface SidebarProps {
  projectsList: string[];
  selectedProjectDir: string | null;
  realRam: string;
  realVram: string;
  onSelectProject: (name: string) => void;
  onCreateNewProjectClick: () => void;
  onRefreshList: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  projectsList,
  selectedProjectDir,
  realRam,
  realVram,
  onSelectProject,
  onCreateNewProjectClick,
  onRefreshList
}) => {
  const extractPercentage = (str: string) => {
    const match = str.match(/\((\d+)%\)/);
    return match ? parseInt(match[1]) : 50;
  };

  return (
    <div 
      style={{ 
        width: '280px', 
        background: 'rgba(15, 23, 42, 0.95)', 
        borderRight: '1px solid var(--border-glass)', 
        display: 'flex', 
        flexDirection: 'column',
        zIndex: 10
      }}
    >
      {/* LOGO BRANDING */}
      <div style={{ padding: '20px', borderBottom: '1px solid var(--border-glass)', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ width: '38px', height: '38px', borderRadius: '10px', background: 'linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 15px rgba(99, 102, 241, 0.5)' }}>
          <Sparkles size={22} color="#fff" />
        </div>
        <div>
          <h1 className="gradient-text" style={{ fontSize: '18px', margin: 0, lineHeight: 1.2 }}>AutoDub AI</h1>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.5px' }}>STUDIO PRO v0.1</span>
        </div>
      </div>

      {/* ACTION BUTTONS */}
      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '10px' }}>
        <button className="btn-primary" onClick={onCreateNewProjectClick} style={{ width: '100%', justifyContent: 'center' }}>
          <PlusCircle size={16} /> TẠO DỰ ÁN MỚI
        </button>
        <button className="btn-secondary" onClick={onRefreshList} style={{ width: '100%', justifyContent: 'center' }}>
          <RefreshCw size={14} /> Làm Mới Danh Sách
        </button>
      </div>

      {/* PROJECTS LIST */}
      <div style={{ flexGrow: 1, overflowY: 'auto', padding: '0 16px 16px 16px' }}>
        <div style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '10px' }}>
          DANH SÁCH DỰ ÁN ({projectsList.length})
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
          {projectsList.length === 0 ? (
            <span style={{ fontSize: '13px', color: '#64748b', fontStyle: 'italic' }}>Chưa có dự án nào</span>
          ) : (
            projectsList.map(name => {
              const isSelected = selectedProjectDir?.endsWith(name);
              return (
                <div
                  key={name}
                  onClick={() => onSelectProject(name)}
                  className="glass-card"
                  style={{
                    padding: '12px 14px',
                    cursor: 'pointer',
                    background: isSelected ? 'rgba(99, 102, 241, 0.2)' : 'rgba(15, 23, 42, 0.5)',
                    borderColor: isSelected ? 'var(--primary)' : 'var(--border-glass)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '10px'
                  }}
                >
                  <FileVideo size={16} style={{ color: isSelected ? 'var(--cyan)' : '#64748b' }} />
                  <span style={{ fontSize: '13px', fontWeight: isSelected ? 700 : 500, color: isSelected ? '#fff' : '#cbd5e1', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {name}
                  </span>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* REAL-TIME DYNAMIC HARDWARE TELEMETRY METRIC WIDGET */}
      <div style={{ padding: '16px', background: 'rgba(2, 6, 23, 0.8)', borderTop: '1px solid var(--border-glass)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <span style={{ fontSize: '11px', fontWeight: 800, color: '#38bdf8', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Activity size={13} /> RESOURCE TELEMETRY
          </span>
          <span className="badge badge-completed" style={{ fontSize: '9px', padding: '1px 6px' }}>LOCAL GPU</span>
        </div>

        {/* System RAM Bar */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
            <span style={{ color: '#94a3b8' }}>System RAM</span>
            <span style={{ color: '#fff', fontWeight: 700 }}>{realRam}</span>
          </div>
          <div style={{ width: '100%', background: '#1e293b', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${extractPercentage(realRam)}%`, background: 'linear-gradient(90deg, #10b981, #f59e0b)', height: '100%', transition: 'width 0.5s ease' }}></div>
          </div>
        </div>

        {/* GPU VRAM Bar */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', marginBottom: '4px' }}>
            <span style={{ color: '#94a3b8' }}>GPU VRAM</span>
            <span style={{ color: '#38bdf8', fontWeight: 700 }}>{realVram}</span>
          </div>
          <div style={{ width: '100%', background: '#1e293b', height: '6px', borderRadius: '3px', overflow: 'hidden' }}>
            <div style={{ width: `${extractPercentage(realVram)}%`, background: 'linear-gradient(90deg, #6366f1, #06b6d4)', height: '100%', transition: 'width 0.5s ease' }}></div>
          </div>
        </div>
      </div>

    </div>
  );
};
