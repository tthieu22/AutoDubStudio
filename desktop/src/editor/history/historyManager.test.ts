import { describe, it, expect, beforeEach } from 'vitest';
import { HistoryManager } from './historyManager';
import { CompositionState } from '../state/types';

describe('HistoryManager', () => {
  let historyManager: HistoryManager;
  let sampleState: CompositionState;

  beforeEach(() => {
    historyManager = new HistoryManager(10);
    sampleState = {
      id: 'proj-1',
      name: 'Test Project',
      width: 1920,
      height: 1080,
      fps: 30,
      duration: 60,
      tracks: [],
      clips: [],
    };
  });

  it('starts with empty stacks', () => {
    expect(historyManager.canUndo()).toBe(false);
    expect(historyManager.canRedo()).toBe(false);
  });

  it('pushes state and enables undo', () => {
    historyManager.push('ADD_CLIP', 'Add text clip', sampleState);
    expect(historyManager.canUndo()).toBe(true);
    expect(historyManager.canRedo()).toBe(false);
  });

  it('handles undo and redo correctly', () => {
    const modifiedState = { ...sampleState, name: 'Modified Project' };
    historyManager.push('UPDATE_COMPOSITION', 'Rename project', sampleState);

    const undoneState = historyManager.undo(modifiedState);
    expect(undoneState).not.toBeNull();
    expect(undoneState?.name).toBe('Test Project');
    expect(historyManager.canRedo()).toBe(true);

    const redoneState = historyManager.redo(undoneState!);
    expect(redoneState).not.toBeNull();
    expect(redoneState?.name).toBe('Modified Project');
  });
});
