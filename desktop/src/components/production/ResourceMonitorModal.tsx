import React from 'react';
import { Cpu, HardDrive, Thermometer, Activity, ShieldAlert, X, CheckCircle2 } from 'lucide-react';
import { HardwareTelemetry } from '../../types/pipeline';

interface ResourceMonitorModalProps {
  isOpen: boolean;
  onClose: () => void;
  telemetry: HardwareTelemetry;
}

export const ResourceMonitorModal: React.FC<ResourceMonitorModalProps> = ({
  isOpen,
  onClose,
  telemetry
}) => {
  if (!isOpen) return null;

  const isLowVram = (telemetry.vram_total_gb - telemetry.vram_used_gb) < 1.0;

  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-[#111318] border border-white/10 rounded-2xl w-full max-w-xl p-6 shadow-2xl space-y-5 text-slate-100 font-sans">
        <div className="flex items-center justify-between border-b border-white/5 pb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
              <Activity size={18} />
            </div>
            <div>
              <h3 className="text-base font-bold text-white font-['Outfit']">Hardware Resource Monitor</h3>
              <p className="text-xs text-slate-400">Live GPU, VRAM, RAM, and system hardware telemetry</p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1 rounded-md text-slate-400 hover:text-white hover:bg-white/10 transition-all"
          >
            <X size={16} />
          </button>
        </div>

        {/* LOW VRAM WARNING BANNER */}
        {isLowVram && (
          <div className="p-3.5 rounded-xl bg-amber-500/15 border border-amber-500/30 text-amber-300 text-xs flex items-center gap-3">
            <ShieldAlert size={20} className="flex-shrink-0 text-amber-400" />
            <div>
              <strong className="block text-amber-200">LOW VRAM WARNING (&lt; 1.0 GB Free)</strong>
              <span>Consider switching to Low VRAM mode or using INT8 quantized Whisper & TTS models to prevent CUDA OOM exceptions.</span>
            </div>
          </div>
        )}

        {/* GAUGES GRID */}
        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
            <div className="flex justify-between text-xs text-slate-400">
              <span className="flex items-center gap-1.5 font-semibold text-slate-200">
                <HardDrive size={14} className="text-purple-400" /> VRAM Usage
              </span>
              <span className="font-bold text-white font-mono">{telemetry.vram_used_gb} / {telemetry.vram_total_gb} GB</span>
            </div>
            <div className="w-full bg-black/60 h-2 rounded-full overflow-hidden">
              <div className="bg-purple-400 h-full rounded-full" style={{ width: `${telemetry.vram_percent}%` }} />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
            <div className="flex justify-between text-xs text-slate-400">
              <span className="flex items-center gap-1.5 font-semibold text-slate-200">
                <Cpu size={14} className="text-emerald-400" /> RAM Usage
              </span>
              <span className="font-bold text-white font-mono">{telemetry.ram_used_gb} GB ({telemetry.ram_percent}%)</span>
            </div>
            <div className="w-full bg-black/60 h-2 rounded-full overflow-hidden">
              <div className="bg-emerald-400 h-full rounded-full" style={{ width: `${telemetry.ram_percent}%` }} />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
            <div className="flex justify-between text-xs text-slate-400">
              <span className="flex items-center gap-1.5 font-semibold text-slate-200">
                <Activity size={14} className="text-cyan-400" /> GPU Load
              </span>
              <span className="font-bold text-white font-mono">{telemetry.gpu_util_percent}%</span>
            </div>
            <div className="w-full bg-black/60 h-2 rounded-full overflow-hidden">
              <div className="bg-cyan-400 h-full rounded-full" style={{ width: `${telemetry.gpu_util_percent}%` }} />
            </div>
          </div>

          <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-2">
            <div className="flex justify-between text-xs text-slate-400">
              <span className="flex items-center gap-1.5 font-semibold text-slate-200">
                <Thermometer size={14} className="text-amber-400" /> CPU / Temp
              </span>
              <span className="font-bold text-white font-mono">{telemetry.cpu_percent}% | {telemetry.temp_c}°C</span>
            </div>
            <div className="w-full bg-black/60 h-2 rounded-full overflow-hidden">
              <div className="bg-amber-400 h-full rounded-full" style={{ width: `${telemetry.cpu_percent}%` }} />
            </div>
          </div>
        </div>

        <div className="pt-2 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-xs font-semibold text-slate-200"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
