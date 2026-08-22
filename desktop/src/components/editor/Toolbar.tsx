import React from 'react';
import { 
  Undo, Redo, Save, Download, Play, Pause,
  Grid, HelpCircle, Magnet, ArrowLeft
} from 'lucide-react';

interface ToolbarProps {
  projectName: string;
  isSaving: boolean;
  lastSavedAt: string | null;
  canUndo: boolean;
  canRedo: boolean;
  showSafeArea: boolean;
  snappingEnabled: boolean;
  onUndo: () => void;
  onRedo: () => void;
  onSave: () => void;
  onToggleSafeArea: () => void;
  onToggleSnapping: () => void;
  onOpenShortcuts: () => void;
  onBackToApp?: () => void;
}

export const Toolbar: React.FC<ToolbarProps> = ({
  projectName,
  isSaving,
  lastSavedAt,
  canUndo,
  canRedo,
  showSafeArea,
  snappingEnabled,
  onUndo,
  onRedo,
  onSave,
  onToggleSafeArea,
  onToggleSnapping,
  onOpenShortcuts,
  onBackToApp,
}) => {
  return (
    <header className="editor-topbar">
      {/* LEFT: BACK BUTTON + BRAND + PROJECT NAME */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        {onBackToApp && (
          <button
            onClick={onBackToApp}
            className="editor-nav-btn"
            style={{ width: '32px', height: '32px' }}
            title="Quay lại bảng điều khiển chính"
          >
            <ArrowLeft size={16} />
          </button>
        )}

        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <div className="editor-brand-badge">
            AD
          </div>
          <span style={{ fontWeight: 800, fontSize: '14px', letterSpacing: '0.5px' }} className="gradient-text">
            AutoDubStudio
          </span>
        </div>

        <div style={{ height: '16px', width: '1px', backgroundColor: 'rgba(255, 255, 255, 0.1)' }} />

        <div className="editor-project-pill">
          <span style={{ fontWeight: 600 }}>{projectName}</span>
          <span style={{ color: '#64748b', fontSize: '10px' }}>▼</span>
        </div>
      </div>

      {/* CENTER: UNDO, REDO, SNAP, GUIDES */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
        <button
          onClick={onUndo}
          disabled={!canUndo}
          className="editor-nav-btn"
          style={{ width: '32px', height: '32px', opacity: canUndo ? 1 : 0.4, cursor: canUndo ? 'pointer' : 'not-allowed' }}
          title="Undo (Ctrl+Z)"
        >
          <Undo size={15} />
        </button>
        <button
          onClick={onRedo}
          disabled={!canRedo}
          className="editor-nav-btn"
          style={{ width: '32px', height: '32px', opacity: canRedo ? 1 : 0.4, cursor: canRedo ? 'pointer' : 'not-allowed' }}
          title="Redo (Ctrl+Shift+Z)"
        >
          <Redo size={15} />
        </button>

        <div style={{ height: '16px', width: '1px', backgroundColor: 'rgba(255, 255, 255, 0.1)', margin: '0 4px' }} />

        <button
          onClick={onToggleSnapping}
          className={`editor-nav-btn ${snappingEnabled ? 'active' : ''}`}
          style={{ width: 'auto', padding: '0 10px', height: '30px', fontSize: '12px', gap: '5px' }}
          title="Bật/Tắt tự động hút mốc (Snapping)"
        >
          <Magnet size={14} />
          <span>Snap</span>
        </button>

        <button
          onClick={onToggleSafeArea}
          className={`editor-nav-btn ${showSafeArea ? 'active' : ''}`}
          style={{ width: 'auto', padding: '0 10px', height: '30px', fontSize: '12px', gap: '5px' }}
          title="Bật/Tắt đường lưới an toàn (Safe Area Guides)"
        >
          <Grid size={14} />
          <span>Guides</span>
        </button>
      </div>

      {/* RIGHT: SAVE STATUS + SAVE + EXPORT */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <div style={{ fontSize: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
          {isSaving ? (
            <span style={{ color: '#f59e0b', fontWeight: 600 }}>Đang lưu...</span>
          ) : (
            <span style={{ color: '#10b981', fontWeight: 500 }}>
              ✓ Đã lưu {lastSavedAt && <span style={{ color: '#64748b', fontSize: '11px' }}>({lastSavedAt})</span>}
            </span>
          )}
        </div>

        <button
          onClick={onSave}
          className="btn-secondary"
          style={{ padding: '6px 12px', fontSize: '12px' }}
        >
          <Save size={14} /> Lưu (Ctrl+S)
        </button>

        <button
          onClick={() => alert('Xuất bản render video chất lượng cao với các layer...')}
          className="btn-primary"
          style={{ padding: '6px 14px', fontSize: '12px' }}
        >
          <Download size={14} /> Render / Export
        </button>
      </div>
    </header>
  );
};
