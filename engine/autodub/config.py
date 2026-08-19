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
DEFAULT_WHISPER_COMPUTE_TYPE = "int8"
DEFAULT_TRANSLATION_MODEL = "qwen2.5:3b"
DEFAULT_TTS_ENGINE = "piper"
DEFAULT_CHUNK_DURATION_SEC = 600  # 10 minutes
