import React from 'react';
import { 
  Activity, FileText, Layers, Mic, ShieldCheck, 
  Terminal, Video, Share2, Settings, ArrowLeft 
} from 'lucide-react';

interface EditorNavigationTabsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  onBackToPipeline: () => void;
}

export const EditorNavigationTabs: React.FC<EditorNavigationTabsProps> = ({
  activeTab,
  onTabChange,
  onBackToPipeline
}) => {
  const tabs = [
    { id: 'timeline', label: 'Timeline & Layers', icon: Layers },
    { id: 'subtitles', label: 'Sửa Phụ Đề', icon: FileText },
    { id: 'voices', label: 'Voice Studio (TTS)', icon: Mic },
    { id: 'pipeline', label: 'Tiến Trình (Pipeline)', icon: Activity },
    { id: 'qc', label: 'Quality Control (QC)', icon: ShieldCheck },
    { id: 'preview', label: 'Xem Trước Video', icon: Video },
    { id: 'export', label: 'Export Presets', icon: Share2 },
    { id: 'logs', label: 'Console Logs', icon: Terminal },
    { id: 'settings', label: 'Cấu Hình', icon: Settings },
  ];

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '4px',
      backgroundColor: '#0d111a',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      padding: '0 16px',
      overflowX: 'auto',
      height: '44px',
      minHeight: '44px',
      userSelect: 'none'
    }}>
      {tabs.map(tab => {
        const Icon = tab.icon;
        const isActive = activeTab === tab.id;

        return (
          <button
            key={tab.id}
            onClick={() => onTabChange(tab.id)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '8px 12px',
              fontSize: '12px',
              fontWeight: isActive ? 700 : 500,
              color: isActive ? '#38bdf8' : '#94a3b8',
              backgroundColor: isActive ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
              border: 'none',
              borderBottom: isActive ? '2px solid #38bdf8' : '2px solid transparent',
              cursor: 'pointer',
              whiteSpace: 'nowrap',
              transition: 'all 0.15s ease'
            }}
          >
            <Icon size={14} color={isActive ? '#38bdf8' : '#94a3b8'} />
            <span>{tab.label}</span>
          </button>
        );
      })}
    </div>
  );
};
