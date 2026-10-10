import React, { useState } from 'react';
import { 
  FileVideo, 
  Music, 
  Sliders, 
  Play, 
  Pause, 
  Volume2, 
  Sparkles, 
  Layers, 
  Scissors, 
  Check, 
  RefreshCw, 
  FolderOpen,
  Radio,
  FileAudio
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface SourceMediaManagerProps {
  projectDir?: string | null;
  onProceedToTranscript?: () => void;
}

export const SourceMediaManager: React.FC<SourceMediaManagerProps> = ({
  projectDir,
  onProceedToTranscript
}) => {
  const [videoFile, setVideoFile] = useState<string>('sample_input_video.mp4');
  const [isPlaying, setIsPlaying] = useState(false);
  
  // Audio separation settings
  const [enableUVR, setEnableUVR] = useState(true);
  const [uvrModel, setUvrModel] = useState('UVR-MDX-NET-Voc-FT');
  const [noiseReduction, setNoiseReduction] = useState(3);

  // Whisper STT settings
  const [whisperModel, setWhisperModel] = useState('whisper-large-v3');
  const [language, setLanguage] = useState('auto');
  const [vadFilter, setVadFilter] = useState(true);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleRunExtraction = () => {
    setIsProcessing(true);
    setTimeout(() => {
      setIsProcessing(false);
      onProceedToTranscript?.();
    }, 1500);
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center border border-cyan-500/20">
            <FileVideo size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Source Media & STT Extraction Workspace (MODE_DUBBING)
            </h2>
            <p className="text-xs text-slate-400">
              Quản lý video đầu vào, tách lời nói (UVR5 Vocal Isolation) và cấu hình Whisper STT.
            </p>
          </div>
        </div>

        <button
          onClick={handleRunExtraction}
          disabled={isProcessing}
          className="px-4 py-2 rounded-lg bg-cyan-500 hover:bg-cyan-400 disabled:opacity-50 text-black font-extrabold text-xs flex items-center gap-2 shadow-md shadow-cyan-500/20 transition-all"
        >
          {isProcessing ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
          <span>{isProcessing ? 'Đang Tách Audio & STT...' : 'BẮT ĐẦU TÁCH AUDIO & STT'}</span>
        </button>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 overflow-hidden">
        {/* LEFT COLUMN: VIDEO PREVIEW & WAVEFORM */}
        <div className="lg:col-span-2 bg-[#111318] rounded-xl border border-white/5 p-4 flex flex-col space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 font-['Outfit'] uppercase flex items-center gap-1.5">
              <FileVideo size={14} className="text-cyan-400" /> Xem Trước Video Đầu Vào
            </span>
            <button className="px-2.5 py-1 rounded bg-white/5 hover:bg-white/10 text-slate-400 text-xs flex items-center gap-1">
              <FolderOpen size={12} /> Đổi File Video
            </button>
          </div>

          {/* VIDEO CONTAINER */}
          <div className="flex-1 bg-black rounded-xl border border-white/10 flex items-center justify-center relative overflow-hidden min-h-[220px]">
            <div className="text-center p-6 space-y-2">
              <div className="w-12 h-12 rounded-full bg-cyan-500/20 text-cyan-400 flex items-center justify-center mx-auto border border-cyan-500/30">
                {isPlaying ? <Pause size={20} /> : <Play size={20} className="ml-1" />}
              </div>
              <p className="text-xs text-slate-300 font-mono">{videoFile}</p>
              <span className="text-[11px] text-slate-500">Full HD 1080p • 29.97 FPS • AAC 48kHz</span>
            </div>
          </div>

          {/* WAVEFORM VISUALIZER MOCK */}
          <div className="p-3 bg-black/40 rounded-xl border border-white/5 space-y-2">
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400 font-mono">Audio Waveform (Track #1 Original)</span>
              <span className="text-cyan-400 font-mono">00:01:45 / 00:04:30</span>
            </div>
            <div className="h-12 bg-cyan-950/20 rounded border border-cyan-500/20 flex items-center justify-around px-2">
              {Array.from({ length: 48 }).map((_, i) => (
                <div
                  key={i}
                  className="w-1 bg-cyan-400/60 rounded-full transition-all"
                  style={{ height: `${Math.max(15, Math.sin(i * 0.5) * 80 + 20)}%` }}
                />
              ))}
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: UVR5 & STT SETTINGS */}
        <div className="bg-[#111318] rounded-xl border border-white/5 p-4 flex flex-col space-y-4 overflow-y-auto custom-scrollbar">
          {/* UVR5 VOCAL ISOLATION */}
          <div className="space-y-3 pb-4 border-b border-white/5">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-cyan-300 uppercase font-['Outfit'] flex items-center gap-1.5">
                <Scissors size={14} /> UVR5 Tách Lời Nói & BGM
              </span>
              <input
                type="checkbox"
                checked={enableUVR}
                onChange={e => setEnableUVR(e.target.checked)}
                className="accent-cyan-500 rounded cursor-pointer"
              />
            </div>

            {enableUVR && (
              <div className="space-y-2 text-xs">
                <div>
                  <label className="text-slate-400 text-[11px] block mb-1">Mô hình tách âm UVR5</label>
                  <select
                    value={uvrModel}
                    onChange={e => setUvrModel(e.target.value)}
                    className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-slate-200 focus:outline-none"
                  >
                    <option value="UVR-MDX-NET-Voc-FT">UVR-MDX-NET-Voc-FT (Khuyên dùng cho thoại)</option>
                    <option value="Kim_Vocal_2">Kim_Vocal_2 (Chất lượng vocal cao)</option>
                    <option value="Demucs-v4">Demucs v4 (Tách 4 tracks Drums/Bass/Vocal/Other)</option>
                  </select>
                </div>

                <div>
                  <div className="flex justify-between text-slate-400 text-[11px] mb-1">
                    <span>Khử nhiễu nền (Noise Gate)</span>
                    <span className="font-mono text-cyan-400">{noiseReduction} dB</span>
                  </div>
                  <input
                    type="range"
                    min={0}
                    max={10}
                    value={noiseReduction}
                    onChange={e => setNoiseReduction(Number(e.target.value))}
                    className="w-full accent-cyan-500"
                  />
                </div>
              </div>
            )}
          </div>

          {/* WHISPER STT SETTINGS */}
          <div className="space-y-3">
            <span className="text-xs font-bold text-purple-300 uppercase font-['Outfit'] flex items-center gap-1.5">
              <Radio size={14} /> Cấu Hình Whisper STT
            </span>

            <div className="space-y-2 text-xs">
              <div>
                <label className="text-slate-400 text-[11px] block mb-1">Model Whisper Size</label>
                <select
                  value={whisperModel}
                  onChange={e => setWhisperModel(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-slate-200 focus:outline-none font-mono"
                >
                  <option value="whisper-large-v3">whisper-large-v3 (Độ chính xác cao nhất)</option>
                  <option value="whisper-medium">whisper-medium (Cân bằng tốc độ/chất lượng)</option>
                  <option value="whisper-base">whisper-base (Nhanh siêu tốc)</option>
                </select>
              </div>

              <div>
                <label className="text-slate-400 text-[11px] block mb-1">Ngôn ngữ nguồn video</label>
                <select
                  value={language}
                  onChange={e => setLanguage(e.target.value)}
                  className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-slate-200 focus:outline-none"
                >
                  <option value="auto">🌐 Tự động phát hiện (Auto Detect)</option>
                  <option value="en">🇺🇸 Tiếng Anh (English)</option>
                  <option value="zh">🇨🇳 Tiếng Trung (Chinese)</option>
                  <option value="ja">🇯🇵 Tiếng Nhật (Japanese)</option>
                  <option value="ko">🇰🇷 Tiếng Hàn (Korean)</option>
                </select>
              </div>

              <label className="flex items-center gap-2 pt-2 text-slate-300 cursor-pointer">
                <input
                  type="checkbox"
                  checked={vadFilter}
                  onChange={e => setVadFilter(e.target.checked)}
                  className="accent-purple-500 rounded"
                />
                <span>Kích hoạt Silero VAD Filter (Bỏ khoảng lặng)</span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
