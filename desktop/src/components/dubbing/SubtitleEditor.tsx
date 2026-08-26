import React, { useState } from 'react';
import { 
  Type, 
  Palette, 
  Clock, 
  Sliders, 
  Download, 
  Plus, 
  Trash2, 
  Check, 
  Sparkles,
  AlignLeft,
  AlignCenter,
  AlignRight
} from 'lucide-react';

interface SubtitleEditorProps {
  projectDir?: string | null;
  activeTab?: string;
  onProceedToVoices?: () => void;
}

export interface SubtitleItem {
  id: string;
  start: string;
  end: string;
  text: string;
}

export const SubtitleEditor: React.FC<SubtitleEditorProps> = ({
  projectDir,
  onProceedToVoices
}) => {
  const [subtitles, setSubtitles] = useState<SubtitleItem[]>([
    { id: 'sub-1', start: '00:00:01.200', end: '00:00:04.500', text: 'Chào mừng các bạn đã quay trở lại với kênh AutoDubStudio!' },
    { id: 'sub-2', start: '00:00:04.800', end: '00:00:08.100', text: 'Hôm nay chúng ta sẽ cùng khám phá công nghệ dịch video và lồng tiếng tự động bằng AI.' }
  ]);

  // Subtitle Style Tokens
  const [fontFamily, setFontFamily] = useState('Roboto');
  const [fontSize, setFontSize] = useState(24);
  const [primaryColor, setPrimaryColor] = useState('#ffffff');
  const [outlineColor, setOutlineColor] = useState('#000000');
  const [alignment, setAlignment] = useState<'BOTTOM' | 'CENTER' | 'TOP'>('BOTTOM');

  const updateSubText = (id: string, text: string) => {
    setSubtitles(prev => prev.map(s => s.id === id ? { ...s, text } : s));
  };

  const handleExportSubtitle = (format: 'SRT' | 'ASS') => {
    alert(`Đã xuất tệp phụ đề ${format} thành công!`);
  };

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
            <Type size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Subtitle Editor & Style Studio (MODE_DUBBING)
            </h2>
            <p className="text-xs text-slate-400">
              Biên tập phụ đề ASS/SRT, tùy chỉnh phông chữ, màu viền, kích thước và căn chỉnh hiển thị.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => handleExportSubtitle('SRT')}
            className="px-3.5 py-1.5 rounded-lg bg-white/10 hover:bg-white/15 text-slate-200 font-extrabold text-xs flex items-center gap-1.5 border border-white/10"
          >
            <Download size={14} /> Xuất SRT
          </button>

          <button
            onClick={() => handleExportSubtitle('ASS')}
            className="px-3.5 py-1.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-extrabold text-xs flex items-center gap-1.5 shadow-md shadow-indigo-600/20"
          >
            <Download size={14} /> Xuất ASS Subtitle
          </button>
        </div>
      </div>

      <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-4 overflow-hidden">
        {/* SUBTITLE LIST */}
        <div className="lg:col-span-2 bg-[#111318] rounded-xl border border-white/5 p-4 flex flex-col space-y-3 overflow-hidden">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-slate-300 uppercase font-['Outfit']">
              Danh Sách Phụ Đề ({subtitles.length} câu)
            </span>
            <button
              onClick={() => {
                const newSub: SubtitleItem = {
                  id: `sub-${Date.now()}`,
                  start: '00:00:10.000',
                  end: '00:00:13.000',
                  text: 'Dòng phụ đề mới...'
                };
                setSubtitles(prev => [...prev, newSub]);
              }}
              className="px-2.5 py-1 rounded bg-indigo-600/20 text-indigo-300 text-xs font-bold flex items-center gap-1 border border-indigo-500/30"
            >
              <Plus size={12} /> Thêm Dòng
            </button>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar pr-1">
            {subtitles.map(s => (
              <div key={s.id} className="p-3 rounded-lg bg-black/40 border border-white/5 space-y-2">
                <div className="flex items-center justify-between text-[11px] font-mono text-slate-400">
                  <div className="flex items-center gap-2">
                    <Clock size={12} className="text-indigo-400" />
                    <span>{s.start} ➔ {s.end}</span>
                  </div>
                  <button
                    onClick={() => setSubtitles(prev => prev.filter(item => item.id !== s.id))}
                    className="text-slate-600 hover:text-rose-400"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>

                <textarea
                  value={s.text}
                  onChange={e => updateSubText(s.id, e.target.value)}
                  rows={2}
                  className="w-full bg-[#111318] border border-white/10 rounded p-2 text-xs text-slate-100 focus:outline-none focus:border-indigo-500"
                />
              </div>
            ))}
          </div>
        </div>

        {/* SUBTITLE STYLE STUDIO */}
        <div className="bg-[#111318] rounded-xl border border-white/5 p-4 space-y-4 overflow-y-auto custom-scrollbar">
          <span className="text-xs font-bold text-indigo-300 uppercase font-['Outfit'] flex items-center gap-1.5">
            <Palette size={14} /> Subtitle Style Studio
          </span>

          <div className="space-y-3 text-xs">
            <div>
              <label className="text-slate-400 text-[11px] block mb-1">Phông chữ (Font Family)</label>
              <select
                value={fontFamily}
                onChange={e => setFontFamily(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-slate-200 focus:outline-none"
              >
                <option value="Roboto">Roboto (Hiện Đại)</option>
                <option value="Inter">Inter (Tinh Tế)</option>
                <option value="Montserrat">Montserrat (Đậm Nét)</option>
                <option value="Outfit">Outfit (Ấn Tượng)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-slate-400 text-[11px] mb-1">
                <span>Kích thước chữ</span>
                <span className="font-mono text-indigo-400">{fontSize} px</span>
              </div>
              <input
                type="range"
                min={14}
                max={48}
                value={fontSize}
                onChange={e => setFontSize(Number(e.target.value))}
                className="w-full accent-indigo-500"
              />
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="text-slate-400 text-[11px] block mb-1">Màu chữ chính</label>
                <input
                  type="color"
                  value={primaryColor}
                  onChange={e => setPrimaryColor(e.target.value)}
                  className="w-full h-8 bg-black/40 border border-white/10 rounded cursor-pointer"
                />
              </div>

              <div>
                <label className="text-slate-400 text-[11px] block mb-1">Màu viền chữ</label>
                <input
                  type="color"
                  value={outlineColor}
                  onChange={e => setOutlineColor(e.target.value)}
                  className="w-full h-8 bg-black/40 border border-white/10 rounded cursor-pointer"
                />
              </div>
            </div>

            {/* PREVIEW CARD */}
            <div className="p-4 bg-black rounded-xl border border-white/10 text-center space-y-2 mt-4">
              <span className="text-[10px] text-slate-500 uppercase tracking-wider block font-mono">Xem Trước Phụ Đề</span>
              <p
                style={{
                  fontFamily,
                  fontSize: `${fontSize}px`,
                  color: primaryColor,
                  textShadow: `1px 1px 2px ${outlineColor}, -1px -1px 2px ${outlineColor}`
                }}
                className="font-bold drop-shadow-md"
              >
                Mẫu phụ đề hiển thị chuẩn trên Video!
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
