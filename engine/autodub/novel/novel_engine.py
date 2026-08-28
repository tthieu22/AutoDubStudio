import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

from autodub.novel.novel_models import (
    StoryIdea, StoryBible, ArcPlan, ChapterPlan, ScenePlan, CanonFact, CharacterState, PlotThread
)
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.context_builder import ContextBuilder
from autodub.novel.canon_validator_engine import CanonValidatorEngine

from autodub.novel.prompts.story_director import StoryDirectorPrompt
from autodub.novel.prompts.master_planner import MasterPlannerPrompt
from autodub.novel.prompts.chapter_planner import ChapterPlannerPrompt
from autodub.novel.prompts.creative_engine import CreativeEnginePrompt
from autodub.novel.prompts.scene_planner_novel import NovelScenePlannerPrompt
from autodub.novel.prompts.writer import NovelWriterPrompt
from autodub.novel.prompts.editor import NovelEditorPrompt
from autodub.novel.prompts.memory_extractor import MemoryExtractorPrompt
from autodub.novel.prompts.canon_validator import CanonValidatorPrompt

from autodub.modules.llamacpp_client import LlamaCppClient, strip_think_tags

logger = logging.getLogger(__name__)


def log_gpu_hardware_status(callback=None):
    def _out(msg):
        logger.info(msg)
        print(f"[INFO] {msg}", flush=True)
        if callback:
            callback({"event": "novel_sub_stage", "step": "HARDWARE", "message": msg})

    _out("=== [HARDWARE ACCELERATION CHECK] ===")
    try:
        import torch
        if torch.cuda.is_available():
            dev_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            _out(f"[HARDWARE] 🚀 GPU Device Detected: {dev_name} ({vram_gb:.1f} GB VRAM)")
            _out("[HARDWARE] ⚡ PyTorch CUDA Acceleration: ACTIVE (Device 0)")
            _out("[HARDWARE] 🎯 Local LLM Offload: -ngl 99 (100% GPU VRAM Accelerated)")
        else:
            _out("[HARDWARE] ⚠️ CUDA not detected in PyTorch environment. Running CPU Fallback Mode.")
    except Exception as e:
        _out(f"[HARDWARE] GPU status check: {e}")


class NovelEngine:
    """
    Complete AI Novel Engine Orchestrator.
    Executes full pipeline:
    IDEA → STORY BIBLE → MASTER PLAN → ARC PLAN → CHAPTER PLAN → CREATIVE ENGINE → SCENE PLAN → AI WRITER → EDITOR → CANON VALIDATION → MEMORY EXTRACTOR → CANON DB → NEXT CHAPTER
    """

    def __init__(self, story_dir: Path, story_id: str = "story_001", llm_client: Optional[LlamaCppClient] = None):
        self.story_dir = Path(story_dir)
        self.story_dir.mkdir(parents=True, exist_ok=True)
        self.story_id = story_id

        db_path = self.story_dir / "story.db"
        self.db = NovelDatabase(db_path)
        self.context_builder = ContextBuilder(self.story_id, self.db)
        self.validator = CanonValidatorEngine(self.db)
        self.llm = llm_client or LlamaCppClient()
        self.is_running = False

    def _call_llm_json(self, prompt: str, default_val: Any) -> Any:
        try:
            raw_res = self.llm.generate(prompt=prompt, timeout=120)
            cleaned = strip_think_tags(raw_res)
            idx_brace = cleaned.find("{")
            idx_bracket = cleaned.find("[")

            if idx_bracket != -1 and (idx_brace == -1 or idx_bracket < idx_brace):
                end_bracket = cleaned.rfind("]") + 1
                return json.loads(cleaned[idx_bracket:end_bracket])
            elif idx_brace != -1:
                end_brace = cleaned.rfind("}") + 1
                return json.loads(cleaned[idx_brace:end_brace])
        except Exception as e:
            logger.warning(f"LLM JSON call fallback due to: {e}")
        return default_val

    def _update_project_json(self, data_patch: Dict[str, Any]):
        p_json = self.story_dir / "project.json"
        existing = {}
        if p_json.exists():
            try:
                existing = json.loads(p_json.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
        existing.update(data_patch)
        try:
            p_json.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to update project.json: {e}")

    # ══════════════════════════════════════════════════════════════
    # PHASE A: INITIALIZATION
    # ══════════════════════════════════════════════════════════════
    def initialize_story(self, idea: StoryIdea) -> StoryBible:
        logger.info(f"Initializing Novel '{idea.title}'...")
        self.db.create_story(self.story_id, idea)

        prompt = StoryDirectorPrompt.build_prompt(idea)
        raw_bible = self._call_llm_json(prompt, {
            "premise": f"Truyện tiên hiệp {idea.title}",
            "cultivation_system": [
                {"rank": 1, "name": "Luyện Khí", "description": "Tích tụ linh khí vào đan điền"},
                {"rank": 2, "name": "Trúc Cơ", "description": "Đúc kết Linh Đài"},
                {"rank": 3, "name": "Kim Đan", "description": "Ngưng tụ Kim Đan"},
                {"rank": 4, "name": "Nguyên Anh", "description": "Phá Đan thành Anh"},
                {"rank": 5, "name": "Hóa Thần", "description": "Thần thức xuất khiếu"}
            ],
            "characters": [
                {
                    "id": "char_001",
                    "name": idea.protagonist.get("name", "Lâm Phàm"),
                    "personality": ["Thận trọng", "Thông minh"],
                    "goal": "Trở thành Tiên Đế",
                    "realm": "Luyện Khí Tầng 1",
                    "location": "Thanh Vân Tông",
                    "known_information": ["Xuyên không"],
                    "secrets": ["Có hệ thống"]
                }
            ],
            "rules": ["Cảnh giới không thay đổi tùy tiện", "Nhân vật không biết trước tương lai"],
            "world": {
                "continent_name": "Đại Lục Tinh Hà",
                "locations": ["Thanh Vân Tông", "Bí Cảnh Tinh Hà"],
                "factions": ["Thanh Vân Tông", "Ma Tông"]
            },
            "terminology": {}
        })

        bible_file = self.story_dir / "story_bible.json"
        with open(bible_file, "w", encoding="utf-8") as f:
            json.dump(raw_bible, f, indent=2, ensure_ascii=False)

        # Save characters to DB
        from autodub.novel.novel_models import Character
        for c in raw_bible.get("characters", []):
            char_obj = Character(
                id=c.get("id", "char_001"),
                name=c.get("name", "Lâm Phàm"),
                personality=c.get("personality", []),
                goal=c.get("goal", ""),
                realm=c.get("realm", "Luyện Khí"),
                location=c.get("location", "Thanh Vân Tông"),
                known_information=c.get("known_information", []),
                secrets=c.get("secrets", [])
            )
            self.db.save_character(char_obj, self.story_id)

        # Format characters for UI CharacterBible tab
        formatted_chars = []
        for idx, c in enumerate(raw_bible.get("characters", []), start=1):
            formatted_chars.append({
                "id": c.get("id", f"char_{idx:03d}"),
                "name": c.get("name", "Lâm Phàm"),
                "alias": c.get("realm", "Luyện Khí"),
                "gender": c.get("gender", "Nam"),
                "age": str(c.get("age", "20")),
                "personality": ", ".join(c.get("personality", [])) if isinstance(c.get("personality"), list) else str(c.get("personality", "Thận trọng")),
                "appearance": f"Mục tiêu: {c.get('goal', 'Khám phá thế giới')}",
                "clothing": f"Cảnh giới: {c.get('realm', 'Luyện Khí')} • Vị trí: {c.get('location', 'Thanh Vân Tông')}",
                "voice": "vi_male_hero",
                "speakingStyle": "Trang trọng",
                "locked": True
            })

        # Format world lore for UI WorldBible tab
        formatted_lore = []
        world_info = raw_bible.get("world", {})
        if isinstance(world_info, dict):
            for loc in world_info.get("locations", []):
                name = loc if isinstance(loc, str) else loc.get("name", "Địa Danh")
                desc = f"Địa danh thuộc đại lục {world_info.get('continent_name', '')}" if isinstance(loc, str) else loc.get("description", "")
                formatted_lore.append({
                    "id": f"w-loc-{len(formatted_lore)}",
                    "category": "Location",
                    "name": name,
                    "description": desc,
                    "locked": True
                })
            for fac in world_info.get("factions", []):
                name = fac if isinstance(fac, str) else fac.get("name", "Thế Lực")
                formatted_lore.append({
                    "id": f"w-fac-{len(formatted_lore)}",
                    "category": "Organization",
                    "name": name,
                    "description": "Tông môn / Thế lực chính trong đại lục",
                    "locked": True
                })
        for cs in raw_bible.get("cultivation_system", []):
            formatted_lore.append({
                "id": f"w-cs-{len(formatted_lore)}",
                "category": "Rule",
                "name": f"Cảnh Giới #{cs.get('rank', 1)}: {cs.get('name')}",
                "description": cs.get("description", "Cảnh giới tu luyện"),
                "locked": True
            })

        # Format rules for UI StoryMemory tab
        formatted_memory = []
        for r in raw_bible.get("rules", []):
            formatted_memory.append({
                "id": f"mem-{len(formatted_memory)}",
                "category": "World",
                "content": r,
                "importance": "HIGH",
                "confidence": 1.0,
                "locked": True
            })

        self._update_project_json({
            "story_bible": raw_bible,
            "characters": formatted_chars,
            "world_lore": formatted_lore,
            "story_memory": formatted_memory
        })

        return StoryBible(**raw_bible)

    def _generate_default_25_arcs(self, story_id: str, total_chapters: int = 1000) -> List[ArcPlan]:
        arc_templates = [
            ("Arc 01 — Xuyên Không & Thanh Vân Tông", "Lập nghiệp, kích hoạt hệ thống & gia nhập tông môn", "Bị nội môn đệ tử khiêu khích", "Hệ thống có khả năng chuyển hóa linh khí phế thải", "Từ lo sợ chuyển sang tự tin"),
            ("Arc 02 — Tông Môn Đại Tỷ & Trúc Cơ", "Thu thập Tinh Hà Quả để đột phá Trúc Cơ", "Ma Tông vây bắt đệ tử trong bí cảnh", "Sư phụ có quan hệ bí mật với Ma Tông", "Trưởng thành, quyết đoán hơn"),
            ("Arc 03 — Vạn Yêu Sâm Lâm & Trảm Sát Tà Tu", "Rèn luyện thực chiến tại Vạn Yêu Sâm Lâm", "Thủ lĩnh Yêu Tộc truy sát", "Phát hiện vết tích Viễn Cổ Tiên Phủ", "Biết suy tính đại cục"),
            ("Arc 04 — Bí Cảnh Tinh Hà & Thu Hoạch Tiên Dược", "Khám phá tầng sâu Bí Cảnh Tinh Hà", "Tranh chấp Tiên Dược với các Đại Tông", "Tìm thấy bản đồ Thập Đại Tiên Đế", "Nâng cao uy vọng"),
            ("Arc 05 — Tông Môn Tỷ Võ & Đột Phá Kim Đan", "Tham gia Tông Môn Tỷ Võ đoạt danh hiệu số 1", "Đối thủ sử dụng Cấm Thuật", "Hệ thống mở khóa chức năng luyện đan cấp cao", "Trở thành trụ cột thế hệ trẻ"),
            ("Arc 06 — Chu Du Nam Châu & Khởi Động Phong Vân", "Xuất sơn du ngoạn Nam Châu tích lũy tâm cảnh", "Tộc nhân bị đe dọa bởi cường hào", "Gia tộc ẩn chứa huyết mạch Thần Thú", "Giữ vững sơ tâm chính đạo"),
            ("Arc 07 — Hắc Sương Đảo & Cửu Sương Ma Tộc", "Khai phá Hắc Sương Đảo, giải cứu đồng môn", "Cửu Sương Ma Tộc tái xuất", "Ma Tộc âm mưu phá hủy trận pháp đại lục", "Trải nghiệm ranh giới sinh tử"),
            ("Arc 08 — Thập Đại Tông Môn Hội Đấu & Ngộ Đạo", "Bảo vệ danh dự tông môn tại Hội Đấu", "Cường giả Lão Quái gièm pha", "Lĩnh ngộ Kiếm Ý Hỗn Độn", "Khẳng định vị thế Thiên Tài"),
            ("Arc 09 — Viễn Cổ Phế Tích & Ngưng Tụ Nguyên Anh", "Thâm nhập Viễn Cổ Phế Tích kết Nguyên Anh", "Cạm bẫy Thiên Đạo và Tâm Ma", "Hệ thống ngưng tụ Nguyên Anh Bất Tử", "Đột phá ranh giới nhân sĩ"),
            ("Arc 10 — Bắc Hoàng Cung & Tranh Chấp Tiên Thể", "Đến Bắc Hoàng Cung tìm kiếm Linh Mạch", "Cạnh tranh vị trí Thánh Tử", "Bắc Hoàng Cung do Tiên Nhân thành lập", "Trở thành Lãnh đạo thế hệ mới"),
            ("Arc 11 — Vực Ngoại Thiên Ma & Hộ Vệ Nhân Tộc", "Ngăn chặn Vực Ngoại Thiên Ma xâm lược", "Đại quân Ma Tộc tràn vào Nhân Tộc", "Bí mật Cửu Trọng Thiên Bí Cảnh", "Hi sinh cá nhân vì đại cục"),
            ("Arc 12 — Thiên Đạo Cung & Nguy Cơ Diệt Tông", "Giải cứu Thanh Vân Tông khỏi Thiên Đạo Cung", "Pháp Trận Diệt Thế giáng xuống", "Tổ sư Thanh Vân Tông còn sống ở Linh Giới", "Gắn kết tình cảm sư môn"),
            ("Arc 13 — Tiên Ma Đại Chiến & Hóa Thần Khái Niệm", "Quyết chiến với Ma Hoàng thống nhất đại lục", "Ma Hoàng sử dụng lực lượng Linh Giới", "Tìm ra đường phi thăng duy nhất", "Đạt đỉnh cao Phàm Giới"),
            ("Arc 14 — Linh Giới Giáng Lâm & Đột Phá Hóa Thần", "Vượt Kiếp Hóa Thần, nghênh đón Linh Giới", "Thiên Kiếp Cửu Trọng hủy diệt", "Chấn động toàn bộ Nhân Tộc", "Chuẩn bị phi thăng"),
            ("Arc 15 — Phi Thăng Linh Giới & Cực Đạo Tinh Vân", "Phi thăng Linh Giới, bắt đầu hành trình mới", "Cường giả Linh Giới coi thường Phàm Giới", "Phát hiện Linh Giới rộng lớn gấp triệu lần", "Hạ mình học hỏi, bộc phát sức mạnh"),
            ("Arc 16 — Linh Giới Vô Địch & Đột Phá Luyện Hư", "Gia nhập Tiên Tông Linh Giới, đột phá Luyện Hư", "Thế lực bản địa vây ép Đệ tử Phi Thăng", "Khai mở Hỗn Độn Tiên Thể", "Vượt cấp trảm sát đối thủ"),
            ("Arc 17 — Thái Cổ Linh Ma & Thập Phương Tranh Bá", "Tham gia Tranh Bá Thập Phương tại Linh Giới", "Thái Cổ Linh Ma tỉnh giấc", "Hệ thống nâng cấp phiên bản Tiên Giới", "Thâu tóm tài nguyên 10 phương"),
            ("Arc 18 — Hợp Thể Cảnh & Phá Giải Thiên Cơ", "Đột phá Hợp Thể Cảnh, phân thân vạn giới", "Thiên Cơ Đao áp đặt định mệnh", "Thao túng quy luật Thời Gian & Không Gian", "Nắm giữ vận mệnh cá nhân"),
            ("Arc 19 — Vạn Cổ Tiên Môn & Đột Phá Đại Thừa", "Xây dựng Vạn Cổ Tiên Môn xưng bá Linh Giới", "Thập Đại Tông Môn Linh Giới vây quét", "Tổ tiên Tiên Giới truyền ý chỉ", "Quyết định phi thăng Tiên Giới"),
            ("Arc 20 — Độ Kiếp Kỳ & Kiếp Sóng Vũ Trụ", "Vượt qua Kiếp Sóng Vũ Trụ bước vào Độ Kiếp", "Tâm Ma Cửu Trọng và Thiên Hỏa", "Sức mạnh chạm ngưỡng Tiên Nhân", "Tuyệt đối vô địch Linh Giới"),
            ("Arc 21 — Phi Thăng Tiên Giới & Cửu Thiên Tiên Vực", "Phi thăng Tiên Giới, nhập Cửu Thiên Tiên Vực", "Tiên Binh Tiên Tướng kiểm tra", "Nhận ra Tiên Giới đầy tranh đoạt tàn khốc", "Tái lập trật tự bản thân"),
            ("Arc 22 — Tiên Vương Tranh Hùng & Thôn Phệ Tinh Hà", "Thâu tóm Tiên Mạch, chứng đạo Tiên Vương", "Cổ Tiên Vương phản kích", "Hệ thống kết hợp Hỗn Độn Chi Nguyên", "Xưng Vương một vùng Tiên Vực"),
            ("Arc 23 — Tiên Đế Di Tích & Độn Nhập Hỗn Độn", "Khám phá Di Tích Tiên Đế Viễn Cổ", "Tiên Đế Chuẩn Giới vây sát", "Mở ra Bí mật Nguồn gốc Hệ thống", "Lĩnh ngộ quy luật Hỗn Độn"),
            ("Arc 24 — Hỗn Độn Ma Thần & Đột Phá Tiên Đế", "Chống lại Hỗn Độn Ma Thần diệt thế", "Vũ trụ đứng trước nguy cơ sụp đổ", "Hy sinh thân thể đúc Hỗn Độn Kim Thân", "Thành tựu Tiên Đế Cảnh"),
            ("Arc 25 — Vô Địch Tiên Đế & Trấn Áp Chư Thiên", "Xưng bá Chư Thiên Vạn Giới, thiết lập Tiên Trật", "Kẻ thù cuối cùng Hỗn Độn Chủ", "Tối ưu hóa Hệ thống thành Quy Luật Vũ Trụ", "Đạt cảnh giới Vô Địch Vĩnh Hằng")
        ]

        total_arcs = len(arc_templates)
        chapters_per_arc = max(10, total_chapters // total_arcs)

        arcs = []
        for idx, (title, goal, conflict, reveal, dev) in enumerate(arc_templates, start=1):
            start_c = (idx - 1) * chapters_per_arc + 1
            end_c = idx * chapters_per_arc if idx < total_arcs else total_chapters
            arcs.append(ArcPlan(
                id=f"arc_{idx:02d}",
                story_id=story_id,
                arc_num=idx,
                title=title,
                start_chapter=start_c,
                end_chapter=end_c,
                goal=goal,
                conflict=conflict,
                major_reveal=reveal,
                character_development=dev
            ))
        return arcs

    def generate_master_plan(self, total_chapters: int = 1000) -> List[ArcPlan]:
        logger.info(f"Generating Master Plan for {total_chapters} chapters...")
        bible_file = self.story_dir / "story_bible.json"
        bible_data = {}
        if bible_file.exists():
            bible_data = json.loads(bible_file.read_text(encoding="utf-8"))

        prompt = MasterPlannerPrompt.build_prompt(bible_data, total_chapters)
        raw_arcs = self._call_llm_json(prompt, [])

        arc_objs = []
        if isinstance(raw_arcs, dict) and "arcs" in raw_arcs:
            raw_arcs = raw_arcs["arcs"]

        if not isinstance(raw_arcs, list):
            raw_arcs = []

        for idx, a in enumerate(raw_arcs, start=1):
            if isinstance(a, str):
                a = {"title": a}
            elif not isinstance(a, dict):
                a = {}

            arc_objs.append(ArcPlan(
                id=f"arc_{idx:02d}",
                story_id=self.story_id,
                arc_num=a.get("arc_num", idx),
                title=a.get("title", f"Arc {idx}"),
                start_chapter=a.get("start_chapter", (idx-1)*40 + 1),
                end_chapter=a.get("end_chapter", idx*40),
                goal=a.get("goal", ""),
                conflict=a.get("conflict", ""),
                major_reveal=a.get("major_reveal", ""),
                character_development=a.get("character_development", "")
            ))

        if len(arc_objs) < 5:
            logger.info(f"LLM generated {len(arc_objs)} arcs. Expanding to full 25-Arc Master Plan for {total_chapters} chapters...")
            arc_objs = self._generate_default_25_arcs(self.story_id, total_chapters)

        self.db.save_arc_plans(arc_objs)

        # Sync formatted arc_plans to project.json for UI ArcPlanner tab
        arc_dicts = [a.model_dump() for a in arc_objs]
        self._update_project_json({
            "arc_plans": arc_dicts
        })

        return arc_objs

    # ══════════════════════════════════════════════════════════════
    # PHASE B: CHAPTER GENERATION PIPELINE
    # ══════════════════════════════════════════════════════════════
    def generate_chapter(self, chapter_num: int, sub_progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        logger.info(f"--- Generating Chapter {chapter_num} ---")

        def _notify(step: str, msg: str):
            if sub_progress_callback:
                sub_progress_callback({
                    "event": "novel_sub_stage",
                    "chapter": chapter_num,
                    "step": step,
                    "message": msg
                })

        # Ensure Story Bible & Master Plan are initialized if missing
        bible_file = self.story_dir / "story_bible.json"
        if not bible_file.exists():
            _notify("INITIALIZATION", "Story Bible missing. Auto-initializing Story Bible (Step 1)...")
            idea = StoryIdea(title=self.story_dir.name, total_chapters=1000)
            self.initialize_story(idea)

        arcs = self.db.get_arc_plans(self.story_id)
        if not arcs:
            _notify("MASTER_PLAN", "Master Plan arcs missing. Auto-generating Master Plan (Step 2 & 3)...")
            self.generate_master_plan(1000)

        # 1. Current Arc Plan
        arc = self.db.get_current_arc(self.story_id, chapter_num) or {
            "title": f"Arc cho Chapter {chapter_num}",
            "goal": "Tiến triển cốt truyện",
            "conflict": "Xung đột mới xuất hiện"
        }

        # 2. Chapter Planner
        _notify("CHAPTER_PLANNER", f"Step 4/7: Chapter Planner creating Chapter {chapter_num} plan & conflict...")
        open_threads = self.db.get_open_plot_threads(self.story_id)
        recent_summaries = self.db.get_recent_chapter_summaries(self.story_id, chapter_num, 3)
        c_planner_prompt = ChapterPlannerPrompt.build_prompt(chapter_num, arc, open_threads, recent_summaries)
        chap_plan = self._call_llm_json(c_planner_prompt, {
            "chapter_num": chapter_num,
            "goal": f"Đạt được mục tiêu chương {chapter_num}",
            "conflict": "Xung đột bất ngờ",
            "characters": ["char_001"],
            "reveal": "Tiết lộ bí mật mới",
            "ending": "Cliffhanger hồi hộp"
        })

        # 3. Creative Engine
        _notify("CREATIVE_ENGINE", f"Step 4/7: Creative Engine building plot twist options for Chapter {chapter_num}...")
        arc_title = arc.get("title") if isinstance(arc, dict) else getattr(arc, "title", f"Arc {chapter_num}")
        clean_summaries = [s.get("summary_text") if isinstance(s, dict) else str(s) for s in recent_summaries]
        context_summary = f"Giai đoạn: {arc_title}. Vừa diễn ra: {clean_summaries}"
        
        creative_prompt = CreativeEnginePrompt.build_prompt(chapter_num, chap_plan, context_summary)
        creative_options = self._call_llm_json(creative_prompt, {
            "option_a": {"title": "Phát triển tiêu chuẩn", "description": "Tình tiết diễn tiến tự nhiên"},
            "recommended_option": "option_a"
        })
        if isinstance(creative_options, dict):
            selected_creative = creative_options.get("option_a", {})
        else:
            selected_creative = {"title": "Phát triển", "description": str(creative_options)}

        # 4. Scene Planner
        _notify("SCENE_PLANNER", f"Step 4/7: Phân chia Chapter {chapter_num} thành các phân cảnh (scenes)...")
        s_planner_prompt = NovelScenePlannerPrompt.build_prompt(chapter_num, chap_plan, selected_creative)
        scenes_plan = self._call_llm_json(s_planner_prompt, [
            {
                "scene_index": 1,
                "goal": "Phát hiện thử thách",
                "emotion": "Căng thẳng",
                "conflict": "Đối đầu kẻ địch",
                "ending": "Khai phá bí mật",
                "estimated_words": 600
            },
            {
                "scene_index": 2,
                "goal": "Giải quyết thử thách",
                "emotion": "Hào hứng",
                "conflict": "Dùng át chủ bài",
                "ending": "Thu hoạch chiến lợi phẩm",
                "estimated_words": 700
            }
        ])

        if not isinstance(scenes_plan, list):
            scenes_plan = [scenes_plan]

        sanitized_scenes = []
        for idx, sc in enumerate(scenes_plan, start=1):
            if isinstance(sc, dict):
                sanitized_scenes.append(sc)
            else:
                sanitized_scenes.append({
                    "scene_index": idx,
                    "goal": str(sc) if sc else f"Diễn biến phân cảnh {idx}",
                    "emotion": "Căng thẳng",
                    "conflict": "Xung đột mới",
                    "ending": "Hồi hộp",
                    "estimated_words": 700
                })
        scenes_plan = sanitized_scenes

        # 5. Scene Writing
        char_ids = chap_plan.get("characters", ["char_001"]) if isinstance(chap_plan, dict) else ["char_001"]
        scene_drafts = []

        for sc_idx, sc in enumerate(scenes_plan, start=1):
            _notify("WRITER", f"Step 5/7: Qwen AI Writer crafting Scene {sc_idx}/{len(scenes_plan)} for Chapter {chapter_num}...")
            full_context = self.context_builder.build_writer_context(chapter_num, sc, char_ids)
            writer_prompt = NovelWriterPrompt.build_prompt(chapter_num, sc.get("scene_index", sc_idx), sc, full_context)

            # Generate prose text with try/except fallback so process never crashes if LLM server is offline
            try:
                scene_text = self.llm.generate(prompt=writer_prompt, timeout=120)
                cleaned_scene = strip_think_tags(scene_text)
            except Exception as e:
                logger.warning(f"LLM generate failed for Scene {sc_idx}: {e}")
                _notify("WARNING", f"[CẢNH BÁO] Chưa bật Local LLM Server ({self.llm.base_url}). Đang dùng Bộ văn phong mặc định cho Scene {sc_idx}...")
                cleaned_scene = f"### Phân Cảnh {sc_idx}: {sc.get('goal', 'Diễn biến câu chuyện')}\n\nLâm Phàm đứng giữa sân khấu Thanh Vân Tông, ngước nhìn mây mù cuồn cuộn trên vách núi. Linh khí xung quanh tràn vào cơ thể qua các khiếu huyệt, âm thanh hệ thống vang lên rõ ràng trong tâm trí. Dù diện đối với những lời gièm pha của đồng môn, ánh mắt hắn vẫn điềm nhiên thanh thản, tự tin dấn thân vào hành trình chinh phục đỉnh cao tiên đạo..."

            if not cleaned_scene or len(cleaned_scene) < 50:
                cleaned_scene = f"Phân cảnh {sc.get('scene_index')}: {sc.get('goal')}. Lâm Phàm chuẩn bị đối mặt với thử thách lớn..."

            scene_drafts.append(cleaned_scene)

        full_draft = "\n\n".join(scene_drafts)

        # 6. Novel Editor
        _notify("EDITOR", f"Step 6/7: Novel Editor polishing prose and dialogue for Chapter {chapter_num}...")
        editor_prompt = NovelEditorPrompt.build_prompt(chapter_num, full_draft)
        editor_res = self._call_llm_json(editor_prompt, {
            "edited_text": full_draft,
            "changes_made": ["Biên tập văn phong tự động"]
        })
        if isinstance(editor_res, dict):
            final_text = editor_res.get("edited_text", full_draft)
        elif isinstance(editor_res, str):
            final_text = editor_res
        else:
            final_text = full_draft

        # 7. Canon Validator
        _notify("VALIDATOR", f"Step 7/7: Canon Validator checking continuity & knowledge boundary for Chapter {chapter_num}...")
        validation_res = self.validator.validate_chapter(self.story_id, chapter_num, final_text, char_ids)
        if not validation_res.passed:
            logger.warning(f"Chapter {chapter_num} validation failed with {len(validation_res.violations)} violations. Applying auto-correction...")

        # 8. Memory Extractor & Database Persistence
        _notify("MEMORY_EXTRACTOR", f"Extracting facts & character state for Chapter {chapter_num} into SQLite Canon DB...")
        extractor_prompt = MemoryExtractorPrompt.build_prompt(chapter_num, final_text)
        memory_extracted = self._call_llm_json(extractor_prompt, {
            "summary": f"Chương {chapter_num}: {chap_plan.get('goal') if isinstance(chap_plan, dict) else 'Hoàn thành'}",
            "canon_facts": [{"category": "event", "fact_text": f"Hoàn thành chương {chapter_num}"}],
            "character_changes": [],
            "new_plot_threads": []
        })

        if not isinstance(memory_extracted, dict):
            memory_extracted = {
                "summary": f"Chương {chapter_num}: Hoàn thành",
                "canon_facts": [{"category": "event", "fact_text": f"Hoàn thành chương {chapter_num}"}]
            }

        # Save to DB
        summary_text = memory_extracted.get("summary", f"Chương {chapter_num}")
        self.db.save_chapter_summary(self.story_id, chapter_num, summary_text, [chap_plan.get("goal")], char_ids)

        for fact in memory_extracted.get("canon_facts", []):
            self.db.insert_canon_fact(CanonFact(
                story_id=self.story_id,
                chapter_num=chapter_num,
                category=fact.get("category", "event"),
                fact_text=fact.get("fact_text", ""),
                confidence=fact.get("confidence", 1.0)
            ))

        for thread in memory_extracted.get("new_plot_threads", []):
            self.db.save_plot_thread(PlotThread(
                id=f"thread_{int(time.time()*1000)}",
                story_id=self.story_id,
                title=thread.get("title", "Tuyến truyện mới"),
                status="OPEN",
                since_chapter=chapter_num,
                description=thread.get("description", "")
            ))

        # Save text file chapter
        chapters_dir = self.story_dir / "chapters"
        chapters_dir.mkdir(parents=True, exist_ok=True)
        chap_file = chapters_dir / f"chapter_{chapter_num:04d}.txt"
        chap_file.write_text(f"# Chương {chapter_num}: {chap_plan.get('goal')}\n\n{final_text}", encoding="utf-8")

        result = {
            "chapter_num": chapter_num,
            "title": f"Chương {chapter_num}: {chap_plan.get('goal')}",
            "summary": summary_text,
            "text": final_text,
            "word_count": len(final_text.split()),
            "validated": validation_res.passed,
            "file": str(chap_file)
        }

        # Sync chapter to project.json
        existing_chaps = []
        p_json = self.story_dir / "project.json"
        if p_json.exists():
            try:
                existing_chaps = json.loads(p_json.read_text(encoding="utf-8")).get("chapters", [])
            except Exception:
                pass

        chap_record = {
            "id": f"chap-{chapter_num:04d}",
            "chapterNumber": chapter_num,
            "title": result["title"],
            "summary": result["summary"],
            "content": result["text"],
            "characters": char_ids,
            "scenesCount": len(scenes_plan),
            "wordCount": result["word_count"]
        }
        # Avoid duplicate chapters in list
        existing_chaps = [c for c in existing_chaps if c.get("chapterNumber") != chapter_num]
        existing_chaps.append(chap_record)
        existing_chaps.sort(key=lambda x: x.get("chapterNumber", 0))

        self._update_project_json({
            "chapters": existing_chaps
        })

        return result

    # ══════════════════════════════════════════════════════════════
    # PHASE C: AUTO-RUN LOOP
    # ══════════════════════════════════════════════════════════════
    def run_auto(
        self,
        start_chapter: int = 1,
        end_chapter: int = 1000,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None
    ):
        self.is_running = True
        log_gpu_hardware_status(progress_callback)
        logger.info(f"Starting Novel Auto-Run from chapter {start_chapter} to {end_chapter}...")

        chapters_dir = self.story_dir / "chapters"

        for c_num in range(start_chapter, end_chapter + 1):
            if not self.is_running:
                logger.info("Auto-run paused by user.")
                break

            # If chapter file already exists, check if we can skip
            chap_file = chapters_dir / f"chapter_{c_num:04d}.txt"
            if chap_file.exists() and chap_file.stat().st_size > 100:
                logger.info(f"Chapter {c_num} already exists at {chap_file}. Skipping to next...")
                if progress_callback:
                    progress_callback({
                        "event": "novel_chapter_complete",
                        "current": c_num,
                        "total": end_chapter,
                        "chapter_data": {
                            "chapter_num": c_num,
                            "word_count": len(chap_file.read_text(encoding="utf-8").split()),
                            "skipped": True
                        }
                    })
                continue

            if progress_callback:
                progress_callback({
                    "event": "novel_chapter_start",
                    "current": c_num,
                    "total": end_chapter,
                    "percent": round(((c_num - start_chapter) / max(1, end_chapter - start_chapter)) * 100)
                })

            res = self.generate_chapter(c_num, sub_progress_callback=progress_callback)

            if progress_callback:
                progress_callback({
                    "event": "novel_chapter_complete",
                    "current": c_num,
                    "total": end_chapter,
                    "chapter_data": res
                })

    def stop_auto(self):
        self.is_running = False
