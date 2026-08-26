import React, { useState } from 'react';
import { 
  Sparkles, 
  Image as ImageIcon, 
  Sliders, 
  RefreshCw, 
  Cpu, 
  HardDrive, 
  Copy, 
  Check, 
  History,
  Layers,
  ArrowRight
} from 'lucide-react';

interface ImageGenerationStudioProps {
  projectDir?: string | null;
}

export const ImageGenerationStudio: React.FC<ImageGenerationStudioProps> = ({ projectDir }) => {
  const [prompt, setPrompt] = useState('A dramatic cinematic shot of a young swordsman standing on a mist-covered pine mountain peak at sunrise, highly detailed, 8k, Unreal Engine 5 render');
  const [negativePrompt, setNegativePrompt] = useState('blurry, low quality, distorted face, extra limbs, bad anatomy, text, watermark');
  const [model, setModel] = useState('SD 1.5 - Realistic Vision v5.1');
  const [steps, setSteps] = useState(20);
  const [cfg, setCfg] = useState(7.0);
  const [seed, setSeed] = useState(123456);
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);

  const [history, setHistory] = useState([
    { id: 1, prompt: 'Pine forest trail in early morning fog', seed: 98765, model: 'SD 1.5' },
    { id: 2, prompt: 'Ancient wooden cottage at mountain valley dusk', seed: 45678, model: 'SD 1.5' }
  ]);

  const handleGenerate = () => {
    setIsGenerating(true);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsGenerating(false);
          setHistory(h => [{ id: Date.now(), prompt, seed, model }, ...h]);
          return 100;
        }
        return prev + 20;
      });
    }, 400);
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center border border-purple-500/20">
            <ImageIcon size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              AI Image Generation Studio (Stable Diffusion)
            </h2>
            <p className="text-xs text-slate-400">
              Generate scene concept art & keyframes with VRAM-optimized local models.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="px-2.5 py-1 rounded-md bg-[#111318] border border-white/10 text-[11px] font-mono text-purple-300 flex items-center gap-1.5">
            <HardDrive size={13} className="text-purple-400" />
            VRAM: 3.4 / 4.0 GB
          </span>
          <button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="px-4 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-purple-600/20 transition-all"
          >
            <Sparkles size={14} /> {isGenerating ? `Generating (${progress}%)` : 'Generate Image'}
          </button>
        </div>
      </div>

      {/* MAIN TWO-COLUMN LAYOUT */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 flex-1 overflow-hidden">
        {/* LEFT 2 COLS: PREVIEW CANVAS & PROMPT INPUTS */}
        <div className="lg:col-span-2 space-y-4 flex flex-col overflow-y-auto custom-scrollbar">
          {/* IMAGE PREVIEW DISPLAY */}
          <div className="w-full h-80 bg-[#111318] rounded-xl border border-white/5 flex flex-col items-center justify-center relative overflow-hidden group">
            {isGenerating ? (
              <div className="flex flex-col items-center space-y-3 text-purple-300">
                <RefreshCw size={28} className="animate-spin text-purple-400" />
                <span className="text-xs font-bold font-mono">Sampling Step {Math.round((progress / 100) * steps)} / {steps} ({progress}%)</span>
                <div className="w-48 bg-black/50 h-2 rounded-full overflow-hidden border border-white/10">
                  <div className="bg-purple-500 h-full rounded-full transition-all" style={{ width: `${progress}%` }} />
                </div>
              </div>
            ) : (
              <div className="flex flex-col items-center text-slate-500">
                <ImageIcon size={48} className="mb-2 text-slate-600" />
                <span className="text-xs font-bold text-slate-300">Generated Image Preview</span>
                <span className="text-[11px] text-slate-500 mt-1">Resolution: 1024 x 576 (16:9)</span>
              </div>
            )}
          </div>

          {/* PROMPT & NEGATIVE PROMPT INPUTS */}
          <div className="space-y-3 bg-[#111318] p-4 rounded-xl border border-white/5">
            <div>
              <label className="text-xs font-bold text-slate-300 uppercase tracking-wider font-['Outfit'] block mb-1">
                Prompt
              </label>
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                rows={3}
                className="w-full bg-black/40 border border-white/10 rounded-lg p-3 text-xs text-slate-200 focus:outline-none focus:border-purple-500 resize-none font-sans"
              />
            </div>

            <div>
              <label className="text-xs font-bold text-slate-400 uppercase tracking-wider font-['Outfit'] block mb-1">
                Negative Prompt
              </label>
              <textarea
                value={negativePrompt}
                onChange={e => setNegativePrompt(e.target.value)}
                rows={2}
                className="w-full bg-black/40 border border-white/10 rounded-lg p-2.5 text-xs text-slate-400 focus:outline-none focus:border-purple-500 resize-none font-sans"
              />
            </div>
          </div>
        </div>

        {/* RIGHT COL: PARAMETERS & HISTORY */}
        <div className="space-y-4 bg-[#111318] p-4 rounded-xl border border-white/5 overflow-y-auto custom-scrollbar">
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-slate-400 font-['Outfit'] flex items-center gap-1.5">
            <Sliders size={14} className="text-purple-400" /> Model Parameters
          </h3>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 font-medium block mb-1">Model Checkpoint</label>
              <select
                value={model}
                onChange={e => setModel(e.target.value)}
                className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-xs text-slate-200 focus:outline-none"
              >
                <option value="SD 1.5 - Realistic Vision v5.1">SD 1.5 - Realistic Vision v5.1</option>
                <option value="SD 1.5 - Anime Anything V5">SD 1.5 - Anime Anything V5</option>
                <option value="SDXL Turbo (Fast 4-step)">SDXL Turbo (Fast 4-step)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-400">Sampling Steps</span>
                <span className="font-mono text-purple-300 font-bold">{steps}</span>
              </div>
              <input
                type="range"
                min={10}
                max={50}
                value={steps}
                onChange={e => setSteps(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            <div>
              <div className="flex justify-between mb-1">
                <span className="text-slate-400">CFG Scale</span>
                <span className="font-mono text-purple-300 font-bold">{cfg}</span>
              </div>
              <input
                type="range"
                min={1}
                max={20}
                step={0.5}
                value={cfg}
                onChange={e => setCfg(Number(e.target.value))}
                className="w-full accent-purple-500"
              />
            </div>

            <div>
              <label className="text-slate-400 font-medium block mb-1">Seed</label>
              <input
                type="number"
                value={seed}
                onChange={e => setSeed(Number(e.target.value))}
                className="w-full bg-[#0b0d10] border border-white/10 rounded-lg p-2 text-xs text-slate-200 font-mono focus:outline-none"
              />
            </div>
          </div>

          <div className="pt-4 border-t border-white/5">
            <h4 className="text-xs font-bold text-slate-400 font-['Outfit'] uppercase mb-2 flex items-center gap-1">
              <History size={13} /> Generation History
            </h4>
            <div className="space-y-2">
              {history.map(item => (
                <div key={item.id} className="p-2 rounded bg-black/40 border border-white/5 text-[11px] space-y-1">
                  <p className="text-slate-300 truncate">{item.prompt}</p>
                  <div className="flex justify-between text-slate-500 text-[10px]">
                    <span>Seed: {item.seed}</span>
                    <span>{item.model}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
