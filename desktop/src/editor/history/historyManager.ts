import { CompositionState, TimelineClip } from '../state/types';

export type HistoryActionType =
  | 'ADD_CLIP'
  | 'DELETE_CLIPS'
  | 'MOVE_CLIP'
  | 'RESIZE_CLIP'
  | 'UPDATE_CLIP_PROPS'
  | 'REORDER_TRACKS'
  | 'UPDATE_COMPOSITION';

export interface HistoryEntry {
  id: string;
  type: HistoryActionType;
  description: string;
  timestamp: number;
  snapshot: CompositionState;
}

export class HistoryManager {
  private past: HistoryEntry[] = [];
  private future: HistoryEntry[] = [];
  private maxHistory: number;

  constructor(maxHistory = 50) {
    this.maxHistory = maxHistory;
  }

  push(type: HistoryActionType, description: string, snapshot: CompositionState) {
    // Clone snapshot to prevent reference mutations
    const entrySnapshot = JSON.parse(JSON.stringify(snapshot));
    this.past.push({
      id: Math.random().toString(36).substring(2, 9),
      type,
      description,
      timestamp: Date.now(),
      snapshot: entrySnapshot,
    });

    if (this.past.length > this.maxHistory) {
      this.past.shift();
    }
    // Clear redo history upon new user action
    this.future = [];
  }

  canUndo(): boolean {
    return this.past.length > 0;
  }

  canRedo(): boolean {
    return this.future.length > 0;
  }

  undo(currentState: CompositionState): CompositionState | null {
    if (!this.canUndo()) return null;
    const previous = this.past.pop()!;
    // Push current state into future stack for Redo
    this.future.push({
      id: Math.random().toString(36).substring(2, 9),
      type: previous.type,
      description: `Revert ${previous.description}`,
      timestamp: Date.now(),
      snapshot: JSON.parse(JSON.stringify(currentState)),
    });

    return previous.snapshot;
  }

  redo(currentState: CompositionState): CompositionState | null {
    if (!this.canRedo()) return null;
    const next = this.future.pop()!;
    // Push current state into past stack for Undo
    this.past.push({
      id: Math.random().toString(36).substring(2, 9),
      type: next.type,
      description: `Redo ${next.description}`,
      timestamp: Date.now(),
      snapshot: JSON.parse(JSON.stringify(currentState)),
    });

    return next.snapshot;
  }

  clear() {
    this.past = [];
    this.future = [];
  }
}
