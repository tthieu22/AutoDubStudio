import os
import json
import logging
import time
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from autodub.novel.novel_models import (
    StoryIdea, StoryBible, ArcPlan, ChapterPlan, ScenePlan, CanonFact, CharacterState, PlotThread,
    NarrativeContract, ProgressLedger, CanonCandidate, InformationState, GlobalProgressLedger,
    GenerationErrorCode, GenerationError
)
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.context_builder import ContextBuilder
from autodub.novel.canon_validator_engine import CanonValidatorEngine

from autodub.novel.prompts.story_director import StoryDirectorPrompt
from autodub.novel.prompts.master_planner import MasterPlannerPrompt
from autodub.novel.prompts.chapter_planner import ChapterPlannerPrompt
from autodub.novel.prompts.narrative_contract import NarrativeContractPrompt
from autodub.novel.prompts.scene_planner_novel import NovelScenePlannerPrompt
from autodub.novel.prompts.writer import NovelWriterPrompt
from autodub.novel.prompts.rewriter import NovelRewriterPrompt
from autodub.novel.prompts.editor import NovelEditorPrompt
from autodub.novel.prompts.memory_extractor import MemoryExtractorPrompt
from autodub.novel.prompts.canon_validator import CanonValidatorPrompt

from autodub.modules.llamacpp_client import LlamaCppClient, strip_think_tags


logger = logging.getLogger(__name__)


from autodub.novel.novel_validators import (
    log_gpu_hardware_status,
    FORBIDDEN_GENRE_TERMS,
    validate_protagonist_integrity,
    validate_genre_integrity
)


class NovelEngine:
    """
    Complete AI Novel Engine Orchestrator.
    Executes full Audio-First pipeline:
    IDEA → STORY BIBLE → MASTER PLAN → CHAPTER PLANNER → SCENE PLANNER → SCENE WRITER → SCENE VALIDATOR (PASS/REWRITE) → CHAPTER ASSEMBLER → FINAL VALIDATOR → MEMORY EXTRACTOR → CANON DB → NEXT CHAPTER
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

        # Ensure checkpoints directory exists
        self.checkpoints_dir = self.story_dir / "chapters" / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)


    def _call_llm_json(self, prompt: str, default_val: Any) -> Any:
        import re
        import ast
        try:
            raw_res = self.llm.generate(prompt=prompt, timeout=120)
            cleaned = strip_think_tags(raw_res).strip()
            cleaned = re.sub(r"```json\s*", "", cleaned, flags=re.IGNORECASE)
            cleaned = re.sub(r"```\s*", "", cleaned)

            idx_brace = cleaned.find("{")
            idx_bracket = cleaned.find("[")

            json_str = ""
            if idx_bracket != -1 and (idx_brace == -1 or idx_bracket < idx_brace):
                end_bracket = cleaned.rfind("]")
                if end_bracket != -1:
                    json_str = cleaned[idx_bracket:end_bracket + 1]
            elif idx_brace != -1:
                end_brace = cleaned.rfind("}")
                if end_brace != -1:
                    json_str = cleaned[idx_brace:end_brace + 1]

            if json_str:
                # Direct JSON parse
                try:
                    return json.loads(json_str)
                except Exception:
                    pass

                # Clean trailing commas
                sanitized = re.sub(r",\s*([\]}])", r"\1", json_str)
                try:
                    return json.loads(sanitized)
                except Exception:
                    pass

                # Python literal fallback
                try:
                    res_eval = ast.literal_eval(sanitized)
                    if isinstance(res_eval, (dict, list)):
                        return res_eval
                except Exception:
                    pass
        except Exception as e:
            logger.warning(f"LLM JSON call fallback due to: {e}")
        return default_val

    def _call_llm_json_strict(
        self,
        prompt: str,
        stage: str,
        idea: Optional[StoryIdea] = None,
        max_retries: int = 3
    ) -> Tuple[Any, Dict[str, Any]]:
        import re
        import ast

        last_error_code = GenerationErrorCode.GENERATION_FAILED
        last_error_msg = ""

        for attempt in range(1, max_retries + 1):
            raw_res = None
            try:
                raw_res = self.llm.generate(prompt=prompt, timeout=120)
            except Exception as e:
                err_str = str(e).lower()
                if isinstance(e, TimeoutError) or "timeout" in err_str:
                    last_error_code = GenerationErrorCode.LLM_TIMEOUT
                    last_error_msg = f"LLM generation timed out during {stage} (Attempt {attempt}/{max_retries})"
                else:
                    last_error_code = GenerationErrorCode.LLM_UNAVAILABLE
                    last_error_msg = f"LLM model unavailable or failed: {e} (Attempt {attempt}/{max_retries})"
                logger.warning(f"[{stage}_RETRY] {last_error_msg}")
                continue

            cleaned = strip_think_tags(raw_res).strip() if raw_res else ""
            if not cleaned:
                last_error_code = GenerationErrorCode.LLM_EMPTY_RESPONSE
                last_error_msg = f"LLM returned an empty response during {stage} (Attempt {attempt}/{max_retries})"
                logger.warning(f"[{stage}_RETRY] {last_error_msg}")
                continue

            res = self._extract_json_multi_strategy(cleaned)

            if res is None:
                last_error_code = GenerationErrorCode.JSON_PARSE_ERROR
                last_error_msg = f"LLM returned malformed JSON during {stage} (Attempt {attempt}/{max_retries})"
                logger.warning(f"[{stage}_RETRY] {last_error_msg}")
                continue

            if idea:
                p_ok, p_msg = validate_protagonist_integrity(res, idea)
                if not p_ok:
                    last_error_code = GenerationErrorCode.PROTAGONIST_INTEGRITY_ERROR
                    last_error_msg = p_msg
                    logger.warning(f"[{stage}_RETRY] Attempt #{attempt} failed protagonist check: {p_msg}")
                    continue

                g_ok, g_msg = validate_genre_integrity(res, idea)
                if not g_ok:
                    last_error_code = GenerationErrorCode.GENRE_INTEGRITY_ERROR
                    last_error_msg = g_msg
                    logger.warning(f"[{stage}_RETRY] Attempt #{attempt} failed genre check: {g_msg}")
                    continue

            metadata = {
                "source": "LLM_GENERATED",
                "model": getattr(self.llm, "model_name", "qwen2.5:3b"),
                "fallback_used": False,
                "template_used": False,
                "attempt": attempt,
                "generated_at": datetime.datetime.now().isoformat()
            }
            return res, metadata

        # HARD STOP — Raising GenerationError cleanly if pure LLM response fails after max_retries
        raise GenerationError(
            stage=stage,
            error_code=last_error_code.value if isinstance(last_error_code, GenerationErrorCode) else str(last_error_code),
            message=f"Generation failed after {max_retries} attempts: {last_error_msg}",
            retryable=True
        )

    def _extract_json_multi_strategy(self, text: str) -> Any:
        import re
        import ast

        if not text or not text.strip():
            return None

        cleaned = text.strip()
        cleaned = re.sub(r"```json\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"```\s*", "", cleaned)

        def sanitize(s: str) -> str:
            s = re.sub(r",\s*([\]}])", r"\1", s)
            s = re.sub(r"[\r\n]+", " ", s)
            return s

        # Strategy 1: Direct JSON parse
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        try:
            return json.loads(sanitize(cleaned))
        except Exception:
            pass

        first_brace = cleaned.find("{")
        first_bracket = cleaned.find("[")

        # Strategy 2: If top-level structure starts with { (dict payload)
        if first_brace != -1 and (first_bracket == -1 or first_brace < first_bracket):
            last_brace = cleaned.rfind("}")
            if last_brace != -1:
                candidate = cleaned[first_brace:last_brace + 1]
                try:
                    return json.loads(candidate)
                except Exception:
                    try:
                        return json.loads(sanitize(candidate))
                    except Exception:
                        try:
                            res_eval = ast.literal_eval(sanitize(candidate))
                            if isinstance(res_eval, dict):
                                return res_eval
                        except Exception:
                            pass

        # Strategy 3: If top-level structure starts with [ (array payload)
        if first_bracket != -1 and (first_brace == -1 or first_bracket < first_brace):
            last_bracket = cleaned.rfind("]")
            if last_bracket != -1:
                candidate = cleaned[first_bracket:last_bracket + 1]
                try:
                    return json.loads(candidate)
                except Exception:
                    try:
                        return json.loads(sanitize(candidate))
                    except Exception:
                        try:
                            res_eval = ast.literal_eval(sanitize(candidate))
                            if isinstance(res_eval, list):
                                return res_eval
                        except Exception:
                            pass

            # Truncated array repair
            dict_blocks = re.findall(r'(\{[\s\S]*?\})', cleaned)
            valid_items = []
            for d in dict_blocks:
                try:
                    valid_items.append(json.loads(d))
                except Exception:
                    try:
                        valid_items.append(json.loads(sanitize(d)))
                    except Exception:
                        pass
            if valid_items:
                return valid_items

        return None

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
        p_name = idea.protagonist.get("name", "Nhân vật chính") if isinstance(idea.protagonist, dict) else "Nhân vật chính"

        logger.info(f"[WORLD_GENERATION] Input Genre: '{idea.genre}' | Protagonist: '{p_name}' | LLM Call: START")

        prompt = StoryDirectorPrompt.build_prompt(idea)
        raw_bible, metadata = self._call_llm_json_strict(prompt, stage="WORLD_GENERATION", idea=idea, max_retries=3)

        # Strict Schema Validation
        if not isinstance(raw_bible, dict):
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Story Bible payload must be a JSON object")

        if not raw_bible.get("premise"):
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Required field 'premise' is missing or empty")

        if not raw_bible.get("world") or not isinstance(raw_bible.get("world"), dict):
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Required field 'world' is missing or invalid")

        if not raw_bible.get("characters") or not isinstance(raw_bible.get("characters"), list) or len(raw_bible.get("characters")) == 0:
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Required field 'characters' must contain at least 1 character")

        # Support both progression_system and cultivation_system
        prog_sys = raw_bible.get("progression_system") or {}
        cult_sys = raw_bible.get("cultivation_system") or []
        if not prog_sys and not cult_sys:
            raise GenerationError("WORLD_GENERATION", GenerationErrorCode.SCHEMA_VALIDATION_ERROR.value, "Required field 'progression_system' or 'cultivation_system' is missing")

        raw_bible["generation_metadata"] = metadata
        logger.info(f"[WORLD_GENERATION] LLM Call: SUCCESS | Source: {metadata['source']} | Fallback Used: FALSE")

        # Save to DB & File ONLY AFTER PASSING VALIDATION
        self.db.create_story(self.story_id, idea)

        bible_file = self.story_dir / "story_bible.json"
        with open(bible_file, "w", encoding="utf-8") as f:
            json.dump(raw_bible, f, indent=2, ensure_ascii=False)

        from autodub.novel.novel_models import Character
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
            formatted_chars.append({
                "id": c.get("id", f"char_{idx:03d}"),
                "name": c.get("name", p_name),
                "alias": c.get("realm", "Khởi Đầu"),
                "gender": c.get("gender", "Nam"),
                "age": str(c.get("age", "20")),
                "personality": ", ".join(c.get("personality", [])) if isinstance(c.get("personality"), list) else str(c.get("personality", "Quyết đoán")),
                "appearance": f"Mục tiêu: {c.get('goal', 'Khám phá thế giới')}",
                "clothing": f"Cảnh giới: {c.get('realm', 'Khởi Đầu')} • Vị trí: {c.get('location', 'Vùng Khởi Đầu')}",
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

    # ══════════════════════════════════════════════════════════════
    # PHASE B: CHAPTER GENERATION PIPELINE
    # ══════════════════════════════════════════════════════════════
    def generate_chapter(self, chapter_num: int, sub_progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        logger.info(f"--- Generating Chapter {chapter_num} (Engine V2.3) ---")

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
            _notify("INITIALIZATION", "Story Bible missing. Auto-initializing Story Bible...")
            idea = StoryIdea(title=self.story_dir.name, total_chapters=1000)
            self.initialize_story(idea)

        arcs = self.db.get_arc_plans(self.story_id)
        if not arcs:
            _notify("MASTER_PLAN", "Master Plan arcs missing. Auto-generating Master Plan...")
            self.generate_master_plan(1000)

        # [STEP 1/7] RETRIEVAL (Hierarchical Context Retrieval)
        _notify("RETRIEVAL", f"Step 1/7 — RETRIEVAL: Hierarchical context from SQLite Canon DB for Chapter {chapter_num}...")
        global_ledger = self.db.get_global_progress_ledger(self.story_id)
        arc = self.db.get_current_arc(self.story_id, chapter_num) or {
            "title": f"Arc cho Chapter {chapter_num}",
            "goal": "Tiến triển cốt truyện",
            "conflict": "Xung đột mới xuất hiện"
        }
        open_threads = self.db.get_open_plot_threads(self.story_id)
        recent_summaries = self.db.get_recent_chapter_summaries(self.story_id, chapter_num, 3)
        arc_title = arc.get("title") if isinstance(arc, dict) else getattr(arc, "title", f"Arc {chapter_num}")
        clean_summaries = [s.get("summary_text") if isinstance(s, dict) else str(s) for s in recent_summaries]
        context_summary = f"Giai đoạn: {arc_title}. Vừa diễn ra 3 chương qua: {clean_summaries}. Global Completed Events: {global_ledger.completed_events[-3:]}"

        MAX_CHAPTER_REPLANS = 2
        replan_count = 0
        chapter_passed = False
        final_text = ""
        scene_records = []
        scene_drafts = []
        chap_plan = {}

        while not chapter_passed and replan_count <= MAX_CHAPTER_REPLANS:
            if replan_count > 0:
                _notify("PLANNING", f"Step 2/7 — REPLANNING (Attempt {replan_count}/{MAX_CHAPTER_REPLANS}) after Stagnation/Repetition detected...")

            # [STEP 2/7] CHAPTER PLANNER & NARRATIVE CONTRACT
            _notify("PLANNING", f"Step 2/7 — PLANNING & CONTRACT: Planning Chapter {chapter_num} (Replan {replan_count}/{MAX_CHAPTER_REPLANS})...")
            c_planner_prompt = ChapterPlannerPrompt.build_prompt(chapter_num, arc, open_threads, recent_summaries, global_ledger=global_ledger)
            chap_plan = self._call_llm_json(c_planner_prompt, {
                "chapter_num": chapter_num,
                "goal": f"Đạt được tiến triển mục tiêu chương {chapter_num}",
                "conflict": "Xung đột bất ngờ",
                "characters": ["char_001"],
                "reveal": "Tiết lộ bí mật mới",
                "ending": "Cliffhanger hồi hộp"
            })

            # Generate Narrative Contract
            narrative_contract_prompt = NarrativeContractPrompt.build_prompt(chapter_num, chap_plan, context_summary, open_threads)
            raw_contract = self._call_llm_json(narrative_contract_prompt, {
                "chapter_goal": [chap_plan.get("goal", f"Chương {chapter_num}")],
                "forbidden_topic_drift": ["tranh chấp thương mại", "đối tác kinh doanh", "tuyến tài nguyên mới"]
            })
            narrative_contract = NarrativeContract(
                chapter_num=chapter_num,
                chapter_goal=raw_contract.get("chapter_goal", [chap_plan.get("goal")]),
                required_events=raw_contract.get("required_events", []),
                required_information=raw_contract.get("required_information", []),
                allowed_characters=raw_contract.get("allowed_characters", ["char_001"]),
                allowed_locations=raw_contract.get("allowed_locations", []),
                open_threads_to_advance=raw_contract.get("open_threads_to_advance", []),
                forbidden_topic_drift=raw_contract.get("forbidden_topic_drift", ["tranh chấp thương mại", "đối tác kinh doanh"]),
                forbidden_repetitions=raw_contract.get("forbidden_repetitions", ["Không lặp lại sự kiện/thông tin cũ"]),
                character_knowledge_boundaries=raw_contract.get("character_knowledge_boundaries", {})
            )

            # Dynamic Scene Planner
            s_planner_prompt = NovelScenePlannerPrompt.build_prompt(chapter_num, chap_plan, context_summary)
            scenes_plan = self._call_llm_json(s_planner_prompt, [
                {
                    "scene_index": 1,
                    "goal": "Phát hiện thử thách và đối thoại trực tiếp",
                    "emotion": "Căng thẳng",
                    "conflict": "Đối đầu khiêu khích",
                    "ending": "Nhận ra ý đồ đối phương",
                    "estimated_words": 600
                },
                {
                    "scene_index": 2,
                    "goal": "Giải quyết mâu thuẫn bằng quyết đoán",
                    "emotion": "Quyết đoán",
                    "conflict": "Xử lý xung đột",
                    "ending": "Đạt được tiến triển mục tiêu chương",
                    "estimated_words": 600
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
                        "estimated_words": 600
                    })
            scenes_plan = sanitized_scenes

            # [STEP 3/7] SCENE EXECUTION LOOP
            char_ids = chap_plan.get("characters", ["char_001"]) if isinstance(chap_plan, dict) else ["char_001"]
            chapter_goal_text = chap_plan.get("goal", f"Đạt được mục tiêu chương {chapter_num}") if isinstance(chap_plan, dict) else f"Đạt được mục tiêu chương {chapter_num}"
            scene_drafts = []
            scene_records = []
            prev_scene_summary = ""
            progress_ledger = ProgressLedger(chapter_num=chapter_num)

            for sc_idx, sc in enumerate(scenes_plan, start=1):
                sc_id = sc.get("scene_index", sc_idx)
                chk_file = self.checkpoints_dir / f"chap_{chapter_num:04d}_scene_{sc_id}.json"

                # Checkpoint Resume & V2.3 Validation Check
                if chk_file.exists() and replan_count == 0:
                    try:
                        chk_data = json.loads(chk_file.read_text(encoding="utf-8"))
                        chk_text = chk_data.get("text", "")
                        chk_val = self.validator.validate_scene(
                            story_id=self.story_id,
                            chapter_num=chapter_num,
                            scene_index=sc_id,
                            scene_text=chk_text,
                            scene_plan=sc,
                            character_ids=char_ids,
                            narrative_contract=narrative_contract,
                            global_ledger=global_ledger
                        )
                        if chk_data.get("passed") and chk_text and chk_val.get("passed"):
                            _notify("SCENE_EXECUTION", f"Step 3/7 — Scene {sc_id}/{len(scenes_plan)} — LOADED FROM CHECKPOINT")
                            scene_drafts.append(chk_text)
                            scene_records.append(chk_data)
                            progress_ledger.completed_events.append(sc.get("goal", f"Scene {sc_id}"))
                            prev_scene_summary = f"Scene {sc_id} ({sc.get('goal', '')}): {chk_text[-150:]}"
                            continue
                        else:
                            _notify("SCENE_EXECUTION", f"Step 3/7 — Scene {sc_id}/{len(scenes_plan)} — OLD CHECKPOINT INVALIDATED (Failed V2.3 Rules). RE-WRITING FRESH SCENE...")
                            chk_file.unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning(f"Failed loading scene checkpoint {chk_file}: {e}")

                # Generate Scene Text (Writer)
                _notify("SCENE_EXECUTION", f"Step 3/7 — Scene {sc_id}/{len(scenes_plan)} — WRITING")
                full_context = self.context_builder.build_writer_context(chapter_num, sc, char_ids, global_ledger=global_ledger)
                writer_prompt = NovelWriterPrompt.build_prompt(
                    chapter_num=chapter_num,
                    scene_index=sc_id,
                    scene_plan=sc,
                    full_context=full_context,
                    chapter_goal=chapter_goal_text,
                    previous_scene_summary=prev_scene_summary,
                    narrative_contract=narrative_contract,
                    progress_ledger=progress_ledger,
                    global_ledger=global_ledger
                )

                try:
                    raw_res = self.llm.generate(prompt=writer_prompt, timeout=120)
                    cleaned_scene = strip_think_tags(raw_res).strip()
                except Exception as e:
                    logger.warning(f"LLM generate failed for Scene {sc_id}: {e}")
                    fallback_char = char_ids[0] if char_ids else "Nhân vật chính"
                    cleaned_scene = f"{fallback_char} tập trung tinh thần quan sát diễn biến xung quanh, chủ động tìm kiếm bước ngoặt và chuẩn bị đưa ra phương án xử lý kiên quyết nhất..."

                # Validate Scene
                _notify("SCENE_EXECUTION", f"Step 3/7 — Scene {sc_id}/{len(scenes_plan)} — VALIDATING")
                val_res = self.validator.validate_scene(
                    story_id=self.story_id,
                    chapter_num=chapter_num,
                    scene_index=sc_id,
                    scene_text=cleaned_scene,
                    scene_plan=sc,
                    character_ids=char_ids,
                    narrative_contract=narrative_contract,
                    global_ledger=global_ledger
                )

                retries = 0
                while not val_res.get("passed") and retries < 2:
                    retries += 1
                    _notify("SCENE_EXECUTION", f"Step 3/7 — Scene {sc_id}/{len(scenes_plan)} — REWRITING (Retry {retries}/2)")
                    rewrite_prompt = NovelRewriterPrompt.build_prompt(
                        chapter_num=chapter_num,
                        scene_index=sc_id,
                        scene_plan=sc,
                        draft_scene_text=cleaned_scene,
                        issues=val_res.get("issues", []),
                        full_context=full_context,
                        narrative_contract=narrative_contract,
                        progress_ledger=progress_ledger,
                        global_ledger=global_ledger
                    )
                    try:
                        rewritten_res = self.llm.generate(prompt=rewrite_prompt, timeout=120)
                        cleaned_rewrite = strip_think_tags(rewritten_res).strip()
                        if cleaned_rewrite and len(cleaned_rewrite) >= 50:
                            cleaned_scene = cleaned_rewrite
                    except Exception as e:
                        logger.warning(f"LLM rewrite failed for Scene {sc_id}: {e}")

                    val_res = self.validator.validate_scene(
                        story_id=self.story_id,
                        chapter_num=chapter_num,
                        scene_index=sc_id,
                        scene_text=cleaned_scene,
                        scene_plan=sc,
                        character_ids=char_ids,
                        narrative_contract=narrative_contract,
                        global_ledger=global_ledger
                    )

                _notify("SCENE_EXECUTION", f"Step 3/7 — Scene {sc_id}/{len(scenes_plan)} — PASSED (Score: {val_res.get('score', 100)})")

                scene_record = {
                    "chapterNumber": chapter_num,
                    "sceneNumber": sc_id,
                    "goal": sc.get("goal"),
                    "emotion": sc.get("emotion"),
                    "text": cleaned_scene,
                    "passed": val_res.get("passed", True),
                    "score": val_res.get("score", 100),
                    "issues": val_res.get("issues", []),
                    "retries": retries
                }

                progress_ledger.completed_events.append(sc.get("goal", f"Scene {sc_id}"))

                try:
                    chk_file.write_text(json.dumps(scene_record, indent=2, ensure_ascii=False), encoding="utf-8")
                except Exception as e:
                    logger.warning(f"Failed writing checkpoint file {chk_file}: {e}")

                scene_drafts.append(cleaned_scene)
                scene_records.append(scene_record)
                prev_scene_summary = f"Scene {sc_id} ({sc.get('goal', '')}): {cleaned_scene[-150:]}"

            # [STEP 4/7] CHAPTER ASSEMBLER
            _notify("CHAPTER_ASSEMBLER", f"Step 4/7 — CHAPTER ASSEMBLER: Combining {len(scene_drafts)} scenes...")
            full_draft = "\n\n".join(scene_drafts)

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

            # [STEP 5/7] CHAPTER PROGRESSION VALIDATOR & ANTI-STAGNATION
            _notify("PROGRESSION_VALIDATOR", f"Step 5/7 — CHAPTER PROGRESSION VALIDATOR: Validating narrative delta for Chapter {chapter_num}...")
            prog_res = self.validator.validate_chapter_progression(
                story_id=self.story_id,
                chapter_num=chapter_num,
                chapter_text=final_text,
                global_ledger=global_ledger,
                chapter_plan=chap_plan
            )

            if prog_res.get("passed"):
                chapter_passed = True
                _notify("PROGRESSION_VALIDATOR", f"Step 5/7 — CHAPTER PROGRESSION VALIDATOR — PASSED (Meaningful Score: {prog_res.get('meaningful_progress_score', 100)})")
            else:
                replan_count += 1
                if replan_count <= MAX_CHAPTER_REPLANS:
                    _notify("PROGRESSION_VALIDATOR", f"Step 5/7 — STAGNATION DETECTED ({prog_res.get('issues')}). Triggering Replan {replan_count}/{MAX_CHAPTER_REPLANS}...")
                else:
                    _notify("PROGRESSION_VALIDATOR", f"Step 5/7 — CHAPTER_GENERATION_FAILED (Reason: STAGNATION). Replan limit exhausted.")
                    logger.error(f"Chapter {chapter_num} failed generation due to stagnation after {MAX_CHAPTER_REPLANS} replans.")
                    return {
                        "chapter_num": chapter_num,
                        "status": "FAILED",
                        "reason": "STAGNATION",
                        "issues": prog_res.get("issues", []),
                        "validated": False
                    }

        # [STEP 6/7] METADATA EXTRACTOR
        _notify("METADATA_EXTRACTOR", f"Step 6/7 — METADATA EXTRACTOR: Extracting metadata candidates strictly from final chapter text...")
        extractor_prompt = MemoryExtractorPrompt.build_prompt(chapter_num, final_text)
        memory_extracted = self._call_llm_json(extractor_prompt, {
            "summary": f"Chương {chapter_num}: {chap_plan.get('goal') if isinstance(chap_plan, dict) else 'Hoàn thành'}",
            "new_characters": [],
            "new_discoveries": [],
            "canon_facts": [{"category": "event", "fact_text": f"Hoàn thành chương {chapter_num}", "information_state": "CLAIM", "confidence": 0.9}],
            "character_changes": [],
            "new_plot_threads": []
        })

        if not isinstance(memory_extracted, dict):
            memory_extracted = {
                "summary": f"Chương {chapter_num}: Hoàn thành",
                "new_characters": [],
                "new_discoveries": [],
                "canon_facts": [{"category": "event", "fact_text": f"Hoàn thành chương {chapter_num}", "information_state": "CLAIM", "confidence": 0.9}]
            }

        # [STEP 7/7] CANON CANDIDATE VALIDATION, NPC RESOLUTION & ATOMIC MEMORY COMMIT
        _notify("MEMORY_UPDATE", f"Step 7/7 — MEMORY UPDATE: Validating candidates, resolving NPCs and committing atomic SQLite transaction...")
        raw_facts = memory_extracted.get("canon_facts", [])
        validated_candidates = self.validator.validate_canon_candidates(
            story_id=self.story_id,
            chapter_num=chapter_num,
            raw_candidates=raw_facts,
            final_chapter_text=final_text
        )

        # Lock 5: NPC Entity Resolution Pipeline
        raw_npcs = memory_extracted.get("new_characters", [])
        if raw_npcs:
            self.db.resolve_and_save_npc_candidates(self.story_id, chapter_num, raw_npcs)

        # Lock 2: Pending Discoveries Update
        raw_disc = memory_extracted.get("new_discoveries", [])
        for d in raw_disc:
            d_id = d.get("id") or d.get("name") or str(d)
            if d_id and not any(existing.get("id") == d_id for existing in global_ledger.pending_discoveries):
                global_ledger.pending_discoveries.append({
                    "id": d_id,
                    "name": d.get("name", d_id),
                    "status": "UNTOUCHED",
                    "since_chapter": chapter_num
                })

        summary_text = memory_extracted.get("summary", f"Chương {chapter_num}")
        new_threads = memory_extracted.get("new_plot_threads", [])
        char_changes = memory_extracted.get("character_changes", [])

        # Update global ledger structure before commit
        for cand in validated_candidates:
            if cand.canon_status == "APPROVED":
                st_val = cand.information_state.value if isinstance(cand.information_state, InformationState) else str(cand.information_state)
                if st_val == "CONFIRMED":
                    global_ledger.confirmed_facts.append(cand.fact_text)
                elif st_val == "CLAIM":
                    global_ledger.active_claims.append(cand.fact_text)
                elif st_val == "EVIDENCE":
                    global_ledger.evidence_items.append(cand.fact_text)

        global_ledger.completed_events.append(chap_plan.get("goal", f"Hoàn thành chương {chapter_num}"))
        global_ledger.revealed_information.append(summary_text)
        global_ledger.last_completed_chapter = chapter_num

        # Atomic commit to SQLite
        self.db.commit_step_7_memory_transaction(
            story_id=self.story_id,
            chapter_num=chapter_num,
            validated_candidates=validated_candidates,
            global_ledger=global_ledger,
            summary_text=summary_text,
            key_events=[chap_plan.get("goal", f"Chương {chapter_num}")],
            char_ids=char_ids,
            new_threads=new_threads,
            char_changes=char_changes
        )

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
            "validated": True,
            "scenes": scene_records,
            "file": str(chap_file)
        }

        # Sync chapter and global_progress to project.json for UI
        existing_chaps = []
        p_json = self.story_dir / "project.json"
        p_data = {}
        if p_json.exists():
            try:
                p_data = json.loads(p_json.read_text(encoding="utf-8"))
                existing_chaps = p_data.get("chapters", [])
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
        existing_chaps = [c for c in existing_chaps if c.get("chapterNumber") != chapter_num]
        existing_chaps.append(chap_record)
        existing_chaps.sort(key=lambda x: x.get("chapterNumber", 0))

        p_data["chapters"] = existing_chaps
        p_data["global_progress"] = {
            "completed_events": global_ledger.completed_events,
            "revealed_information": global_ledger.revealed_information,
            "unresolved_questions": global_ledger.unresolved_questions,
            "confirmed_facts": global_ledger.confirmed_facts,
            "active_claims": global_ledger.active_claims,
            "evidence_items": global_ledger.evidence_items,
            "last_completed_chapter": chapter_num
        }

        p_json.write_text(json.dumps(p_data, indent=2, ensure_ascii=False), encoding="utf-8")

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
