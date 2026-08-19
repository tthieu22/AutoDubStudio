# AutoDubStudio Engine (Phase 8 Complete)

CLI engine responsible for project management, pipeline state machine execution, atomic save & recovery, checkpointing, **real FFmpeg audio extraction**, **real faster-whisper speech-to-text**, **real Ollama local translation**, **real Piper local text-to-speech**, **real FFmpeg atempo audio synchronization**, and **real FFmpeg video mixing & rendering**.

## Local Dependencies
1. **FFmpeg**: Standalone binaries inside `runtime/ffmpeg/` or PATH (`ffmpeg.exe`, `ffprobe.exe`).
2. **Ollama**: Local LLM runner listening at `http://localhost:11434`. Model: `ollama pull qwen2.5:3b`.
3. **Piper TTS**: Local neural TTS binary in `runtime/piper/piper.exe` or system PATH. Voice models in `runtime/piper/voices/<voice>.onnx` and `<voice>.onnx.json`.

## CLI Usage

```bash
# Activate virtual environment
.venv\Scripts\activate

# 1. Create a project
python -m autodub.cli create my-video --source source/input.mp4

# 2. Extract Audio
python -m autodub.cli extract my-video

# 3. Transcribe Audio
python -m autodub.cli transcribe my-video --model small --compute-type int8

# 4. Translate Subtitles
python -m autodub.cli translate my-video --source-language en --target-language vi --model qwen2.5:3b

# 5. Synthesize Local Text-to-Speech (Piper)
python -m autodub.cli tts my-video --voice vi_VN-viss-low --language vi

# 6. Audio Synchronization (FFmpeg atempo)
python -m autodub.cli sync my-video --speed-min 0.50 --speed-max 2.00 --overlap-policy TRIM

# 7. Video Mixing & Final Rendering (FFmpeg)
python -m autodub.cli render my-video --audio-mode DUCK_ORIGINAL --codec H264 --encoder AUTO --subtitle-mode BURN_IN

# 8. Check status & run full pipeline
python -m autodub.cli status my-video
python -m autodub.cli run my-video
```

## Running Automated Tests & Benchmarks
```bash
# Run all automated tests (144/144 PASS)
python -m unittest discover -s tests

# Run Phase 8 Audio Mixing & Final Video Rendering Benchmark
python ..\scripts\benchmark_phase8.py
```
