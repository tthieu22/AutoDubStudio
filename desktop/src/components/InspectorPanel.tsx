import React from 'react';
import { Sliders, X, ChevronRight, Info, Eye, Layers, Settings, ChevronLeft } from 'lucide-react';

interface InspectorPanelProps {
  title?: string;
  isCollapsed: boolean;
  onToggleCollapse: () => void;
  width: number;
  children?: React.ReactNode;
  activeTab?: string;
  onTabChange?: (tab: string) => void;
}

export const InspectorPanel: React.FC<InspectorPanelProps> = ({
  title = 'Inspector',
  isCollapsed,
  onToggleCollapse,
  width,
  children,
  activeTab = 'general',
  onTabChange
}) => {
  if (isCollapsed) {
    return (
      <aside className="w-9 bg-[#0e1015] border-l border-white/5 flex flex-col items-center py-3 flex-shrink-0 select-none z-20">
        <button
          onClick={onToggleCollapse}
          className="p-1.5 rounded-md text-slate-400 hover:text-white hover:bg-white/5 transition-all"
          title="Expand Inspector Panel"
        >
          <ChevronLeft size={16} />
        </button>
        <div className="mt-8 transform -rotate-90 origin-center text-[10px] font-extrabold tracking-widest text-slate-500 uppercase font-['Outfit'] whitespace-nowrap">
          Inspector
        </div>
      </aside>
    );
  }

  return (
    <aside
      className="bg-[#0e1015] border-l border-white/5 flex flex-col flex-shrink-0 select-none relative z-20"
      style={{ width }}
    >
      {/* INSPECTOR HEADER */}
      <div className="h-10 px-3 bg-[#111318] border-b border-white/5 flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-2 text-xs font-bold text-slate-200 font-['Outfit']">
          <Sliders size={14} className="text-indigo-400" />
          <span className="truncate">{title}</span>
        </div>

        <button
          onClick={onToggleCollapse}
          className="p-1 rounded text-slate-400 hover:text-white hover:bg-white/10 transition-all"
          title="Collapse Inspector"
        >
          <ChevronRight size={15} />
        </button>
      </div>

      {/* INSPECTOR CONTENT CONTAINER */}
      <div className="flex-1 overflow-y-auto p-3 custom-scrollbar text-xs">
        {children || (
          <div className="h-full flex flex-col items-center justify-center text-center p-4 text-slate-500">
            <Info size={32} className="mb-2 text-slate-600" />
            <p className="font-medium text-slate-400">No Item Selected</p>
            <p className="text-[11px] mt-1">Select a scene, clip, segment, or character to view properties in the Inspector.</p>
          </div>
        )}
      </div>
    </aside>
  );
};
