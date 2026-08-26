import React, { useState, useEffect } from 'react';
import { 
  Sparkles, 
  Plus, 
  Trash2, 
  Check, 
  Edit3, 
  Search, 
  Flame, 
  Sliders, 
  Tag, 
  Info,
  Layers,
  RotateCcw
} from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

export interface SlangTrendItem {
  id: string;
  category: 'MEME' | 'ANCIENT' | 'EMOTIONAL' | 'DRAMATIC';
  phrase: string;
  explanation: string;
  enabled: boolean;
}

export const INITIAL_TIKTOK_TRENDS: SlangTrendItem[] = [
  { id: 't-1', category: 'MEME', phrase: 'Đèo mẹ', explanation: 'Từ ẩn ý nói lái lách luật cảm thán hài hước', enabled: true },
  { id: 't-2', category: 'MEME', phrase: 'Đỉnh nóc kịch trần bay phấp phới', explanation: 'Khen ngợi xuất sắc, tuyệt vời đến cực hạn', enabled: true },
  { id: 't-3', category: 'MEME', phrase: 'Tuyệt đối điện ảnh', explanation: 'Hình ảnh hoặc khoảnh khắc đẹp mê ly như phim', enabled: true },
  { id: 't-4', category: 'MEME', phrase: 'Dữ liệu không khớp với server gốc', explanation: 'Nói dối, bốc phét, thông tin sai sự thật', enabled: true },
  { id: 't-5', category: 'MEME', phrase: 'Thu thập dữ liệu xã hội', explanation: 'Hóng hớt chuyện xung quanh', enabled: true },
  { id: 't-6', category: 'MEME', phrase: 'Đang trong quá trình tích lũy tài sản', explanation: 'Cách nói giảm nói tránh của hết tiền / nghèo', enabled: true },
  { id: 't-7', category: 'MEME', phrase: 'Giảm sức mạnh con tướng này giúp em', explanation: 'Khen đối phương quá giỏi / out trình', enabled: true },
  { id: 't-8', category: 'MEME', phrase: 'Anh em mình cứ thế thôi, hẹ hẹ hẹ', explanation: 'Thể hiện sự đồng lòng vô tri', enabled: true },
  { id: 't-9', category: 'MEME', phrase: 'Trí thông minh giản zị', explanation: 'Mỉa mai khéo phát ngôn ngốc nghếch', enabled: true },
  { id: 't-10', category: 'MEME', phrase: 'Gia môn bất hạnh', explanation: 'Cảm thán hài hước khi gặp chuyện bất ổn', enabled: true },
  { id: 't-11', category: 'MEME', phrase: 'Ủa alo', explanation: 'Cảm thán ngơ ngác khi có sự cố lạ', enabled: true },
  { id: 't-12', category: 'MEME', phrase: 'Xu cà cà', explanation: 'Cảm thán xui xẻo', enabled: true },
  { id: 't-13', category: 'ANCIENT', phrase: 'Trùng sinh nghịch thiên cải mệnh', explanation: 'Văn phong cổ trang tiên hiệp trùng sinh', enabled: true },
  { id: 't-14', category: 'EMOTIONAL', phrase: 'Giai điệu chữa lành tâm hồn', explanation: 'Văn phong dịu dàng sâu lắng', enabled: true },
  { id: 't-15', category: 'DRAMATIC', phrase: 'Pha lật kèo kinh hoàng 3s đầu', explanation: 'Tạo hook kịch tính giật gân', enabled: true }
];

interface TikTokTrendManagerProps {
  projectDir?: string | null;
}

export const TikTokTrendManager: React.FC<TikTokTrendManagerProps> = ({ projectDir }) => {
  const [trends, setTrends] = useState<SlangTrendItem[]>(INITIAL_TIKTOK_TRENDS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [density, setDensity] = useState<'LOW' | 'MEDIUM' | 'HIGH'>('LOW');

  const [newPhrase, setNewPhrase] = useState('');
  const [newExplanation, setNewExplanation] = useState('');

  const toggleEnable = (id: string) => {
    setTrends(prev => prev.map(t => t.id === id ? { ...t, enabled: !t.enabled } : t));
  };

  const handleAddTrend = () => {
    if (!newPhrase.trim()) return;
    const item: SlangTrendItem = {
      id: `t-${Date.now()}`,
      category: 'MEME',
      phrase: newPhrase.trim(),
      explanation: newExplanation.trim() || 'Custom user trend',
      enabled: true
    };
    setTrends(prev => [item, ...prev]);
    setNewPhrase('');
    setNewExplanation('');
  };

  const handleDeleteTrend = (id: string) => {
    setTrends(prev => prev.filter(t => t.id !== id));
  };

  const filteredTrends = trends.filter(t => {
    const matchesCat = selectedCategory === 'ALL' || t.category === selectedCategory;
    const matchesQuery = t.phrase.toLowerCase().includes(searchQuery.toLowerCase()) || t.explanation.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCat && matchesQuery;
  });

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-flame-500/10 bg-amber-500/10 text-amber-400 flex items-center justify-center border border-amber-500/20">
            <Flame size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              TikTok Viral Slang & Trend Dictionary (2026)
            </h2>
            <p className="text-xs text-slate-400">
              Quản lý danh sách từ lóng, nói lái, trend viral để truyền vào AI Qwen 2.5 Instruct viết lại kịch bản.
            </p>
          </div>
        </div>

        {/* DENSITY SLIDER */}
        <div className="flex items-center gap-2 bg-black/40 px-3 py-1.5 rounded-lg border border-white/10 text-xs">
          <Sliders size={14} className="text-purple-400" />
          <span className="text-slate-400 font-medium">Mật độ dùng Trend:</span>
          <select
            value={density}
            onChange={e => setDensity(e.target.value as any)}
            className="bg-[#111318] border border-white/10 rounded px-2 py-0.5 text-xs text-purple-300 font-bold focus:outline-none"
          >
            <option value="LOW">Thưa thớt (1-2 từ/chương - Khuyên dùng)</option>
            <option value="MEDIUM">Vừa phải (3-4 từ/chương)</option>
            <option value="HIGH">Nhiều (5+ từ/chương)</option>
          </select>
        </div>
      </div>

      {/* ADD NEW TREND FORM & FILTER BAR */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* ADD TREND INPUT */}
        <div className="bg-[#111318] p-3.5 rounded-xl border border-white/5 space-y-2.5">
          <h3 className="text-xs font-extrabold uppercase tracking-wider text-purple-300 font-['Outfit'] flex items-center gap-1.5">
            <Plus size={14} /> Thêm Từ Lóng / Trend Mới
          </h3>

          <input
            type="text"
            value={newPhrase}
            onChange={e => setNewPhrase(e.target.value)}
            placeholder="Nhập cụm từ trend (e.g. Đèo mẹ, Đỉnh nóc...)"
            className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-xs text-slate-200 focus:outline-none focus:border-purple-500"
          />

          <input
            type="text"
            value={newExplanation}
            onChange={e => setNewExplanation(e.target.value)}
            placeholder="Giải thích / Ngữ cảnh sử dụng..."
            className="w-full bg-black/40 border border-white/10 rounded-lg p-2 text-xs text-slate-400 focus:outline-none focus:border-purple-500"
          />

          <button
            onClick={handleAddTrend}
            className="w-full py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white font-extrabold text-xs flex items-center justify-center gap-1 shadow-md shadow-purple-600/20"
          >
            <Plus size={13} /> Thêm Vào Từ Điển AI
          </button>
        </div>

        {/* SEARCH & FILTER BAR */}
        <div className="lg:col-span-2 bg-[#111318] p-3.5 rounded-xl border border-white/5 flex flex-col justify-between space-y-2">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search size={14} className="absolute left-3 top-2.5 text-slate-400" />
              <input
                type="text"
                value={searchQuery}
                onChange={e => setSearchQuery(e.target.value)}
                placeholder="Tìm kiếm trend, từ lóng, giải nghĩa..."
                className="w-full bg-black/40 border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none"
              />
            </div>
            <button
              onClick={() => setTrends(INITIAL_TIKTOK_TRENDS)}
              className="px-2.5 py-1.5 rounded-lg bg-white/5 hover:bg-white/10 text-slate-400 text-xs font-semibold flex items-center gap-1"
              title="Khôi phục mặc định"
            >
              <RotateCcw size={12} /> Khôi phục
            </button>
          </div>

          <div className="flex items-center gap-2 text-xs overflow-x-auto">
            {['ALL', 'MEME', 'ANCIENT', 'EMOTIONAL', 'DRAMATIC'].map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-2.5 py-1 rounded-lg font-semibold transition-all ${
                  selectedCategory === cat
                    ? 'bg-purple-600/20 text-purple-300 border border-purple-500/40'
                    : 'text-slate-400 hover:bg-white/5'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* TREND DICTIONARY CARDS GRID */}
      <div className="flex-1 overflow-y-auto space-y-2 custom-scrollbar">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
          {filteredTrends.map(item => (
            <div
              key={item.id}
              className={`p-3 rounded-xl border transition-all ${
                item.enabled
                  ? 'bg-[#111318] border-white/10 hover:border-purple-500/40'
                  : 'bg-black/30 border-white/5 opacity-50'
              }`}
            >
              <div className="flex items-center justify-between mb-1.5">
                <span className="px-2 py-0.5 rounded bg-purple-500/15 text-purple-300 border border-purple-500/30 text-[10px] font-bold font-mono">
                  {item.category}
                </span>

                <div className="flex items-center gap-1.5">
                  <button
                    onClick={() => toggleEnable(item.id)}
                    className={`px-2 py-0.5 rounded text-[10px] font-bold transition-all ${
                      item.enabled ? 'bg-emerald-500/20 text-emerald-300' : 'bg-white/5 text-slate-500'
                    }`}
                  >
                    {item.enabled ? '✓ KÍCH HOẠT' : '○ ẨN'}
                  </button>
                  <button
                    onClick={() => handleDeleteTrend(item.id)}
                    className="p-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400"
                    title="Xóa Trend"
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>

              <h4 className="text-sm font-bold text-white font-['Outfit'] mb-1">"{item.phrase}"</h4>
              <p className="text-xs text-slate-400 line-clamp-2">{item.explanation}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
