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

# Translation Configuration (Qwen2.5-3B-Instruct Q4_K_M via llama.cpp CUDA)
TRANSLATION_MODEL = "qwen2.5-3b-instruct"
DEFAULT_TRANSLATION_MODEL = "qwen2.5-3b-instruct"
DEFAULT_TRANSLATION_LANGUAGE = "zh-vi"
DEFAULT_TRANSLATION_BATCH_SIZE = 20
MAX_TRANSLATION_BATCH_SIZE = 50
MIN_TRANSLATION_BATCH_SIZE = 1
MAX_CONCURRENT_BATCHES = 1

# Supported Production Translation Models (llama.cpp CUDA)
TRANSLATION_MODELS = {
    "qwen2.5-3b-instruct": {
        "id": "Qwen/Qwen2.5-3B-Instruct-GGUF",
        "name": "Qwen2.5-3B-Instruct (Q4_K_M - llama.cpp CUDA)",
        "type": "llama_cpp",
        "gguf_filename": "Qwen2.5-3B-Instruct-Q4_K_M.gguf",
        "device": "cuda",
        "vram_mb": 2200
    }
}

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
    "llamacpp_concurrency": 1,
    "llamacpp_server_url": "http://localhost:8080",
    "gpu_inference_concurrency": 1,
    "max_vram_mb": 4096,
    "min_free_vram_mb": 1200
}
