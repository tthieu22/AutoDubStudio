import React, { useState } from 'react';
import { 
  Mic, 
  User, 
  Volume2, 
  Play, 
  Pause, 
  Sliders, 
  RefreshCw, 
  Sparkles, 
  Check, 
  Music,
  Plus
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

interface VoiceStudioProps {
  projectDir?: string | null;
  pipelineStatus?: string;
  stageProgresses?: any;
  onResumePipeline?: () => void;
}

export interface SpeakerVoiceMapping {
  speakerId: string;
  speakerName: string;
  voiceModel: string;
  speed: number;
  pitch: number;
  segmentsCount: number;
}

export const VoiceStudio: React.FC<VoiceStudioProps> = ({
  projectDir,
  onResumePipeline
}) => {
  const [speakers, setSpeakers] = useState<SpeakerVoiceMapping[]>([
    {
      speakerId: 'spk-01',
      speakerName: 'Speaker 1 (Nhân vật Nam)',
      voiceModel: 'vi_VN-vais1000-medium',
      speed: 1.0,
      pitch: 0,
      segmentsCount: 14
    },
    {
      speakerId: 'spk-02',
      speakerName: 'Speaker 2 (Nhân vật Nữ)',
      voiceModel: 'vi_female_soft',
      speed: 1.05,
      pitch: 1,
      segmentsCount: 8
    }
  ]);

  const [activeTestingId, setActiveTestingId] = useState<string | null>(null);
  const [isSynthesizing, setIsSynthesizing] = useState(false);

  const handleTestVoice = (id: string) => {
    setActiveTestingId(id);
    setTimeout(() => {
      setActiveTestingId(null);
    }, 2000);
  };

  const updateSpeaker = (id: string, updates: Partial<SpeakerVoiceMapping>) => {
    setSpeakers(prev => prev.map(s => s.speakerId === id ? { ...s, ...updates } : s));
  };

  const handleSynthesizeAll = () => {
    setIsSynthesizing(true);
    setTimeout(() => {
      setIsSynthesizing(false);
      alert('Đã tổng hợp toàn bộ giọng đọc TTS bằng Piper TTS thành công!');
    }, 1800);
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center border border-emerald-500/20">
            <Mic size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Voice Studio & Piper TTS Assignment (MODE_DUBBING)
            </h2>
            <p className="text-xs text-slate-400">
              Gán giọng đọc AI Piper TTS, điều chỉnh tốc độ/cao độ cho từng nhân vật trong video.
            </p>
          </div>
        </div>

        <button
          onClick={handleSynthesizeAll}
          disabled={isSynthesizing}
          className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-black font-extrabold text-xs flex items-center gap-2 shadow-md shadow-emerald-500/20 transition-all"
        >
          {isSynthesizing ? <RefreshCw size={14} className="animate-spin" /> : <Sparkles size={14} />}
          <span>{isSynthesizing ? 'Đang Tổng Hợp Giọng TTS...' : 'TẠO LẠI TOÀN BỘ AUDIO TTS'}</span>
        </button>
      </div>

      {/* SPEAKERS MAPPING LIST */}
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {speakers.map(spk => (
          <div
            key={spk.speakerId}
            className="p-4 rounded-xl bg-[#111318] border border-white/5 flex flex-col md:flex-row md:items-center justify-between gap-4"
          >
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <div className="w-7 h-7 rounded-full bg-emerald-500/20 text-emerald-300 flex items-center justify-center border border-emerald-500/30">
                  <User size={14} />
                </div>
                <h3 className="text-sm font-bold text-white font-['Outfit']">{spk.speakerName}</h3>
                <span className="px-2 py-0.5 rounded bg-white/5 text-slate-400 font-mono text-[10px]">
                  {spk.segmentsCount} câu thoại
                </span>
              </div>
              <p className="text-xs text-slate-400 pl-9">ID: {spk.speakerId} • Piper Neural Voice Adapter</p>
            </div>

            <div className="flex flex-wrap items-center gap-4 text-xs">
              {/* VOICE MODEL SELECTOR */}
              <div className="w-56">
                <label className="text-[11px] text-slate-400 block mb-1">Mô hình giọng TTS</label>
                <select
                  value={spk.voiceModel}
                  onChange={e => updateSpeaker(spk.speakerId, { voiceModel: e.target.value })}
                  className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-slate-200 focus:outline-none font-medium"
                >
                  <option value="vi_VN-vais1000-medium">vi_VN-vais1000-medium (Giọng Nam Chuẩn)</option>
                  <option value="vi_female_soft">vi_female_soft (Giọng Nữ Dịu Dàng)</option>
                  <option value="vi_male_hero">vi_male_hero (Giọng Truyện Hero)</option>
                  <option value="vi_southern_male">vi_southern_male (Giọng Nam Miền Nam)</option>
                </select>
              </div>

              {/* SPEED SLIDER */}
              <div className="w-32">
                <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                  <span>Tốc độ</span>
                  <span className="font-mono text-emerald-400">{spk.speed}x</span>
                </div>
                <input
                  type="range"
                  min={0.7}
                  max={1.4}
                  step={0.05}
                  value={spk.speed}
                  onChange={e => updateSpeaker(spk.speakerId, { speed: Number(e.target.value) })}
                  className="w-full accent-emerald-500"
                />
              </div>

              {/* TEST AUDIO BUTTON */}
              <button
                onClick={() => handleTestVoice(spk.speakerId)}
                className="px-3 py-2 rounded-lg bg-white/5 hover:bg-white/10 text-slate-200 font-semibold text-xs flex items-center gap-1.5 border border-white/10"
              >
                {activeTestingId === spk.speakerId ? <RefreshCw size={14} className="animate-spin text-emerald-400" /> : <Play size={14} />}
                <span>{activeTestingId === spk.speakerId ? 'Đang đọc...' : 'Nghe thử'}</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
