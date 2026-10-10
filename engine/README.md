# AutoDubStudio Engine (Phase 9 Complete)

CLI engine responsible for project management, pipeline state machine execution, atomic save & recovery, checkpointing, **real FFmpeg audio extraction**, **real faster-whisper speech-to-text**, **real Ollama local translation**, **real Piper local text-to-speech**, **real FFmpeg atempo audio synchronization**, **real FFmpeg video mixing & rendering**, and **production-ready pipeline orchestration & batch job management**.

## Local Dependencies
1. **FFmpeg**: Standalone binaries inside `runtime/ffmpeg/` or PATH (`ffmpeg.exe`, `ffprobe.exe`).
2. **Ollama**: Local LLM runner listening at `http://localhost:11434`. Model: `ollama pull qwen3:4b`.
3. **Piper TTS**: Local neural TTS binary in `runtime/piper/piper.exe` or system PATH. Voice models in `runtime/piper/voices/<voice>.onnx` and `<voice>.onnx.json`.

## CLI Usage

```bash
# Activate virtual environment
.venv\Scripts\activate

# Single Project Pipeline Execution
python -m autodub.cli run --project projects/my-video --input input.mp4

# Batch Job Engine
python -m autodub.cli batch --input-dir /videos --output-dir /outputs --workers 4 --priority 5

# Job Control Commands
python -m autodub.cli list --status RUNNING
python -m autodub.cli status --job-id job_12345 --json
python -m autodub.cli pause --job-id job_12345
python -m autodub.cli resume --job-id job_12345
python -m autodub.cli cancel --job-id job_12345
python -m autodub.cli retry --job-id job_12345
python -m autodub.cli recover
python -m autodub.cli clean --status COMPLETED --older-than 7d
```

## Running Automated Tests & Benchmarks
```bash
# Run all automated tests (175/175 PASS)
python -m unittest discover -s tests

# Run Phase 9 Batch Engine Benchmark
python ..\scripts\benchmark_phase9.py
```
