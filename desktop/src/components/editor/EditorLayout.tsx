import React, { useState, useEffect } from 'react';
import { editorStore } from '../../editor/state/editorStore';
import { CompositionState, EditorUiState } from '../../editor/state/types';
import { 
  Film, Layers, Type, Music, HelpCircle
} from 'lucide-react';
import { VideoCanvas } from './VideoCanvas';
import { Timeline } from './Timeline';
import { MediaPanel } from './MediaPanel';
import { Inspector } from './Inspector';
import { LayerPanel } from './LayerPanel';
import { Toolbar } from './Toolbar';
import { ShortcutsModal } from './ShortcutsModal';

interface EditorLayoutProps {
  onBackToApp?: () => void;
  onRender?: (preset: string) => void;
  isRendering?: boolean;
}

export const EditorLayout: React.FC<EditorLayoutProps> = ({ 
  onBackToApp,
  onRender,
  isRendering = false,
}) => {
  const [comp, setComp] = useState<CompositionState>(editorStore.getComposition());
  const [uiState, setUiState] = useState<EditorUiState>(editorStore.getUiState());
  const [leftTab, setLeftTab] = useState<'media' | 'layers' | 'text' | 'audio'>('media');
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [selectedRatio, setSelectedRatio] = useState<string>('16:9');
  
  useEffect(() => {
    if (comp.width === 1080 && comp.height === 1920) {
      setSelectedRatio('9:16');
    } else if (comp.width === 1920 && comp.height === 1080) {
      setSelectedRatio('16:9');
    }
  }, [comp.width, comp.height]);

  const handleRatioChange = (ratio: string) => {
    setSelectedRatio(ratio);
    if (ratio === '16:9') {
      editorStore.setComposition({
        ...comp,
        width: 1920,
        height: 1080
      }, true);
    } else if (ratio === '9:16') {
      editorStore.setComposition({
        ...comp,
        width: 1080,
        height: 1920
      }, true);
    }
  };
  
  // Resizable panel states
  const [leftCollapsed, setLeftCollapsed] = useState(false);
  const [leftWidth, setLeftWidth] = useState(280);
  const [rightWidth, setRightWidth] = useState(280);
  const [timelineHeight, setTimelineHeight] = useState(260);
  
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);
  const [isResizingTimeline, setIsResizingTimeline] = useState(false);

  useEffect(() => {
    const unsubscribe = editorStore.subscribe(() => {
      setComp(editorStore.getComposition());
      setUiState(editorStore.getUiState());
    });
    return () => {
      unsubscribe();
    };
  }, []);

  // Panel resize drag listeners
  useEffect(() => {
    const handlePointerMove = (e: MouseEvent) => {
      if (isResizingLeft) {
        setLeftWidth(Math.max(180, Math.min(500, e.clientX - 52)));
      } else if (isResizingRight) {
        setRightWidth(Math.max(200, Math.min(500, window.innerWidth - e.clientX)));
      } else if (isResizingTimeline) {
        setTimelineHeight(Math.max(160, Math.min(500, window.innerHeight - e.clientY)));
      }
    };

    const handlePointerUp = () => {
      setIsResizingLeft(false);
      setIsResizingRight(false);
      setIsResizingTimeline(false);
    };

    if (isResizingLeft || isResizingRight || isResizingTimeline) {
      window.addEventListener('mousemove', handlePointerMove);
      window.addEventListener('mouseup', handlePointerUp);
    }
    return () => {
      window.removeEventListener('mousemove', handlePointerMove);
      window.removeEventListener('mouseup', handlePointerUp);
    };
  }, [isResizingLeft, isResizingRight, isResizingTimeline]);

  // Keyboard shortcut listener
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      if (e.code === 'Space') {
        e.preventDefault();
        editorStore.setUiState({ isPlaying: !uiState.isPlaying });
      } else if (e.ctrlKey && e.code === 'KeyZ') {
        e.preventDefault();
        if (e.shiftKey) editorStore.redo();
        else editorStore.undo();
      } else if (e.ctrlKey && e.code === 'KeyS') {
        e.preventDefault();
        editorStore.setUiState({ isSaving: true });
        setTimeout(() => {
          editorStore.setUiState({ isSaving: false, lastSavedAt: new Date().toLocaleTimeString() });
        }, 500);
      } else if (e.ctrlKey && e.code === 'KeyD') {
        e.preventDefault();
        editorStore.duplicateSelectedClips();
      } else if (e.code === 'Delete' || e.code === 'Backspace') {
        e.preventDefault();
        editorStore.deleteSelectedClips();
      } else if (e.code === 'KeyB') {
        e.preventDefault();
        if (uiState.selectedClipIds.length > 0) {
          editorStore.splitClipAtPlayhead(uiState.selectedClipIds[0]);
        }
      } else if (e.code === 'Slash' && e.shiftKey) {
        e.preventDefault();
        setShowShortcuts(true);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [uiState]);

  return (
    <div className="editor-root">
      {/* 1. TOP BAR */}
      <Toolbar 
        projectName={comp.name}
        isSaving={uiState.isSaving}
        lastSavedAt={uiState.lastSavedAt}
        canUndo={editorStore.canUndo()}
        canRedo={editorStore.canRedo()}
        showSafeArea={uiState.showSafeArea}
        snappingEnabled={uiState.snapping.enabled}
        onUndo={() => editorStore.undo()}
        onRedo={() => editorStore.redo()}
        onSave={() => {
          editorStore.setUiState({ isSaving: true });
          setTimeout(() => editorStore.setUiState({ isSaving: false, lastSavedAt: new Date().toLocaleTimeString() }), 500);
        }}
        onToggleSafeArea={() => editorStore.setUiState({ showSafeArea: !uiState.showSafeArea })}
        onToggleSnapping={() => editorStore.setUiState({ 
          snapping: { ...uiState.snapping, enabled: !uiState.snapping.enabled } 
        })}
        onOpenShortcuts={() => setShowShortcuts(true)}
        onBackToApp={onBackToApp}
        onRender={onRender || ((p) => alert('Render preset: ' + p))}
        isRendering={isRendering}
        selectedRatio={selectedRatio}
        onRatioChange={handleRatioChange}
      />

      {/* 2. MAIN WORKSPACE (LEFT NAV + LEFT PANEL | CENTER CANVAS | RIGHT INSPECTOR) */}
      <div className="editor-workspace">
        {/* LEFT NAV ICON BAR */}
        <div className="editor-left-nav">
          <button
            onClick={() => {
              if (leftTab === 'media' && !leftCollapsed) setLeftCollapsed(true);
              else { setLeftTab('media'); setLeftCollapsed(false); }
            }}
            className={`editor-nav-btn ${leftTab === 'media' && !leftCollapsed ? 'active' : ''}`}
            title="Media Assets (Ấn để ẩn/hiện panel)"
          >
            <Film size={18} />
          </button>
          <button
            onClick={() => {
              if (leftTab === 'layers' && !leftCollapsed) setLeftCollapsed(true);
              else { setLeftTab('layers'); setLeftCollapsed(false); }
            }}
            className={`editor-nav-btn ${leftTab === 'layers' && !leftCollapsed ? 'active' : ''}`}
            title="Layer Hierarchy (Ấn để ẩn/hiện panel)"
          >
            <Layers size={18} />
          </button>
          <button
            onClick={() => {
              if (leftTab === 'text' && !leftCollapsed) setLeftCollapsed(true);
              else { setLeftTab('text'); setLeftCollapsed(false); }
            }}
            className={`editor-nav-btn ${leftTab === 'text' && !leftCollapsed ? 'active' : ''}`}
            title="Text & Titles (Ấn để ẩn/hiện panel)"
          >
            <Type size={18} />
          </button>
          <button
            onClick={() => {
              if (leftTab === 'audio' && !leftCollapsed) setLeftCollapsed(true);
              else { setLeftTab('audio'); setLeftCollapsed(false); }
            }}
            className={`editor-nav-btn ${leftTab === 'audio' && !leftCollapsed ? 'active' : ''}`}
            title="Audio & Dubbing (Ấn để ẩn/hiện panel)"
          >
            <Music size={18} />
          </button>
          <div style={{ marginTop: 'auto' }}>
            <button
              onClick={() => setShowShortcuts(true)}
              className="editor-nav-btn"
              title="Phím tắt trợ giúp (?)"
            >
              <HelpCircle size={18} />
            </button>
          </div>
        </div>

        {/* LEFT PANEL CONTENT */}
        {!leftCollapsed && (
          <div 
            className="editor-side-panel"
            style={{ width: `${leftWidth}px`, minWidth: `${leftWidth}px` }}
          >
            {leftTab === 'media' && <MediaPanel />}
            {leftTab === 'layers' && <LayerPanel composition={comp} selectedClipIds={uiState.selectedClipIds} />}
            {leftTab === 'text' && (
              <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid rgba(255, 255, 255, 0.08)', paddingBottom: '10px' }}>
                  <h3 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px', color: '#f1f5f9', margin: 0 }}>
                    Text & Titles
                  </h3>
                </div>
                <button
                  onClick={() => {
                    editorStore.addClip({
                      id: `text-${Date.now()}`,
                      name: 'Text Layer',
                      type: 'text',
                      trackId: 'track-text',
                      startTime: uiState.currentTime,
                      duration: 4,
                      visible: true,
                      locked: false,
                      opacity: 1,
                      zIndex: 10,
                      x: 50,
                      y: 50,
                      width: 30,
                      height: 12,
                      rotation: 0,
                      scaleX: 1,
                      scaleY: 1,
                      textProps: {
                        content: 'Tiêu Đề Mới',
                        fontFamily: 'Outfit',
                        fontSize: 36,
                        fontWeight: 'bold',
                        color: '#ffffff',
                        textAlign: 'center',
                      },
                    });
                  }}
                  className="btn-primary"
                  style={{ width: '100%', justifyContent: 'center', padding: '10px' }}
                >
                  <Type size={16} /> + Thêm Layer Chữ (Text)
                </button>
              </div>
            )}
            {leftTab === 'audio' && (
              <div style={{ padding: '16px', fontSize: '12px', color: '#94a3b8' }}>
                <h3 style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#f1f5f9', marginBottom: '8px' }}>
                  Voice & Dubbing Audio
                </h3>
                <p>Kênh giọng lồng tiếng AI đồng bộ mượt mà với Video.</p>
              </div>
            )}

            {/* RESIZE HANDLE LEFT */}
            <div 
              onMouseDown={() => setIsResizingLeft(true)}
              className={`editor-resizer-vertical ${isResizingLeft ? 'resizing' : ''}`}
              style={{ right: 0 }}
            />
          </div>
        )}

        {/* CENTER VIDEO CANVAS */}
        <div className="editor-canvas-container">
          <VideoCanvas 
            composition={comp} 
            selectedClipIds={uiState.selectedClipIds} 
            showSafeArea={uiState.showSafeArea}
            currentTime={uiState.currentTime}
            isPlaying={uiState.isPlaying}
          />
        </div>

        {/* RIGHT INSPECTOR */}
        <div 
          className="editor-inspector-panel"
          style={{ width: `${rightWidth}px`, minWidth: `${rightWidth}px` }}
        >
          {/* RESIZE HANDLE RIGHT */}
          <div 
            onMouseDown={() => setIsResizingRight(true)}
            className={`editor-resizer-vertical ${isResizingRight ? 'resizing' : ''}`}
            style={{ left: 0 }}
          />
          <Inspector composition={comp} selectedClipIds={uiState.selectedClipIds} />
        </div>
      </div>

      {/* RESIZE HANDLE TIMELINE TOP */}
      <div 
        onMouseDown={() => setIsResizingTimeline(true)}
        className={`editor-resizer-horizontal ${isResizingTimeline ? 'resizing' : ''}`}
      />

      {/* 3. BOTTOM TIMELINE CONTAINER */}
      <div 
        style={{ height: `${timelineHeight}px`, minHeight: '160px' }} 
        className="editor-timeline-panel"
      >
        <Timeline 
          composition={comp}
          uiState={uiState}
          onPlayheadChange={(time) => editorStore.setUiState({ currentTime: time })}
        />
      </div>

      {showShortcuts && <ShortcutsModal onClose={() => setShowShortcuts(false)} />}
    </div>
  );
};
