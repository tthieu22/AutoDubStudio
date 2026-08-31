import json
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from autodub.novel.novel_models import (
    StoryIdea, StoryBible, ArcPlan, Character, GenerationError, GenerationErrorCode
)
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.prompts.story_director import StoryDirectorPrompt
from autodub.novel.prompts.master_planner import MasterPlannerPrompt


logger = logging.getLogger(__name__)


class StoryPlanner:
    """
    Component handling Story Bible initialization (Phase A1) and Master Plan Arc Generation (Phase A2).
    """

    def __init__(
        self,
        story_id: str,
        story_dir: Path,
        db: NovelDatabase,
        llm_strict_caller: Callable[..., Tuple[Any, Dict[str, Any]]],
        project_json_updater: Callable[[Dict[str, Any]], None],
        checkpoints_dir: Path
    ):
        self.story_id = story_id
        self.story_dir = story_dir
        self.db = db
        self._call_llm_json_strict = llm_strict_caller
        self._update_project_json = project_json_updater
        self.checkpoints_dir = checkpoints_dir

    def initialize_story(self, idea: StoryIdea) -> StoryBible:
        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"

        logger.info(f"[WORLD_GENERATION] Starting Modular Initialization for '{idea.title}' (Genre: '{idea.genre}')...")

        # Step 1A: Primary World Generation Prompt
        world_prompt = StoryDirectorPrompt.build_world_prompt(idea)
        raw_bible, metadata = self._call_llm_json_strict(world_prompt, stage="WORLD_GENERATION", idea=idea, max_retries=3)
        if not isinstance(raw_bible, dict):
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Story Bible payload must be a JSON object")

        if not raw_bible.get("premise"):
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Required field 'premise' is missing or empty")

        if not raw_bible.get("world") or not isinstance(raw_bible.get("world"), dict):
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Required field 'world' is missing or invalid")

        # Step 1B: Progression System (Fetch via sub-step if missing)
        prog_sys = raw_bible.get("progression_system") or {}
        cult_sys = raw_bible.get("cultivation_system") or []
        if not prog_sys and not cult_sys:
            logger.info("[WORLD_GENERATION] 'progression_system' missing in primary payload. Invoking Sub-Step 1B...")
            prog_prompt = StoryDirectorPrompt.build_progression_prompt(idea, raw_bible.get("premise", ""))
            prog_res, _ = self._call_llm_json_strict(prog_prompt, stage="PROGRESSION_GENERATION", idea=idea, max_retries=2)
            if isinstance(prog_res, dict):
                raw_bible["progression_system"] = prog_res.get("progression_system", prog_res)
                raw_bible["cultivation_system"] = prog_res.get("cultivation_system", [])

        prog_sys = raw_bible.get("progression_system") or {}
        cult_sys = raw_bible.get("cultivation_system") or []
        if not prog_sys and not cult_sys:
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Required field 'progression_system' or 'cultivation_system' is missing")

        # Step 1C: Full Cast Generation (Fetch via sub-step if missing or < 2 characters)
        chars = raw_bible.get("characters", [])
        if not isinstance(chars, list) or len(chars) < 2:
            logger.info("[WORLD_GENERATION] 'characters' missing or incomplete in primary payload. Invoking Sub-Step 1C...")
            cast_prompt = StoryDirectorPrompt.build_cast_prompt(idea, raw_bible)
            cast_res, _ = self._call_llm_json_strict(cast_prompt, stage="CAST_GENERATION", idea=idea, max_retries=2)
            if isinstance(cast_res, list) and len(cast_res) > 0:
                raw_bible["characters"] = cast_res
            elif isinstance(cast_res, dict) and "characters" in cast_res:
                raw_bible["characters"] = cast_res["characters"]

        if not raw_bible.get("characters") or not isinstance(raw_bible.get("characters"), list) or len(raw_bible.get("characters")) == 0:
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Required field 'characters' must contain at least 1 character")

        # Step 1D: World Rules (Fetch via sub-step if missing)
        if not raw_bible.get("rules"):
            rules_prompt = StoryDirectorPrompt.build_rules_prompt(idea, raw_bible)
            rules_res, _ = self._call_llm_json_strict(rules_prompt, stage="RULES_GENERATION", idea=idea, max_retries=2)
            if isinstance(rules_res, list):
                raw_bible["rules"] = rules_res
            elif isinstance(rules_res, dict) and "rules" in rules_res:
                raw_bible["rules"] = rules_res["rules"]

        # Step 1E: Terminology (Fetch via sub-step if missing)
        if not raw_bible.get("terminology"):
            term_prompt = StoryDirectorPrompt.build_terminology_prompt(idea, raw_bible)
            term_res, _ = self._call_llm_json_strict(term_prompt, stage="TERMINOLOGY_GENERATION", idea=idea, max_retries=2)
            if isinstance(term_res, dict):
                raw_bible["terminology"] = term_res.get("terminology", term_res)

        raw_bible["generation_metadata"] = metadata
        raw_bible["enable_tiktok_slang"] = getattr(idea, "enable_tiktok_slang", False)
        logger.info(f"[WORLD_GENERATION] Initialization SUCCESS | Source: {metadata['source']} | Characters: {len(raw_bible.get('characters', []))}")

        # Save to DB & File ONLY AFTER PASSING VALIDATION
        self.db.create_story(self.story_id, idea)

        # Clear any stale scene checkpoints from previous runs/projects
        if self.checkpoints_dir.exists():
            for chk_f in self.checkpoints_dir.glob("*.json"):
                try:
                    chk_f.unlink()
                except Exception:
                    pass

        bible_file = self.story_dir / "story_bible.json"
        with open(bible_file, "w", encoding="utf-8") as f:
            json.dump(raw_bible, f, indent=2, ensure_ascii=False)

        for c in raw_bible.get("characters", []):
            char_obj = Character(
                id=c.get("id", "char_001"),
                name=c.get("name", p_name),
                personality=c.get("personality", []),
                goal=c.get("goal", ""),
                realm=c.get("realm", "Khởi Đầu"),
                location=c.get("location", "Khởi Đầu"),
                known_information=c.get("known_information", []),
                secrets=c.get("secrets", [])
            )
            self.db.save_character(char_obj, self.story_id)

        # Format characters for UI CharacterBible tab
        formatted_chars = []
        for idx, c in enumerate(raw_bible.get("characters", []), start=1):
            c_gender = str(c.get("gender", "")).strip()
            if not c_gender:
                c_gender = "Nữ" if idx in (2, 4) else "Nam"

            c_voice = "vi_female_hero" if c_gender.lower() in ("nữ", "female") else "vi_male_hero"

            formatted_chars.append({
                "id": c.get("id", f"char_{idx:03d}"),
                "name": c.get("name", p_name),
                "alias": c.get("realm", "Khởi Đầu"),
                "gender": c_gender,
                "age": str(c.get("age", "20")),
                "personality": ", ".join(c.get("personality", [])) if isinstance(c.get("personality"), list) else str(c.get("personality", "Quyết đoán")),
                "appearance": f"Mục tiêu: {c.get('goal', 'Khám phá thế giới')}",
                "clothing": f"Cảnh giới: {c.get('realm', 'Khởi Đầu')} • Vị trí: {c.get('location', 'Vùng Khởi Đầu')}",
                "voice": c_voice,
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
                    "description": "Thế lực chính trong đại lục",
                    "locked": True
                })
        
        ranks_list = cult_sys if cult_sys else prog_sys.get("ranks", [])
        for cs in ranks_list:
            if isinstance(cs, dict):
                formatted_lore.append({
                    "id": f"w-cs-{len(formatted_lore)}",
                    "category": "Rule",
                    "name": f"Cấp độ #{cs.get('rank', 1)}: {cs.get('name')}",
                    "description": cs.get("description", "Cấp độ sức mạnh / Tiến trình"),
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

    def generate_master_plan(self, total_chapters: int = 1000) -> List[ArcPlan]:
        bible_file = self.story_dir / "story_bible.json"
        if not bible_file.exists():
            raise GenerationError("MASTER_PLAN", GenerationErrorCode.DEPENDENCY_NOT_READY.value, "Valid Story Bible is required before generating Master Plan", retryable=False)

        bible_data = {}
        try:
            bible_data = json.loads(bible_file.read_text(encoding="utf-8"))
        except Exception:
            raise GenerationError("MASTER_PLAN", GenerationErrorCode.DEPENDENCY_NOT_READY.value, "Story Bible file is corrupt or unreadable", retryable=False)

        if not bible_data.get("premise"):
            raise GenerationError("MASTER_PLAN", GenerationErrorCode.DEPENDENCY_NOT_READY.value, "Story Bible premise is empty or invalid", retryable=False)

        premise = bible_data.get("premise", "Cốt truyện chính")
        logger.info(f"[MASTER_PLAN_GENERATION] Input Premise: '{premise[:40]}' | Total Chapters: {total_chapters} | LLM Call: START")

        prompt = MasterPlannerPrompt.build_prompt(bible_data, total_chapters)
        raw_arcs, metadata = self._call_llm_json_strict(prompt, stage="MASTER_PLAN", idea=None, max_retries=3)

        if isinstance(raw_arcs, dict) and "arcs" in raw_arcs:
            raw_arcs = raw_arcs["arcs"]

        if not isinstance(raw_arcs, list) or len(raw_arcs) == 0:
            raise GenerationError("MASTER_PLAN", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Field 'arcs' must contain at least one valid Arc plan", retryable=True)

        arc_objs = []
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

        logger.info(f"[MASTER_PLAN_GENERATION] LLM Call: SUCCESS | Source: {metadata['source']} | Fallback Used: {metadata['fallback_used']} | Arc Count: {len(arc_objs)}")

        self.db.save_arc_plans(arc_objs)

        # Sync formatted arc_plans to project.json for UI ArcPlanner tab
        arc_dicts = [a.model_dump() for a in arc_objs]
        self._update_project_json({
            "arc_plans": arc_dicts
        })

        return arc_objs
