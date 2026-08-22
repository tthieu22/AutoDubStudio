import React from 'react';

interface TimelineToolbarProps {
  onUndo: () => void;
  onRedo: () => void;
  canUndo: boolean;
  canRedo: boolean;
  onAddLayer: (type: 'title' | 'text' | 'logo' | 'image') => void;
}

export const TimelineToolbar: React.FC<TimelineToolbarProps> = ({
  onUndo,
  onRedo,
  canUndo,
  canRedo,
  onAddLayer
}) => {
  return (
    <div className="flex items-center justify-between bg-slate-900/90 border border-slate-800 rounded-xl p-4 shadow-lg backdrop-blur-md">
      <div className="flex items-center space-x-3">
        <div className="bg-indigo-600/20 text-indigo-400 p-2 rounded-lg border border-indigo-500/30">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 4v16M17 4v16M3 8h18M3 16h18" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-bold tracking-wide">Multi-Track Video Timeline & Layer Studio</h2>
          <p className="text-xs text-slate-400">Interactive Layer Composition & Timeline Editor</p>
        </div>
      </div>

      <div className="flex items-center space-x-2">
        <button
          onClick={onUndo}
          disabled={!canUndo}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-xs font-semibold rounded-lg border border-slate-700 transition"
        >
          ↩ Undo (Ctrl+Z)
        </button>
        <button
          onClick={onRedo}
          disabled={!canRedo}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-40 text-xs font-semibold rounded-lg border border-slate-700 transition"
        >
          ↪ Redo (Ctrl+Y)
        </button>
        <div className="h-6 w-px bg-slate-800 mx-2" />
        <button
          onClick={() => onAddLayer('title')}
          className="px-3 py-1.5 bg-indigo-600 hover:bg-indigo-500 text-xs font-bold text-white rounded-lg shadow-lg shadow-indigo-600/30 transition"
        >
          + Add Title
        </button>
        <button
          onClick={() => onAddLayer('text')}
          className="px-3 py-1.5 bg-slate-800 hover:bg-slate-700 text-xs font-bold text-slate-200 rounded-lg border border-slate-700 transition"
        >
          + Add Text
        </button>
        <button
          onClick={() => onAddLayer('logo')}
          className="px-3 py-1.5 bg-cyan-600 hover:bg-cyan-500 text-xs font-bold text-white rounded-lg shadow-lg shadow-cyan-600/30 transition"
        >
          + Add Logo Watermark
        </button>
      </div>
    </div>
  );
};
