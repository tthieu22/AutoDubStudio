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
from autodub.novel.prompts.master_blueprint import MasterBlueprintPrompt
from autodub.novel.prompts.arc_roadmap import ArcRoadmapPrompt


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
        raw_chars = cast_res if isinstance(cast_res, list) else (cast_res.get("characters", []) if isinstance(cast_res, dict) else [])
        if not raw_chars:
            raise GenerationError("CAST_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  f"LLM không tạo được danh sách nhân vật hợp lệ cho '{p_name}'. Hãy thử lại.")

        unique_chars = []
        seen_names = set()
        for idx, c in enumerate(raw_chars, start=1):
            if not isinstance(c, dict):
                continue
            name = str(c.get("name") or "").strip()
            if not name or name in seen_names:
                logger.warning(f"[STORY_PLANNER] Bỏ qua nhân vật rỗng hoặc trùng tên: '{name}'")
                continue
            seen_names.add(name)
            c["id"] = f"char_{idx:03d}"
            unique_chars.append(c)

        if not unique_chars:
            raise GenerationError("CAST_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  f"Danh sách nhân vật tạo ra bị trùng lặp toàn bộ. Hãy thử lại.")

        raw_bible["characters"] = unique_chars

        # Step 1D: World Rules — FAIL-CLOSED (No Fallback)
        msg_1d = f"[INFO] === PROMPT 1D/5: Sáng tạo Quy Tắc Thế Giới Quan ==="
        logger.info(msg_1d)
        _safe_print(msg_1d)
        rules_prompt = StoryDirectorPrompt.build_rules_prompt(idea, raw_bible)
        rules_res, _ = self._call_llm_json_strict(rules_prompt, stage="RULES_GENERATION", max_retries=3)
        raw_rules = rules_res if isinstance(rules_res, list) else (rules_res.get("rules", []) if isinstance(rules_res, dict) else [])
        unique_rules = []
        seen_r = set()
        for r in raw_rules:
            clean_r = str(r).strip()
            if clean_r and clean_r not in seen_r:
                seen_r.add(clean_r)
                unique_rules.append(clean_r)

        if not unique_rules:
            raise GenerationError("RULES_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  "LLM không tạo được danh sách Quy Tắc Thế Giới hợp lệ. Hãy thử lại.")

        raw_bible["rules"] = unique_rules

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

        # Save Story Bible JSON to disk
        bible_path = self.story_dir / "story_bible.json"
        try:
            bible_path.write_text(json.dumps(raw_bible, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"Saved Story Bible to {bible_path}")
        except Exception as e:
            logger.error(f"Failed to write story_bible.json: {e}")

        # Sync characters with SQLite DB
        formatted_chars = []
        for c in raw_bible.get("characters", []):
            if isinstance(c, dict):
                c_id = c.get("id", f"char_{len(formatted_chars)+1:03d}")
                c_name = c.get("name", p_name)
                c_realm = c.get("realm", "Khởi Đầu")
                c_loc = c.get("location", "Vùng Khởi Đầu")
                c_gender = c.get("gender", "Nam")
                self.db.save_character(Character(
                    id=c_id,
                    name=c_name,
                    personality=c.get("personality", []),
                    goal=c.get("goal", ""),
                    realm=c_realm,
                    location=c_loc,
                    known_information=c.get("known_information", []),
                    secrets=c.get("secrets", [])
                ), self.story_id)
                formatted_chars.append({
                    "id": c_id,
                    "name": c_name,
                    "alias": c.get("realm", "Khởi Đầu"),
                    "gender": c_gender,
                    "age": str(c.get("age", "20")),
                    "personality": ", ".join(c.get("personality", [])) if isinstance(c.get("personality"), list) else str(c.get("personality", "Quyết đoán")),
                    "appearance": f"Mục tiêu: {c.get('goal', 'Khám phá thế giới')}",
                    "clothing": f"Cảnh giới: {c_realm} • Vị trí: {c_loc}",
                    "voice": "vi_female_hero" if c_gender.lower() in ("nữ", "female") else "vi_male_hero",
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

        # Format rules for UI StoryMemory tab with deduplication
        formatted_memory = []
        seen_mem = set()
        for r in raw_bible.get("rules", []):
            clean_r = str(r).strip()
            if not clean_r or clean_r in seen_mem:
                continue
            seen_mem.add(clean_r)
            formatted_memory.append({
                "id": f"mem-{len(formatted_memory)}",
                "category": "World",
                "content": clean_r,
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

        # Step 2B: Generate Master Story Blueprint Skeleton (Prompt 1F) AFTER Arcs are created
        try:
            self.generate_master_blueprint(arc_dicts)
        except Exception as e:
            logger.warning(f"Failed generating Master Story Blueprint Skeleton: {e}")

        # Auto-generate Arc 1 Chapter Roadmap so it's ready immediately
        try:
            self.generate_arc_roadmap(1)
        except Exception as e:
            logger.warning(f"Failed auto-generating Arc 1 Roadmap: {e}")

        return arc_objs

    def generate_master_blueprint(self, arc_dicts: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Generates Master Story Blueprint Skeleton (Prompt 1F) AFTER Master Plan Arcs are created."""
        story_bible = {}
        bible_file = self.story_dir / "story_bible.json"
        if bible_file.exists():
            try:
                with open(bible_file, "r", encoding="utf-8") as f:
                    story_bible = json.load(f)
            except Exception:
                story_bible = {}


        total_chapters = 1000
        if isinstance(story_bible, dict) and story_bible.get("total_chapters"):
            total_chapters = story_bible["total_chapters"]
        else:
            try:
                ledger = self.db.get_global_progress_ledger(self.story_id)
                if ledger and getattr(ledger, "total_chapters", 0) > 0:
                    total_chapters = ledger.total_chapters
            except Exception:
                pass



        if not arc_dicts:
            arc_objs = self.db.get_arc_plans(self.story_id)
            arc_dicts = [a.model_dump() if hasattr(a, "model_dump") else a for a in arc_objs]

        msg_1f = f"[INFO] === PROMPT 1F: Sáng tạo Sườn Kịch Bản Tổng Thể (Master Blueprint Skeleton) Dựa Trên Danh Sách {len(arc_dicts)} Arcs ==="
        logger.info(msg_1f)
        _safe_print(msg_1f)

        bp_prompt = MasterBlueprintPrompt.build_prompt(story_bible, total_chapters, arc_dicts)
        bp_res, _ = self._call_llm_json_strict(bp_prompt, stage="MASTER_BLUEPRINT_GENERATION", max_retries=3)

        if isinstance(bp_res, dict) and bp_res.get("overall_arc_summary"):
            story_bible["master_blueprint"] = bp_res
            # Update story_bible.json file
            bible_file = self.story_dir / "story_bible.json"
            with open(bible_file, "w", encoding="utf-8") as f:
                json.dump(story_bible, f, indent=2, ensure_ascii=False)

            # Sync to project.json
            self._update_project_json({
                "story_bible": story_bible
            })
            return bp_res
        else:
            raise GenerationError("MASTER_BLUEPRINT_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  "LLM không tạo được Sườn Kịch Bản Tổng Thể hợp lệ (thiếu 'overall_arc_summary'). Hãy thử lại.")




    def generate_arc_roadmap(self, arc_num: int) -> List[Dict[str, Any]]:
        """Generates a 20-chapter continuous causal roadmap for a specific Arc."""
        arcs = self.db.get_arc_plans(self.story_id)
        current_arc = None
        for a in arcs:
            if getattr(a, "arc_num", 0) == arc_num or (isinstance(a, dict) and a.get("arc_num") == arc_num):
                current_arc = a if isinstance(a, dict) else a.model_dump()
                break

        if not current_arc:
            current_arc = {
                "arc_num": arc_num,
                "title": f"Arc {arc_num:02d}",
                "start_chapter": (arc_num - 1) * 20 + 1,
                "end_chapter": arc_num * 20,
                "goal": f"Tiến triển kịch bản Arc {arc_num}",
                "conflict": "Xung đột mới",
                "major_reveal": "Bí mật mới"
            }

        bible_file = self.story_dir / "story_bible.json"
        bible_data = {}
        if bible_file.exists():
            try:
                bible_data = json.loads(bible_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        master_bp = bible_data.get("master_blueprint", {})

        msg = f"[INFO] === TẠO DÀN Ý KỊCH BẢN 20 CHƯƠNG CHO ARC {arc_num} ({current_arc.get('title')}) ==="
        logger.info(msg)
        _safe_print(msg)

        prompt = ArcRoadmapPrompt.build_prompt(current_arc, bible_data, master_bp)
        raw_roadmap, _ = self._call_llm_json_strict(prompt, stage=f"ARC_{arc_num}_ROADMAP", max_retries=3)

        if isinstance(raw_roadmap, dict) and "roadmap" in raw_roadmap:
            raw_roadmap = raw_roadmap["roadmap"]

        if not isinstance(raw_roadmap, list) or len(raw_roadmap) == 0:
            raise GenerationError(f"ARC_{arc_num}_ROADMAP", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  f"LLM không tạo được Dàn Ý 20 Chương hợp lệ cho Arc {arc_num}. Hãy thử lại.")


        # Store in project.json under arc_roadmaps
        p_json = self.story_dir / "project.json"
        p_data = {}
        if p_json.exists():
            try:
                p_data = json.loads(p_json.read_text(encoding="utf-8"))
            except Exception:
                pass

        existing_roadmaps = p_data.get("arc_roadmaps", {})
        existing_roadmaps[f"arc_{arc_num:02d}"] = raw_roadmap
        p_data["arc_roadmaps"] = existing_roadmaps

        try:
            p_json.write_text(json.dumps(p_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed writing arc_roadmaps to project.json: {e}")

        success_msg = f"[SUCCESS] Đã tạo xong Dàn Ý 20 Chương liên hoàn cho Arc {arc_num} ({len(raw_roadmap)} chương)!"
        logger.info(success_msg)
        _safe_print(success_msg)

        return raw_roadmap


