import React from 'react';
import { 
  Play, 
  Pause, 
  RefreshCw, 
  Square, 
  CheckCircle2, 
  Eye, 
  Activity, 
  Cpu, 
  HardDrive, 
  Thermometer, 
  Terminal, 
  Lock, 
  CheckCircle, 
  XCircle,
  FileVideo,
  Clock,
  Layers,
  ArrowRight,
  AlertTriangle,
  ChevronRight,
  Sparkles
} from 'lucide-react';
import { PipelineStatus, StageName, StageProgressInfo, HardwareTelemetry, PipelineMode } from '../types/pipeline';
import { SidebarTab } from './Sidebar';

interface DashboardProps {
  projectName: string;
  mode: PipelineMode;
  status: PipelineStatus;
  overallProgress: number;
  stageProgresses: Partial<Record<StageName, StageProgressInfo>>;
  telemetry: HardwareTelemetry;
  logs: string[];
  onStart: () => void;
  onPause: () => void;
  onResume: () => void;
  onRetry: () => void;
  onCancel: () => void;
  onReview: () => void;
  onApproveGate?: () => void;
  onRejectGate?: () => void;
  onNavigateTab?: (tab: SidebarTab) => void;
}

interface StepNode {
  key: StageName;
  label: string;
  tab: SidebarTab;
}

const DUBBING_STEPPER: StepNode[] = [
  { key: 'EXTRACT', label: 'Source', tab: 'source' },
  { key: 'TRANSCRIBE', label: 'Transcript', tab: 'transcript' },
  { key: 'TRANSLATE', label: 'Translation', tab: 'translation' },
  { key: 'TTS', label: 'Audio / Voice', tab: 'voice' },
  { key: 'SUBTITLE', label: 'Subtitle', tab: 'subtitles' },
  { key: 'TIMELINE', label: 'Timeline', tab: 'timeline' },
  { key: 'RENDER', label: 'Render', tab: 'render' }
];

const STORY_STEPPER: StepNode[] = [
  { key: 'COLLECT', label: 'Source', tab: 'source' },
  { key: 'CLEAN', label: 'Clean', tab: 'story' },
  { key: 'ANALYZE', label: 'Analyze', tab: 'story' },
  { key: 'MEMORY', label: 'Memory', tab: 'memory' },
  { key: 'SCENE', label: 'Scenes', tab: 'scenes' },
  { key: 'IMAGE', label: 'Images', tab: 'images' },
  { key: 'TTS', label: 'TTS Voice', tab: 'voice' },
  { key: 'TIMELINE', label: 'Timeline', tab: 'timeline' },
  { key: 'RENDER', label: 'Render', tab: 'render' }
];

export const Dashboard: React.FC<DashboardProps> = ({
  projectName,
  mode,
  status,
  overallProgress,
  stageProgresses,
  telemetry,
  logs,
  onStart,
  onPause,
  onResume,
  onRetry,
  onCancel,
  onReview,
  onApproveGate,
  onRejectGate,
  onNavigateTab
}) => {
  const steps = mode === 'STORY' ? STORY_STEPPER : DUBBING_STEPPER;

  const getStepBadge = (stKey: StageName) => {
    const info = stageProgresses[stKey];
    const stStatus = info?.status || 'PENDING';

    switch (stStatus) {
      case 'COMPLETED':
      case 'APPROVED':
        return {
          icon: '✓',
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10 border-emerald-500/30',
          text: 'COMPLETED'
        };
      case 'RUNNING':
        return {
          icon: '●',
          color: 'text-cyan-400 animate-pulse',
          bg: 'bg-cyan-500/15 border-cyan-500/40 shadow-sm shadow-cyan-500/20',
          text: `${info?.progress || 0}%`
        };
      case 'REVIEW_REQUIRED':
        return {
          icon: '!',
          color: 'text-amber-400',
          bg: 'bg-amber-500/15 border-amber-500/40',
          text: 'REVIEW'
        };
      case 'FAILED':
        return {
          icon: '×',
          color: 'text-rose-400',
          bg: 'bg-rose-500/15 border-rose-500/40',
          text: 'FAILED'
        };
      case 'PENDING':
      default:
        return {
          icon: '○',
          color: 'text-slate-500',
          bg: 'bg-white/5 border-white/5',
          text: 'PENDING'
        };
    }
  };

  const getStatusBadge = () => {
    switch (status) {
      case 'RUNNING':
        return (
          <span className="px-2.5 py-1 rounded-md bg-cyan-500/15 border border-cyan-500/30 text-cyan-300 text-xs font-extrabold tracking-wider flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-ping" />
            RUNNING ({overallProgress}%)
          </span>
        );
      case 'PAUSED':
        return (
          <span className="px-2.5 py-1 rounded-md bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs font-extrabold tracking-wider">
            PAUSED
          </span>
        );
      case 'REVIEW_REQUIRED':
        return (
          <span className="px-2.5 py-1 rounded-md bg-pink-500/20 border border-pink-500/40 text-pink-300 text-xs font-extrabold tracking-wider flex items-center gap-1.5">
            <Lock size={12} />
            REVIEW REQUIRED
          </span>
        );
      case 'COMPLETED':
        return (
          <span className="px-2.5 py-1 rounded-md bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 text-xs font-extrabold tracking-wider flex items-center gap-1.5">
            <CheckCircle size={12} />
            COMPLETED
          </span>
        );
      case 'FAILED':
        return (
          <span className="px-2.5 py-1 rounded-md bg-rose-500/15 border border-rose-500/30 text-rose-300 text-xs font-extrabold tracking-wider flex items-center gap-1.5">
            <XCircle size={12} />
            FAILED
          </span>
        );
      default:
        return (
          <span className="px-2.5 py-1 rounded-md bg-white/5 border border-white/10 text-slate-400 text-xs font-extrabold tracking-wider">
            IDLE
          </span>
        );
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto space-y-6 text-slate-100 font-sans">
      {/* 1. TOP HEADER & MODE TITLE */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 bg-[#111318] p-5 rounded-xl border border-white/5 shadow-md">
        <div>
          <div className="flex items-center gap-2 text-xs text-slate-500 font-extrabold uppercase tracking-wider font-['Outfit']">
            <span>Project Workspace</span>
            <ChevronRight size={12} />
            <span className="text-indigo-400">{mode} PIPELINE</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight mt-1 flex items-center gap-3 font-['Outfit']">
            {projectName}
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-extrabold border ${
              mode === 'STORY' 
                ? 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30' 
                : 'bg-indigo-500/10 text-indigo-300 border-indigo-500/30'
            }`}>
              {mode === 'STORY' ? '📖 MODE_STORY' : '🎬 MODE_DUBBING'}
            </span>
          </h1>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <div className="text-[11px] text-slate-400 uppercase font-semibold">Current State</div>
            {getStatusBadge()}
          </div>
        </div>
      </div>

      {/* 2. SOURCE METADATA & PIPELINE OVERVIEW CARD */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        {/* SOURCE VIDEO METADATA CARD */}
        <div className="bg-[#111318] p-5 rounded-xl border border-white/5 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-extrabold text-slate-400 uppercase tracking-wider font-['Outfit'] flex items-center gap-1.5">
              <FileVideo size={14} className="text-indigo-400" />
              Source Video
            </span>
            <span className="px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 text-[10px] font-bold">
              READY
            </span>
          </div>

          <div className="space-y-2 pt-1 text-xs">
            <div className="flex justify-between py-1 border-b border-white/5 text-slate-300">
              <span className="text-slate-500">File Name</span>
              <span className="font-semibold truncate max-w-[170px]" title="source/input.mp4">input.mp4</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5 text-slate-300">
              <span className="text-slate-500">Duration</span>
              <span className="font-mono font-medium">18:32.40</span>
            </div>
            <div className="flex justify-between py-1 border-b border-white/5 text-slate-300">
              <span className="text-slate-500">Resolution</span>
              <span className="font-mono font-medium">1920 x 1080 (1080p)</span>
            </div>
            <div className="flex justify-between py-1 text-slate-300">
              <span className="text-slate-500">Target Language</span>
              <span className="font-semibold text-cyan-400 uppercase">Vietnamese (vi)</span>
            </div>
          </div>
        </div>

        {/* PIPELINE PROGRESS SUMMARY */}
        <div className="lg:col-span-2 bg-[#111318] p-5 rounded-xl border border-white/5 flex flex-col justify-between space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <span className="text-xs font-extrabold text-slate-400 uppercase tracking-wider font-['Outfit']">
                Pipeline Execution Progress
              </span>
              <h3 className="text-lg font-bold text-white mt-0.5 font-['Outfit']">
                Overall Completion: <span className="text-cyan-400">{overallProgress}%</span>
              </h3>
            </div>

            <div className="flex items-center gap-2">
              {status === 'RUNNING' ? (
                <button
                  onClick={onCancel}
                  className="px-3 py-1.5 rounded-lg bg-rose-500/20 text-rose-300 hover:bg-rose-500/30 border border-rose-500/30 text-xs font-semibold flex items-center gap-1.5 transition-all"
                >
                  <Square size={13} /> Cancel
                </button>
              ) : (
                <button
                  onClick={onStart}
                  className="px-4 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold flex items-center gap-1.5 shadow-md shadow-indigo-500/20 transition-all"
                >
                  <Play size={13} /> Start Pipeline
                </button>
              )}
            </div>
          </div>

          {/* PROGRESS BAR */}
          <div className="space-y-1.5">
            <div className="w-full bg-black/50 h-3 rounded-full overflow-hidden p-0.5 border border-white/5">
              <div
                className="h-full rounded-full bg-gradient-to-r from-indigo-500 via-cyan-400 to-emerald-400 transition-all duration-500 shadow-sm shadow-cyan-500/30"
                style={{ width: `${overallProgress}%` }}
              />
            </div>
            <div className="flex justify-between text-[11px] text-slate-500">
              <span>Pipeline Stage 1 / {steps.length}</span>
              <span>{overallProgress === 100 ? 'Ready for Export' : 'In Progress'}</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3. PIPELINE HORIZONTAL STEPPER WITH CLICKABLE NODES */}
      <div className="bg-[#111318] p-5 rounded-xl border border-white/5 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-xs font-extrabold text-slate-400 uppercase tracking-wider font-['Outfit'] flex items-center gap-2">
            <Layers size={14} className="text-cyan-400" />
            Interactive Stepper (Click node to open module workspace)
          </span>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-7 gap-2.5">
          {steps.map((st, idx) => {
            const badge = getStepBadge(st.key);
            return (
              <button
                key={st.key}
                onClick={() => onNavigateTab?.(st.tab)}
                className={`p-3 rounded-lg border flex flex-col items-start justify-between text-left transition-all hover:scale-[1.02] ${badge.bg}`}
                title={`Open ${st.label} Workspace`}
              >
                <div className="flex items-center justify-between w-full mb-2">
                  <span className="text-[10px] font-bold text-slate-500">0{idx + 1}</span>
                  <span className={`text-xs font-extrabold ${badge.color}`}>{badge.icon}</span>
                </div>
                <div>
                  <div className="text-xs font-bold text-slate-200 font-['Outfit'] truncate w-full">{st.label}</div>
                  <div className="text-[10px] font-semibold text-slate-400 mt-0.5">{badge.text}</div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* 4. MANDATORY REVIEW GATE BANNER */}
      {status === 'REVIEW_REQUIRED' && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-amber-500/20 text-amber-400 flex items-center justify-center flex-shrink-0">
              <Lock size={18} />
            </div>
            <div>
              <h4 className="text-xs font-extrabold text-amber-300 uppercase tracking-wider font-['Outfit']">
                🔒 REVIEW GATE MANDATORY: Human Review Required
              </h4>
              <p className="text-xs text-slate-300 mt-0.5">
                Downstream pipeline stages are locked until human approval. Please inspect generated subtitles & audio before approving.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={onRejectGate}
              className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 border border-rose-500/40 text-rose-300 text-xs font-bold flex items-center gap-1 transition-all"
            >
              <XCircle size={14} /> Reject
            </button>
            <button
              onClick={onApproveGate}
              className="px-4 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold flex items-center gap-1 shadow-md shadow-emerald-600/20 transition-all"
            >
              <CheckCircle size={14} /> Approve Gate
            </button>
          </div>
        </div>
      )}

      {/* 5. HARDWARE TELEMETRY GAUGES */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {/* GPU UTILIZATION */}
        <div className="bg-[#111318] p-3.5 rounded-xl border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Activity size={13} className="text-cyan-400" /> GPU
            </span>
            <span className="font-bold text-white font-mono">{telemetry.gpu_util_percent}%</span>
          </div>
          <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden">
            <div className="bg-cyan-400 h-full rounded-full" style={{ width: `${telemetry.gpu_util_percent}%` }} />
          </div>
        </div>

        {/* VRAM USAGE */}
        <div className="bg-[#111318] p-3.5 rounded-xl border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-semibold text-slate-300">
              <HardDrive size={13} className="text-purple-400" /> VRAM
            </span>
            <span className="font-bold text-white font-mono">{telemetry.vram_used_gb} / {telemetry.vram_total_gb} GB</span>
          </div>
          <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden">
            <div className="bg-purple-400 h-full rounded-full" style={{ width: `${telemetry.vram_percent}%` }} />
          </div>
        </div>

        {/* RAM USAGE */}
        <div className="bg-[#111318] p-3.5 rounded-xl border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Cpu size={13} className="text-emerald-400" /> RAM
            </span>
            <span className="font-bold text-white font-mono">{telemetry.ram_used_gb} GB ({telemetry.ram_percent}%)</span>
          </div>
          <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden">
            <div className="bg-emerald-400 h-full rounded-full" style={{ width: `${telemetry.ram_percent}%` }} />
          </div>
        </div>

        {/* CPU & TEMP */}
        <div className="bg-[#111318] p-3.5 rounded-xl border border-white/5 space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span className="flex items-center gap-1.5 font-semibold text-slate-300">
              <Thermometer size={13} className="text-amber-400" /> CPU / Temp
            </span>
            <span className="font-bold text-white font-mono">{telemetry.cpu_percent}% | {telemetry.temp_c}°C</span>
          </div>
          <div className="w-full bg-black/40 h-1.5 rounded-full overflow-hidden">
            <div className="bg-amber-400 h-full rounded-full" style={{ width: `${telemetry.cpu_percent}%` }} />
          </div>
        </div>
      </div>
    </div>
  );
};
