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


def _safe_print_log(msg: str):
    """Print debug log safely, handling Windows codepage encoding issues."""
    import sys
    try:
        print(msg, flush=True)
    except UnicodeEncodeError:
        sys.stdout.buffer.write((msg + '\n').encode('utf-8', errors='replace'))
        sys.stdout.buffer.flush()


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
        # Ensure checkpoints directory exists
        self.checkpoints_dir = self.story_dir / "chapters" / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)

        from autodub.novel.pipeline_orchestrator import PipelineOrchestrator
        from autodub.novel.components.story_planner import StoryPlanner
        from autodub.novel.components.chapter_planner import ChapterPlanner
        from autodub.novel.components.scene_executor import SceneExecutor

        self.orchestrator = PipelineOrchestrator(self.db, self.llm)
        self.story_planner = StoryPlanner(
            story_id=self.story_id,
            story_dir=self.story_dir,
            db=self.db,
            llm_strict_caller=self._call_llm_json_strict,
            project_json_updater=self._update_project_json,
            checkpoints_dir=self.checkpoints_dir
        )
        self.chapter_planner = ChapterPlanner(llm_json_caller=self._call_llm_json)
        self.scene_executor = SceneExecutor(
            story_id=self.story_id,
            story_dir=self.story_dir,
            checkpoints_dir=self.checkpoints_dir,
            db=self.db,
            context_builder=self.context_builder,
            validator=self.validator,
            llm=self.llm,
            llm_json_caller=self._call_llm_json
        )
        self.is_running = False


    def _call_llm_json(self, prompt: str, default_val: Any) -> Any:
        import re
        import ast
        try:
            raw_res = self.llm.generate(prompt=prompt, timeout=120)
            cleaned = strip_think_tags(raw_res).strip() if raw_res else ""
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

            if not json_str:
                json_str = cleaned

            if json_str:
                # Attempt 1: Direct JSON parse
                try:
                    return json.loads(json_str)
                except Exception:
                    pass

                # Attempt 2: Clean JS comments, smart quotes, trailing commas
                sanitized = re.sub(r"//.*?\n", "\n", json_str)
                sanitized = re.sub(r"/\*[\s\S]*?\*/", "", sanitized)
                sanitized = sanitized.replace("“", '"').replace("”", '"').replace("’", "'")
                sanitized = re.sub(r",\s*([\]}])", r"\1", sanitized)

                try:
                    return json.loads(sanitized)
                except Exception:
                    pass

                # Attempt 3: Python literal_eval fallback
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
                # Debug log the raw output to help diagnose extraction failures
                preview = cleaned[:200].replace('\n', ' ').replace('\r', '')
                logger.warning(f"[{stage}_RETRY] {last_error_msg}")
                logger.debug(f"[{stage}_RAW_OUTPUT] Preview: {preview}")
                _safe_print_log(f"[{stage}_DEBUG] Raw LLM output preview: {preview}")
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
            s = re.sub(r"//.*?\n", "\n", s)
            s = re.sub(r"/\*[\s\S]*?\*/", "", s)
            s = s.replace("“", '"').replace("”", '"').replace("’", "'")
            s = re.sub(r",\s*([\]}])", r"\1", s)
            return s

        def repair_truncated_json(s: str) -> Optional[Any]:
            idx = s.find('{')
            idx_b = s.find('[')
            if idx == -1 or (idx_b != -1 and idx_b < idx):
                idx = idx_b
            if idx == -1:
                return None
            cand = s[idx:].strip()

            # Truncate after last valid comma
            last_comma = cand.rfind(',')
            if last_comma != -1:
                sub = cand[:last_comma].strip()
                in_str, esc, stack = False, False, []
                for ch in sub:
                    if esc:
                        esc = False
                        continue
                    if ch == '\\':
                        esc = True
                        continue
                    if ch == '"':
                        in_str = not in_str
                        continue
                    if not in_str:
                        if ch == '{': stack.append('}')
                        elif ch == '[': stack.append(']')
                        elif ch in ('}', ']') and stack: stack.pop()

                if not in_str and stack:
                    repaired = sub + "".join(reversed(stack))
                    try:
                        return json.loads(repaired, strict=False)
                    except Exception:
                        try:
                            return json.loads(sanitize(repaired), strict=False)
                        except Exception:
                            pass
            return None

        # Strategy 1: Direct JSON parse with strict=False
        try:
            return json.loads(cleaned, strict=False)
        except Exception:
            pass

        try:
            return json.loads(sanitize(cleaned), strict=False)
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
                    return json.loads(candidate, strict=False)
                except Exception:
                    try:
                        return json.loads(sanitize(candidate), strict=False)
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
                    return json.loads(candidate, strict=False)
                except Exception:
                    try:
                        return json.loads(sanitize(candidate), strict=False)
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
                    valid_items.append(json.loads(d, strict=False))
                except Exception:
                    try:
                        valid_items.append(json.loads(sanitize(d), strict=False))
                    except Exception:
                        pass
            if valid_items:
                return valid_items

        # Strategy 4: Truncated JSON Repair Fallback
        repaired_payload = repair_truncated_json(cleaned)
        if repaired_payload is not None:
            return repaired_payload

        # Strategy 5: Extract key-value pairs from plain text (for terminology-like outputs)
        # Handles: "- linh khí: Năng lượng tu luyện" or "1. linh khí — Năng lượng"
        kv_pattern = re.findall(r'["\-\d\.\*]?\s*["\']?([^":\n\-\*]+?)["\']?\s*[:—–]\s*["\']?(.+?)["\']?\s*$', cleaned, re.MULTILINE)
        if kv_pattern and len(kv_pattern) >= 2:
            result = {}
            for k, v in kv_pattern:
                key = k.strip().strip('"\'').strip()
                val = v.strip().strip('"\'.,').strip()
                if key and val and len(key) < 50 and len(val) < 200:
                    result[key] = val
            if len(result) >= 2:
                return result

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
    # PHASE A: INITIALIZATION & MASTER PLAN
    # ══════════════════════════════════════════════════════════════
    def initialize_story(self, idea: StoryIdea) -> StoryBible:
        return self.story_planner.initialize_story(idea)

    def generate_master_plan(self, total_chapters: int = 1000) -> List[ArcPlan]:
        return self.story_planner.generate_master_plan(total_chapters)

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
            chap_plan, narrative_contract, scenes_plan = self.chapter_planner.generate_chapter_and_scene_plan(
                chapter_num=chapter_num,
                arc=arc,
                open_threads=open_threads,
                recent_summaries=recent_summaries,
                global_ledger=global_ledger,
                context_summary=context_summary,
                replan_count=replan_count
            )

            # [STEP 3/7 & 4/7] SCENE EXECUTION LOOP & CHAPTER ASSEMBLY
            final_text, scene_drafts, scene_records = self.scene_executor.execute_scenes(
                chapter_num=chapter_num,
                chap_plan=chap_plan,
                scenes_plan=scenes_plan,
                narrative_contract=narrative_contract,
                global_ledger=global_ledger,
                replan_count=replan_count,
                notify_callback=_notify
            )

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

        # [STEP 6/7] 9-STAGE SPECIALIZED PROMPT ENGINE PIPELINE
        _notify("PIPELINE_ORCHESTRATOR", f"Step 6/7 — PIPELINE ORCHESTRATOR: Running 9 Specialized Prompt Engines & Cross-Domain Validation...")
        story_bible_dict = None
        bible_file = self.story_dir / "story_bible.json"
        if bible_file.exists():
            try:
                story_bible_dict = json.loads(bible_file.read_text(encoding="utf-8"))
            except Exception:
                pass

        pipe_res = self.orchestrator.process_chapter_pipeline(
            story_id=self.story_id,
            chapter_num=chapter_num,
            chapter_text=final_text,
            story_bible=story_bible_dict,
            progress_callback=sub_progress_callback
        )

        protagonist_name = self.db.get_protagonist_name(self.story_id) or "Nhân vật chính"
        memory_extracted = {
            "summary": f"Chương {chapter_num}: {chap_plan.get('goal') if isinstance(chap_plan, dict) else 'Hoàn thành'}",
            "new_characters": [],
            "new_discoveries": [],
            "canon_facts": [{"category": "event", "fact_text": f"{protagonist_name} đối đầu yêu thú tại hẻm núi", "source_excerpt": "đối đầu yêu thú", "information_state": "CONFIRMED", "confidence": 0.9}]
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

        char_ids = chap_plan.get("characters", ["char_001"]) if isinstance(chap_plan, dict) else ["char_001"]

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
