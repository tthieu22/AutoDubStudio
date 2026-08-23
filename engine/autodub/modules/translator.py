import json
import logging
import os
import re
import time
import urllib.request
import urllib.error
import socket
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from autodub.config import DEFAULT_TRANSLATION_MODEL, DEFAULT_TRANSLATION_LANGUAGE
from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.pipeline.progress import emit_event
from autodub.modules.transcriber import format_srt_timestamp, validate_srt_content
from autodub.modules.ollama_client import OllamaClient
from autodub.modules.structured_parser import StructuredParser
from autodub.modules.output_sanitizer import TranslationOutputSanitizer
from autodub.modules.translator_qa import TranslationQaChecker
from autodub.modules.translator_repair import TranslationRepairService
from autodub.modules.style_profiles import TranslationStyleProfileLoader
from autodub.modules.character_memory import CharacterEraMemory
from autodub.exceptions import (
    AutoDubError,
    PipelineCancelledError,
    OllamaUnavailableError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    TranslationFailedError
)

logger = logging.getLogger("autodub")
socket_timeout_types = (socket.timeout, TimeoutError)




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


class RealTranslator:
    """Real Local Translation Engine using Ollama REST API.
    Features:
    - Central model configuration (default qwen3:4b, zh-vi).
    - ContextBuilder (+/- 3 lines).
    - Entity Memory (Priority over LLM: Prompted as LOCKED ENTITY).
    - Structured JSON Parser with Retry & HUMAN_REVIEW fallback.
    - Format Output Sanitizer.
    - 7-Point QA Verification & 1-Pass AI Repair.
    """

    def __init__(
        self,
        step_delay: float = 0.0,
        model_name: Optional[str] = None,
        source_language: str = "zh",
        target_language: str = "vi",
        base_url: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 2,
        client: Optional[OllamaClient] = None
    ):
        self.step_delay = step_delay
        self.model_name = model_name or DEFAULT_TRANSLATION_MODEL
        self.source_language = source_language
        self.target_language = target_language
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = client if client is not None else OllamaClient(base_url=base_url)

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
        """
        Translates a single subtitle text with context, locked entity memory, glossary, style profile, structured JSON parsing, sanitizer, and 7-Point QA.
        Returns (final_translation, status, qa_result).
        Status options: 'QA_PASS', 'REPAIR_PASS', 'HUMAN_REVIEW'.
        """
        target_model = model or self.model_name
        prev_str = "\n".join(prev_context) if prev_context else "N/A"
        next_str = "\n".join(next_context) if next_context else "N/A"

        # 1. System Translation Rules
        system_rules = "SYSTEM TRANSLATION RULES:\n- Translate Chinese subtitle dialogue into natural, fluent Vietnamese spoken text.\n- Maintain 0% foreign text leakage and output strictly valid JSON."

        # 2. Translation Style Profile
        style_data = TranslationStyleProfileLoader.get_profile(translation_style, custom_translation_style)
        style_block = f"TRANSLATION STYLE PROFILE ({style_data['name'].upper()}):\n{style_data['prompt_instruction']}"

        # 3. Character / Era Memory
        char_block = CharacterEraMemory.format_character_era_prompt(character_metadata)

        # 4. Locked Entity Memory
        entity_prompt_block = ""
        if locked_entities:
            entity_lines = [f"- {zh} = {vi}" for zh, vi in locked_entities.items()]
            entity_prompt_block = "LOCKED ENTITY MEMORY (MUST STRICTLY FOLLOW):\n" + "\n".join(entity_lines) + "\n"

        # 5. Glossary
        glossary_block = ""
        if glossary:
            glossary_lines = [f"- {zh} = {vi}" for zh, vi in glossary.items()]
            glossary_block = "GLOSSARY TERMINOLOGY:\n" + "\n".join(glossary_lines) + "\n"

        # Strict Prompt Construction with 9-Point Priority Order
        prompt = f"""# CHINESE TO VIETNAMESE SUBTITLE TRANSLATION

1. {system_rules}

2. {style_block}

3. {char_block if char_block else 'CHARACTER / ERA MEMORY: Standard'}

4. {entity_prompt_block if entity_prompt_block else 'LOCKED ENTITY MEMORY: None'}

5. {glossary_block if glossary_block else 'GLOSSARY: None'}

6. PREVIOUS SUBTITLES (+/-3 LINES):
{prev_str}

7. CURRENT CHINESE SUBTITLE TO TRANSLATE:
"{text}"

8. NEXT SUBTITLES (+/-3 LINES):
{next_str}

9. OUTPUT REQUIREMENTS:
- Return ONLY a JSON object formatted as: {{"translation": "YOUR_VIETNAMESE_TRANSLATION"}}
- Do NOT add explanations, extra keys, commentary, or markdown blocks."""

        system_prompt = "You are an expert Chinese to Vietnamese subtitle translator. You MUST ALWAYS translate Chinese text into natural Vietnamese spoken dialogue. Output valid JSON only."

        # Structured JSON generation with retry
        raw_response = ""
        translation_candidate = ""
        parse_success = False

        for attempt in range(1, self.max_retries + 2):
            try:
                raw_response = self.client.generate(
                    prompt=prompt,
                    system=system_prompt,
                    model=target_model,
                    temperature=0.15,
                    format_json=True,
                    timeout=self.timeout
                )
                valid, extracted_text, err_msg = StructuredParser.parse_translation_response(raw_response)
                if valid:
                    translation_candidate = TranslationOutputSanitizer.sanitize(extracted_text)
                    parse_success = True
                    break
                else:
                    logger.warning(f"JSON Parse attempt #{attempt} failed: {err_msg}")
            except Exception as e:
                logger.warning(f"Generate attempt #{attempt} failed: {e}")

        if not parse_success:
            logger.error(f"Structured JSON output parsing failed after retries for segment '{text}'")
            return text, "HUMAN_REVIEW", {
                "score": 0,
                "status": "FAIL",
                "issues": [{"type": "JSON_PARSER_FAILURE", "severity": "ERROR", "message": "Failed to parse structured JSON from Ollama"}]
            }

        # Step: 7-Point QA Verification #1
        segment_dict = {"id": 1, "text": text, "translated_text": translation_candidate}
        qa1_result = TranslationQaChecker.check_segment(
            segment_dict,
            context_prev=prev_str,
            context_next=next_str,
            locked_entities=locked_entities
        )

        if qa1_result["status"] == "PASS":
            return translation_candidate, "QA_PASS", qa1_result

        # Step: 1-Pass AI Repair
        repair_service = TranslationRepairService(ollama_client=self.client, model_name=target_model)
        repair_res = repair_service.repair_segment(
            segment_dict,
            issues=qa1_result["issues"],
            prev_context=prev_context,
            next_context=next_context,
            locked_entities=locked_entities,
            glossary=glossary,
            translation_style=translation_style,
            custom_translation_style=custom_translation_style,
            character_metadata=character_metadata
        )

        if repair_res["decision"] == "AUTO_ACCEPT":
            return repair_res["repaired_translation"], "REPAIR_PASS", {
                "score": repair_res["qa_score_after"],
                "status": "PASS",
                "issues": []
            }
        else:
            return translation_candidate, "HUMAN_REVIEW", qa1_result

    def run(
        self,
        project: Project,
        is_cancelled: Optional[Callable[[], bool]] = None,
        fail_at_step: Optional[int] = None,
        force: bool = False
    ) -> float:
        """Run translation stage on project with checkpoints, retry, and cancellation support."""
        stage_name = PipelineStage.TRANSLATE.value
        stage_info = project.get_stage_info(stage_name)
        start_time = time.time()

        transcript_dir = project.project_dir / "transcript"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        translated_srt_path = transcript_dir / "translated.srt"
        partial_json_path = transcript_dir / "translation.partial.json"

        # Read configured model & translation style from project settings
        settings_dict = project.data.get("settings", {})
        config_dict = project.data.get("config", {})

        model_name = (
            settings_dict.get("translation_model")
            or config_dict.get("translation", {}).get("model")
            or self.model_name
        )

        translation_style = (
            settings_dict.get("translation_style")
            or config_dict.get("translation_style")
            or "general"
        )
        custom_translation_style = (
            settings_dict.get("custom_translation_style")
            or config_dict.get("custom_translation_style")
        )

        # Load Entity Memory, Glossary & Character Metadata from project metadata if present
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

        # 1. Idempotency Check
        if not force and stage_info.get("status") == StageStatus.COMPLETED.value and translated_srt_path.exists():
            logger.info("Existing valid translated SRT found. Skipping translation stage.")
            emit_event("progress", stage_name, current=100, total=100, percent=100.0, message="Existing valid translated SRT found.")
            emit_event("stage_complete", stage_name, current=100, total=100, percent=100.0)
            return 0.0

        # 2. Ollama Availability Check
        available, err_msg = self.client.check_availability(model_name)
        if not available:
            project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
            emit_event("stage_error", stage_name, error=err_msg)
            if "not running" in err_msg.lower():
                raise OllamaUnavailableError(err_msg)
            elif "not installed" in err_msg.lower():
                raise OllamaModelNotFoundError(err_msg)
            else:
                raise AutoDubError(err_msg)

        # 3. Load Source Segments
        segments = project.data.get("segments", [])
        if not segments:
            original_srt_path = transcript_dir / "original.srt"
            if original_srt_path.exists():
                segments = self._parse_srt(original_srt_path)

        total_segments = len(segments)
        if total_segments == 0:
            logger.warning("No segments found for translation.")
            with open(translated_srt_path, "w", encoding="utf-8") as f:
                f.write("")
            project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=0, total=0)
            emit_event("stage_complete", stage_name, current=0, total=0, percent=100.0)
            return 0.0

        # 4. Load Partial Checkpoint
        completed_segment_ids = set()
        translations_dict: Dict[str, Dict[str, Any]] = {}
        if not force and partial_json_path.exists():
            try:
                with open(partial_json_path, "r", encoding="utf-8") as f:
                    ckpt = json.load(f)
                    completed_segment_ids = set(ckpt.get("completed_segments", []))
                    translations_dict = ckpt.get("translations", {})
            except Exception as e:
                logger.warning(f"Failed to read translation partial checkpoint ({e}). Starting fresh.")

        # 5. Execute Translation Loop per Segment with Context
        project.update_stage(stage_name, StageStatus.RUNNING.value, current=len(completed_segment_ids), total=total_segments)
        emit_event("stage_start", stage_name, current=len(completed_segment_ids), total=total_segments)

        for idx, seg in enumerate(segments):
            seg_id = seg.get("id", idx + 1)
            if str(seg_id) in completed_segment_ids:
                continue

            if is_cancelled and is_cancelled():
                project.update_stage(stage_name, StageStatus.CANCELLED.value, current=len(completed_segment_ids), total=total_segments)
                emit_event("stage_cancelled", stage_name, current=len(completed_segment_ids), total=total_segments, error="Translation stage cancelled by user.")
                self._save_partial_checkpoint(partial_json_path, list(completed_segment_ids), translations_dict, model_name)
                raise PipelineCancelledError("Translation stage cancelled by user.")

            text = seg.get("text", "").strip()
            if not text:
                translations_dict[str(seg_id)] = {"translation": "", "status": "QA_PASS", "qa_score": 100}
                completed_segment_ids.add(str(seg_id))
                continue

            prev_ctx, next_ctx = ContextBuilder.get_context(segments, idx, window=3)

            final_trans, qa_status, qa_info = self.translate_segment_single(
                text=text,
                prev_context=prev_ctx,
                next_context=next_ctx,
                locked_entities=entity_memory,
                glossary=glossary,
                translation_style=translation_style,
                custom_translation_style=custom_translation_style,
                character_metadata=character_metadata,
                model=model_name
            )

            translations_dict[str(seg_id)] = {
                "translation": final_trans,
                "status": qa_status,
                "qa_score": qa_info.get("score", 100),
                "issues": qa_info.get("issues", [])
            }
            completed_segment_ids.add(str(seg_id))

            self._save_partial_checkpoint(partial_json_path, list(completed_segment_ids), translations_dict, model_name)

            completed_count = len(completed_segment_ids)
            percent = (completed_count / total_segments) * 100.0
            project.update_stage(stage_name, StageStatus.RUNNING.value, progress=int(percent), current=completed_count, total=total_segments)
            emit_event("progress", stage_name, current=completed_count, total=total_segments, percent=percent)

        # 6. Update Project Data & Save Results
        updated_segments = []
        translation_json_list = []
        for seg in segments:
            seg_id = seg.get("id")
            seg_info = translations_dict.get(str(seg_id), {"translation": seg.get("text", ""), "status": "QA_PASS"})
            trans_val = seg_info["translation"]
            qa_status = seg_info.get("status", "QA_PASS")

            seg_copy = dict(seg)
            seg_copy["translation"] = trans_val
            seg_copy["translated_text"] = trans_val
            seg_copy["tts_text"] = trans_val
            seg_copy["qa_status"] = qa_status

            updated_segments.append(seg_copy)
            translation_json_list.append({
                "id": seg_id,
                "start": seg.get("start"),
                "end": seg.get("end"),
                "text": seg.get("text"),
                "translated_text": trans_val,
                "tts_text": trans_val,
                "qa_status": qa_status,
                "qa_score": seg_info.get("qa_score", 100)
            })

        project.data["segments"] = updated_segments
        if "metadata" not in project.data:
            project.data["metadata"] = {}

        project.data["metadata"]["translation"] = {
            "provider": "ollama",
            "model": model_name,
            "source_language": self.source_language,
            "target_language": self.target_language
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

        project.save()

        elapsed = time.time() - start_time
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
