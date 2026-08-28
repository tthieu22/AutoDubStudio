import React, { useState, useEffect } from 'react';
import { Layers, Search, ChevronRight, Target, Flame, Eye, Sparkles } from 'lucide-react';
import { PythonEngineService } from '../../services/pythonEngine';

export interface ArcPlanItem {
  id: string;
  arc_num: number;
  title: string;
  start_chapter: number;
  end_chapter: number;
  goal: string;
  conflict: string;
  major_reveal: string;
  character_development: string;
  status: string;
}

interface ArcPlannerProps {
  projectDir?: string | null;
}

const DEFAULT_25_ARCS: ArcPlanItem[] = [
  { id: 'arc_01', arc_num: 1, title: 'Arc 01 — Xuyên Không & Thanh Vân Tông', start_chapter: 1, end_chapter: 40, goal: 'Lập nghiệp, kích hoạt hệ thống & gia nhập tông môn', conflict: 'Bị nội môn đệ tử khiêu khích', major_reveal: 'Hệ thống có khả năng chuyển hóa linh khí phế thải', character_development: 'Từ lo sợ chuyển sang tự tin', status: 'PLANNED' },
  { id: 'arc_02', arc_num: 2, title: 'Arc 02 — Tông Môn Đại Tỷ & Trúc Cơ', start_chapter: 41, end_chapter: 80, goal: 'Thu thập Tinh Hà Quả để đột phá Trúc Cơ', conflict: 'Ma Tông vây bắt đệ tử trong bí cảnh', major_reveal: 'Sư phụ có quan hệ bí mật với Ma Tông', character_development: 'Trưởng thành, quyết đoán hơn', status: 'PLANNED' },
  { id: 'arc_03', arc_num: 3, title: 'Arc 03 — Vạn Yêu Sâm Lâm & Trảm Sát Tà Tu', start_chapter: 81, end_chapter: 120, goal: 'Rèn luyện thực chiến tại Vạn Yêu Sâm Lâm', conflict: 'Thủ lĩnh Yêu Tộc truy sát', major_reveal: 'Phát hiện vết tích Viễn Cổ Tiên Phủ', character_development: 'Biết suy tính đại cục', status: 'PLANNED' },
  { id: 'arc_04', arc_num: 4, title: 'Arc 04 — Bí Cảnh Tinh Hà & Thu Hoạch Tiên Dược', start_chapter: 121, end_chapter: 160, goal: 'Khám phá tầng sâu Bí Cảnh Tinh Hà', conflict: 'Tranh chấp Tiên Dược với các Đại Tông', major_reveal: 'Tìm thấy bản đồ Thập Đại Tiên Đế', character_development: 'Nâng cao uy vọng', status: 'PLANNED' },
  { id: 'arc_05', arc_num: 5, title: 'Arc 05 — Tông Môn Tỷ Võ & Đột Phá Kim Đan', start_chapter: 161, end_chapter: 200, goal: 'Tham gia Tông Môn Tỷ Võ đoạt danh hiệu số 1', conflict: 'Đối thủ sử dụng Cấm Thuật', major_reveal: 'Hệ thống mở khóa chức năng luyện đan cấp cao', character_development: 'Trở thành trụ cột thế hệ trẻ', status: 'PLANNED' },
  { id: 'arc_06', arc_num: 6, title: 'Arc 06 — Chu Du Nam Châu & Khởi Động Phong Vân', start_chapter: 201, end_chapter: 240, goal: 'Xuất sơn du ngoạn Nam Châu tích lũy tâm cảnh', conflict: 'Tộc nhân bị đe dọa bởi cường hào', major_reveal: 'Gia tộc ẩn chứa huyết mạch Thần Thú', character_development: 'Giữ vững sơ tâm chính đạo', status: 'PLANNED' },
  { id: 'arc_07', arc_num: 7, title: 'Arc 07 — Hắc Sương Đảo & Cửu Sương Ma Tộc', start_chapter: 241, end_chapter: 280, goal: 'Khai phá Hắc Sương Đảo, giải cứu đồng môn', conflict: 'Cửu Sương Ma Tộc tái xuất', major_reveal: 'Ma Tộc âm mưu phá hủy trận pháp đại lục', character_development: 'Trải nghiệm ranh giới sinh tử', status: 'PLANNED' },
  { id: 'arc_08', arc_num: 8, title: 'Arc 08 — Thập Đại Tông Môn Hội Đấu & Ngộ Đạo', start_chapter: 281, end_chapter: 320, goal: 'Bảo vệ danh dự tông môn tại Hội Đấu', conflict: 'Cường giả Lão Quái gièm pha', major_reveal: 'Lĩnh ngộ Kiếm Ý Hỗn Độn', character_development: 'Khẳng định vị thế Thiên Tài', status: 'PLANNED' },
  { id: 'arc_09', arc_num: 9, title: 'Arc 09 — Viễn Cổ Phế Tích & Ngưng Tụ Nguyên Anh', start_chapter: 321, end_chapter: 360, goal: 'Thâm nhập Viễn Cổ Phế Tích kết Nguyên Anh', conflict: 'Cạm bẫy Thiên Đạo và Tâm Ma', major_reveal: 'Hệ thống ngưng tụ Nguyên Anh Bất Tử', character_development: 'Đột phá ranh giới nhân sĩ', status: 'PLANNED' },
  { id: 'arc_10', arc_num: 10, title: 'Arc 10 — Bắc Hoàng Cung & Tranh Chấp Tiên Thể', start_chapter: 361, end_chapter: 400, goal: 'Đến Bắc Hoàng Cung tìm kiếm Linh Mạch', conflict: 'Cạnh tranh vị trí Thánh Tử', major_reveal: 'Bắc Hoàng Cung do Tiên Nhân thành lập', character_development: 'Trở thành Lãnh đạo thế hệ mới', status: 'PLANNED' },
  { id: 'arc_11', arc_num: 11, title: 'Arc 11 — Vực Ngoại Thiên Ma & Hộ Vệ Nhân Tộc', start_chapter: 401, end_chapter: 440, goal: 'Ngăn chặn Vực Ngoại Thiên Ma xâm lược', conflict: 'Đại quân Ma Tộc tràn vào Nhân Tộc', major_reveal: 'Bí mật Cửu Trọng Thiên Bí Cảnh', character_development: 'Hi sinh cá nhân vì đại cục', status: 'PLANNED' },
  { id: 'arc_12', arc_num: 12, title: 'Arc 12 — Thiên Đạo Cung & Nguy Cơ Diệt Tông', start_chapter: 441, end_chapter: 480, goal: 'Giải cứu Thanh Vân Tông khỏi Thiên Đạo Cung', conflict: 'Pháp Trận Diệt Thế giáng xuống', major_reveal: 'Tổ sư Thanh Vân Tông còn sống ở Linh Giới', character_development: 'Gắn kết tình cảm sư môn', status: 'PLANNED' },
  { id: 'arc_13', arc_num: 13, title: 'Arc 13 — Tiên Ma Đại Chiến & Hóa Thần Khái Niệm', start_chapter: 481, end_chapter: 520, goal: 'Quyết chiến với Ma Hoàng thống nhất đại lục', conflict: 'Ma Hoàng sử dụng lực lượng Linh Giới', major_reveal: 'Tìm ra đường phi thăng duy nhất', character_development: 'Đạt đỉnh cao Phàm Giới', status: 'PLANNED' },
  { id: 'arc_14', arc_num: 14, title: 'Arc 14 — Linh Giới Giáng Lâm & Đột Phá Hóa Thần', start_chapter: 521, end_chapter: 560, goal: 'Vượt Kiếp Hóa Thần, nghênh đón Linh Giới', conflict: 'Thiên Kiếp Cửu Trọng hủy diệt', major_reveal: 'Chấn động toàn bộ Nhân Tộc', character_development: 'Chuẩn bị phi thăng', status: 'PLANNED' },
  { id: 'arc_15', arc_num: 15, title: 'Arc 15 — Phi Thăng Linh Giới & Cực Đạo Tinh Vân', start_chapter: 561, end_chapter: 600, goal: 'Phi thăng Linh Giới, bắt đầu hành trình mới', conflict: 'Cường giả Linh Giới coi thường Phàm Giới', major_reveal: 'Phát hiện Linh Giới rộng lớn gấp triệu lần', character_development: 'Hạ mình học hỏi, bộc phát sức mạnh', status: 'PLANNED' },
  { id: 'arc_16', arc_num: 16, title: 'Arc 16 — Linh Giới Vô Địch & Đột Phá Luyện Hư', start_chapter: 601, end_chapter: 640, goal: 'Gia nhập Tiên Tông Linh Giới, đột phá Luyện Hư', conflict: 'Thế lực bản địa vây ép Đệ tử Phi Thăng', major_reveal: 'Khai mở Hỗn Độn Tiên Thể', character_development: 'Vượt cấp trảm sát đối thủ', status: 'PLANNED' },
  { id: 'arc_17', arc_num: 17, title: 'Arc 17 — Thái Cổ Linh Ma & Thập Phương Tranh Bá', start_chapter: 641, end_chapter: 680, goal: 'Tham gia Tranh Bá Thập Phương tại Linh Giới', conflict: 'Thái Cổ Linh Ma tỉnh giấc', major_reveal: 'Hệ thống nâng cấp phiên bản Tiên Giới', character_development: 'Thâu tóm tài nguyên 10 phương', status: 'PLANNED' },
  { id: 'arc_18', arc_num: 18, title: 'Arc 18 — Hợp Thể Cảnh & Phá Giải Thiên Cơ', start_chapter: 681, end_chapter: 720, goal: 'Đột phá Hợp Thể Cảnh, phân thân vạn giới', conflict: 'Thiên Cơ Đao áp đặt định mệnh', major_reveal: 'Thao túng quy luật Thời Gian & Không Gian', character_development: 'Nắm giữ vận mệnh cá nhân', status: 'PLANNED' },
  { id: 'arc_19', arc_num: 19, title: 'Arc 19 — Vạn Cổ Tiên Môn & Đột Phá Đại Thừa', start_chapter: 721, end_chapter: 760, goal: 'Xây dựng Vạn Cổ Tiên Môn xưng bá Linh Giới', conflict: 'Thập Đại Tông Môn Linh Giới vây quét', major_reveal: 'Tổ tiên Tiên Giới truyền ý chỉ', character_development: 'Quyết định phi thăng Tiên Giới', status: 'PLANNED' },
  { id: 'arc_20', arc_num: 20, title: 'Arc 20 — Độ Kiếp Kỳ & Kiếp Sóng Vũ Trụ', start_chapter: 761, end_chapter: 800, goal: 'Vượt qua Kiếp Sóng Vũ Trụ bước vào Độ Kiếp', conflict: 'Tâm Ma Cửu Trọng và Thiên Hỏa', major_reveal: 'Sức mạnh chạm ngưỡng Tiên Nhân', character_development: 'Tuyệt đối vô địch Linh Giới', status: 'PLANNED' },
  { id: 'arc_21', arc_num: 21, title: 'Arc 21 — Phi Thăng Tiên Giới & Cửu Thiên Tiên Vực', start_chapter: 801, end_chapter: 840, goal: 'Phi thăng Tiên Giới, nhập Cửu Thiên Tiên Vực', conflict: 'Tiên Binh Tiên Tướng kiểm tra', major_reveal: 'Tiên Giới đầy tranh đoạt tàn khốc', character_development: 'Tái lập trật tự bản thân', status: 'PLANNED' },
  { id: 'arc_22', arc_num: 22, title: 'Arc 22 — Tiên Vương Tranh Hùng & Thôn Phệ Tinh Hà', start_chapter: 841, end_chapter: 880, goal: 'Thâu tóm Tiên Mạch, chứng đạo Tiên Vương', conflict: 'Cổ Tiên Vương phản kích', major_reveal: 'Hệ thống kết hợp Hỗn Độn Chi Nguyên', character_development: 'Xưng Vương một vùng Tiên Vực', status: 'PLANNED' },
  { id: 'arc_23', arc_num: 23, title: 'Arc 23 — Tiên Đế Di Tích & Độn Nhập Hỗn Độn', start_chapter: 881, end_chapter: 920, goal: 'Khám phá Di Tích Tiên Đế Viễn Cổ', conflict: 'Tiên Đế Chuẩn Giới vây sát', major_reveal: 'Mở ra Bí mật Nguồn gốc Hệ thống', character_development: 'Lĩnh ngộ quy luật Hỗn Độn', status: 'PLANNED' },
  { id: 'arc_24', arc_num: 24, title: 'Arc 24 — Hỗn Độn Ma Thần & Đột Phá Tiên Đế', start_chapter: 921, end_chapter: 960, goal: 'Chống lại Hỗn Độn Ma Thần diệt thế', conflict: 'Vũ trụ đứng trước nguy cơ sụp sổng', major_reveal: 'Hy sinh thân thể đúc Hỗn Độn Kim Thân', character_development: 'Thành tựu Tiên Đế Cảnh', status: 'PLANNED' },
  { id: 'arc_25', arc_num: 25, title: 'Arc 25 — Vô Địch Tiên Đế & Trấn Áp Chư Thiên', start_chapter: 961, end_chapter: 1000, goal: 'Xưng bá Chư Thiên Vạn Giới, thiết lập Tiên Trật', conflict: 'Kẻ thù cuối cùng Hỗn Độn Chủ', major_reveal: 'Tối ưu hóa Hệ thống thành Quy Luật Vũ Trụ', character_development: 'Đạt cảnh giới Vô Địch Vĩnh Hằng', status: 'PLANNED' }
];

export const ArcPlanner: React.FC<ArcPlannerProps> = ({ projectDir }) => {
  const [arcs, setArcs] = useState<ArcPlanItem[]>(DEFAULT_25_ARCS);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedArcId, setSelectedArcId] = useState<string>('');

  useEffect(() => {
    if (projectDir) {
      PythonEngineService.readProjectJson(projectDir).then(data => {
        if (data && data.arc_plans && Array.isArray(data.arc_plans) && data.arc_plans.length >= 5) {
          setArcs(data.arc_plans);
        } else {
          setArcs(DEFAULT_25_ARCS);
        }
      }).catch(() => {
        setArcs(DEFAULT_25_ARCS);
      });
    }
  }, [projectDir]);

  const filteredArcs = arcs.filter(a =>
    a.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    a.goal.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="h-full flex flex-col bg-[#0b0d10] text-slate-100 p-4 space-y-4 font-sans">
      {/* HEADER */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[#111318] p-4 rounded-xl border border-white/5 shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center border border-indigo-500/20">
            <Layers size={18} />
          </div>
          <div>
            <h2 className="text-base font-bold text-white font-['Outfit'] tracking-tight">
              Master Plan — Danh Sách 20-30 Arcs Truyện
            </h2>
            <p className="text-xs text-slate-400">
              Cấu trúc tổng thể định hướng toàn bộ 1.000 chương truyện tu tiên.
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 relative max-w-xs w-full">
          <Search size={14} className="absolute left-3 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Tìm kiếm Arc..."
            className="w-full bg-[#0b0d10] border border-white/10 rounded-lg pl-9 pr-3 py-1.5 text-xs text-slate-200 focus:outline-none"
          />
        </div>
      </div>

      {/* ARCS GRID */}
      <div className="flex-1 overflow-y-auto space-y-3 custom-scrollbar">
        {filteredArcs.length === 0 ? (
          <div className="h-full min-h-[300px] flex flex-col items-center justify-center border-2 border-dashed border-white/10 rounded-2xl bg-[#111318]/50 p-8 text-center">
            <Layers size={32} className="text-indigo-400 mb-3" />
            <h3 className="text-base font-bold text-white mb-1 font-['Outfit']">Chưa Có Kế Hoạch Arc</h3>
            <p className="text-xs text-slate-400 max-w-md">
              Vào Novel Dashboard và nhấn "Tạo Thế Giới & Master Plan" để AI xây dựng toàn bộ Arcs cho bộ truyện dài.
            </p>
          </div>
        ) : (
          filteredArcs.map(arc => {
            const isSelected = selectedArcId === arc.id;
            return (
              <div
                key={arc.id || arc.arc_num}
                onClick={() => setSelectedArcId(arc.id || String(arc.arc_num))}
                className={`p-4 rounded-xl border transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-indigo-500/10 border-indigo-500/50 shadow-md shadow-indigo-500/10'
                    : 'bg-[#111318] hover:bg-[#161a22] border-white/5'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 text-xs font-bold font-mono">
                      Arc #{arc.arc_num}
                    </span>
                    <h3 className="text-sm font-bold text-white font-['Outfit']">{arc.title}</h3>
                  </div>

                  <span className="text-xs font-mono text-cyan-400 font-semibold">
                    Chương {arc.start_chapter} – {arc.end_chapter}
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs pt-2 border-t border-white/5">
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                      <Target size={11} className="text-emerald-400" /> Mục Tiêu Arc
                    </span>
                    <p className="text-slate-300">{arc.goal}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                      <Flame size={11} className="text-rose-400" /> Xung Đột Chính
                    </span>
                    <p className="text-slate-300">{arc.conflict}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="text-[10px] text-slate-500 uppercase font-bold flex items-center gap-1">
                      <Eye size={11} className="text-amber-400" /> Tiết Lộ Lớn (Major Reveal)
                    </span>
                    <p className="text-slate-300">{arc.major_reveal}</p>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
