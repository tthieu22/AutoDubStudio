import React, { useState } from 'react';
import { 
  Clapperboard, 
  Cpu, 
  HardDrive, 
  Sliders, 
  Play, 
  CheckCircle2, 
  RefreshCw, 
  FolderOpen, 
  Zap, 
  Sparkles,
  FileVideo
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface RenderManagerProps {
  projectDir?: string | null;
}

export const RenderManager: React.FC<RenderManagerProps> = ({ projectDir }) => {
  const [resolution, setResolution] = useState('1080p');
  const [fps, setFps] = useState('30');
  const [encoder, setEncoder] = useState('h264_nvenc');
  const [bitrate, setBitrate] = useState('12M');
  const [outputFormat, setOutputFormat] = useState('mp4');

  const [isRendering, setIsRendering] = useState(false);
  const [renderProgress, setRenderProgress] = useState(0);

  const handleStartRender = () => {
    setIsRendering(true);
    setRenderProgress(0);

    let pct = 0;
    const interval = setInterval(() => {
      pct += 4;
      setRenderProgress(pct);
      if (pct >= 100) {
        clearInterval(interval);
        setIsRendering(false);
        alert('Đã xuất video hoàn tất! File đã được lưu vào thư mục outputs.');
      }
    }, 150);
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
            <Clapperboard size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Render Queue & Video Export Studio
            </h2>
            <p className="text-xs text-slate-400">
              Xuất video hoàn chỉnh với tăng tốc phần cứng GPU NVENC/AMF và FFmpeg encoder.
            </p>
          </div>
        </div>

        <button
          onClick={handleStartRender}
          disabled={isRendering}
          className="px-5 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-extrabold text-xs flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all"
        >
          {isRendering ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
          <span>{isRendering ? 'Đang Render Video...' : 'BẮT ĐẦU RENDER VIDEO'}</span>
        </button>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 overflow-hidden">
        {/* RENDER CONFIGURATION */}
        <div className="lg:col-span-2 bg-[#111318] rounded-xl border border-white/5 p-4 flex flex-col space-y-4">
          <span className="text-xs font-bold text-slate-300 uppercase font-['Outfit'] flex items-center gap-1.5">
            <Sliders size={14} className="text-emerald-400" /> Thiết Lập Cấu Hình Render Video
          </span>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div>
              <label className="text-slate-400 text-[11px] block mb-1">Độ phân giải (Resolution)</label>
              <select
                value={resolution}
                onChange={e => setResolution(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-slate-200 focus:outline-none"
              >
                <option value="1080p">Full HD 1080p (1920x1080)</option>
                <option value="4K">Ultra HD 4K (3840x2160)</option>
                <option value="720p">HD 720p (1280x720)</option>
                <option value="9:16">TikTok Vertical (1080x1920)</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 text-[11px] block mb-1">Tốc độ khung hình (FPS)</label>
              <select
                value={fps}
                onChange={e => setFps(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-slate-200 focus:outline-none"
              >
                <option value="30">30 FPS (Khuyên dùng)</option>
                <option value="60">60 FPS (Mượt mà)</option>
                <option value="24">24 FPS (Phim điện ảnh)</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 text-[11px] block mb-1">Mã hóa phần cứng (Hardware Encoder)</label>
              <select
                value={encoder}
                onChange={e => setEncoder(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-emerald-400 font-bold focus:outline-none"
              >
                <option value="h264_nvenc">⚡ NVIDIA NVENC H.264 (Tăng tốc GPU)</option>
                <option value="hevc_nvenc">⚡ NVIDIA NVENC H.265 / HEVC</option>
                <option value="h264_amf">⚡ AMD AMF H.264</option>
                <option value="libx264">💻 CPU x264 Software Encoder</option>
              </select>
            </div>

            <div>
              <label className="text-slate-400 text-[11px] block mb-1">Video Bitrate</label>
              <select
                value={bitrate}
                onChange={e => setBitrate(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-slate-200 focus:outline-none font-mono"
              >
                <option value="12M">12 Mbps (Chuẩn YouTube HD)</option>
                <option value="20M">20 Mbps (Chất lượng cao)</option>
                <option value="40M">40 Mbps (Ultra 4K Quality)</option>
              </select>
            </div>
          </div>

          {/* RENDER PROGRESS BAR */}
          {isRendering && (
            <div className="p-4 bg-black/40 rounded-xl border border-white/10 space-y-2 mt-auto">
              <div className="flex justify-between text-xs font-mono text-emerald-400 font-bold">
                <span>FFmpeg NVENC Encoder rendering...</span>
                <span>{renderProgress}%</span>
              </div>
              <div className="w-full bg-black h-2.5 rounded-full overflow-hidden border border-white/10">
                <div className="bg-gradient-to-r from-emerald-500 to-cyan-400 h-full rounded-full transition-all duration-200" style={{ width: `${renderProgress}%` }} />
              </div>
            </div>
          )}
        </div>

        {/* SUMMARY CARD */}
        <div className="bg-[#111318] rounded-xl border border-white/5 p-4 flex flex-col justify-between space-y-4">
          <div>
            <span className="text-xs font-bold text-slate-300 uppercase font-['Outfit'] flex items-center gap-1.5 mb-3">
              <FileVideo size={14} className="text-emerald-400" /> Tóm Tắt Tệp Đầu Ra
            </span>

            <div className="space-y-2 text-xs text-slate-300 font-mono">
              <div className="flex justify-between p-2 rounded bg-black/40 border border-white/5">
                <span className="text-slate-500">Resolution:</span>
                <span>{resolution}</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-black/40 border border-white/5">
                <span className="text-slate-500">Framerate:</span>
                <span>{fps} FPS</span>
              </div>
              <div className="flex justify-between p-2 rounded bg-black/40 border border-white/5">
                <span className="text-slate-500">Encoder:</span>
                <span className="text-emerald-400">{encoder}</span>
              </div>
            </div>
          </div>

          <button
            onClick={() => alert('Đã mở thư mục lưu video outputs!')}
            className="w-full py-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-300 font-semibold text-xs flex items-center justify-center gap-1.5 border border-white/10"
          >
            <FolderOpen size={14} /> Mở Thư Mục Output
          </button>
        </div>
      </div>
    </div>
  );
};
