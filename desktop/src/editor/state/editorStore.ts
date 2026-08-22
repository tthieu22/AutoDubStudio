import { CompositionState, EditorUiState, TimelineClip, Track, LayerType } from './types';
import { HistoryManager, HistoryActionType } from '../history/historyManager';

export const INITIAL_TRACKS: Track[] = [
  { id: 'track-video', name: 'Video 1', type: 'video', muted: false, locked: false, height: 50, color: '#3b82f6' },
  { id: 'track-subtitle', name: 'Subtitles', type: 'subtitle', muted: false, locked: false, height: 44, color: '#f59e0b' },
  { id: 'track-text', name: 'Text & Titles', type: 'text', muted: false, locked: false, height: 44, color: '#ec4899' },
  { id: 'track-image', name: 'Images & Logos', type: 'image', muted: false, locked: false, height: 44, color: '#8b5cf6' },
  { id: 'track-audio', name: 'Dubbed Voice', type: 'audio', muted: false, locked: false, height: 44, color: '#10b981' },
];

export const INITIAL_COMPOSITION: CompositionState = {
  id: 'proj-default',
  name: 'Untitled Project',
  width: 1920,
  height: 1080,
  fps: 30,
  duration: 180, // 3 minutes default
  tracks: INITIAL_TRACKS,
  clips: [
    {
      id: 'demo-title',
      name: 'Welcome Title',
      type: 'text',
      trackId: 'track-text',
      startTime: 2,
      duration: 5,
      visible: true,
      locked: false,
      opacity: 1,
      zIndex: 10,
      x: 50, // center %
      y: 20, // top 20%
      width: 40,
      height: 15,
      rotation: 0,
      scaleX: 1,
      scaleY: 1,
      textProps: {
        content: 'AutoDub Studio AI Editor',
        fontFamily: 'Outfit',
        fontSize: 48,
        fontWeight: 'bold',
        color: '#38bdf8',
        textAlign: 'center',
      },
    },
    {
      id: 'demo-sub-1',
      name: 'Subtitle 1',
      type: 'subtitle',
      trackId: 'track-subtitle',
      startTime: 1.5,
      duration: 3.5,
      visible: true,
      locked: false,
      opacity: 1,
      zIndex: 5,
      x: 50,
      y: 85,
      width: 60,
      height: 10,
      rotation: 0,
      scaleX: 1,
      scaleY: 1,
      subtitleProps: {
        text: 'Chào mừng bạn đến với trình chỉnh sửa video AI tự động!',
        fontFamily: 'Plus Jakarta Sans',
        fontSize: 24,
        color: '#ffffff',
        backgroundColor: 'rgba(0, 0, 0, 0.75)',
      },
    },
  ],
};

export const INITIAL_UI_STATE: EditorUiState = {
  currentTime: 0,
  isPlaying: false,
  zoomLevel: 50, // 50px per sec
  selectedClipIds: ['demo-title'],
  activeLeftTab: 'media',
  showSafeArea: true,
  snapping: {
    enabled: true,
    snapToPlayhead: true,
    snapToClipEdges: true,
    snapToGrid: true,
    thresholdPx: 8,
  },
  splitMode: false,
  isSaving: false,
  lastSavedAt: new Date().toLocaleTimeString(),
};

type Listener = () => void;

class EditorStore {
  private composition: CompositionState = INITIAL_COMPOSITION;
  private uiState: EditorUiState = INITIAL_UI_STATE;
  private historyManager = new HistoryManager(50);
  private listeners: Set<Listener> = new Set();

  public subscribe(listener: Listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notify() {
    this.listeners.forEach((l) => l());
  }

  public getComposition(): CompositionState {
    return this.composition;
  }

  public getUiState(): EditorUiState {
    return this.uiState;
  }

  public setComposition(newComp: CompositionState, recordHistory = true, actionType: HistoryActionType = 'UPDATE_COMPOSITION', actionDesc = 'Update composition') {
    if (recordHistory) {
      this.historyManager.push(actionType, actionDesc, this.composition);
    }
    this.composition = newComp;
    this.notify();
  }

  public setUiState(partialUi: Partial<EditorUiState>) {
    this.uiState = { ...this.uiState, ...partialUi };
    this.notify();
  }

  public selectClip(clipId: string, multiSelect = false) {
    let newSelected: string[];
    if (multiSelect) {
      if (this.uiState.selectedClipIds.includes(clipId)) {
        newSelected = this.uiState.selectedClipIds.filter((id) => id !== clipId);
      } else {
        newSelected = [...this.uiState.selectedClipIds, clipId];
      }
    } else {
      newSelected = [clipId];
    }
    this.setUiState({ selectedClipIds: newSelected });
  }

  public clearSelection() {
    this.setUiState({ selectedClipIds: [] });
  }

  public updateClip(clipId: string, updates: Partial<TimelineClip>, recordHistory = false) {
    const updatedClips = this.composition.clips.map((clip) => {
      if (clip.id !== clipId) return clip;
      return { ...clip, ...updates };
    });

    const newComp = { ...this.composition, clips: updatedClips };
    if (recordHistory) {
      this.setComposition(newComp, true, 'RESIZE_CLIP', `Update clip ${clipId}`);
    } else {
      this.composition = newComp;
      this.notify();
    }
  }

  public addClip(clip: TimelineClip) {
    const newComp = {
      ...this.composition,
      clips: [...this.composition.clips, clip],
    };
    this.setComposition(newComp, true, 'ADD_CLIP', `Add layer clip ${clip.name}`);
    this.selectClip(clip.id);
  }

  public deleteSelectedClips() {
    if (this.uiState.selectedClipIds.length === 0) return;
    const idsToRemove = new Set(this.uiState.selectedClipIds);
    const remainingClips = this.composition.clips.filter((c) => !idsToRemove.has(c.id));
    const newComp = { ...this.composition, clips: remainingClips };
    this.setComposition(newComp, true, 'DELETE_CLIPS', `Delete ${idsToRemove.size} clip(s)`);
    this.setUiState({ selectedClipIds: [] });
  }

  public duplicateSelectedClips() {
    if (this.uiState.selectedClipIds.length === 0) return;
    const selectedClips = this.composition.clips.filter((c) => this.uiState.selectedClipIds.includes(c.id));
    const duplicatedClips: TimelineClip[] = selectedClips.map((c) => ({
      ...JSON.parse(JSON.stringify(c)),
      id: `clip-${Math.random().toString(36).substring(2, 9)}`,
      name: `${c.name} (Copy)`,
      startTime: c.startTime + 0.5,
    }));

    const newComp = {
      ...this.composition,
      clips: [...this.composition.clips, ...duplicatedClips],
    };

    this.setComposition(newComp, true, 'ADD_CLIP', 'Duplicate clip(s)');
    this.setUiState({ selectedClipIds: duplicatedClips.map((c) => c.id) });
  }

  public splitClipAtPlayhead(clipId: string) {
    const clip = this.composition.clips.find((c) => c.id === clipId);
    if (!clip) return;
    const playhead = this.uiState.currentTime;

    if (playhead <= clip.startTime || playhead >= clip.startTime + clip.duration) {
      return; // Playhead not inside clip
    }

    const firstDuration = playhead - clip.startTime;
    const secondDuration = clip.duration - firstDuration;

    const firstClip: TimelineClip = { ...clip, duration: firstDuration };
    const secondClip: TimelineClip = {
      ...JSON.parse(JSON.stringify(clip)),
      id: `clip-${Math.random().toString(36).substring(2, 9)}`,
      name: `${clip.name} (Part 2)`,
      startTime: playhead,
      duration: secondDuration,
    };

    const newClips = this.composition.clips
      .filter((c) => c.id !== clipId)
      .concat([firstClip, secondClip]);

    const newComp = { ...this.composition, clips: newClips };
    this.setComposition(newComp, true, 'RESIZE_CLIP', `Split clip ${clip.name}`);
    this.selectClip(secondClip.id);
  }

  public undo() {
    const prev = this.historyManager.undo(this.composition);
    if (prev) {
      this.composition = prev;
      this.notify();
    }
  }

  public redo() {
    const next = this.historyManager.redo(this.composition);
    if (next) {
      this.composition = next;
      this.notify();
    }
  }

  public canUndo(): boolean {
    return this.historyManager.canUndo();
  }

  public canRedo(): boolean {
    return this.historyManager.canRedo();
  }
}

export const editorStore = new EditorStore();
