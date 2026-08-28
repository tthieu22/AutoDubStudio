import React, { useState, useEffect } from 'react';
import { 
  Sparkles, FolderOpen, Loader2, RefreshCw, Languages, Info, 
  ChevronDown, ChevronUp, Video, BookOpen, SlidersHorizontal, Check 
} from 'lucide-react';
import { open } from '@tauri-apps/api/dialog';

export interface TranslationStyleOption {
  id: string;
  name: string;
  description: string;
}

const TRANSLATION_STYLES: TranslationStyleOption[] = [
  { id: 'general', name: 'General / Tự động', description: 'Dịch tiếng Việt tự nhiên, phù hợp hội thoại thông thường.' },
  { id: 'modern', name: 'Hiện đại', description: 'Tiếng Việt hiện đại, tự nhiên, phù hợp phim đô thị và đời thường.' },
  { id: 'ancient', name: 'Cổ trang', description: 'Phong cách tiếng Việt phù hợp phim cổ trang Trung Quốc, chú trọng địa vị và cách xưng hô.' },
  { id: 'time_travel', name: 'Xuyên không', description: 'Kết hợp ngôn ngữ hiện đại và cổ trang tùy theo thời đại của từng nhân vật.' },
  { id: 'xianxia', name: 'Tiên hiệp / Kiếm hiệp', description: 'Phù hợp tiên hiệp, kiếm hiệp, tu tiên và thế giới võ hiệp.' },
  { id: 'palace', name: 'Cung đấu', description: 'Phù hợp cung đấu, hoàng cung, quan hệ vua/chúa và tầng lớp quý tộc.' },
  { id: 'cartoon', name: 'Hoạt hình / Trẻ em', description: 'Tiếng Việt đơn giản, tự nhiên, dễ nghe, phù hợp hoạt hình.' },
  { id: 'custom', name: 'Tùy chỉnh', description: 'Cho phép người dùng nhập yêu cầu phong cách riêng.' }
];

interface NewProjectModalProps {
  isCreating: boolean;
  onCreateProject: (
    name: string, 
    videoPath: string, 
    style?: string, 
    customStyle?: string, 
    mode?: 'STORY' | 'DUBBING', 
    storyText?: string
  ) => Promise<void>;
}

export const NewProjectModal: React.FC<NewProjectModalProps> = ({
  isCreating,
  onCreateProject
}) => {
  const generateTimestampName = () => {
    const now = new Date();
    const YYYY = now.getFullYear();
    const MM = String(now.getMonth() + 1).padStart(2, '0');
    const DD = String(now.getDate()).padStart(2, '0');
    const hh = String(now.getHours()).padStart(2, '0');
    const mm = String(now.getMinutes()).padStart(2, '0');
    return `DuAn_${YYYY}${MM}${DD}_${hh}${mm}`;
  };

  const [projectMode, setProjectMode] = useState<'DUBBING' | 'STORY'>('DUBBING');
  const [projectName, setProjectName] = useState(generateTimestampName);
  const [videoPath, setVideoPath] = useState('');
  const [storyText, setStoryText] = useState('');
  const [translationStyle, setTranslationStyle] = useState('general');
  const [customStyleText, setCustomStyleText] = useState('');
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    setProjectName(generateTimestampName());
  }, []);

  const selectedStyleObj = TRANSLATION_STYLES.find(s => s.id === translationStyle) || TRANSLATION_STYLES[0];

  const handleSelectVideoFile = async () => {
    try {
      const selected = await open({
        multiple: false,
        filters: [{ name: 'Video Files', extensions: ['mp4', 'mkv', 'avi', 'mov'] }]
      });
      if (selected && typeof selected === 'string') {
        setVideoPath(selected);
        return;
      }
    } catch (err) {
      console.warn('Tauri dialog unavailable, falling back to manual input:', err);
    }

    const manualPath = prompt('Nhập đường dẫn file video (hoặc để mặc định):', videoPath || 'C:/Videos/sample_demo_video.mp4');
    if (manualPath) {
      setVideoPath(manualPath);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const finalProjectName = projectName.trim() || generateTimestampName();
    const finalMediaPath = videoPath.trim() || (projectMode === 'DUBBING' ? 'C:/Videos/sample_demo_video.mp4' : 'source/story.txt');

    await onCreateProject(
      finalProjectName,
      finalMediaPath,
      translationStyle,
      translationStyle === 'custom' ? customStyleText : undefined,
      projectMode,
      storyText
    );
  };

  return (
    <div className="h-full w-full flex flex-col items-center justify-center p-4 md:p-8 overflow-y-auto custom-scrollbar select-none bg-[#0b0d10]">
      <div className="w-full max-w-xl bg-[#111318] border border-white/10 rounded-2xl p-6 md:p-8 shadow-2xl shadow-black/80 space-y-6">
        
        {/* MODAL HEADER */}
        <div className="text-center space-y-1.5">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-gradient-to-tr from-cyan-500/20 to-indigo-500/20 text-cyan-400 border border-cyan-500/30 mb-2 shadow-lg shadow-cyan-500/10">
            <Sparkles size={24} />
          </div>
          <h2 className="text-xl md:text-2xl font-extrabold text-white font-['Outfit'] tracking-tight">
            Tạo Dự Án Mới
          </h2>
          <p className="text-xs text-slate-400 max-w-md mx-auto">
            Chọn loại dự án và bắt đầu tự động hóa quy trình lồng tiếng hoặc làm video truyện AI.
          </p>
        </div>

        {/* MODE SELECTOR (DUBBING / STORY) */}
        <div className="grid grid-cols-2 gap-3 p-1 bg-black/40 border border-white/5 rounded-xl">
          <button
            type="button"
            onClick={() => setProjectMode('DUBBING')}
            className={`py-3 px-4 rounded-lg flex items-center justify-center gap-2.5 text-xs font-extrabold transition-all cursor-pointer ${
              projectMode === 'DUBBING'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20 scale-[1.02]'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <Video size={16} />
            <span>Dịch & Lồng Tiếng Video</span>
          </button>

          <button
            type="button"
            onClick={() => setProjectMode('STORY')}
            className={`py-3 px-4 rounded-lg flex items-center justify-center gap-2.5 text-xs font-extrabold transition-all cursor-pointer ${
              projectMode === 'STORY'
                ? 'bg-gradient-to-r from-purple-500 to-indigo-600 text-white shadow-lg shadow-purple-500/20 scale-[1.02]'
                : 'text-slate-400 hover:text-slate-200 hover:bg-white/5'
            }`}
          >
            <BookOpen size={16} />
            <span>Tạo Video Truyện AI</span>
          </button>
        </div>

        {/* FORM FIELDS */}
        <form onSubmit={handleSubmit} className="space-y-4">
          
          {/* PROJECT NAME */}
          <div>
            <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
              Tên Dự Án
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={projectName}
                onChange={e => setProjectName(e.target.value)}
                placeholder="ví dụ: Project_2026..."
                className="flex-1 bg-[#07080a] border border-white/10 rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-cyan-500 font-mono font-semibold"
              />
              <button 
                type="button" 
                onClick={() => setProjectName(generateTimestampName())}
                title="Đặt tên tự động"
                className="px-3 py-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-slate-300 text-xs font-bold flex items-center gap-1.5 border border-white/10 transition-all cursor-pointer"
              >
                <RefreshCw size={13} />
                <span className="hidden sm:inline">Tự Động</span>
              </button>
            </div>
          </div>

          {/* DUBBING MODE: VIDEO PATH */}
          {projectMode === 'DUBBING' && (
            <div>
              <label className="block text-xs font-bold text-slate-300 mb-1.5 uppercase tracking-wider">
                File Video Đầu Vào (MP4 / MKV / AVI)
              </label>
              <div className="flex gap-2">
                <input
                  type="text"
                  readOnly
                  value={videoPath}
                  placeholder="Chọn file video từ máy tính (hoặc để trống làm mẫu)..."
                  className="flex-1 bg-[#07080a] border border-white/10 rounded-xl px-3.5 py-2.5 text-xs text-slate-200 placeholder-slate-600 font-mono truncate"
                />
                <button 
                  type="button" 
                  onClick={handleSelectVideoFile}
                  className="px-4 py-2.5 rounded-xl bg-cyan-500/15 hover:bg-cyan-500/25 text-cyan-300 text-xs font-bold flex items-center gap-1.5 border border-cyan-500/30 transition-all cursor-pointer"
                >
                  <FolderOpen size={15} />
                  <span>Chọn File</span>
                </button>
              </div>
            </div>
          )}

          {/* STORY MODE INFO BOX */}
          {projectMode === 'STORY' && (
            <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/25 flex items-start gap-3">
              <Sparkles size={18} className="text-purple-400 flex-shrink-0 mt-0.5" />
              <div className="text-xs text-purple-200 leading-relaxed">
                <span className="font-bold text-purple-300">Động cơ AI Novel Engine tự động:</span> Ý tưởng, thế giới (World Bible), phân arc (Master Plan) và tự động sáng tác sẽ được AI xây dựng ngay trong workspace sau khi tạo dự án.
              </div>
            </div>
          )}

          {/* TOGGLE ADVANCED SETTINGS */}
          <div className="pt-1">
            <button
              type="button"
              onClick={() => setShowAdvanced(!showAdvanced)}
              className="flex items-center gap-2 text-xs text-slate-400 hover:text-cyan-400 font-semibold transition-colors cursor-pointer"
            >
              <SlidersHorizontal size={14} />
              <span>{showAdvanced ? 'Ẩn cấu hình nâng cao' : 'Cấu hình nâng cao (Dịch thuật, AI Model)'}</span>
              {showAdvanced ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>
          </div>

          {/* COLLAPSIBLE ADVANCED SETTINGS PANEL */}
          {showAdvanced && (
            <div className="p-4 rounded-xl bg-black/40 border border-white/5 space-y-3.5 text-xs animate-fadeIn">
              {projectMode === 'DUBBING' ? (
                <>
                  <div>
                    <label className="block font-bold text-slate-300 mb-1 flex items-center gap-1.5">
                      <Languages size={14} className="text-cyan-400" />
                      <span>Phong Cách Dịch Thuật (Translation Style)</span>
                    </label>
                    <select
                      value={translationStyle}
                      onChange={e => setTranslationStyle(e.target.value)}
                      className="w-full bg-[#07080a] border border-white/10 rounded-lg p-2 text-xs text-cyan-300 font-semibold focus:outline-none"
                    >
                      {TRANSLATION_STYLES.map(style => (
                        <option key={style.id} value={style.id} className="bg-[#0f172a] text-white">
                          {style.name}
                        </option>
                      ))}
                    </select>
                    <p className="text-[11px] text-slate-400 mt-1 italic">
                      {selectedStyleObj.description}
                    </p>
                  </div>

                  {translationStyle === 'custom' && (
                    <div>
                      <label className="block font-bold text-amber-400 mb-1">
                        Yêu Cầu Dịch Tùy Chỉnh
                      </label>
                      <textarea
                        value={customStyleText}
                        onChange={e => setCustomStyleText(e.target.value)}
                        placeholder="Ví dụ: 'Dịch tiếng Việt tự nhiên như phim chiếu rạp, ưu tiên xưng hô thân mật'..."
                        rows={2}
                        className="w-full bg-[#07080a] border border-amber-500/30 rounded-lg p-2 text-xs text-white focus:outline-none"
                      />
                    </div>
                  )}
                </>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block font-bold text-slate-300 mb-1">
                      🎨 Mô Hình AI Tạo Ảnh
                    </label>
                    <select className="w-full bg-[#07080a] border border-white/10 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500">
                      <option value="runwayml/stable-diffusion-v1-5">SD 1.5 - Realistic Vision v5.1 (GPU Local)</option>
                      <option value="anything-v5">SD 1.5 - Anything V5 (Phong cách Anime / Truyện Tranh)</option>
                      <option value="stabilityai/sdxl-turbo">SDXL Turbo (Siêu Tốc 4-Step)</option>
                      <option value="procedural">Procedural Preview Renderer (Tạo ảnh phác thảo siêu tốc)</option>
                    </select>
                  </div>
                  <div>
                    <label className="block font-bold text-slate-300 mb-1">
                      🗣️ Giọng Đọc Piper TTS
                    </label>
                    <select className="w-full bg-[#07080a] border border-white/10 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500">
                      <option value="vi_VN-vais1000-medium">vi_VN-vais1000-medium (Giọng Đọc Tiếng Việt Truyền Cảm - Mặc định)</option>
                      <option value="vi_VN-vivos-x_low">vi_VN-vivos-x_low (Giọng Đọc Tiếng Việt Siêu Tốc)</option>
                      <option value="vi_VN-viss-low">vi_VN-viss-low (Giọng Đọc Tiếng Việt Nhẹ & Nhanh)</option>
                    </select>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* SUBMIT BUTTON */}
          <button 
            type="submit" 
            disabled={isCreating}
            className={`w-full py-3.5 px-4 rounded-xl font-extrabold text-sm flex items-center justify-center gap-2 shadow-xl transition-all cursor-pointer active:scale-[0.99] disabled:opacity-50 mt-2 ${
              projectMode === 'DUBBING'
                ? 'bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-white shadow-cyan-500/25'
                : 'bg-gradient-to-r from-purple-500 to-indigo-600 hover:from-purple-400 hover:to-indigo-500 text-white shadow-purple-500/25'
            }`}
          >
            {isCreating ? <Loader2 size={18} className="animate-spin" /> : <Sparkles size={18} />} 
            <span>{isCreating ? 'Đang Khởi Tạo Dự Án...' : 'TẠO DỰ ÁN NGAY'}</span>
          </button>
        </form>

      </div>
    </div>
  );
};
