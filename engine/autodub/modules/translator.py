import json
import logging
import os
import re
import time
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Tuple

from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.pipeline.progress import emit_event
from autodub.modules.transcriber import format_srt_timestamp, validate_srt_content
from autodub.exceptions import (
    AutoDubError,
    PipelineCancelledError,
    OllamaUnavailableError,
    OllamaModelNotFoundError,
    OllamaTimeoutError,
    TranslationFailedError
)

logger = logging.getLogger("autodub")

def clean_translation(raw_text: str) -> str:
    """Clean raw LLM translation response."""
    if not raw_text:
        return ""
    
    text = raw_text.strip()
    
    # Remove markdown code blocks if wrapped
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 2:
            text = "\n".join(lines[1:-1]).strip()
            
    # Remove common prefix hallucinations like "Dịch:", "Bản dịch:", "Translation:"
    prefix_pattern = r'^(bản dịch|dịch|translation|vietnamese translation|việt nam):\s*'
    text = re.sub(prefix_pattern, '', text, flags=re.IGNORECASE).strip()
    
    # Strip surrounding quotes if matching
    if (text.startswith('"') and text.endswith('"')) or (text.startswith("'") and text.endswith("'")):
        text = text[1:-1].strip()
        
    return text

class OllamaClient:
    """HTTP client for communicating with local Ollama REST API server."""
    def __init__(self, base_url: Optional[str] = None):
        if not base_url:
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
        self.base_url = base_url.rstrip("/")

    def check_availability(self, model_name: str = "qwen2.5:3b") -> Tuple[bool, str]:
        """Check if Ollama is reachable and the specified model is installed."""
        url = f"{self.base_url}/api/tags"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AutoDubStudio"})
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status != 200:
                    return False, f"Ollama returned HTTP status {response.status}"
                data = json.loads(response.read().decode("utf-8"))
        except Exception as e:
            return False, f"Ollama is not running at {self.base_url}"

        models = data.get("models", [])
        installed_names = []
        for m in models:
            name = m.get("name", "")
            model_tag = m.get("model", "")
            installed_names.extend([name, model_tag])

        target_base = model_name.split(":")[0]
        found = False
        for installed in installed_names:
            if not installed:
                continue
            if installed == model_name or installed.startswith(f"{model_name}:"):
                found = True
                break
            if installed == target_base or installed.startswith(f"{target_base}:"):
                found = True
                break

        if not found:
            return False, f"Ollama model '{model_name}' is not installed."

        return True, ""

    def generate(self, prompt: str, system: Optional[str] = None, model: str = "qwen2.5:3b", timeout: int = 120) -> str:
        """Call Ollama /api/generate REST endpoint synchronously."""
        url = f"{self.base_url}/api/generate"
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.3
            }
        }
        if system:
            payload["system"] = system

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data_bytes,
            headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                if response.status != 200:
                    raise TranslationFailedError(f"Ollama returned HTTP error status {response.status}")
                res_data = json.loads(response.read().decode("utf-8"))
                return res_data.get("response", "")
        except urllib.error.URLError as e:
            if isinstance(e.reason, socket_timeout_types):
                raise OllamaTimeoutError(f"Ollama generate request timed out after {timeout} seconds.")
            raise OllamaUnavailableError(f"Failed to connect to Ollama: {e}")
        except Exception as e:
            if "timed out" in str(e).lower():
                raise OllamaTimeoutError(f"Ollama generate request timed out after {timeout} seconds.")
            raise TranslationFailedError(f"Ollama API request failed: {e}")

import socket
socket_timeout_types = (socket.timeout, TimeoutError)

class RealTranslator:
    """Real Local Translation module using Ollama REST API (Qwen2.5 3B)."""
    def __init__(
        self,
        step_delay: float = 0.0,
        model_name: str = "qwen2.5:3b",
        source_language: str = "en",
        target_language: str = "vi",
        base_url: Optional[str] = None,
        timeout: int = 120,
        max_retries: int = 3,
        client: Optional[OllamaClient] = None
    ):
        self.step_delay = step_delay
        self.model_name = model_name
        self.source_language = source_language
        self.target_language = target_language
        self.timeout = timeout
        self.max_retries = max_retries
        self.client = client if client is not None else OllamaClient(base_url=base_url)

    def translate_segments(
        self,
        segments: List[Dict[str, Any]],
        source_language: Optional[str] = None,
        target_language: Optional[str] = None,
        model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """API method for direct segment list translation."""
        src_lang = source_language or self.source_language
        tgt_lang = target_language or self.target_language
        mdl = model or self.model_name

        system_prompt = (
            f"You are a professional subtitle translator.\n"
            f"Translate the following subtitle segment from {src_lang} to {tgt_lang}.\n\n"
            f"Rules:\n"
            f"- Return ONLY the {tgt_lang} translation.\n"
            f"- Do not explain or add commentary.\n"
            f"- Do not enclose output in quotes, markdown code blocks, or tags.\n"
            f"- Preserve original meaning, names, and technical terms when appropriate.\n"
            f"- Keep output concise and natural for subtitles."
        )

        translated_segments = []
        for seg in segments:
            text = seg.get("text", "").strip()
            if not text:
                seg_copy = dict(seg)
                seg_copy["translation"] = ""
                translated_segments.append(seg_copy)
                continue

            raw_res = self.client.generate(prompt=text, system=system_prompt, model=mdl, timeout=self.timeout)
            cleaned = clean_translation(raw_res)
            seg_copy = dict(seg)
            seg_copy["translation"] = cleaned
            translated_segments.append(seg_copy)

        return translated_segments

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

        completed_segment_ids = set()
        translations_dict: Dict[str, str] = {}

        # Handle simulated step failure for pipeline state machine unit tests
        if fail_at_step is not None:
            err_msg = f"Simulated error in stage {stage_name} at step {fail_at_step}"
            failed_current = max(0, fail_at_step - 1)
            project.update_stage(stage_name, StageStatus.FAILED.value, current=failed_current, total=10, error=err_msg)
            emit_event("stage_error", stage_name, current=failed_current, total=10, error=err_msg)
            raise RuntimeError(err_msg)

        # 1. Idempotency Check
        if not force and stage_info.get("status") == StageStatus.COMPLETED.value and translated_srt_path.exists():
            logger.info("Existing valid translated SRT found. Skipping translation stage.")
            emit_event("progress", stage_name, current=100, total=100, percent=100.0, message="Existing valid translated SRT found.")
            emit_event("stage_complete", stage_name, current=100, total=100, percent=100.0)
            return 0.0

        # 2. Ollama Availability & Model Check
        available, err_msg = self.client.check_availability(self.model_name)
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
            # Fallback: parse original.srt if segments array is empty
            original_srt_path = transcript_dir / "original.srt"
            if original_srt_path.exists():
                segments = self._parse_srt(original_srt_path)

        total_segments = len(segments)

        if total_segments == 0:
            logger.warning("No segments found for translation. Creating empty translated SRT.")
            with open(translated_srt_path, "w", encoding="utf-8") as f:
                f.write("")
            project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=0, total=0)
            emit_event("stage_complete", stage_name, current=0, total=0, percent=100.0)
            return 0.0

        # 4. Load Partial Checkpoint
        completed_segment_ids = set()
        translations_dict: Dict[str, str] = {}
        if not force and partial_json_path.exists():
            try:
                with open(partial_json_path, "r", encoding="utf-8") as f:
                    ckpt = json.load(f)
                    completed_segment_ids = set(ckpt.get("completed_segments", []))
                    translations_dict = ckpt.get("translations", {})
                logger.info(f"Resuming translation checkpoint: {len(completed_segment_ids)}/{total_segments} segments completed.")
            except Exception as e:
                logger.warning(f"Failed to read translation partial checkpoint ({e}). Starting fresh.")

        # 5. Execute Stage Loop
        project.update_stage(stage_name, StageStatus.RUNNING.value, current=len(completed_segment_ids), total=total_segments)
        emit_event("stage_start", stage_name, current=len(completed_segment_ids), total=total_segments)

        system_prompt = (
            f"You are a professional subtitle translator.\n"
            f"Translate the following subtitle segment from {self.source_language} to {self.target_language}.\n\n"
            f"Rules:\n"
            f"- Return ONLY the {self.target_language} translation.\n"
            f"- Do not explain or add commentary.\n"
            f"- Do not enclose output in quotes, markdown code blocks, or tags.\n"
            f"- Preserve original meaning, names, and technical terms when appropriate.\n"
            f"- Keep output concise and natural for subtitles."
        )

        for idx, seg in enumerate(segments):
            step_num = idx + 1
            seg_id = seg.get("id", step_num)

            # Check user cancellation
            if is_cancelled and is_cancelled():
                project.update_stage(stage_name, StageStatus.CANCELLED.value, current=idx, total=total_segments)
                emit_event("stage_cancelled", stage_name, current=idx, total=total_segments, error="Translation stage cancelled by user.")
                self._save_partial_checkpoint(partial_json_path, list(completed_segment_ids), translations_dict)
                raise PipelineCancelledError("Translation stage cancelled by user.")

            # Check simulated step failure (for pipeline unit tests)
            if fail_at_step is not None and (step_num == fail_at_step or (step_num == total_segments and fail_at_step > total_segments)):
                err_msg = f"Simulated error in stage {stage_name} at step {fail_at_step}"
                project.update_stage(stage_name, StageStatus.FAILED.value, current=idx, total=total_segments, error=err_msg)
                emit_event("stage_error", stage_name, current=idx, total=total_segments, error=err_msg)
                self._save_partial_checkpoint(partial_json_path, list(completed_segment_ids), translations_dict)
                raise RuntimeError(err_msg)

            # Skip already completed segment
            if seg_id in completed_segment_ids:
                percent = (step_num / total_segments) * 100.0
                project.update_stage(stage_name, StageStatus.RUNNING.value, progress=int(percent), current=step_num, total=total_segments)
                emit_event("progress", stage_name, current=step_num, total=total_segments, percent=percent)
                continue

            orig_text = seg.get("text", "").strip()

            if not orig_text:
                translations_dict[str(seg_id)] = ""
                completed_segment_ids.add(seg_id)
            else:
                # Call Ollama with max 3 retries (backoff 1s, 2s, 4s)
                success = False
                last_exc = None
                for attempt in range(1, self.max_retries + 1):
                    try:
                        raw_res = self.client.generate(
                            prompt=orig_text,
                            system=system_prompt,
                            model=self.model_name,
                            timeout=self.timeout
                        )
                        cleaned = clean_translation(raw_res)
                        translations_dict[str(seg_id)] = cleaned
                        completed_segment_ids.add(seg_id)
                        success = True
                        break
                    except (OllamaUnavailableError, OllamaModelNotFoundError):
                        raise
                    except Exception as e:
                        last_exc = e
                        logger.warning(f"Translation attempt {attempt}/{self.max_retries} failed for segment {seg_id}: {e}")
                        if attempt < self.max_retries:
                            backoff_sec = 2 ** (attempt - 1)
                            time.sleep(backoff_sec)

                if not success:
                    self._save_partial_checkpoint(partial_json_path, list(completed_segment_ids), translations_dict)
                    err_msg = f"Translation failed for segment {seg_id} after {self.max_retries} retries: {last_exc}"
                    project.update_stage(stage_name, StageStatus.FAILED.value, current=idx, total=total_segments, error=err_msg)
                    emit_event("stage_error", stage_name, current=idx, total=total_segments, error=err_msg)
                    raise TranslationFailedError(err_msg)

            # Save checkpoint after each segment
            self._save_partial_checkpoint(partial_json_path, list(completed_segment_ids), translations_dict)

            percent = (step_num / total_segments) * 100.0
            project.update_stage(stage_name, StageStatus.RUNNING.value, progress=int(percent), current=step_num, total=total_segments)
            emit_event("progress", stage_name, current=step_num, total=total_segments, percent=percent)

        # 6. Update Project Data Segments & Metadata
        updated_segments = []
        for seg in segments:
            seg_id = seg.get("id")
            seg_copy = dict(seg)
            seg_copy["translation"] = translations_dict.get(str(seg_id), seg.get("text", ""))
            updated_segments.append(seg_copy)

        project.data["segments"] = updated_segments
        if "metadata" not in project.data:
            project.data["metadata"] = {}

        project.data["metadata"]["translation"] = {
            "provider": "ollama",
            "model": self.model_name,
            "source_language": self.source_language,
            "target_language": self.target_language
        }

        # 7. Generate translated.srt (preserve timestamps and count exactly)
        srt_lines = []
        for idx, seg in enumerate(updated_segments, start=1):
            srt_lines.append(str(idx))
            start_ts = format_srt_timestamp(seg["start"])
            end_ts = format_srt_timestamp(seg["end"])
            srt_lines.append(f"{start_ts} --> {end_ts}")
            srt_text = seg.get("translation", "").strip()
            if not srt_text:
                srt_text = "-"
            srt_lines.append(srt_text)
            srt_lines.append("")

        translated_srt_content = "\n".join(srt_lines).strip() + "\n"

        # Validate SRT content & segment count match
        if not validate_srt_content(translated_srt_content):
            project.update_stage(stage_name, StageStatus.FAILED.value, error="Generated translated SRT content failed validation.")
            emit_event("stage_error", stage_name, error="Generated translated SRT content failed validation.")
            raise AutoDubError("Generated translated SRT content failed validation.")

        tmp_srt = transcript_dir / "translated.srt.tmp"
        with open(tmp_srt, "w", encoding="utf-8") as f:
            f.write(translated_srt_content)
        tmp_srt.replace(translated_srt_path)

        project.save()

        # Mark COMPLETED
        elapsed = time.time() - start_time
        project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=total_segments, total=total_segments)
        emit_event("stage_complete", stage_name, current=total_segments, total=total_segments, percent=100.0)

        return elapsed

    def _save_partial_checkpoint(
        self,
        path: Path,
        completed_segment_ids: List[Any],
        translations_dict: Dict[str, str]
    ):
        """Save translation checkpoint atomically."""
        ckpt_data = {
            "model": self.model_name,
            "source_language": self.source_language,
            "target_language": self.target_language,
            "completed_segments": completed_segment_ids,
            "translations": translations_dict
        }
        tmp_path = path.with_suffix(".tmp")
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(ckpt_data, f, indent=2, ensure_ascii=False)
        tmp_path.replace(path)

    def _parse_srt(self, srt_path: Path) -> List[Dict[str, Any]]:
        """Helper to parse SRT into segment dictionaries if project.json segments array is empty."""
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
                segments.append({
                    "id": seg_id,
                    "start": start_sec,
                    "end": end_sec,
                    "text": text
                })
            except Exception:
                continue
        return segments

    def _parse_srt_timestamp(self, ts_str: str) -> float:
        """Parse HH:MM:SS,mmm timestamp string into float seconds."""
        parts = ts_str.replace(",", ".").split(":")
        hours = float(parts[0])
        mins = float(parts[1])
        secs = float(parts[2])
        return hours * 3600.0 + mins * 60.0 + secs

OllamaTranslator = RealTranslator
