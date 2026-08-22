import React from 'react';
import { X, Keyboard } from 'lucide-react';

interface ShortcutsModalProps {
  onClose: () => void;
}

export const ShortcutsModal: React.FC<ShortcutsModalProps> = ({ onClose }) => {
  const shortcuts = [
    { key: 'Space', desc: 'Play / Pause Video Preview' },
    { key: 'Ctrl + Z', desc: 'Undo Action' },
    { key: 'Ctrl + Shift + Z', desc: 'Redo Action' },
    { key: 'Ctrl + S', desc: 'Save Project State' },
    { key: 'Ctrl + D', desc: 'Duplicate Selected Layer/Clip' },
    { key: 'Delete / Backspace', desc: 'Delete Selected Layer/Clip' },
    { key: 'B', desc: 'Split Selected Clip at Playhead' },
    { key: 'Shift + ?', desc: 'Open Shortcuts Helper' },
  ];

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111827] border border-white/10 rounded-xl w-full max-w-md overflow-hidden shadow-2xl">
        <div className="flex items-center justify-between px-5 py-4 border-b border-white/10">
          <div className="flex items-center gap-2 text-indigo-400">
            <Keyboard className="w-5 h-5" />
            <h3 className="font-bold text-sm text-slate-100 uppercase tracking-wider">Keyboard Shortcuts</h3>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-5 space-y-3 max-h-[60vh] overflow-y-auto">
          {shortcuts.map((s, i) => (
            <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-white/5">
              <span className="text-slate-300 font-medium">{s.desc}</span>
              <kbd className="px-2 py-1 bg-slate-900 border border-white/10 rounded font-mono text-[11px] text-cyan-400 font-semibold shadow">
                {s.key}
              </kbd>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
