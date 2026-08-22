import React, { useState } from 'react';
import { 
  Folder, Activity, FileText, Layers, Mic, ShieldCheck, 
  Terminal, Video, Share2, Settings, PlusCircle, RefreshCw, 
  ChevronLeft, ChevronRight, Search, FileVideo
} from 'lucide-react';

interface SidebarProps {
  projectsList: string[];
  selectedProjectDir: string | null;
  activeTab: string;
  setActiveTab: (tab: any) => void;
  onSelectProject: (name: string) => void;
  onCreateNewProjectClick: () => void;
  onRefreshList: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  projectsList,
  selectedProjectDir,
  activeTab,
  setActiveTab,
  onSelectProject,
  onCreateNewProjectClick,
  onRefreshList
}) => {
  const [isProjectsExpanded, setIsProjectsExpanded] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  const filteredProjects = projectsList.filter(name => 
    name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const navItems = [
    { id: 'pipeline', label: 'Pipeline Process', icon: Activity, color: '#06b6d4' },
    { id: 'subtitles', label: 'Subtitle Editor', icon: FileText, color: '#6366f1' },
    { id: 'timeline', label: 'Timeline & Layers', icon: Layers, color: '#10b981' },
    { id: 'voices', label: 'Voice Studio', icon: Mic, color: '#a855f7' },
    { id: 'qc', label: 'Quality Control', icon: ShieldCheck, color: '#f59e0b' },
    { id: 'logs', label: 'Console Logs', icon: Terminal, color: '#94a3b8' },
    { id: 'preview', label: 'Video Preview', icon: Video, color: '#3b82f6' },
    { id: 'export', label: 'Export Presets', icon: Share2, color: '#ec4899' },
    { id: 'settings', label: 'Settings', icon: Settings, color: '#64748b' }
  ];

  return (
    <div style={{ display: 'flex', height: '100%', zIndex: 10 }}>
      {/* 1. NARROW ACTIVITY BAR NAVIGATION (64px) */}
      <div 
        style={{ 
          width: '64px', 
          background: '#0B0D10', 
          borderRight: '1px solid rgba(255, 255, 255, 0.05)', 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          padding: '16px 0', 
          gap: '8px' 
        }}
      >
        {/* Toggle Projects panel button */}
        <button
          onClick={() => setIsProjectsExpanded(!isProjectsExpanded)}
          style={{
            width: '40px',
            height: '40px',
            borderRadius: '8px',
            background: isProjectsExpanded ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
            color: isProjectsExpanded ? '#6366f1' : '#94a3b8',
            border: 'none',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            cursor: 'pointer',
            transition: 'all 0.15s ease',
            marginBottom: '16px'
          }}
          title={isProjectsExpanded ? 'Hide Projects Explorer' : 'Show Projects Explorer'}
        >
          <Folder size={20} />
        </button>

        {/* Navigation Tabs */}
        {navItems.map(item => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                width: '40px',
                height: '40px',
                borderRadius: '8px',
                background: isActive ? 'rgba(255, 255, 255, 0.05)' : 'transparent',
                color: isActive ? item.color : '#94a3b8',
                border: 'none',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'all 0.15s ease',
                position: 'relative'
              }}
              title={item.label}
            >
              <Icon size={20} />
              {isActive && (
                <div 
                  style={{ 
                    position: 'absolute', 
                    left: 0, 
                    top: '10px', 
                    width: '3px', 
                    height: '20px', 
                    background: item.color, 
                    borderRadius: '0 2px 2px 0' 
                  }} 
                />
              )}
            </button>
          );
        })}
      </div>

      {/* 2. EXPANDABLE PROJECT EXPLORER PANEL */}
      {isProjectsExpanded && (
        <div 
          style={{ 
            width: '240px', 
            background: '#111318', 
            borderRight: '1px solid rgba(255, 255, 255, 0.05)', 
            display: 'flex', 
            flexDirection: 'column' 
          }}
        >
          {/* Header */}
          <div style={{ padding: '16px', borderBottom: '1px solid rgba(255, 255, 255, 0.05)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
              <span style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Project Explorer
              </span>
              <button 
                onClick={onRefreshList} 
                style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer', display: 'flex', padding: '4px' }}
                title="Refresh projects"
              >
                <RefreshCw size={13} />
              </button>
            </div>

            {/* Create Project Button */}
            <button 
              className="btn-primary" 
              onClick={onCreateNewProjectClick} 
              style={{ width: '100%', justifyContent: 'center', padding: '8px 12px', fontSize: '12px', gap: '6px' }}
            >
              <PlusCircle size={14} /> NEW PROJECT
            </button>
          </div>

          {/* Search Box */}
          <div style={{ padding: '12px 16px', borderBottom: '1px solid rgba(255, 255, 255, 0.03)', position: 'relative' }}>
            <Search size={14} style={{ position: 'absolute', left: '26px', top: '22px', color: '#64748b' }} />
            <input 
              type="text" 
              placeholder="Search projects..." 
              value={searchQuery}
              onChange={e => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                background: '#0B0D10',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                borderRadius: '6px',
                padding: '6px 12px 6px 30px',
                color: '#fff',
                fontSize: '12px',
                outline: 'none'
              }}
            />
          </div>

          {/* Project List */}
          <div style={{ flexGrow: 1, overflowY: 'auto', padding: '12px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              {filteredProjects.length === 0 ? (
                <span style={{ fontSize: '12px', color: '#64748b', fontStyle: 'italic', padding: '8px' }}>
                  No projects found
                </span>
              ) : (
                filteredProjects.map(name => {
                  const isSelected = selectedProjectDir?.endsWith(name);
                  return (
                    <div
                      key={name}
                      onClick={() => onSelectProject(name)}
                      style={{
                        padding: '10px 12px',
                        cursor: 'pointer',
                        borderRadius: '6px',
                        background: isSelected ? 'rgba(99, 102, 241, 0.12)' : 'transparent',
                        border: '1px solid',
                        borderColor: isSelected ? 'rgba(99, 102, 241, 0.3)' : 'transparent',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '10px',
                        transition: 'all 0.15s ease'
                      }}
                    >
                      <FileVideo size={15} style={{ color: isSelected ? '#06b6d4' : '#64748b' }} />
                      <span 
                        style={{ 
                          fontSize: '12px', 
                          fontWeight: isSelected ? 600 : 400, 
                          color: isSelected ? '#fff' : '#cbd5e1', 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis', 
                          whiteSpace: 'nowrap',
                          flexGrow: 1
                        }}
                      >
                        {name}
                      </span>
                    </div>
                  );
                })
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
