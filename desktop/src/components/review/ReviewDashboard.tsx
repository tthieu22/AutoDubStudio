import React, { useState } from 'react';
import { 
  CheckCircle2, 
  XCircle, 
  Eye, 
  RefreshCw, 
  Edit3, 
  Lock, 
  ShieldCheck, 
  Sparkles, 
  Layers, 
  ArrowRight,
  Sliders,
  Check
} from 'lucide-react';
import { SidebarTab } from '../Sidebar';

interface ReviewDashboardProps {
  onNavigateTab?: (tab: SidebarTab) => void;
  onApproveAll?: () => void;
}

interface ReviewModuleItem {
  id: string;
  name: string;
  tab: SidebarTab;
  status: 'APPROVED' | 'REVIEW_REQUIRED' | 'REJECTED' | 'WAITING';
  itemsCount: string;
  description: string;
}

export const ReviewDashboard: React.FC<ReviewDashboardProps> = ({ onNavigateTab, onApproveAll }) => {
  const [modules, setModules] = useState<ReviewModuleItem[]>([
    { id: 'm-1', name: 'Story & Narrative Structure', tab: 'story', status: 'APPROVED', itemsCount: '2 Chapters', description: 'Chapters breakdown and story flow outline.' },
    { id: 'm-2', name: 'Character Bible', tab: 'characters', status: 'APPROVED', itemsCount: '2 Characters', description: 'Character appearances, personalities, and TTS voices.' },
    { id: 'm-3', name: 'Scene Board', tab: 'scenes', status: 'APPROVED', itemsCount: '8/10 Scenes', description: 'Visual prompts, location settings, dialogue timings.' },
    { id: 'm-4', name: 'AI Image Keyframes', tab: 'images', status: 'APPROVED', itemsCount: '7/10 Images', description: 'Generated Stable Diffusion concept images.' },
    { id: 'm-5', name: 'TTS Voice Audio', tab: 'voice', status: 'APPROVED', itemsCount: '10/10 Clips', description: 'Piper TTS character voice synthesis audio clips.' },
    { id: 'm-6', name: 'Subtitle Timing', tab: 'subtitles', status: 'APPROVED', itemsCount: '10/10 Subs', description: 'Subtitle alignment, formatting, and positioning.' },
    { id: 'm-7', name: 'Timeline Composition', tab: 'timeline', status: 'REVIEW_REQUIRED', itemsCount: 'Review Required', description: 'Multi-track composition, audioducking, transitions.' },
    { id: 'm-8', name: 'Final Video Render', tab: 'render', status: 'WAITING', itemsCount: 'Pending Gate', description: 'Final composition rendering and video export.' }
  ]);

  const updateModuleStatus = (id: string, status: ReviewModuleItem['status']) => {
    setModules(prev => prev.map(m => m.id === id ? { ...m, status } : m));
  };

  const getStatusBadge = (st: ReviewModuleItem['status']) => {
    switch (st) {
      case 'APPROVED':
        return <span className="px-2.5 py-1 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-extrabold tracking-wider flex items-center gap-1">✓ APPROVED</span>;
      case 'REVIEW_REQUIRED':
        return <span className="px-2.5 py-1 rounded-md bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-extrabold tracking-wider flex items-center gap-1 animate-pulse">! REVIEW REQUIRED</span>;
      case 'REJECTED':
        return <span className="px-2.5 py-1 rounded-md bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs font-extrabold tracking-wider flex items-center gap-1">× REJECTED</span>;
      case 'WAITING':
      default:
        return <span className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-slate-400 text-xs font-extrabold tracking-wider">○ WAITING</span>;
    }
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/20">
            <ShieldCheck size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Project Review Dashboard & Quality Gates
            </h2>
            <p className="text-xs text-slate-400">
              Audit AI generated outputs across every pipeline module before final rendering.
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            setModules(prev => prev.map(m => ({ ...m, status: 'APPROVED' })));
            onApproveAll?.();
          }}
          className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-emerald-600/20 transition-all"
        >
          <CheckCircle2 size={14} /> Approve All Modules ➔
        </button>
      </div>

      {/* MODULE REVIEW CARDS LIST */}
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {modules.map(m => (
          <div key={m.id} className="p-4 rounded-xl bg-[#111318] border border-white/5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <h3 className="text-sm font-bold text-white font-['Outfit']">{m.name}</h3>
                <span className="text-xs font-mono text-slate-500">• {m.itemsCount}</span>
              </div>
              <p className="text-xs text-slate-400">{m.description}</p>
            </div>

            <div className="flex items-center gap-3 flex-shrink-0">
              {getStatusBadge(m.status)}

              <button
                onClick={() => onNavigateTab?.(m.tab)}
                className="px-3 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-200 border border-white/10 text-xs font-semibold flex items-center gap-1 transition-all"
              >
                <Eye size={13} /> Inspect
              </button>

              <button
                onClick={() => updateModuleStatus(m.id, 'APPROVED')}
                className="px-3 py-1.5 rounded-lg bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-300 border border-emerald-500/30 text-xs font-bold transition-all"
              >
                Approve
              </button>

              <button
                onClick={() => updateModuleStatus(m.id, 'REJECTED')}
                className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 border border-rose-500/30 text-xs font-bold transition-all"
              >
                Reject
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
