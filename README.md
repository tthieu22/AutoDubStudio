# AutoDubStudio (MVP v0.1)

Desktop Application for 100% Local, Free AI Video Translation & Dubbing.

## Key Features
- **100% Local & Free**: No paid APIs, no cloud video uploads.
- **Low Hardware Footprint**: Optimized for Intel i5-10300H, 16GB RAM, NVIDIA GTX 1650 Ti (4GB VRAM).
- **Sequential AI Pipeline**:
  - Audio Extraction (FFmpeg)
  - Speech-to-Text (`faster-whisper`)
  - Translation (Ollama / `Qwen2.5 3B`)
  - TTS (`piper`)
  - Audio Sync (Time-stretching / dynamic alignment)
  - Video Render (FFmpeg)
- **State Checkpointing & Resume**: Crash recovery and stage-by-stage progression.

## Project Structure
```
AutoDubStudio/
├── desktop/           # Tauri + React + TypeScript + Vite Desktop UI
├── engine/            # Python CLI & Core Dubbing Pipeline Engine
├── projects/          # Workspace folder storing user projects & output
├── models/            # Local storage for AI models (Whisper, Piper, etc.)
├── runtime/           # Standalone binaries (FFmpeg)
├── scripts/           # Utility & development scripts
└── README.md
```

## Prerequisites & Local Setup

### 1. FFmpeg
Make sure standalone `ffmpeg` is available on system PATH or in `runtime/ffmpeg/bin/ffmpeg.exe`.

### 2. Ollama & Translation Model (Phase 5)
- Download and install Ollama from [https://ollama.com](https://ollama.com).
- Start Ollama server: `ollama serve`
- Pull translation model: `ollama pull qwen2.5:3b`

### 3. Piper Local TTS (Phase 6)
- Place `piper.exe` binary in `runtime/piper/piper.exe` or system PATH.
- Place Piper voice ONNX model files in `runtime/piper/voices/vi_VN-viss-low.onnx` and `vi_VN-viss-low.onnx.json`.

### 4. Audio Synchronization (Phase 7)
- Pitch-preserving time-stretching using FFmpeg `atempo` filter.
- Automatic overlap resolution (`TRIM`, `SHIFT`) and silent gap insertion for timeline continuity.

### 5. Audio Mixing & Final Video Rendering (Phase 8)
- 4 Audio modes (`DUB_ONLY`, `ORIGINAL_ONLY`, `MIX`, `DUCK_ORIGINAL`).
- Dynamic background audio ducking via sidechain compression filter graph.
- Hardware NVENC GPU acceleration (`h264_nvenc`, `hevc_nvenc`) with CPU auto-fallback.
- Subtitle modes (`NONE`, `COPY` soft streams, `BURN_IN` hard subtitles).

- **Pipeline Orchestration & Batch Engine (Phase 9)**:
  - SQLite transaction store (`.autodub/jobs.db`) with WAL journal mode.
  - Priority FIFO Queue & multi-worker thread pool (`WorkerPool`).
  - File-based atomic locking (`.lock`) and stale lock detection.
  - Whole-pipeline checkpointing (`output/pipeline.partial.json`) & configuration hashing.
  - Automatic startup crash recovery engine.

## Quick Start (Engine CLI)
```bash
cd engine
# Activate venv
.venv\Scripts\activate

# Run single project pipeline
python autodub/cli.py run --project projects/my_video --input input.mp4

# Batch processing
python autodub/cli.py batch --input-dir /videos --output-dir /outputs --workers 4 --priority 5

# Job Management
python autodub/cli.py list --status RUNNING
python autodub/cli.py status --job-id job_12345 --json
python autodub/cli.py pause --job-id job_12345
python autodub/cli.py resume --job-id job_12345
python autodub/cli.py cancel --job-id job_12345
python autodub/cli.py retry --job-id job_12345
python autodub/cli.py recover
```
