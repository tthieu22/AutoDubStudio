import os
from pathlib import Path

# Path configuration using pathlib
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENGINE_DIR = BASE_DIR / "engine"
PROJECTS_DIR = BASE_DIR / "projects"
MODELS_DIR = BASE_DIR / "models"
RUNTIME_DIR = BASE_DIR / "runtime"
FFMPEG_BIN = RUNTIME_DIR / "ffmpeg" / "ffmpeg.exe" if os.name == "nt" else RUNTIME_DIR / "ffmpeg" / "ffmpeg"

# Defaults
DEFAULT_WHISPER_MODEL = "small"
DEFAULT_WHISPER_COMPUTE_TYPE = "float16"
DEFAULT_WHISPER_DEVICE = "cuda"
DEFAULT_CPU_THREADS = 4
DEFAULT_WHISPER_WORKERS = 1
DEFAULT_BEAM_SIZE = 1
DEFAULT_BEST_OF = 1
DEFAULT_VAD_FILTER = True
DEFAULT_CHUNK_DURATION_SEC = 600  # 10 minutes

# Translation Defaults (Central Config)
DEFAULT_TRANSLATION_MODEL = "qwen3:4b"
DEFAULT_TRANSLATION_LANGUAGE = "zh-vi"

# Centralized Hardware-Aware Profile (GTX 1650 Ti 4GB VRAM / 4C 8T CPU)
HARDWARE_PROFILE = {
    "profile_name": "gtx_1650_4gb",
    "cpu_threads": DEFAULT_CPU_THREADS,
    "whisper_workers": DEFAULT_WHISPER_WORKERS,
    "max_parallel_jobs": 1,
    "default_whisper_model": DEFAULT_WHISPER_MODEL,
    "default_compute_type": DEFAULT_WHISPER_COMPUTE_TYPE,
    "beam_size": DEFAULT_BEAM_SIZE,
    "best_of": DEFAULT_BEST_OF,
    "vad_filter": DEFAULT_VAD_FILTER,
    "ollama_concurrency": 1,
    "gpu_inference_concurrency": 1,
    "max_vram_mb": 4096,
    "min_free_vram_mb": 1200
}
