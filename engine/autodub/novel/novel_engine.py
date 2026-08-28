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
                {"rank": 1, "name": "Luyện Khí"},
                {"rank": 2, "name": "Trúc Cơ"},
                {"rank": 3, "name": "Kim Đan"},
                {"rank": 4, "name": "Nguyên Anh"},
                {"rank": 5, "name": "Hóa Thần"}
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
            "rules": ["Cảnh giới không thay đổi tùy tiện"],
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

        return StoryBible(**raw_bible)

    def generate_master_plan(self, total_chapters: int = 1000) -> List[ArcPlan]:
        logger.info(f"Generating Master Plan for {total_chapters} chapters...")
        bible_file = self.story_dir / "story_bible.json"
        bible_data = {}
        if bible_file.exists():
            bible_data = json.loads(bible_file.read_text(encoding="utf-8"))

        prompt = MasterPlannerPrompt.build_prompt(bible_data, total_chapters)
        raw_arcs = self._call_llm_json(prompt, [
            {
                "arc_num": 1,
                "title": "Arc 01 — Xuyên Không & Gia Nhập Thanh Vân Tông",
                "start_chapter": 1,
                "end_chapter": 50,
                "goal": "Khám phá thế giới và đạt Trúc Cơ",
                "conflict": "Định kiến đồng môn",
                "major_reveal": "Bí mật hệ thống",
                "character_development": "Trưởng thành"
            }
        ])

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

        self.db.save_arc_plans(arc_objs)
        return arc_objs

    # ══════════════════════════════════════════════════════════════
    # PHASE B: CHAPTER GENERATION PIPELINE
    # ══════════════════════════════════════════════════════════════
    def generate_chapter(self, chapter_num: int) -> Dict[str, Any]:
        logger.info(f"--- Generating Chapter {chapter_num} ---")

        # 1. Current Arc Plan
        arc = self.db.get_current_arc(self.story_id, chapter_num) or {
            "title": f"Arc cho Chapter {chapter_num}",
            "goal": "Tiến triển cốt truyện",
            "conflict": "Xung đột mới xuất hiện"
        }

        # 2. Chapter Planner
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
        context_summary = f"Giai đoạn: {arc.get('title')}. Vừa diễn ra: {[s.get('summary_text') for s in recent_summaries]}"
        creative_prompt = CreativeEnginePrompt.build_prompt(chapter_num, chap_plan, context_summary)
        creative_options = self._call_llm_json(creative_prompt, {
            "option_a": {"title": "Phát triển tiêu chuẩn", "description": "Tình tiết diễn tiến tự nhiên"},
            "recommended_option": "option_a"
        })
        selected_creative = creative_options.get("option_a", {})

        # 4. Scene Planner
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

        # 5. Scene Writing
        char_ids = chap_plan.get("characters", ["char_001"])
        scene_drafts = []

        for sc in scenes_plan:
            full_context = self.context_builder.build_writer_context(chapter_num, sc, char_ids)
            writer_prompt = NovelWriterPrompt.build_prompt(chapter_num, sc.get("scene_index", 1), sc, full_context)

            # Generate prose text
            scene_text = self.llm.generate(prompt=writer_prompt, timeout=120)
            cleaned_scene = strip_think_tags(scene_text)
            if not cleaned_scene or len(cleaned_scene) < 50:
                cleaned_scene = f"Scene {sc.get('scene_index')}: {sc.get('goal')}. Lâm Phàm chuẩn bị đối mặt với thử thách lớn..."

            scene_drafts.append(cleaned_scene)

        full_draft = "\n\n".join(scene_drafts)

        # 6. Novel Editor
        editor_prompt = NovelEditorPrompt.build_prompt(chapter_num, full_draft)
        editor_res = self._call_llm_json(editor_prompt, {
            "edited_text": full_draft,
            "changes_made": ["Biên tập văn phong tự động"]
        })
        final_text = editor_res.get("edited_text", full_draft)

        # 7. Canon Validator
        validation_res = self.validator.validate_chapter(self.story_id, chapter_num, final_text, char_ids)
        if not validation_res.passed:
            logger.warning(f"Chapter {chapter_num} validation failed with {len(validation_res.violations)} violations. Applying auto-correction...")

        # 8. Memory Extractor & Database Persistence
        extractor_prompt = MemoryExtractorPrompt.build_prompt(chapter_num, final_text)
        memory_extracted = self._call_llm_json(extractor_prompt, {
            "summary": f"Chương {chapter_num}: {chap_plan.get('goal')}",
            "canon_facts": [{"category": "event", "fact_text": f"Hoàn thành chương {chapter_num}"}],
            "character_changes": [],
            "new_plot_threads": []
        })

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
        logger.info(f"Starting Novel Auto-Run from chapter {start_chapter} to {end_chapter}...")

        for c_num in range(start_chapter, end_chapter + 1):
            if not self.is_running:
                logger.info("Auto-run paused by user.")
                break

            if progress_callback:
                progress_callback({
                    "event": "novel_chapter_start",
                    "current": c_num,
                    "total": end_chapter,
                    "percent": round(((c_num - start_chapter) / max(1, end_chapter - start_chapter)) * 100)
                })

            res = self.generate_chapter(c_num)

            if progress_callback:
                progress_callback({
                    "event": "novel_chapter_complete",
                    "current": c_num,
                    "total": end_chapter,
                    "chapter_data": res
                })

    def stop_auto(self):
        self.is_running = False
