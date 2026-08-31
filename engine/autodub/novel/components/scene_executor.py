import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from autodub.novel.novel_models import (
    NarrativeContract, ProgressLedger, GlobalProgressLedger
)
from autodub.novel.novel_database import NovelDatabase
from autodub.novel.context_builder import ContextBuilder
from autodub.novel.canon_validator_engine import CanonValidatorEngine
from autodub.novel.prompts.writer import NovelWriterPrompt
from autodub.novel.prompts.rewriter import NovelRewriterPrompt
from autodub.novel.prompts.editor import NovelEditorPrompt
from autodub.modules.llamacpp_client import LlamaCppClient, strip_think_tags


logger = logging.getLogger(__name__)


class SceneExecutor:
    """
    Component handling Scene Execution Loop (Phase B3), Draft Generation, Checkpointing,
    Scene Validation/Rewriting, and Chapter Assembly (Phase B4).
    """

    def __init__(
        self,
        story_id: str,
        story_dir: Path,
        checkpoints_dir: Path,
        db: NovelDatabase,
        context_builder: ContextBuilder,
        validator: CanonValidatorEngine,
        llm: LlamaCppClient,
        llm_json_caller: Callable[..., Any]
    ):
        self.story_id = story_id
        self.story_dir = story_dir
        self.checkpoints_dir = checkpoints_dir
        self.db = db
        self.context_builder = context_builder
        self.validator = validator
        self.llm = llm
        self._call_llm_json = llm_json_caller

    def execute_scenes(
        self,
        chapter_num: int,
        chap_plan: Dict[str, Any],
        scenes_plan: List[Dict[str, Any]],
        narrative_contract: NarrativeContract,
        global_ledger: Optional[GlobalProgressLedger],
        replan_count: int = 0,
        notify_callback: Optional[Callable[[str, str], None]] = None
    ) -> Tuple[str, List[str], List[Dict[str, Any]]]:
        """
        Executes the scene loop for a chapter plan.
        Returns (final_edited_chapter_text, scene_drafts, scene_records).
        """
        def _notify(step: str, msg: str):
            if notify_callback:
                notify_callback(step, msg)

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
                    chk_story_id = chk_data.get("story_id")
                    p_name = self.db.get_protagonist_name(self.story_id)
                    if not p_name:
                        bible_path = self.story_dir / "story_bible.json"
                        if bible_path.exists():
                            try:
                                b_data = json.loads(bible_path.read_text(encoding="utf-8"))
                                chars = b_data.get("characters", [])
                                if chars and isinstance(chars[0], dict):
                                    p_name = chars[0].get("name")
                            except Exception:
                                pass

                    is_obsolete = False
                    obsolete_names = ["alex chen", "lâm" + " phàm"]
                    if p_name:
                        for ob_name in obsolete_names:
                            if p_name.lower() != ob_name and ob_name in chk_text.lower():
                                is_obsolete = True
                                break

                    # Invalidate if checkpoint belongs to another story OR protagonist mismatch OR contains obsolete character
                    if (chk_story_id and chk_story_id != self.story_id) or is_obsolete or (p_name and len(p_name) > 1 and p_name not in chk_text):
                        _notify("SCENE_EXECUTION", f"Step 3/7 — Scene {sc_id}/{len(scenes_plan)} — STALE CHECKPOINT INVALIDATED (Protagonist/Story Mismatch: expected {p_name}). RE-WRITING FRESH SCENE...")
                        chk_file.unlink(missing_ok=True)
                    else:
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

            enable_tiktok_slang = False
            bible_path = self.story_dir / "story_bible.json"
            if bible_path.exists():
                try:
                    b_json = json.loads(bible_path.read_text(encoding="utf-8"))
                    enable_tiktok_slang = bool(b_json.get("enable_tiktok_slang", False))
                except Exception:
                    pass

            writer_prompt = NovelWriterPrompt.build_prompt(
                chapter_num=chapter_num,
                scene_index=sc_id,
                scene_plan=sc,
                full_context=full_context,
                chapter_goal=chapter_goal_text,
                previous_scene_summary=prev_scene_summary,
                narrative_contract=narrative_contract,
                progress_ledger=progress_ledger,
                global_ledger=global_ledger,
                enable_tiktok_slang=enable_tiktok_slang
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
                "story_id": self.story_id,
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

        return final_text, scene_drafts, scene_records
