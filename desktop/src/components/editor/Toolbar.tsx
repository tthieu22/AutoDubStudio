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
  onRender: (preset: string) => void;
  isRendering?: boolean;
  selectedRatio: string;
  onRatioChange: (ratio: string) => void;
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
  onRender,
  isRendering = false,
  selectedRatio,
  onRatioChange,
}) => {
  return (
    <header className="editor-topbar">
      {/* LEFT: BRAND */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span style={{ fontWeight: 800, fontSize: '14px', letterSpacing: '0.5px', color: '#fff', marginLeft: '12px' }}>AutoDubStudio</span>
      </div>

      {/* CENTER: UNDO, REDO, SNAP, GUIDES */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', position: 'absolute', left: '50%', transform: 'translateX(-50%)' }}>
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

        <button
          onClick={onOpenShortcuts}
          className="editor-nav-btn"
          style={{ width: 'auto', padding: '0 10px', height: '30px', fontSize: '12px', gap: '5px' }}
          title="Xem danh sách phím tắt trợ giúp (Shift+?)"
        >
          <HelpCircle size={14} />
          <span>Help</span>
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

        <select
          value={selectedRatio}
          onChange={(e) => onRatioChange(e.target.value)}
          disabled={isRendering}
          style={{ background: '#0B0D10', border: '1px solid rgba(255, 255, 255, 0.1)', color: '#fff', padding: '6px', borderRadius: '4px', fontSize: '12px', outline: 'none' }}
        >
          <option value="16:9">YouTube (16:9)</option>
          <option value="9:16">TikTok & Shorts (9:16)</option>
          <option value="audio">Audio Only (.WAV)</option>
          <option value="srt">Subtitles Only (.SRT)</option>
        </select>

        <button
          onClick={() => onRender(selectedRatio)}
          disabled={isRendering}
          className="btn-primary"
          style={{ padding: '6px 14px', fontSize: '12px', background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)' }}
        >
          <Download size={14} /> {isRendering ? 'Rendering...' : 'Render / Export'}
        </button>
      </div>
    </header>
  );
};
