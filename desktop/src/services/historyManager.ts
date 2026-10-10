export class HistoryManager<T> {
  private undoStack: T[] = [];
  private redoStack: T[] = [];
  private maxDepth: number;

  constructor(maxDepth = 50) {
    this.maxDepth = maxDepth;
  }

  push(state: T): void {
    const serialized = JSON.parse(JSON.stringify(state));
    this.undoStack.push(serialized);
    if (this.undoStack.length > this.maxDepth) {
      this.undoStack.shift();
    }
    this.redoStack = [];
  }

  canUndo(): boolean {
    return this.undoStack.length > 1;
  }

  canRedo(): boolean {
    return this.redoStack.length > 0;
  }

  undo(currentState: T): T | null {
    if (!this.canUndo()) return null;
    const current = this.undoStack.pop();
    if (current) {
      this.redoStack.push(JSON.parse(JSON.stringify(currentState)));
    }
    const previous = this.undoStack[this.undoStack.length - 1];
    return previous ? JSON.parse(JSON.stringify(previous)) : null;
  }

  redo(currentState: T): T | null {
    if (!this.canRedo()) return null;
    const next = this.redoStack.pop();
    if (next) {
      this.undoStack.push(JSON.parse(JSON.stringify(next)));
      return JSON.parse(JSON.stringify(next));
    }
    return null;
  }

  clear(): void {
    this.undoStack = [];
    this.redoStack = [];
  }
}
