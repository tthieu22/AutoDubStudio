import os
import sys
import time
import json
import wave
import math
import shutil
import subprocess
from pathlib import Path
from typing import Optional, Dict, List, Tuple, Callable, Any

from autodub.config import BASE_DIR, RUNTIME_DIR, MODELS_DIR
from autodub.models.project import Project
from autodub.pipeline.state import PipelineStage, StageStatus
from autodub.pipeline.progress import emit_event
from autodub.utils.logging import setup_logger
from autodub.exceptions import (
    AutoDubError,
    PiperUnavailableError,
    PiperVoiceNotFoundError,
    PiperSynthesisError,
    PiperInvalidOutputError,
    PiperTimeoutError,
    TTSSynthesisFailedError,
    PipelineCancelledError
)

logger = setup_logger()


import re

VIETNAMESE_PRONUNCIATION_MAP = {
    r"\bpodcast\b": "pót cát",
    r"\bvideo\b": "vi-đê-ô",
    r"\bvideos\b": "vi-đê-ô",
    r"\bonline\b": "on-lai",
    r"\bwebsite\b": "trang web",
    r"\bwebsites\b": "trang web",
    r"\baudio\b": "ô-đi-ô",
    r"\bfacebook\b": "phây-sbút",
    r"\byoutube\b": "du-túp",
    r"\bgoogle\b": "gút-gồ",
    r"\bapp\b": "áp",
    r"\bapps\b": "áp",
    r"\blink\b": "linh",
    r"\bemail\b": "e-mai",
    r"\bclip\b": "clíp",
    r"\bclips\b": "clíp",
    r"\bchannel\b": "kênh",
    r"\benglish\b": "tiếng Anh",
    r"\bai\b": "A I",
    r"\bcpu\b": "C P U",
    r"\bgpu\b": "G P U",
}

import unicodedata

def sanitize_text_for_piper(text: str) -> str:
    """Sanitize text input for Piper TTS process, applying Vietnamese phonetics, cleaning hallucinations, and normalizations."""
    if not text:
        return "Xin chào"
    
    # Strip lone surrogates and weird unicode
    try:
        clean = text.encode("utf-8", "ignore").decode("utf-8", "ignore")
    except Exception:
        clean = text

    clean = unicodedata.normalize("NFC", clean)

    # Remove non-printable / control / surrogate chars
    clean = "".join(c for c in clean if (c.isprintable() or c in "\n\r\t ") and ord(c) < 0xD800 or ord(c) > 0xDFFF)

    # Remove Chinese / Japanese / Korean characters (hallucinations from Qwen)
    clean = re.sub(r'[\u2E80-\u2FD5\u3000-\u303F\u3040-\u309F\u30A0-\u30FF\u31F0-\u31FF\u3200-\u32FE\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF\uFE30-\uFE4F]+', ' ', clean)

    # Collapse repetitive phrases/words (e.g. 'nào đó nào đó...' or 'nào đó' repeated 3+ times)
    clean = re.sub(r'(\b[\w\s]{2,20}\b)(?:\s+\1){2,}', r'\1', clean, flags=re.IGNORECASE)

    # Apply Vietnamese phonetic mappings for foreign words
    for pattern, replacement in VIETNAMESE_PRONUNCIATION_MAP.items():
        clean = re.sub(pattern, replacement, clean, flags=re.IGNORECASE)

    # Replace special symbols with spoken words
    clean = clean.replace("%", " phần trăm")
    clean = clean.replace("$", " đô-la")
    clean = clean.replace("&", " và ")
    clean = clean.replace("@", " a-còng ")

    clean = re.sub(r'\s+', ' ', clean).strip()

    # Limit overly long continuous string to prevent ONNX memory explosion
    if len(clean) > 300:
        clean = clean[:300]

    return clean if clean.strip() else "Xin chào"


class PiperClient:
    """Wrapper around local Piper TTS library and voice models using Python API and GPU/CUDA."""

    def __init__(self, executable_path: Optional[Path] = None, voices_dir: Optional[Path] = None, use_cuda: Optional[bool] = None):
        self.executable_path = executable_path or self.find_executable()
        self.voices_dir = voices_dir or (RUNTIME_DIR / "piper" / "voices")
        self._setup_dll_directories()
        self.use_cuda = use_cuda if use_cuda is not None else self._detect_cuda()
        self._loaded_voices = {}
        if self.use_cuda:
            logger.info("Piper TTS: CUDA GPU acceleration enabled.")
        else:
            logger.info("Piper TTS: Running on CPU.")

    def _setup_dll_directories(self):
        """Add nvidia site-packages bin directories to Windows DLL path so ONNX Runtime can find CUDA/cuDNN dlls."""
        if sys.platform != "win32":
            return
        if getattr(self, "_dll_directories_setup", False):
            return
        import importlib.util
        dll_paths = []
        for pkg in ["nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_runtime", "nvidia.cuda_nvrtc", "nvidia.cufft", "nvidia.curand", "nvidia.nvjitlink"]:
            try:
                spec = importlib.util.find_spec(pkg)
                if spec and spec.submodule_search_locations:
                    for loc in spec.submodule_search_locations:
                        bin_path = Path(loc) / "bin"
                        if bin_path.exists():
                            os.add_dll_directory(str(bin_path))
                            dll_paths.append(str(bin_path.resolve()))
                            logger.info(f"Piper CUDA setup: Added DLL directory {bin_path}")
            except Exception as e:
                logger.debug(f"Piper CUDA setup: Failed to add DLL directory for {pkg}: {e}")
        
        # Prepend to PATH environment variable as well (ONNX Runtime Windows loader workaround)
        if dll_paths:
            os.environ["PATH"] = ";".join(dll_paths) + ";" + os.environ.get("PATH", "")
            
        self._dll_directories_setup = True

    @staticmethod
    def _detect_cuda() -> bool:
        """Auto-detect if CUDA is available and functional for ONNX Runtime."""
        try:
            if sys.platform == "win32":
                import importlib.util
                dll_paths = []
                for pkg in ["nvidia.cublas", "nvidia.cudnn", "nvidia.cuda_runtime", "nvidia.cuda_nvrtc", "nvidia.cufft", "nvidia.curand", "nvidia.nvjitlink"]:
                    try:
                        spec = importlib.util.find_spec(pkg)
                        if spec and spec.submodule_search_locations:
                            for loc in spec.submodule_search_locations:
                                bin_path = Path(loc) / "bin"
                                if bin_path.exists():
                                    os.add_dll_directory(str(bin_path))
                                    dll_paths.append(str(bin_path.resolve()))
                    except Exception:
                        pass
                if dll_paths:
                    os.environ["PATH"] = ";".join(dll_paths) + ";" + os.environ.get("PATH", "")

            import onnxruntime
            providers = onnxruntime.get_available_providers()
            if "CUDAExecutionProvider" not in providers:
                logger.info("CUDA detect: CUDAExecutionProvider not in available providers.")
                return False

            # Validate CUDA execution provider loads successfully
            dummy_onnx = (
                b'\x08\x07\x12\x04test\x1a\x04test"\x1a\n\x08Identity'
                b'\x12\x01x\x1a\x01y"\x08Identity*\x00:\x00Z\x11\n\x01x'
                b'\x12\x0c\n\n\x08\x01\x12\x06\n\x00\n\x02\x08\x01b\x11'
                b'\n\x01y\x12\x0c\n\n\x08\x01\x12\x06\n\x00\n\x02\x08\x01'
            )
            try:
                onnxruntime.InferenceSession(dummy_onnx, providers=["CUDAExecutionProvider"])
            except Exception as e:
                if "Missing opset in the model" in str(e):
                    logger.info("CUDA detect: CUDAExecutionProvider successfully loaded and verified.")
                    return True
                logger.info(f"CUDA detect: InferenceSession creation failed: {e}")
                return False
            return True
        except ImportError:
            logger.info("CUDA detect: onnxruntime not installed.")
            return False
        except Exception as e:
            logger.info(f"CUDA detect: check failed with error: {e}")
            return False

    def find_executable(self) -> Optional[Path]:
        """Locate Piper binary in runtime/piper/, .venv Scripts, or system PATH."""
        candidates = [
            Path(sys.executable).parent / "piper.exe",
            Path(sys.executable).parent / "piper",
            RUNTIME_DIR / "piper" / "piper.exe",
            RUNTIME_DIR / "piper" / "piper",
            RUNTIME_DIR / "piper.exe",
            BASE_DIR / "engine" / ".venv" / "Scripts" / "piper.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()

        which_path = shutil.which("piper")
        if which_path:
            return Path(which_path).resolve()

        return None

    def find_voice(self, voice_name: str) -> Tuple[Optional[Path], Optional[Path]]:
        """
        Locate .onnx and .onnx.json for given voice model name or path.
        Returns (onnx_path, json_path).
        """
        voice_path = Path(voice_name)
        if voice_path.is_file() and voice_path.suffix == ".onnx":
            json_path = voice_path.with_suffix(".onnx.json")
            if json_path.exists():
                return (voice_path.resolve(), json_path.resolve())

        # Search candidates in voices_dir, piper_voices, or runtime/piper
        search_dirs = [
            self.voices_dir,
            BASE_DIR / "piper_voices",
            RUNTIME_DIR / "piper",
            MODELS_DIR / "piper",
        ]
        
        # Clean extension if provided
        clean_name = voice_name[:-5] if voice_name.endswith(".onnx") else voice_name

        for s_dir in search_dirs:
            if not s_dir.exists():
                continue
            onnx_candidate = s_dir / f"{clean_name}.onnx"
            json_candidate = s_dir / f"{clean_name}.onnx.json"
            if onnx_candidate.exists() and json_candidate.exists():
                return (onnx_candidate.resolve(), json_candidate.resolve())

        return (None, None)

    def check_availability(self, voice_name: str) -> Tuple[bool, str, int]:
        """
        Validate executable and voice model availability.
        Returns (available, error_message, sample_rate).
        """
        exe = self.find_executable()
        if not exe or not exe.exists():
            return False, "Piper TTS executable not found in runtime/piper/ or system PATH.", 22050

        onnx_p, json_p = self.find_voice(voice_name)
        if not onnx_p or not json_p:
            return False, f"Piper voice model '{voice_name}' (.onnx and .onnx.json) not found in {self.voices_dir}.", 22050

        # Read sample rate from json config
        sample_rate = 22050
        try:
            with open(json_p, "r", encoding="utf-8") as f:
                v_config = json.load(f)
                sample_rate = v_config.get("audio", {}).get("sample_rate", 22050)
        except Exception as e:
            logger.warning(f"Could not parse sample rate from {json_p}: {e}")

        return True, "", sample_rate

    def synthesize(
        self,
        text: str,
        output_wav_path: Path,
        voice_name: str,
        timeout: int = 120,
        speaker: Optional[str] = None
    ) -> float:
        """
        Synthesize text into WAV file using Python PiperVoice API.
        Returns synthesis duration in seconds.
        """
        onnx_p, json_p = self.find_voice(voice_name)
        if not onnx_p:
            raise PiperVoiceNotFoundError(f"Voice model '{voice_name}' not found.")

        output_wav_path.parent.mkdir(parents=True, exist_ok=True)
        clean_text = sanitize_text_for_piper(text)

        start_time = time.time()
        try:
            from piper import PiperVoice
            from piper.config import SynthesisConfig

            voice_key = str(onnx_p)
            if voice_key not in self._loaded_voices:
                logger.info(f"Loading Piper voice model (CUDA={self.use_cuda}): {onnx_p}")
                self._loaded_voices[voice_key] = PiperVoice.load(str(onnx_p), use_cuda=self.use_cuda)

            voice = self._loaded_voices[voice_key]

            # Determine speaker ID
            speaker_id = None
            if speaker is not None:
                try:
                    speaker_id = int(speaker)
                except ValueError:
                    try:
                        speaker_id = voice.config.speaker_id_map.get(speaker, 0)
                    except Exception:
                        speaker_id = 0

            syn_config = SynthesisConfig(speaker_id=speaker_id)

            with wave.open(str(output_wav_path), "wb") as wav_file:
                # Pre-set wave parameters to prevent wave.Error: # channels not specified
                # if clean_text is empty or does not yield any audio frames.
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(voice.config.sample_rate)
                voice.synthesize_wav(clean_text, wav_file, syn_config=syn_config, set_wav_format=False)

            return time.time() - start_time
        except Exception as e:
            if output_wav_path.exists():
                try:
                    output_wav_path.unlink()
                except OSError:
                    pass
            if not isinstance(e, AutoDubError):
                raise PiperSynthesisError(f"Piper python synthesis failed: {e}") from e
            raise


def validate_wav_file(file_path: Path) -> Dict[str, Any]:
    """Validate WAV audio file existence, header integrity, sample rate, channels, duration."""
    if not file_path.exists() or file_path.stat().st_size == 0:
        raise PiperInvalidOutputError(f"WAV audio file {file_path} is empty or missing.")

    try:
        with wave.open(str(file_path), "rb") as wf:
            channels = wf.getnchannels()
            sample_rate = wf.getframerate()
            nframes = wf.getnframes()
            duration = nframes / float(sample_rate) if sample_rate > 0 else 0.0

            if duration <= 0 or not math.isfinite(duration):
                raise PiperInvalidOutputError(f"Invalid audio duration ({duration}s) in {file_path}.")

            return {
                "channels": channels,
                "sample_rate": sample_rate,
                "duration": round(duration, 4),
                "format": "wav"
            }
    except wave.Error as e:
        raise PiperInvalidOutputError(f"Invalid or corrupted WAV file header in {file_path}: {e}") from e


class RealTTS:
    """Real Text-to-Speech stage runner using local Piper TTS engine."""

    def __init__(self, step_delay: float = 0.05, client: Optional[PiperClient] = None):
        self.step_delay = step_delay
        self.client = client or PiperClient()

    def run(
        self,
        project: Project,
        is_cancelled: Optional[Callable[[], bool]] = None,
        fail_at_step: Optional[int] = None,
        force: bool = False,
        voice_name: Optional[str] = None,
        language: str = "vi"
    ) -> float:
        stage_name = PipelineStage.TTS.value
        stage_info = project.get_stage_info(stage_name)
        start_time = time.time()

        audio_tts_dir = project.project_dir / "audio" / "tts"
        audio_tts_dir.mkdir(parents=True, exist_ok=True)
        partial_json_path = audio_tts_dir / "tts.partial.json"

        # Determine voice model name
        target_voice = (
            voice_name
            or project.data.get("tts", {}).get("voice")
            or project.data.get("config", {}).get("tts", {}).get("voice")
            or "vi_VN-vais1000-medium"
        )
        # Verify if voice exists, otherwise fallback to any existing model in search dirs
        onnx_chk, _ = self.client.find_voice(target_voice)
        if not onnx_chk:
            for fallback_name in ["vi_VN-vais1000-medium", "vi_VN-vivos-x_low", "vi_VN-viss-low"]:
                onnx_chk, _ = self.client.find_voice(fallback_name)
                if onnx_chk:
                    target_voice = fallback_name
                    break

        completed_segment_ids = set()
        segment_metadata_map: Dict[str, Dict[str, Any]] = {}

        # Handle simulated step failure for pipeline state machine unit tests
        if fail_at_step is not None:
            err_msg = f"Simulated error in stage {stage_name} at step {fail_at_step}"
            failed_current = max(0, fail_at_step - 1)
            project.update_stage(stage_name, StageStatus.FAILED.value, current=failed_current, total=10, error=err_msg)
            emit_event("stage_error", stage_name, current=failed_current, total=10, error=err_msg)
            raise RuntimeError(err_msg)

        # 1. Idempotency Check
        if not force and stage_info.get("status") == StageStatus.COMPLETED.value:
            # Check if all TTS output files exist
            segments = project.data.get("segments", [])
            all_valid = len(segments) > 0
            for seg in segments:
                if seg.get("tts", {}).get("status") == "SKIPPED":
                    continue
                wav_file = audio_tts_dir / f"{seg.get('id', 1):06d}.wav"
                if not wav_file.exists() or wav_file.stat().st_size == 0:
                    all_valid = False
                    break
            if all_valid:
                logger.info("Existing valid TTS audio files found. Skipping TTS stage.")
                emit_event("progress", stage_name, current=100, total=100, percent=100.0, message="Existing valid TTS output found.")
                emit_event("stage_complete", stage_name, current=100, total=100, percent=100.0)
                return 0.0

        # 2. Piper & Voice Model Discovery Check
        available, err_msg, voice_sample_rate = self.client.check_availability(target_voice)
        if not available:
            logger.error(f"TTS Stage Error: {err_msg}")
            project.update_stage(stage_name, StageStatus.FAILED.value, error=err_msg)
            emit_event("stage_error", stage_name, error=err_msg)
            if "executable not found" in err_msg.lower():
                raise PiperUnavailableError(err_msg)
            else:
                raise PiperVoiceNotFoundError(err_msg)

        # 3. Load Translated Segments
        segments = project.data.get("segments", [])
        if not segments:
            translated_srt = project.project_dir / "transcript" / "translated.srt"
            if translated_srt.exists():
                segments = self._parse_srt(translated_srt)

        total_segments = len(segments)
        if total_segments == 0:
            logger.warning("No segments found for TTS synthesis.")
            project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=0, total=0)
            emit_event("stage_complete", stage_name, current=0, total=0, percent=100.0)
            return 0.0

        # 4. Read Partial Checkpoint if resuming
        if not force and partial_json_path.exists():
            try:
                with open(partial_json_path, "r", encoding="utf-8") as f:
                    checkpoint_data = json.load(f)
                    completed_segment_ids = set(checkpoint_data.get("completed_segments", []))
                    segment_metadata_map = checkpoint_data.get("segments", {})
                    logger.info(f"Loaded TTS checkpoint: {len(completed_segment_ids)} completed segments.")
            except Exception as e:
                logger.warning(f"Could not load TTS partial checkpoint: {e}. Starting fresh.")

        # Update Project Stage State to RUNNING
        project.update_stage(stage_name, StageStatus.RUNNING.value, progress=0, current=0, total=total_segments)
        emit_event("stage_start", stage_name, current=0, total=total_segments, percent=0.0)

        total_audio_duration = 0.0

        # Collect uncompleted segments
        unprocessed = []
        for idx, seg in enumerate(segments):
            if is_cancelled and is_cancelled():
                err = "TTS stage cancelled by user."
                logger.warning(err)
                project.update_stage(stage_name, StageStatus.CANCELLED.value, current=idx, total=total_segments, error=err)
                emit_event("stage_cancelled", stage_name, current=idx, total=total_segments, error=err)
                self._save_partial_checkpoint(partial_json_path, target_voice, language, list(completed_segment_ids), segment_metadata_map)
                raise PipelineCancelledError(err)

            seg_id = seg.get("id", idx + 1)
            wav_filename = f"{seg_id:06d}.wav"
            final_wav_path = audio_tts_dir / wav_filename

            raw_text = seg.get("translation") or seg.get("text") or ""
            # Skip segment if it is empty, whitespace-only, or contains no spoken/alphanumeric characters (e.g., "...")
            if not raw_text or not raw_text.strip() or not re.search(r'[a-zA-Z0-9\u00c0-\u1ef9]', raw_text):
                logger.info(f"Segment {seg_id} text is empty/whitespace or has no spoken characters. Skipping TTS synthesis.")
                seg_meta = {
                    "audio_file": f"audio/tts/{wav_filename}",
                    "status": "SKIPPED",
                    "reason": "EMPTY_TEXT",
                    "duration": 0.0
                }
                seg["tts"] = seg_meta
                completed_segment_ids.add(seg_id)
                segment_metadata_map[str(seg_id)] = seg_meta
                continue

            tts_text = sanitize_text_for_piper(raw_text)

            if not force and seg_id in completed_segment_ids and final_wav_path.exists():
                try:
                    wav_info = validate_wav_file(final_wav_path)
                    seg["tts"] = {
                        "audio_file": f"audio/tts/{wav_filename}",
                        "duration": wav_info["duration"],
                        "sample_rate": wav_info["sample_rate"],
                        "channels": wav_info["channels"],
                        "format": "wav"
                    }
                    total_audio_duration += wav_info["duration"]
                    continue
                except PiperInvalidOutputError:
                    logger.warning(f"Segment {seg_id} audio corrupt. Re-synthesizing.")
                    completed_segment_ids.discard(seg_id)

            unprocessed.append((idx, seg, seg_id, tts_text, wav_filename, final_wav_path))

        self._save_partial_checkpoint(partial_json_path, target_voice, language, list(completed_segment_ids), segment_metadata_map)

        if unprocessed:
            logger.info(f"Synthesizing {len(unprocessed)} segments using 4 parallel TTS workers...")

            def process_single(item):
                idx, seg, seg_id, tts_text, wav_filename, final_wav_path = item
                tmp_wav_path = audio_tts_dir / f"{wav_filename}.{os.getpid()}_{idx}.tmp"

                retries = 3
                backoff_delays = [0.5, 1.0, 2.0]
                for attempt in range(retries):
                    if is_cancelled and is_cancelled():
                        raise PipelineCancelledError("TTS stage cancelled by user.")
                    try:
                        if tmp_wav_path.exists():
                            try: tmp_wav_path.unlink()
                            except OSError: pass

                        self.client.synthesize(
                            text=tts_text,
                            output_wav_path=tmp_wav_path,
                            voice_name=target_voice,
                            timeout=120,
                            speaker=seg.get("speaker")
                        )
                        wav_info = validate_wav_file(tmp_wav_path)
                        if final_wav_path.exists():
                            try: final_wav_path.unlink()
                            except OSError: pass
                        tmp_wav_path.rename(final_wav_path)

                        seg_meta = {
                            "audio_file": f"audio/tts/{wav_filename}",
                            "duration": wav_info["duration"],
                            "sample_rate": wav_info["sample_rate"],
                            "channels": wav_info["channels"],
                            "format": "wav"
                        }
                        return seg, seg_id, seg_meta, wav_info["duration"]
                    except Exception as e:
                        if tmp_wav_path.exists():
                            try: tmp_wav_path.unlink()
                            except OSError: pass
                        if attempt == retries - 1:
                            raise e
                        time.sleep(backoff_delays[attempt])

            from concurrent.futures import ThreadPoolExecutor, as_completed
            completed_count = len(segments) - len(unprocessed)

            workers = max(1, min(4, (os.cpu_count() or 4) // 2))
            logger.info(f"Synthesizing {len(unprocessed)} segments using {workers} worker threads...")

            with ThreadPoolExecutor(max_workers=workers) as executor:
                future_map = {executor.submit(process_single, item): item for item in unprocessed}
                for future in as_completed(future_map):
                    if is_cancelled and is_cancelled():
                        executor.shutdown(wait=False, cancel_futures=True)
                        raise PipelineCancelledError("TTS stage cancelled by user.")
                    try:
                        processed_seg, seg_id, seg_meta, dur = future.result()
                        # Find original segment reference and update it
                        for s in segments:
                            if s.get("id") == seg_id:
                                s["tts"] = seg_meta
                                break
                        completed_segment_ids.add(seg_id)
                        segment_metadata_map[str(seg_id)] = seg_meta
                        total_audio_duration += dur
                        completed_count += 1

                        pct = min(100.0, round((completed_count / total_segments) * 100, 2))
                        project.update_stage(stage_name, StageStatus.RUNNING.value, progress=pct, current=completed_count, total=total_segments)
                        emit_event("progress", stage_name, current=completed_count, total=total_segments, percent=pct, segment_id=seg_id)
                        self._save_partial_checkpoint(partial_json_path, target_voice, language, list(completed_segment_ids), segment_metadata_map)
                    except Exception as e:
                        logger.error(f"Error in parallel TTS synthesis: {e}")
                        project.update_stage(stage_name, StageStatus.FAILED.value, error=str(e))
                        emit_event("stage_error", stage_name, error=str(e))
                        raise TTSSynthesisFailedError(f"TTS synthesis failed: {e}") from e

        # 5. Create Optional Combined WAV File
        self._create_combined_audio(audio_tts_dir, segments)

        # 6. Update Project Data & Complete Stage
        total_time = time.time() - start_time
        rtf = total_time / total_audio_duration if total_audio_duration > 0 else 0.0

        project.data["tts"] = {
            "engine": "piper",
            "voice": target_voice,
            "language": language,
            "completed_segments": len(completed_segment_ids),
            "total_audio_duration": round(total_audio_duration, 4),
            "processing_time": round(total_time, 4),
            "rtf": round(rtf, 4)
        }
        project.data["segments"] = segments

        # Atomic Save Project Model
        project.update_stage(stage_name, StageStatus.COMPLETED.value, progress=100, current=total_segments, total=total_segments)
        project.save()

        # Clean up partial checkpoint upon full completion
        if partial_json_path.exists():
            try: partial_json_path.unlink()
            except OSError: pass

        emit_event("stage_complete", stage_name, current=total_segments, total=total_segments, percent=100.0)
        logger.info(f"TTS Stage completed successfully in {total_time:.2f}s (RTF: {rtf:.4f}).")

        return total_time

    def _save_partial_checkpoint(
        self,
        checkpoint_path: Path,
        voice: str,
        language: str,
        completed_ids: List[int],
        segment_meta: Dict[str, Any]
    ):
        """Atomically write tts.partial.json checkpoint file."""
        tmp_checkpoint = checkpoint_path.with_suffix(".tmp")
        data = {
            "engine": "piper",
            "voice": voice,
            "language": language,
            "completed_segments": sorted(list(completed_ids)),
            "segments": segment_meta
        }
        try:
            with open(tmp_checkpoint, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            tmp_checkpoint.replace(checkpoint_path)
        except Exception as e:
            logger.warning(f"Could not save TTS partial checkpoint: {e}")

    def _create_combined_audio(self, tts_dir: Path, segments: List[Dict[str, Any]]):
        """Concatenate individual segment WAVs into audio/tts/combined.wav."""
        combined_path = tts_dir / "combined.wav"
        wav_files = []
        for seg in segments:
            if seg.get("tts", {}).get("status") == "SKIPPED":
                continue
            seg_id = seg.get("id", 1)
            f_path = tts_dir / f"{seg_id:06d}.wav"
            if f_path.exists() and f_path.stat().st_size > 0:
                wav_files.append(f_path)

        if not wav_files:
            return

        try:
            params = None
            audio_frames = []
            for w_file in wav_files:
                with wave.open(str(w_file), "rb") as wf:
                    if params is None:
                        params = wf.getparams()
                    audio_frames.append(wf.readframes(wf.getnframes()))

            if params and audio_frames:
                with wave.open(str(combined_path), "wb") as wf:
                    wf.setparams(params)
                    for frame_data in audio_frames:
                        wf.writeframes(frame_data)
                logger.info(f"Combined WAV generated at {combined_path}")
        except Exception as e:
            logger.warning(f"Failed to generate combined.wav: {e}")

    def _parse_srt(self, srt_path: Path) -> List[Dict[str, Any]]:
        """Fallback SRT parser when segments array is missing in project.json."""
        segments = []
        with open(srt_path, "r", encoding="utf-8") as f:
            content = f.read().strip()

        blocks = content.split("\n\n")
        for block in blocks:
            lines = [l.strip() for l in block.split("\n") if l.strip()]
            if len(lines) >= 2:
                try:
                    seg_id = int(lines[0])
                    times = lines[1].split(" --> ")
                    start_sec = self._srt_time_to_seconds(times[0])
                    end_sec = self._srt_time_to_seconds(times[1])
                    text = " ".join(lines[2:]) if len(lines) >= 3 else ""
                    segments.append({
                        "id": seg_id,
                        "start": start_sec,
                        "end": end_sec,
                        "translation": text,
                        "text": text
                    })
                except Exception:
                    continue
        return segments

    @staticmethod
    def _srt_time_to_seconds(time_str: str) -> float:
        parts = time_str.replace(",", ".").split(":")
        hours = float(parts[0])
        minutes = float(parts[1])
        seconds = float(parts[2])
        return hours * 3600 + minutes * 60 + seconds


# Alias for backward compatibility / pipeline manager integration
PiperTTS = RealTTS
