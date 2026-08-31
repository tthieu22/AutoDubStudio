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


def _safe_print(msg: str):
    """Print to stdout safely, handling Windows codepage encoding issues."""
    import sys
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((msg + '\n').encode('utf-8', errors='replace'))
        sys.stdout.buffer.flush()


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

        # Step 1A: Primary World Generation Prompt (Premise & World)
        msg_1a = f"[INFO] === PROMPT 1A/5: Sáng tạo Bối Cảnh Thế Giới & Premise ==="
        logger.info(msg_1a)
        _safe_print(msg_1a)
        world_prompt = StoryDirectorPrompt.build_world_prompt(idea)
        w_res, metadata = self._call_llm_json_strict(world_prompt, stage="WORLD_GENERATION", idea=idea, max_retries=3)
        if not isinstance(w_res, dict):
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Story Bible payload must be a JSON object")

        raw_bible = {
            "premise": w_res.get("premise", f"Hành trình của {idea.title}"),
            "world": w_res.get("world", {})
        }

        # Step 1B: Progression System — FAIL-CLOSED (No Fallback)
        msg_1b = f"[INFO] === PROMPT 1B/5: Sáng tạo Hệ Thống Cảnh Giới & Sức Mạnh ==="
        logger.info(msg_1b)
        _safe_print(msg_1b)
        prog_prompt = StoryDirectorPrompt.build_progression_prompt(idea, raw_bible)
        prog_res, _ = self._call_llm_json_strict(prog_prompt, stage="PROGRESSION_GENERATION", max_retries=3)
        if isinstance(prog_res, dict):
            raw_bible["progression_system"] = prog_res.get("progression_system", prog_res)
            raw_bible["cultivation_system"] = prog_res.get("cultivation_system", prog_res.get("ranks", []))
        elif isinstance(prog_res, list):
            raw_bible["progression_system"] = {"type": "level", "ranks": prog_res}
            raw_bible["cultivation_system"] = prog_res
        else:
            raise GenerationError("PROGRESSION_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  "LLM trả về dữ liệu Hệ Thống Cảnh Giới không hợp lệ (không phải dict hoặc list)")

        # Step 1C: Full Cast Generation — FAIL-CLOSED (No Fallback)
        msg_1c = f"[INFO] === PROMPT 1C/5: Sáng tạo Dàn Nhân Vật Nam & Nữ ==="
        logger.info(msg_1c)
        _safe_print(msg_1c)
        cast_prompt = StoryDirectorPrompt.build_cast_prompt(idea, raw_bible)
        cast_res, _ = self._call_llm_json_strict(cast_prompt, stage="CAST_GENERATION", idea=idea, max_retries=3)
        if isinstance(cast_res, list) and len(cast_res) > 0:
            raw_bible["characters"] = cast_res
        elif isinstance(cast_res, dict) and "characters" in cast_res and len(cast_res["characters"]) > 0:
            raw_bible["characters"] = cast_res["characters"]
        else:
            raise GenerationError("CAST_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  f"LLM không tạo được danh sách nhân vật hợp lệ cho '{p_name}'. Hãy thử lại.")

        # Step 1D: World Rules — FAIL-CLOSED (No Fallback)
        msg_1d = f"[INFO] === PROMPT 1D/5: Sáng tạo Quy Tắc Thế Giới Quan ==="
        logger.info(msg_1d)
        _safe_print(msg_1d)
        rules_prompt = StoryDirectorPrompt.build_rules_prompt(idea, raw_bible)
        rules_res, _ = self._call_llm_json_strict(rules_prompt, stage="RULES_GENERATION", max_retries=3)
        if isinstance(rules_res, list) and len(rules_res) > 0:
            raw_bible["rules"] = rules_res
        elif isinstance(rules_res, dict) and "rules" in rules_res and len(rules_res["rules"]) > 0:
            raw_bible["rules"] = rules_res["rules"]
        else:
            raise GenerationError("RULES_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  "LLM không tạo được danh sách Quy Tắc Thế Giới hợp lệ. Hãy thử lại.")

        # Step 1E: Terminology — FAIL-CLOSED (No Fallback)
        msg_1e = f"[INFO] === PROMPT 1E/5: Sáng tạo Từ Điển Thuật Ngữ ==="
        logger.info(msg_1e)
        _safe_print(msg_1e)
        term_prompt = StoryDirectorPrompt.build_terminology_prompt(idea, raw_bible)
        term_res, _ = self._call_llm_json_strict(term_prompt, stage="TERMINOLOGY_GENERATION", max_retries=3)
        if isinstance(term_res, dict):
            if "terminology" in term_res and isinstance(term_res["terminology"], dict) and len(term_res["terminology"]) > 0:
                raw_bible["terminology"] = term_res["terminology"]
            elif len(term_res) > 0 and all(isinstance(v, str) for v in term_res.values()):
                raw_bible["terminology"] = term_res
            else:
                raise GenerationError("TERMINOLOGY_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                      "LLM không tạo được Từ Điển Thuật Ngữ hợp lệ (dict rỗng). Hãy thử lại.")
        else:
            raise GenerationError("TERMINOLOGY_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  "LLM trả về dữ liệu Thuật Ngữ không hợp lệ (không phải dict). Hãy thử lại.")

        raw_bible["generation_metadata"] = metadata
        raw_bible["enable_tiktok_slang"] = getattr(idea, "enable_tiktok_slang", False)
        done_msg = f"[INFO] === THÀNH CÔNG: Hoàn thành 5/5 Prompts Khởi Tạo Thế Giới Quan ==="
        logger.info(done_msg)
        _safe_print(done_msg)

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
        
        prog_sys = raw_bible.get("progression_system", {})
        cult_sys = raw_bible.get("cultivation_system", [])
        ranks_list = cult_sys if (isinstance(cult_sys, list) and len(cult_sys) > 0) else (prog_sys.get("ranks", []) if isinstance(prog_sys, dict) else [])
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

        # Calculate expected arc count (~20 chapters per arc)
        chaps_per_arc = 20
        expected_arcs = max(5, min(50, (total_chapters + chaps_per_arc - 1) // chaps_per_arc))
        
        # Batch size: max 10 arcs per LLM call to prevent output truncation on small models
        BATCH_SIZE = 10
        all_raw_arcs = []
        batch_num = 0
        arcs_remaining = expected_arcs

        logger.info(f"[MASTER_PLAN_GENERATION] Input Premise: '{premise[:40]}' | Total Chapters: {total_chapters} | Expected Arcs: {expected_arcs} | Batch Size: {BATCH_SIZE}")

        while arcs_remaining > 0:
            batch_num += 1
            batch_count = min(BATCH_SIZE, arcs_remaining)
            arc_start_idx = len(all_raw_arcs) + 1
            arc_end_idx = arc_start_idx + batch_count - 1
            
            # Calculate chapter ranges for this batch
            batch_start_chapter = (arc_start_idx - 1) * chaps_per_arc + 1
            batch_end_chapter = min(arc_end_idx * chaps_per_arc, total_chapters)

            batch_msg = f"[INFO] === MASTER PLAN BATCH {batch_num}: Tạo Arc {arc_start_idx}-{arc_end_idx} (Chương {batch_start_chapter}-{batch_end_chapter}) ==="
            logger.info(batch_msg)
            _safe_print(batch_msg)

            prompt = MasterPlannerPrompt.build_batch_prompt(
                bible_data, total_chapters, 
                batch_start=arc_start_idx, batch_end=arc_end_idx,
                chaps_per_arc=chaps_per_arc,
                previous_arcs=all_raw_arcs
            )
            raw_arcs, metadata = self._call_llm_json_strict(prompt, stage="MASTER_PLAN", idea=None, max_retries=3)

            if isinstance(raw_arcs, dict) and "arcs" in raw_arcs:
                raw_arcs = raw_arcs["arcs"]

            if not isinstance(raw_arcs, list) or len(raw_arcs) == 0:
                raise GenerationError("MASTER_PLAN", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, 
                                      f"LLM không tạo được Arc {arc_start_idx}-{arc_end_idx}. Batch {batch_num} trả về dữ liệu rỗng.", retryable=True)

            all_raw_arcs.extend(raw_arcs)
            arcs_remaining -= len(raw_arcs)
            
            batch_done_msg = f"[INFO] Batch {batch_num} hoàn thành: {len(raw_arcs)} Arcs | Tổng hiện tại: {len(all_raw_arcs)}/{expected_arcs}"
            logger.info(batch_done_msg)
            _safe_print(batch_done_msg)

        # Validate minimum arc count
        if len(all_raw_arcs) < max(5, expected_arcs // 2):
            raise GenerationError("MASTER_PLAN", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  f"Số lượng Arc quá ít ({len(all_raw_arcs)}/{expected_arcs}). Cần ít nhất {max(5, expected_arcs // 2)} Arcs cho {total_chapters} chương.", retryable=True)

        arc_objs = []
        total_arcs_count = len(all_raw_arcs)
        for idx, a in enumerate(all_raw_arcs, start=1):
            if isinstance(a, str):
                a = {"title": a}
            elif not isinstance(a, dict):
                a = {}

            # Strictly enforce continuous chapter math (no LLM hallucinated chapter gaps/overlaps)
            calc_start = (idx - 1) * chaps_per_arc + 1
            calc_end = total_chapters if idx == total_arcs_count else idx * chaps_per_arc

            raw_title = str(a.get("title", f"Arc {idx:02d}")).strip()
            if not raw_title:
                raw_title = f"Arc {idx:02d} — Kịch Bản Phân Đoạn {idx}"

            arc_objs.append(ArcPlan(
                id=f"arc_{idx:02d}",
                story_id=self.story_id,
                arc_num=idx,
                title=raw_title,
                start_chapter=calc_start,
                end_chapter=calc_end,
                goal=a.get("goal", f"Mục tiêu cốt truyện trong Arc {idx}"),
                conflict=a.get("conflict", f"Xung đột kịch bản trong Arc {idx}"),
                major_reveal=a.get("major_reveal", f"Manh mối quan trọng trong Arc {idx}"),
                character_development=a.get("character_development", f"Tiến trình phát triển nhân vật trong Arc {idx}")
            ))

        success_msg = f"[INFO] === MASTER PLAN HOÀN THÀNH: {len(arc_objs)} Arcs cho {total_chapters} chương ==="
        logger.info(success_msg)
        _safe_print(success_msg)

        self.db.save_arc_plans(arc_objs)

        # Sync formatted arc_plans to project.json for UI ArcPlanner tab
        arc_dicts = [a.model_dump() for a in arc_objs]
        self._update_project_json({
            "arc_plans": arc_dicts
        })

        return arc_objs
