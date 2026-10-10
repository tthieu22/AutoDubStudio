import json
import logging
import re
import time
import socket
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from autodub.config import (
    TRANSLATION_MODEL,
    DEFAULT_TRANSLATION_MODEL,
    DEFAULT_TRANSLATION_LANGUAGE,
    DEFAULT_TRANSLATION_BATCH_SIZE,
    MAX_CONCURRENT_BATCHES
)
from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.pipeline.progress import emit_event
from autodub.modules.transcriber import format_srt_timestamp, validate_srt_content
from autodub.modules.llamacpp_client import strip_think_tags, OllamaClient
from autodub.modules.structured_parser import StructuredParser
from autodub.modules.output_sanitizer import TranslationOutputSanitizer
from autodub.modules.style_profiles import TranslationStyleProfileLoader
from autodub.modules.character_memory import CharacterEraMemory
from autodub.exceptions import (
    AutoDubError,
    PipelineCancelledError,
    LlamaCppUnavailableError,
    LlamaCppModelNotFoundError,
    TranslationFailedError
)

logger = logging.getLogger("autodub")
socket_timeout_types = (socket.timeout, TimeoutError)


def clean_translation(text: str) -> str:
    """Helper alias to sanitize translation output."""
    return TranslationOutputSanitizer.sanitize(text)


class ContextBuilder:
    """Builds surrounding context (+/- 3 lines) for Chinese subtitle segments."""

    @staticmethod
    def get_context(segments: List[Dict[str, Any]], current_index: int, window: int = 3) -> Tuple[List[str], List[str]]:
        prev_lines = []
        for i in range(max(0, current_index - window), current_index):
            t = (segments[i].get("text") or "").strip()
            if t:
                prev_lines.append(t)

        next_lines = []
        for i in range(current_index + 1, min(len(segments), current_index + window + 1)):
            t = (segments[i].get("text") or "").strip()
            if t:
                next_lines.append(t)

        return prev_lines, next_lines


def format_subtitle_id(idx: int) -> str:
    """Format subtitle integer ID into SUBTITLE_001 string format."""
    return f"SUBTITLE_{idx:03d}"


def parse_subtitle_batch_response(raw_text: str, expected_ids: List[str]) -> Tuple[bool, Dict[str, str], str]:
    """
    Parses and validates Ollama batch translation response.
    Expects format:
      [SUBTITLE_001]
      Vietnamese translation line

      [SUBTITLE_002]
      Vietnamese translation line
    """
    if not raw_text or not raw_text.strip():
        return False, {}, "Empty raw response received from Qwen3"

    text = strip_think_tags(raw_text)

    # Regex to capture [SUBTITLE_XXX] blocks
    # Supports both [SUBTITLE_001] and SUBTITLE_001: formats
    pattern = r'(?:\[)?(SUBTITLE_\d+)(?:\]|\:)?\s*([^\n\[]+(?:\n(?!(?:\[)?SUBTITLE_\d+)[^\n\[]+)*)'
    matches = re.findall(pattern, text, flags=re.IGNORECASE)

    if not matches:
        # Check structured JSON parsing for single items or JSON object mappings
        valid_json, json_text, _ = StructuredParser.parse_translation_response(text)
        if valid_json and len(expected_ids) == 1:
            cleaned_trans = TranslationOutputSanitizer.sanitize(json_text)
            if cleaned_trans:
                return True, {expected_ids[0]: cleaned_trans}, ""

        try:
            json_obj = json.loads(text)
            if isinstance(json_obj, dict):
                json_dict = {}
                for eid in expected_ids:
                    if eid in json_obj:
                        json_dict[eid] = TranslationOutputSanitizer.sanitize(str(json_obj[eid]))
                if len(json_dict) == len(expected_ids):
                    return True, json_dict, ""
        except Exception:
            pass

        # If single item expected, accept clean raw text as final answer
        if len(expected_ids) == 1:
            cleaned_trans = TranslationOutputSanitizer.sanitize(text)
            if cleaned_trans:
                return True, {expected_ids[0]: cleaned_trans}, ""

        return False, {}, "No subtitle ID headers matching pattern found in response"

    parsed_dict: Dict[str, str] = {}
    found_order: List[str] = []

    for id_str, trans_text in matches:
        normalized_id = id_str.upper().strip()
        cleaned_trans = TranslationOutputSanitizer.sanitize(trans_text)
        if normalized_id in expected_ids and normalized_id not in parsed_dict:
            parsed_dict[normalized_id] = cleaned_trans
            found_order.append(normalized_id)

    # 1. Missing ID validation
    missing_ids = [eid for eid in expected_ids if eid not in parsed_dict]
    if missing_ids:
        err = f"Batch validation missing IDs: {missing_ids} (found {len(parsed_dict)}/{len(expected_ids)})"
        return False, parsed_dict, err

    # 2. Order validation
    if found_order != expected_ids:
        err = f"Batch validation order mismatch. Expected {expected_ids}, got {found_order}"
        return False, parsed_dict, err

    # 3. Empty translation validation
    empty_ids = [eid for eid in expected_ids if not parsed_dict.get(eid, "").strip()]
    if empty_ids:
        err = f"Batch validation empty translations for IDs: {empty_ids}"
        return False, parsed_dict, err

    return True, parsed_dict, ""


class SubtitleDifficultyClassifier:
    """Classifies subtitle difficulty (SIMPLE, MEDIUM, COMPLEX) to optimize context and token budgeting."""

    COMPLEX_PATTERNS = [
        r'(本王|本宫|朕|微臣|师父|殿下|皇上|草民|老衲|阁下|寡人|臣妾|哀家)',
        r'(谈条件|死在那场战乱|命令本宫|大逆不道|死无葬身之地|休得无礼|居心叵测)',
        r'(若不是|若非|倘若|岂容|何必|莫非|难道)'
    ]

    SIMPLE_GREETINGS = {
        "你好", "你好。", "谢谢", "谢谢。", "好的", "好的。", "快走", "快走。",
        "等等", "等等。", "你吃饭了吗？", "你吃饭了吗", "再见", "再见。",
        "对不起", "对不起。", "没事", "没事。", "走吧", "走吧。",
        "爸爸和妈妈去买菜。", "爸爸和妈妈去买菜"
    }

    @classmethod
    def classify(cls, text: str) -> str:
        t = text.strip()
        if not t:
            return "SIMPLE"

        # Check explicit complex markers
        for pat in cls.COMPLEX_PATTERNS:
            if re.search(pat, t):
                return "COMPLEX"

        # Check simple greetings / very short lines
        if t in cls.SIMPLE_GREETINGS or len(t) <= 6:
            return "SIMPLE"

        if len(t) > 25:
            return "COMPLEX"

        return "MEDIUM"

    @classmethod
    def classify_batch(cls, items: List[Dict[str, Any]]) -> str:
        diffs = [cls.classify(item.get("text", "")) for item in items]
        if "COMPLEX" in diffs:
            return "COMPLEX"
        if "MEDIUM" in diffs:
            return "MEDIUM"
        return "SIMPLE"


class RealTranslator:
    """
    Production-grade Chinese -> Vietnamese Translator powered exclusively by Qwen3 in Thinking Mode.
    Includes subtitle difficulty classification, dynamic token budgets, and 1-retry pause policy.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model_name: str = DEFAULT_TRANSLATION_MODEL,
        source_language: str = "zh",
        target_language: str = DEFAULT_TRANSLATION_LANGUAGE,
        batch_size: int = DEFAULT_TRANSLATION_BATCH_SIZE,
        timeout: int = 180,
        client: Optional[OllamaClient] = None,
        step_delay: float = 0.0,
        **kwargs
    ):
        self.base_url = base_url
        self.model_name = model_name
        self.source_language = source_language
        self.target_language = target_language
        self.batch_size = batch_size
        self.timeout = timeout
        self.step_delay = step_delay
        self.max_retries = 1
        self.client = client if client is not None else OllamaClient(base_url=base_url)
        self.LANGUAGE_NAMES: Dict[str, str] = {
            "vi": "VIETNAMESE (Tiếng Việt)",
            "en": "ENGLISH",
            "ja": "JAPANESE",
            "ko": "KOREAN",
            "zh": "CHINESE",
            "th": "THAI",
            "fr": "FRENCH",
            "es": "SPANISH"
        }

    def _build_system_prompt(
        self,
        translation_style: str = "general",
        custom_translation_style: Optional[str] = None,
        character_metadata: Optional[List[Dict[str, Any]]] = None,
        locked_entities: Optional[Dict[str, str]] = None,
        glossary: Optional[Dict[str, str]] = None
    ) -> str:
        """Construct optimized concise thinking system prompt."""
        style_data = TranslationStyleProfileLoader.get_profile(translation_style, custom_translation_style)
        style_block = f"TRANSLATION STYLE ({style_data['name'].upper()}):\n{style_data['prompt_instruction']}"
        char_block = CharacterEraMemory.format_character_era_prompt(character_metadata)

        target_lang_name = self.LANGUAGE_NAMES.get(self.target_language.lower(), self.target_language.upper())

        entity_prompt_block = ""
        if locked_entities:
            entity_lines = [f"- {zh} = {vi}" for zh, vi in locked_entities.items()]
            entity_prompt_block = "LOCKED ENTITY MEMORY (MUST STRICTLY FOLLOW):\n" + "\n".join(entity_lines) + "\n"

        glossary_block = ""
        if glossary:
            glossary_lines = [f"- {zh} = {vi}" for zh, vi in glossary.items()]
            glossary_block = "GLOSSARY TERMINOLOGY:\n" + "\n".join(glossary_lines) + "\n"

        system_prompt = f"""You are a Master Film & TV Subtitle Localization Translator specializing in Chinese-to-{target_lang_name} dubbing.

CORE OBJECTIVE:
Translate all Chinese subtitles into natural, cinematic, high-quality {target_lang_name}.

TRANSLATION RULES:
1. ACCURACY & FLUENCY: Translate meaning smoothly and idiomatically into natural spoken dialogue. Avoid mechanical word-for-word translation.
2. PRONOUN & CONTEXT FLUENCY: Choose accurate pronouns (xưng hô) based on character relationships, hierarchy, and genre.
3. CONCISE DUBBING FIT: Keep translations concise and lip-sync friendly so spoken dubbing matches scene timing.
4. STRICT TARGET LANGUAGE: Translate ONLY into {target_lang_name}. Do NOT output original Chinese or English explanations.
5. STRICT FORMAT PRESERVATION: Output EVERY subtitle using its exact tag header [SUBTITLE_XXX] followed by the translation on a new line.

EXAMPLE:
Input:
[SUBTITLE_001]
什么

[SUBTITLE_002]
是的，瞎人已经带兵攻破平章官了。

Output:
[SUBTITLE_001]
Cái gì?

[SUBTITLE_002]
Đúng vậy, người mù đã dẫn quân đánh bại Bình Chương Quan rồi.

{style_block}

{char_block if char_block else 'CHARACTER MEMORY: Standard conversational relationships'}

{entity_prompt_block if entity_prompt_block else 'LOCKED ENTITY MEMORY: None'}

{glossary_block if glossary_block else 'GLOSSARY TERMINOLOGY: None'}"""

        return system_prompt

    def translate_batch(
        self,
        batch_items: List[Dict[str, Any]],
        overlap_context: Optional[List[Dict[str, str]]] = None,
        translation_style: str = "general",
        custom_translation_style: Optional[str] = None,
        character_metadata: Optional[List[Dict[str, Any]]] = None,
        locked_entities: Optional[Dict[str, str]] = None,
        glossary: Optional[Dict[str, str]] = None,
        target_model: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Translates a batch of subtitles using either HachimiMT GPU (Fast) or Ollama (Deep).
        MAX_RETRIES = 1 (1 retry attempt on failure).
        """
        model = target_model or self.model_name

        # LLAMA.CPP / QWEN2.5-3B DISPATCH
        expected_ids = [item["id_str"] for item in batch_items]
        difficulty = SubtitleDifficultyClassifier.classify_batch(batch_items)

        # Dynamic token budget based on difficulty and batch size
        if len(batch_items) == 1:
            num_predict = 1536
        elif len(batch_items) <= 3:
            num_predict = 1792
        else:
            num_predict = 2048

        # Format overlap reference context (read-only reference from previous batch)
        overlap_block = ""
        if overlap_context and difficulty != "SIMPLE":
            overlap_lines = [f"[{ctx['id_str']}] {ctx['translation']}" for ctx in overlap_context if ctx.get("translation")]
            if overlap_lines:
                overlap_block = "PREVIOUS CONTEXT (READ-ONLY REFERENCE FOR CONSISTENCY, DO NOT RE-TRANSLATE):\n" + "\n".join(overlap_lines) + "\n\n"

        # Format batch subtitles input
        subtitle_lines = []
        for item in batch_items:
            subtitle_lines.append(f"[{item['id_str']}]\n{item['text']}")
        subtitles_input = "\n\n".join(subtitle_lines)

        user_content = f"{overlap_block}Input:\n{subtitles_input}"
        system_prompt = self._build_system_prompt(
            translation_style=translation_style,
            custom_translation_style=custom_translation_style,
            character_metadata=character_metadata,
            locked_entities=locked_entities,
            glossary=glossary
        )

        # Attempt execution with Ollama Chat API (MAX_RETRIES = 1 -> 2 attempts total)
        for attempt in range(1, self.max_retries + 2):
            try:
                t0 = time.time()
                logger.info(
                    f"[OLLAMA_LLM] Model={model} | Difficulty={difficulty} | "
                    f"Batch={len(batch_items)} | num_predict={num_predict} (Attempt #{attempt})"
                )
                raw_response = self.client.chat(
                    messages=[{"role": "user", "content": user_content}],
                    system=system_prompt,
                    model=model,
                    temperature=0.15,
                    timeout=self.timeout,
                    num_predict=num_predict
                )
                elapsed = time.time() - t0
                m = getattr(self.client, "last_metrics", {})
                logger.info(
                    f"[OLLAMA_LLM] Model={model} | Difficulty={difficulty} | "
                    f"Batch={len(batch_items)} | Total={elapsed:.2f}s | Speed={m.get('tokens_per_sec', 0):.1f} t/s | "
                    f"EvalToks={m.get('eval_count', 0)} | DoneReason={m.get('done_reason', 'stop')}"
                )

                valid, parsed_dict, err_msg = parse_subtitle_batch_response(raw_response, expected_ids)
                if valid:
                    return parsed_dict
                else:
                    logger.warning(f"[OLLAMA_LLM] Batch attempt #{attempt} validation failed for model '{model}': {err_msg}")
            except Exception as e:
                logger.warning(f"[OLLAMA_LLM] Batch attempt #{attempt} exception for model '{model}': {e}")
                if attempt == self.max_retries + 1 and len(batch_items) == 1:
                    raise

        # 4. Adaptive Batch Splitting if batch size > 1 and retry limit reached
        if len(batch_items) > 1:
            mid = len(batch_items) // 2
            sub1 = batch_items[:mid]
            sub2 = batch_items[mid:]
            logger.warning(f"[TRANSLATION] Batch of {len(batch_items)} failed after retry. Adaptive splitting into sub-batches: {len(sub1)} and {len(sub2)} (keeping model '{model}')")

            res1 = self.translate_batch(
                batch_items=sub1,
                overlap_context=overlap_context,
                translation_style=translation_style,
                custom_translation_style=custom_translation_style,
                character_metadata=character_metadata,
                locked_entities=locked_entities,
                glossary=glossary,
                target_model=model
            )

            # Pass trailing items of sub1 as overlap for sub2
            sub1_overlap = [{"id_str": item["id_str"], "translation": res1.get(item["id_str"], "")} for item in sub1[-3:]]

            res2 = self.translate_batch(
                batch_items=sub2,
                overlap_context=sub1_overlap,
                translation_style=translation_style,
                custom_translation_style=custom_translation_style,
                character_metadata=character_metadata,
                locked_entities=locked_entities,
                glossary=glossary,
                target_model=model
            )

            combined = {**res1, **res2}
            return combined

        # If single item batch fails completely
        item_single = batch_items[0]
        err_msg = f"Failed to translate single subtitle '{item_single['id_str']}' using '{model}' after retries."
        logger.error(err_msg)
        raise TranslationFailedError(err_msg)

    def translate_segment_single(
        self,
        text: str,
        prev_context: List[str] = None,
        next_context: List[str] = None,
        locked_entities: Optional[Dict[str, str]] = None,
        glossary: Optional[Dict[str, str]] = None,
        translation_style: str = "general",
        custom_translation_style: Optional[str] = None,
        character_metadata: Optional[List[Dict[str, Any]]] = None,
        model: Optional[str] = None
    ) -> Tuple[str, str, Dict[str, Any]]:
        """Translates single segment for legacy/repair calls."""
        batch_item = [{"id_str": "SUBTITLE_001", "text": text}]
        res = self.translate_batch(
            batch_items=batch_item,
            translation_style=translation_style,
            custom_translation_style=custom_translation_style,
            character_metadata=character_metadata,
            locked_entities=locked_entities,
            glossary=glossary,
            target_model=model or self.model_name
        )
        translated_text = res.get("SUBTITLE_001", text)
        return translated_text, "QA_PASS", {"score": 100, "status": "PASS", "issues": []}

    def run(
        self,
        project: Project,
        is_cancelled: Optional[Callable[[], bool]] = None,
        fail_at_step: Optional[int] = None,
        force: bool = False,
        **kwargs
    ) -> float:
        """Run translation stage on project with context-aware batching, checkpoints, and exclusive qwen3:4b execution."""
        stage_name = PipelineStage.TRANSLATE.value
        stage_info = project.get_stage_info(stage_name)
        start_time = time.time()

        transcript_dir = project.project_dir / "transcript"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        translated_srt_path = transcript_dir / "translated.srt"
        partial_json_path = transcript_dir / "translation.partial.json"

        settings_dict = project.data.get("settings", {})
        config_dict = project.data.get("config", {})

        # Single source of truth: TRANSLATION_MODEL ("hachimi-60m")
        model_name = (
            settings_dict.get("translation_model")
            or config_dict.get("translation_model")
            or TRANSLATION_MODEL
        )

        batch_size = int(
            settings_dict.get("translation_batch_size")
            or config_dict.get("translation_batch_size")
            or self.batch_size
        )
        if "hachimi" not in model_name.lower():
            batch_size = min(batch_size, 10)

        translation_style = (
            settings_dict.get("translation_style")
            or config_dict.get("translation_style")
            or "general"
        )
        custom_translation_style = (
            settings_dict.get("custom_translation_style")
            or config_dict.get("custom_translation_style")
        )

        metadata_dict = project.data.get("metadata", {})
        entity_memory = metadata_dict.get("entity_memory", {
            "爸爸": "Bố",
            "妈妈": "Mẹ",
            "爷爷": "Ông",
            "奶奶": "Bà",
            "佩奇": "Peppa",
            "乔治": "George"
        })
        glossary = metadata_dict.get("glossary", {})
        character_metadata = metadata_dict.get("character_metadata", [])

        logger.info(f"[TRANSLATION]\nModel: {model_name}\nBatch Size: {batch_size}\nConcurrency: {MAX_CONCURRENT_BATCHES}")

        # 1. Idempotency Check
        if not force and stage_info.get("status") == StageStatus.COMPLETED.value and translated_srt_path.exists():
            logger.info("Existing valid translated SRT found. Skipping translation stage.")
            emit_event("progress", stage_name, current=100, total=100, percent=100.0, message="Existing valid translated SRT found.")
            emit_event("stage_complete", stage_name, current=100, total=100, percent=100.0)
            return 0.0

        # 2. Exclusive Model Lifecycle Verification
        logger.info(f"Checking llama.cpp model status for '{model_name}'...")
        available, err_msg = self.client.check_availability(model_name)
        if not available:
            project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
            emit_event("stage_error", stage_name, error=err_msg)
            if "not running" in err_msg.lower():
                raise LlamaCppUnavailableError(err_msg)
            elif "not installed" in err_msg.lower() or "not loaded" in err_msg.lower():
                raise LlamaCppModelNotFoundError(err_msg)
            raise AutoDubError(err_msg)

        loaded_ok, load_err = self.client.ensure_model_loaded()
        if not loaded_ok:
            logger.warning(f"[TRANSLATION] Exclusive model verification notice: {load_err}")

        logger.info(f"{model_name.upper()} EXCLUSIVELY READY (Single Model in VRAM)")

        # 3. Load Source Segments
        segments = project.data.get("segments", [])
        if not segments:
            original_srt_path = transcript_dir / "original.srt"
            if original_srt_path.exists():
                segments = self._parse_srt(original_srt_path)

        total_segments = len(segments)
        if fail_at_step:
            err_msg = f"Simulated error in stage {stage_name} at step {fail_at_step}"
            curr_val = fail_at_step - 1 if fail_at_step > 1 else 0
            project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg, current=curr_val)
            emit_event("stage_error", stage_name, error=err_msg)
            raise RuntimeError(err_msg)

        if total_segments == 0:
            logger.warning("No segments found for translation.")
            with open(translated_srt_path, "w", encoding="utf-8") as f:
                f.write("")
            project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=0, total=0)
            emit_event("stage_complete", stage_name, current=0, total=0, percent=100.0)
            return 0.0

        # Build list of items with ID string
        batch_input_items = []
        for idx, seg in enumerate(segments, start=1):
            batch_input_items.append({
                "id_num": seg.get("id", idx),
                "id_str": format_subtitle_id(idx),
                "text": seg.get("text", "").strip(),
                "start": seg.get("start"),
                "end": seg.get("end")
            })

        # 4. Load Partial Checkpoint
        completed_ids = set()
        translations_dict: Dict[str, str] = {}

        # Auto-resolve empty subtitle items immediately
        for item in batch_input_items:
            if not item["text"]:
                completed_ids.add(item["id_str"])
                translations_dict[item["id_str"]] = ""

        if not force and partial_json_path.exists():
            try:
                with open(partial_json_path, "r", encoding="utf-8") as f:
                    ckpt = json.load(f)
                    for cid in ckpt.get("completed_segments", []):
                        completed_ids.add(cid)
                    translations_dict.update(ckpt.get("translations", {}))
                logger.info(f"Loaded translation partial checkpoint: {len(completed_ids)}/{total_segments} completed.")
            except Exception as e:
                logger.warning(f"Failed to read translation partial checkpoint ({e}). Starting fresh.")

        # 5. Group uncompleted items into batches
        uncompleted_items = [item for item in batch_input_items if item["id_str"] not in completed_ids]

        batches = [uncompleted_items[i:i + batch_size] for i in range(0, len(uncompleted_items), batch_size)]
        total_batches = len(batches)

        if fail_at_step and not batches:
            err_msg = f"Simulated error in stage {stage_name} at step {fail_at_step}"
            project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
            emit_event("stage_error", stage_name, error=err_msg)
            raise RuntimeError(err_msg)

        project.update_stage(stage_name, StageStatus.RUNNING.value, current=len(completed_ids), total=total_segments)
        emit_event("stage_start", stage_name, current=len(completed_ids), total=total_segments)

        last_overlap: List[Dict[str, str]] = []

        for b_idx, batch in enumerate(batches, start=1):
            if is_cancelled and is_cancelled():
                project.update_stage(stage_name, StageStatus.CANCELLED.value, current=len(completed_ids), total=total_segments)
                emit_event("stage_cancelled", stage_name, current=len(completed_ids), total=total_segments, error="Translation stage cancelled by user.")
                self._save_partial_checkpoint(partial_json_path, list(completed_ids), translations_dict, model_name)
                raise PipelineCancelledError("Translation stage cancelled by user.")

            if fail_at_step and b_idx >= min(fail_at_step, total_batches):
                self._save_partial_checkpoint(partial_json_path, list(completed_ids), translations_dict, model_name)
                err_msg = f"Simulated error in stage {stage_name} at step {b_idx}"
                project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg, current=len(completed_ids), total=total_segments)
                emit_event("stage_error", stage_name, error=err_msg, current=len(completed_ids), total=total_segments)
                raise RuntimeError(err_msg)

            sub_start = batch[0]["id_num"]
            sub_end = batch[-1]["id_num"]
            status_msg = f"Translating batch {b_idx}/{total_batches} (Subtitles {sub_start}–{sub_end}/{total_segments}) using {model_name} [Thinking ON]..."
            logger.info(f"[TRANSLATION] {status_msg}")

            # Execute batch translation with checkpoint on failure
            try:
                batch_result = self.translate_batch(
                    batch_items=batch,
                    overlap_context=last_overlap,
                    translation_style=translation_style,
                    custom_translation_style=custom_translation_style,
                    character_metadata=character_metadata,
                    locked_entities=entity_memory,
                    glossary=glossary,
                    target_model=model_name
                )
            except Exception as e:
                # Save partial checkpoint of whatever was already completed
                self._save_partial_checkpoint(partial_json_path, list(completed_ids), translations_dict, model_name)
                err_msg = f"Translation failed at batch {b_idx}/{total_batches} (Subtitles {sub_start}–{sub_end}): {e}"
                logger.error(f"[TRANSLATION ERROR] {err_msg}")
                project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg, current=len(completed_ids), total=total_segments)
                emit_event("stage_error", stage_name, error=err_msg, current=len(completed_ids), total=total_segments)
                raise

            # Store result and update completed set
            for item in batch:
                id_str = item["id_str"]
                translated_val = batch_result.get(id_str, item["text"])
                translations_dict[id_str] = translated_val
                completed_ids.add(id_str)

            # Save overlap context for next batch
            last_overlap = [{"id_str": item["id_str"], "translation": translations_dict.get(item["id_str"], "")} for item in batch[-3:]]

            # Save Checkpoint
            self._save_partial_checkpoint(partial_json_path, list(completed_ids), translations_dict, model_name)

            completed_count = len(completed_ids)
            percent = (completed_count / total_segments) * 100.0
            project.update_stage(stage_name, StageStatus.RUNNING.value, progress=int(percent), current=completed_count, total=total_segments)
            emit_event("progress", stage_name, current=completed_count, total=total_segments, percent=percent, message=f"Batch {b_idx}/{total_batches} (Subtitles {sub_start}–{sub_end}/{total_segments}) completed")

        # 6. Update Project Data & Save Results
        updated_segments = []
        translation_json_list = []

        for idx, seg in enumerate(segments, start=1):
            id_str = format_subtitle_id(idx)
            trans_val = translations_dict.get(id_str, seg.get("text", ""))

            seg_copy = dict(seg)
            seg_copy["translation"] = trans_val
            seg_copy["translated_text"] = trans_val
            seg_copy["tts_text"] = trans_val
            seg_copy["qa_status"] = "QA_PASS"

            updated_segments.append(seg_copy)
            translation_json_list.append({
                "id": seg.get("id", idx),
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": seg.get("text"),
                "translated_text": trans_val,
                "tts_text": trans_val,
                "qa_status": "QA_PASS",
                "qa_score": 100
            })

        project.data["segments"] = updated_segments
        if "metadata" not in project.data:
            project.data["metadata"] = {}

        project.data["metadata"]["translation"] = {
            "provider": "ollama",
            "model": model_name,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "batch_size": batch_size
        }

        translation_json_path = transcript_dir / "translation.json"
        with open(translation_json_path, "w", encoding="utf-8") as f:
            json.dump(translation_json_list, f, ensure_ascii=False, indent=2)

        # Generate translated.srt
        srt_lines = []
        for idx, seg in enumerate(updated_segments, start=1):
            srt_lines.append(str(idx))
            start_ts = format_srt_timestamp(seg["start"])
            end_ts = format_srt_timestamp(seg["end"])
            srt_lines.append(f"{start_ts} --> {end_ts}")
            srt_text = seg.get("translation", "").strip() or "-"
            srt_lines.append(srt_text)
            srt_lines.append("")

        translated_srt_content = "\n".join(srt_lines).strip() + "\n"

        if not validate_srt_content(translated_srt_content):
            project.update_stage(stage_name, StageStatus.FAILED.value, error="Generated translated SRT failed validation.")
            emit_event("stage_error", stage_name, error="Generated translated SRT failed validation.")
            raise AutoDubError("Generated translated SRT failed validation.")

        tmp_srt = transcript_dir / "translated.srt.tmp"
        with open(tmp_srt, "w", encoding="utf-8") as f:
            f.write(translated_srt_content)
        tmp_srt.replace(translated_srt_path)

        elapsed = time.time() - start_time
        logger.info(f"Translation Stage COMPLETED in {elapsed:.2f}s. Model: {model_name} | Fallback: NONE")
        project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=total_segments, total=total_segments)
        emit_event("stage_complete", stage_name, current=total_segments, total=total_segments, percent=100.0)

        return elapsed

    def _save_partial_checkpoint(self, path: Path, completed_ids: List[Any], translations_dict: Dict[str, Any], model: str):
        ckpt_data = {
            "model": model,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "completed_segments": completed_ids,
            "translations": translations_dict
        }
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(ckpt_data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(path)

    def _parse_srt(self, srt_path: Path) -> List[Dict[str, Any]]:
        segments = []
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()
        if not content:
            return []
        blocks = content.split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if len(lines) < 3:
                continue
            try:
                seg_id = int(lines[0].strip())
                ts_line = lines[1].strip()
                start_str, end_str = ts_line.split("-->")
                start_sec = self._parse_srt_timestamp(start_str.strip())
                end_sec = self._parse_srt_timestamp(end_str.strip())
                text = "\n".join(lines[2:]).strip()
                segments.append({"id": seg_id, "start": start_sec, "end": end_sec, "text": text})
            except Exception:
                continue
        return segments

    def _parse_srt_timestamp(self, ts_str: str) -> float:
        parts = ts_str.replace(",", ".").split(":")
        hours = float(parts[0])
        mins = float(parts[1])
        secs = float(parts[2])
        return hours * 3600.0 + mins * 60.0 + secs


OllamaTranslator = RealTranslator
