import json
import re
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


def extract_list_from_json(data: Any, expected_keys: Optional[List[str]] = None) -> List[Any]:
    """
    Intelligently extracts a list of items from any parsed LLM JSON response.
    Handles:
    - Direct list: [{...}, ...]
    - Dict with list under known container keys
    - Dict mapping keys/IDs to item dicts: {"arc_1": {...}, "arc_2": {...}}
    - Dict of a single item object: {"arc_num": 1, "title": "..."}
    - Nested dict: {"data": {"arcs": [...]}}
    """
    if isinstance(data, list):
        return data

    if isinstance(data, dict):
        # 1. Known container keys
        for k in ["arcs", "master_plan", "plan", "data", "arcs_list", "items", "roadmap", "chapters", "characters", "rules", "result", "response"]:
            if k in data and isinstance(data[k], list) and len(data[k]) > 0:
                return data[k]

        # 2. Any key holding a non-empty list
        for v in data.values():
            if isinstance(v, list) and len(v) > 0:
                return v

        # 3. Dict of dicts (e.g. {"arc_1": {...}, "arc_2": {...}})
        dict_vals = list(data.values())
        if dict_vals and all(isinstance(v, dict) for v in dict_vals):
            if expected_keys:
                if any(any(k in v for k in expected_keys) for v in dict_vals):
                    return dict_vals
            else:
                return dict_vals

        # 4. Dict of a single item object (e.g. {"title": "Arc 01", ...})
        if expected_keys and any(k in data for k in expected_keys):
            return [data]

        # 5. Recursive check inside any nested dict
        for v in data.values():
            if isinstance(v, dict):
                res = extract_list_from_json(v, expected_keys)
                if res:
                    return res

    return []


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

    def initialize_story(self, idea: StoryIdea, resume: bool = True) -> StoryBible:
        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"

        logger.info(f"[WORLD_GENERATION] Starting Modular Initialization for '{idea.title}' (Genre: '{idea.genre}', Resume: {resume})...")

        raw_bible = {}
        bible_path = self.story_dir / "story_bible.json"
        
        # Load existing bible if resume mode is active
        if resume and bible_path.exists():
            try:
                raw_bible = json.loads(bible_path.read_text(encoding="utf-8"))
                logger.info(f"[RESUME_WORLD_INIT] Found existing story_bible.json. Resuming from uncompleted steps...")
            except Exception as e:
                logger.warning(f"Could not load existing story_bible.json for resume: {e}")
                raw_bible = {}

        if not resume or not raw_bible:
            try:
                self.db.clear_all_story_data(self.story_id)
            except Exception as e:
                logger.warning(f"Could not purge old story db data: {e}")

        def _save_intermediate_bible():
            try:
                bible_path.write_text(json.dumps(raw_bible, indent=2, ensure_ascii=False), encoding="utf-8")
                self._update_project_json({"story_bible": raw_bible})
            except Exception as e:
                logger.warning(f"Could not write intermediate story_bible.json: {e}")

        # Step 1A: Primary World Generation Prompt (Premise & World)
        if raw_bible.get("premise") and raw_bible.get("world"):
            msg_1a = f"[INFO] === PROMPT 1A/5: Bối Cảnh Thế Giới đã tồn tại (Bỏ qua) ==="
            logger.info(msg_1a)
            _safe_print(msg_1a)
            metadata = raw_bible.get("generation_metadata", {})
        # Step 1A: Primary World Generation Prompt (Premise & World)
        if raw_bible.get("premise") and raw_bible.get("world"):
            msg_1a = f"[INFO] === PROMPT 1A/5: Bối Cảnh Thế Giới đã tồn tại (Bỏ qua) ==="
            logger.info(msg_1a)
            _safe_print(msg_1a)
            metadata = raw_bible.get("generation_metadata", {})
        else:
            msg_1a = f"[INFO] === PROMPT 1A/5: Sáng tạo Bối Cảnh Thế Giới & Premise ==="
            logger.info(msg_1a)
            _safe_print(msg_1a)
            world_prompt = StoryDirectorPrompt.build_world_prompt(idea)
            w_res, metadata = self._call_llm_json_strict(world_prompt, stage="WORLD_GENERATION", idea=idea, max_retries=3)
            if not isinstance(w_res, dict):
                raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Story Bible payload must be a JSON object")

            raw_bible["premise"] = w_res.get("premise", f"Hành trình của {idea.title}")
            raw_bible["world"] = w_res.get("world", {})
            _save_intermediate_bible()

        # Step 1B: Progression System — FAIL-CLOSED
        if raw_bible.get("progression_system") and raw_bible.get("cultivation_system"):
            msg_1b = f"[INFO] === PROMPT 1B/5: Hệ Thống Cảnh Giới đã tồn tại (Bỏ qua) ==="
            logger.info(msg_1b)
            _safe_print(msg_1b)
        else:
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
            _save_intermediate_bible()

        # Step 1C: Full Cast Generation — FAIL-CLOSED
        if raw_bible.get("characters") and isinstance(raw_bible.get("characters"), list) and len(raw_bible.get("characters")) > 0:
            msg_1c = f"[INFO] === PROMPT 1C/5: Dàn Nhân Vật đã tồn tại (Bỏ qua) ==="
            logger.info(msg_1c)
            _safe_print(msg_1c)
        else:
            msg_1c = f"[INFO] === PROMPT 1C/5: Sáng tạo Dàn Nhân Vật Nam & Nữ ==="
            logger.info(msg_1c)
            _safe_print(msg_1c)
            cast_prompt = StoryDirectorPrompt.build_cast_prompt(idea, raw_bible)
            cast_res, _ = self._call_llm_json_strict(cast_prompt, stage="CAST_GENERATION", idea=idea, max_retries=3)

            raw_chars = extract_list_from_json(cast_res, expected_keys=["name", "role", "background"])
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
                # Sanitize personality string to list of strings
                p_val = c.get("personality", [])
                if isinstance(p_val, str):
                    c["personality"] = [p.strip() for p in p_val.split(",") if p.strip()]
                elif not isinstance(p_val, list):
                    c["personality"] = ["Điềm tĩnh", "Thông minh", "Quyết đoán"]
                unique_chars.append(c)

            if not unique_chars:
                raise GenerationError("CAST_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                      f"Danh sách nhân vật tạo ra bị trùng lặp toàn bộ. Hãy thử lại.")

            raw_bible["characters"] = unique_chars
            _save_intermediate_bible()

        # Step 1D: World Rules — FAIL-CLOSED
        if raw_bible.get("rules") and isinstance(raw_bible.get("rules"), list) and len(raw_bible.get("rules")) > 0:
            msg_1d = f"[INFO] === PROMPT 1D/5: Quy Tắc Thế Giới đã tồn tại (Bỏ qua) ==="
            logger.info(msg_1d)
            _safe_print(msg_1d)
        else:
            msg_1d = f"[INFO] === PROMPT 1D/5: Sáng tạo Quy Tắc Thế Giới Quan ==="
            logger.info(msg_1d)
            _safe_print(msg_1d)
            rules_prompt = StoryDirectorPrompt.build_rules_prompt(idea, raw_bible)
            rules_res, _ = self._call_llm_json_strict(rules_prompt, stage="RULES_GENERATION", max_retries=3)

            raw_rules = extract_list_from_json(rules_res)
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
            _save_intermediate_bible()

        # Step 1E: Terminology — FAIL-CLOSED
        if raw_bible.get("terminology") and isinstance(raw_bible.get("terminology"), dict) and len(raw_bible.get("terminology")) > 0:
            msg_1e = f"[INFO] === PROMPT 1E/5: Từ Điển Thuật Ngữ đã tồn tại (Bỏ qua) ==="
            logger.info(msg_1e)
            _safe_print(msg_1e)
        else:
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
            _save_intermediate_bible()

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
        for idx, c in enumerate(raw_bible.get("characters", []), 1):
            if isinstance(c, dict):
                c_id = c.get("id", f"char_{idx:03d}")
                c_name = c.get("name", p_name)
                c_realm = c.get("realm", "Khởi Đầu")
                c_loc = c.get("location", "Vùng Khởi Đầu")
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
                formatted_chars.append(self._format_character_dict(c, idx, p_name))

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

        # Priority: read user's configured total_chapters from project.json if available
        proj_json_file = self.story_dir / "project.json"
        if proj_json_file.exists():
            try:
                pdata = json.loads(proj_json_file.read_text(encoding="utf-8"))
                user_idea = pdata.get("novel_idea", {})
                if isinstance(user_idea, dict) and user_idea.get("total_chapters"):
                    total_chapters = int(user_idea["total_chapters"])
            except Exception as e:
                logger.warning(f"Could not read total_chapters from project.json: {e}")

        bible_data = {}
        try:
            self.db.clear_arc_plans(self.story_id)
        except Exception as e:
            logger.warning(f"Could not purge old arc plans DB data: {e}")

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
        
        # Batch size: max 5 arcs per LLM call to prevent output truncation on small models
        BATCH_SIZE = 5
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
            raw_arcs_res, metadata = self._call_llm_json_strict(prompt, stage="MASTER_PLAN", idea=None, max_retries=3)
            raw_arcs = extract_list_from_json(raw_arcs_res, expected_keys=["title", "goal", "conflict", "arc_num"])

            if not isinstance(raw_arcs, list) or len(raw_arcs) == 0:
                err_msg = f"[ERROR] LLM không tạo được Arc {arc_start_idx}-{arc_end_idx}. Batch {batch_num} trả về dữ liệu rỗng."
                logger.warning(err_msg)
                _safe_print(err_msg)
                raise GenerationError("MASTER_PLAN", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, err_msg, retryable=True)

            all_raw_arcs.extend(raw_arcs)
            arcs_remaining -= len(raw_arcs)
            
            batch_done_msg = f"[INFO] Batch {batch_num} hoàn thành: {len(raw_arcs)} Arcs | Tổng hiện tại: {len(all_raw_arcs)}/{expected_arcs}"
            logger.info(batch_done_msg)
            _safe_print(batch_done_msg)

        # Validate minimum arc count
        if len(all_raw_arcs) < max(2, expected_arcs // 2):
            raise GenerationError("MASTER_PLAN", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  f"Số lượng Arc quá ít ({len(all_raw_arcs)}/{expected_arcs}). Cần ít nhất {max(2, expected_arcs // 2)} Arcs cho {total_chapters} chương.", retryable=True)

        arc_objs = []
        total_arcs_count = len(all_raw_arcs)
        seen_titles = set()
        for idx, a in enumerate(all_raw_arcs, start=1):
            if isinstance(a, str):
                a = {"title": a}
            elif not isinstance(a, dict):
                a = {}

            # Strictly enforce continuous chapter math (no LLM hallucinated chapter gaps/overlaps)
            calc_start = (idx - 1) * chaps_per_arc + 1
            calc_end = total_chapters if idx == total_arcs_count else idx * chaps_per_arc

            raw_title = str(a.get("title", f"Arc {idx:02d}")).strip()
            basename = re.sub(r"^Arc\s*\d+[\s—:-]*", "", raw_title, flags=re.IGNORECASE).strip()
            basename_clean = re.sub(r"\[.*?\]", "", basename).strip()

            if not basename_clean or basename_clean.lower() in seen_titles or basename_clean.lower() in ["thăng đường thân vực", "tựa đề độc nhất sáng tạo"]:
                arc_goal = str(a.get("goal", "")).strip()
                arc_conflict = str(a.get("conflict", "")).strip()
                if arc_goal and len(arc_goal) > 5 and not arc_goal.startswith("["):
                    basename_clean = arc_goal[:35].rstrip(".")
                elif arc_conflict and len(arc_conflict) > 5 and not arc_conflict.startswith("["):
                    basename_clean = arc_conflict[:35].rstrip(".")
                else:
                    fallback_titles = [
                        "Tân Thủ Xuất Sơn Lập Nghiệp",
                        "Gia Nhập Thế Lực Khởi Đầu",
                        "Khảo Nghiệm Đột Phá Cảnh Giới",
                        "Chuyên Viên Khiêu Chiến Ngầm",
                        "Đối Đầu Thế Lực Đỉnh Cao"
                    ]
                    basename_clean = fallback_titles[idx - 1] if idx <= len(fallback_titles) else f"Tiến Trình Cốt Truyện Giai Đoạn {idx}"

            seen_titles.add(basename_clean.lower())
            final_title = f"Arc {idx:02d} — {basename_clean}"

            arc_objs.append(ArcPlan(
                id=f"arc_{idx:02d}",
                story_id=self.story_id,
                arc_num=idx,
                title=final_title,
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
            try:
                bible_file.write_text(json.dumps(story_bible, indent=2, ensure_ascii=False), encoding="utf-8")
            except Exception as e:
                logger.warning(f"Failed writing master_blueprint to story_bible.json: {e}")

            # Also sync master_blueprint directly to project.json
            self._update_project_json({
                "master_blueprint": bp_res
            })
            return bp_res
        
        return {}




    def generate_arc_roadmap(self, arc_num: int) -> List[Dict[str, Any]]:
        """Generates a 20-chapter continuous causal roadmap for a specific Arc in 5-chapter sub-batches."""
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

        start_chap = current_arc.get("start_chapter", (arc_num - 1) * 20 + 1)
        end_chap = current_arc.get("end_chapter", arc_num * 20)

        bible_file = self.story_dir / "story_bible.json"
        bible_data = {}
        if bible_file.exists():
            try:
                bible_data = json.loads(bible_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        master_bp = bible_data.get("master_blueprint", {})

        msg = f"[INFO] === TẠO DÀN Ý KỊCH BẢN 20 CHƯƠNG CHO ARC {arc_num} ({current_arc.get('title')}: Chương {start_chap}-{end_chap}) ==="
        logger.info(msg)
        _safe_print(msg)

        # Generate in sub-batches of max 5 chapters to prevent truncation on small models
        SUB_BATCH_SIZE = 5
        all_roadmaps: List[Dict[str, Any]] = []
        curr_chap = start_chap

        while curr_chap <= end_chap:
            batch_end = min(curr_chap + SUB_BATCH_SIZE - 1, end_chap)
            b_msg = f"[INFO] [ARC {arc_num} ROADMAP] Đang tạo dàn ý Chương {curr_chap} -> Chương {batch_end}..."
            logger.info(b_msg)
            _safe_print(b_msg)

            prompt = ArcRoadmapPrompt.build_sub_batch_prompt(
                current_arc, bible_data, master_bp,
                batch_start_chap=curr_chap,
                batch_end_chap=batch_end,
                previous_roadmaps=all_roadmaps
            )

            raw_res, _ = self._call_llm_json_strict(prompt, stage=f"ARC_{arc_num}_ROADMAP_CH{curr_chap}_{batch_end}", max_retries=3)

            found_by_ch = {}
            if isinstance(raw_res, dict):
                for c in range(curr_chap, batch_end + 1):
                    rel_idx = c - curr_chap + 1
                    k_options = [
                        f"chapter_{c}", f"chapter_{c:02d}", str(c), c,
                        f"chapter_{rel_idx}", f"chapter_{rel_idx:02d}", str(rel_idx), rel_idx
                    ]
                    for k in k_options:
                        if k in raw_res and isinstance(raw_res[k], dict):
                            found_by_ch[c] = dict(raw_res[k])
                            found_by_ch[c]["chapter_num"] = c
                            break

            # Fallback parsing if LLM returned array or wrapper
            batch_items = []
            if not found_by_ch:
                batch_items = extract_list_from_json(raw_res, expected_keys=["chapter_num", "summary", "title", "goal", "key_event"])
                if isinstance(batch_items, list):
                    for idx, item in enumerate(batch_items):
                        if isinstance(item, dict):
                            c_n = item.get("chapter_num")
                            try:
                                c_n_int = int(c_n) if c_n is not None else (curr_chap + idx)
                            except (ValueError, TypeError):
                                c_n_int = curr_chap + idx
                            found_by_ch[c_n_int] = item

            # Strict Fail-Closed: raise GenerationError if LLM failed to produce items for this batch
            if len(found_by_ch) == 0:
                err_msg = f"LLM không tạo được dàn ý hợp lệ cho các Chương {curr_chap}-{batch_end} (Arc {arc_num})."
                logger.warning(f"[ARC_{arc_num}_ROADMAP] {err_msg}")
                raise GenerationError(f"ARC_{arc_num}_ROADMAP", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, err_msg, retryable=True)

            for c in range(curr_chap, batch_end + 1):
                item = found_by_ch.get(c)
                if not isinstance(item, dict):
                    idx_in_batch = c - curr_chap
                    item_by_idx = found_by_ch.get(idx_in_batch) or (batch_items[idx_in_batch] if isinstance(batch_items, list) and len(batch_items) > idx_in_batch else None)
                    if isinstance(item_by_idx, dict):
                        item = item_by_idx
                    else:
                        raise GenerationError(f"ARC_{arc_num}_ROADMAP", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                              f"LLM không tạo đủ dữ liệu kịch bản cho Chương {c}. Hãy thử lại.", retryable=True)

                t_str = str(item.get("title", "")).strip()
                t_clean = re.sub(r"^Chương\s*\d+[\s:-]*", "", t_str, flags=re.IGNORECASE).strip()
                t_clean = re.sub(r"\[.*?\]", "", t_clean).strip()

                g_str = str(item.get("goal", "")).strip()
                g_clean = re.sub(r"\[.*?\]", "", g_str).strip()
                item["goal"] = g_clean if g_clean else f"Tiến triển cốt truyện Arc {arc_num} trong Chương {c}"

                # If title is missing or generic, derive a rich novelistic title from chapter goal or trigger_event
                if not t_clean or "Tiến Trình Diễn Biến" in t_clean or t_clean.lower() in ["diễn biến kịch bản mới", "tựa đề 1", "tựa đề 2"]:
                    if g_clean and len(g_clean) > 5:
                        t_clean = g_clean[:32].rstrip(".")
                    else:
                        e_str = str(item.get("trigger_event", "")).strip()
                        t_clean = e_str[:32].rstrip(".") if e_str else f"Biến Cố Chương {c}"

                item["title"] = f"Chương {c}: {t_clean}"

                all_roadmaps.append(item)

            curr_chap = batch_end + 1

        if len(all_roadmaps) == 0:
            raise GenerationError(f"ARC_{arc_num}_ROADMAP", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  f"LLM không tạo được Dàn Ý 20 Chương hợp lệ cho Arc {arc_num}. Hãy thử lại.")

        raw_roadmap = all_roadmaps


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

    def _load_existing_idea_and_bible(self) -> Tuple[StoryIdea, Dict[str, Any]]:
        project_json_path = self.story_dir / "project.json"
        idea_data = {}
        if project_json_path.exists():
            try:
                p_data = json.loads(project_json_path.read_text(encoding="utf-8"))
                idea_data = p_data.get("story_idea") or p_data.get("idea") or p_data.get("novel_idea") or {}
                if not idea_data.get("title"):
                    idea_data["title"] = p_data.get("name", "Hành Trình Mới")
                if not idea_data.get("genre"):
                    idea_data["genre"] = p_data.get("genre", "Hành động viễn tưởng")
                if not idea_data.get("total_chapters"):
                    idea_data["total_chapters"] = p_data.get("total_chapters", 1000)
            except Exception as e:
                logger.warning(f"Could not read project.json: {e}")

        story_bible_path = self.story_dir / "story_bible.json"
        bible_data = {}
        if story_bible_path.exists():
            try:
                bible_data = json.loads(story_bible_path.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning(f"Could not read story_bible.json: {e}")

        idea = StoryIdea(
            title=idea_data.get("title", "Hành Trình Mới"),
            genre=idea_data.get("genre", "Hành động viễn tưởng"),
            style=idea_data.get("style", "Dễ đọc, tiết tấu nhanh"),
            total_chapters=idea_data.get("total_chapters", 1000),
            protagonist=idea_data.get("protagonist") or {"name": "Diệp Phàm", "background": "Thế giới khởi đầu"}
        )
        return idea, bible_data

    def regenerate_characters_only(self) -> List[Dict[str, Any]]:
        idea, bible_data = self._load_existing_idea_and_bible()
        msg = f"[INFO] === TÁI TẠO DUY NHẤT DÀN NHÂN VẬT (STEP 1C) ==="
        logger.info(msg)
        _safe_print(msg)
        try:
            self.db.clear_characters(self.story_id)
        except Exception as e:
            logger.warning(f"Could not purge old characters DB data: {e}")

        cast_prompt = StoryDirectorPrompt.build_cast_prompt(idea, bible_data)
        cast_res, _ = self._call_llm_json_strict(cast_prompt, stage="CAST_GENERATION", idea=idea, max_retries=3)
        raw_cast = extract_list_from_json(cast_res, expected_keys=["name", "role", "background"])
        if not isinstance(raw_cast, list) or len(raw_cast) == 0:
            raise GenerationError("CAST_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value,
                                  "LLM không tạo được Dàn Nhân Vật hợp lệ. Hãy thử lại.")

        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"
        unique_chars = []
        seen_names = set()
        formatted_chars = []

        for idx, c in enumerate(raw_cast, 1):
            if not isinstance(c, dict):
                continue
            name = str(c.get("name") or "").strip()
            if not name or name in seen_names:
                continue
            seen_names.add(name)
            c_id = f"char_{idx:03d}"
            c["id"] = c_id
            unique_chars.append(c)

            c_realm = c.get("realm", "Khởi Đầu")
            c_loc = c.get("location", "Vùng Khởi Đầu")
            c_gender = c.get("gender", "Nam")
            c_app = c.get("appearance") or "Thần thái kiên định, dáng người nhã nhặn"
            c_goal = c.get("goal") or "Phát triển sức mạnh & khám phá thế giới"

            self.db.save_character(Character(
                id=c_id,
                name=name,
                personality=c.get("personality", []),
                goal=c_goal,
                realm=c_realm,
                location=c_loc,
                known_information=c.get("known_information", []),
                secrets=c.get("secrets", [])
            ), self.story_id)

            formatted_chars.append(self._format_character_dict(c, idx, p_name))

        bible_data["characters"] = unique_chars
        story_bible_path = self.story_dir / "story_bible.json"
        try:
            story_bible_path.write_text(json.dumps(bible_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed writing story_bible.json: {e}")

        self._update_project_json({
            "characters": formatted_chars,
            "story_bible": bible_data
        })

        success_msg = f"[SUCCESS] Đã tái tạo thành công {len(formatted_chars)} nhân vật!"
        logger.info(success_msg)
        _safe_print(success_msg)
        return formatted_chars

    def _format_character_dict(self, c: dict, idx: int, p_name: str) -> dict:
        c_id = c.get("id") or f"char_{idx:03d}"
        c_name = str(c.get("name") or f"Nhân vật {idx}").strip()
        c_realm = c.get("realm", "Khởi Đầu")
        c_loc = c.get("location", "Vùng Khởi Đầu")
        c_gender = c.get("gender", "Nam")

        # Clean personality list from duplicates (e.g. ['Cố chấp', 'Cố chấp', 'Cố chấp'] -> ['Cố chấp', 'Thông minh', 'Quyết đoán'])
        raw_p = c.get("personality", [])
        if isinstance(raw_p, str):
            raw_p = [p.strip() for p in raw_p.split(",") if p.strip()]
        unique_p = []
        if isinstance(raw_p, list):
            for tag in raw_p:
                clean_tag = str(tag).strip()
                if clean_tag and clean_tag not in unique_p:
                    unique_p.append(clean_tag)
        if not unique_p:
            unique_p = ["Điềm tĩnh", "Thông minh", "Quyết đoán"]
        if len(unique_p) == 1:
            unique_p.extend(["Mưu trí", "Quyết đoán"])

        # Clean appearance (ensure unique physical appearance per role/age/gender)
        raw_app = str(c.get("appearance") or "").strip()
        role_lower = str(c.get("role", "")).lower()
        if not raw_app or ("thân hình cao lớn" in raw_app.lower() and idx > 1):
            if c_gender.lower() in ("nữ", "female"):
                raw_app = "Khuôn mặt trái xoan thanh tú, đôi mắt trong veo rạng rỡ, dáng người thon thả"
            elif "sư phụ" in role_lower or int(c.get("age", 20)) > 40:
                raw_app = "Mái tóc điểm bạc phơ, râu dài che ngực, dáng vẻ tiên phong đạo cốt, ánh mắt trầm ngâm"
            elif "phản diện" in role_lower:
                raw_app = "Khuôn mặt góc cạnh thâm trầm, vết sẹo mờ ở đuôi mắt, ánh mắt lạnh lẽo nham hiểm"
            else:
                raw_app = "Dáng người thon gọn, phong thái kiên định, ánh mắt sáng như sao"

        # Clean address pronouns
        raw_pro = str(c.get("address_pronouns") or c.get("addressPronouns") or "").strip()
        if not raw_pro or raw_pro == f"Sư huynh ({c.get('alias', '')})":
            if "sư phụ" in role_lower or int(c.get("age", 20)) > 40:
                raw_pro = f"Xưng với {p_name}: Vi sư - Đồ nhi (Tiền bối - Vãn bối)"
            elif c_gender.lower() in ("nữ", "female"):
                raw_pro = f"Xưng với {p_name}: Huynh - Muội (Sư huynh - Muội muội)"
            elif "phản diện" in role_lower:
                raw_pro = f"Xưng với {p_name}: Ta - Ngươi / Lão tử - Ngươi"
            else:
                raw_pro = "Xưng: Ta - Ngươi / Ta - Hắn"

        c_goal = str(c.get("goal") or f"Phát triển bản thân và hỗ trợ {p_name}").strip()

        return {
            "id": c_id,
            "name": c_name,
            "alias": c.get("role") or c.get("alias") or c_realm,
            "gender": c_gender,
            "age": str(c.get("age", "20")),
            "relationship": c.get("relationship") or f"Mối quan hệ sát cánh cùng {p_name}",
            "addressPronouns": raw_pro,
            "personality": ", ".join(unique_p),
            "appearance": raw_app,
            "goal": c_goal,
            "clothing": c.get("clothing") or f"Cảnh giới: {c_realm} • Vị trí: {c_loc}",
            "voice": "vi_female_hero" if c_gender.lower() in ("nữ", "female") else "vi_male_hero",
            "speakingStyle": "Trang trọng",
            "locked": True
        }

    def regenerate_world_only(self) -> Dict[str, Any]:
        idea, bible_data = self._load_existing_idea_and_bible()
        msg = f"[INFO] === TÁI TẠO DUY NHẤT BỐI CẢNH THẾ GIỚI (STEP 1A) ==="
        logger.info(msg)
        _safe_print(msg)

        world_prompt = StoryDirectorPrompt.build_world_prompt(idea)
        w_res, _ = self._call_llm_json_strict(world_prompt, stage="WORLD_GENERATION", idea=idea, max_retries=3)
        if not isinstance(w_res, dict):
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Story Bible payload must be a JSON object")

        bible_data["premise"] = w_res.get("premise", f"Hành trình của {idea.title}")
        bible_data["world"] = w_res.get("world", {})

        formatted_lore = []
        world_info = bible_data.get("world", {})
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
                    "description": f"Thế lực chính cai trị đại lục {world_info.get('continent_name', '')}",
                    "locked": True
                })

        story_bible_path = self.story_dir / "story_bible.json"
        try:
            story_bible_path.write_text(json.dumps(bible_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed writing story_bible.json: {e}")

        self._update_project_json({
            "world_lore": formatted_lore,
            "story_bible": bible_data
        })

        success_msg = f"[SUCCESS] Đã tái tạo thành công {len(formatted_lore)} mục bối cảnh thế giới!"
        logger.info(success_msg)
        _safe_print(success_msg)
        return {"premise": bible_data["premise"], "world_lore": formatted_lore}

    def regenerate_rules_only(self) -> List[Dict[str, Any]]:
        idea, bible_data = self._load_existing_idea_and_bible()
        msg = f"[INFO] === TÁI TẠO DUY NHẤT QUY TẮC & KÝ ỨC THẾ GIỚI (STEP 1D) ==="
        logger.info(msg)
        _safe_print(msg)

        rules_prompt = StoryDirectorPrompt.build_rules_prompt(idea, bible_data)
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

        bible_data["rules"] = unique_rules

        formatted_memories = [
            {
                "id": f"mem-{idx}",
                "category": "World",
                "content": rule_str,
                "importance": "HIGH",
                "confidence": 1.0,
                "locked": True
            }
            for idx, rule_str in enumerate(unique_rules)
        ]

        story_bible_path = self.story_dir / "story_bible.json"
        try:
            story_bible_path.write_text(json.dumps(bible_data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed writing story_bible.json: {e}")

        self._update_project_json({
            "story_memories": formatted_memories,
            "story_bible": bible_data
        })

        success_msg = f"[SUCCESS] Đã tái tạo thành công {len(formatted_memories)} quy tắc thế giới!"
        logger.info(success_msg)
        _safe_print(success_msg)
        return formatted_memories


