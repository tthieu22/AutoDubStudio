# AutoDubStudio System Architecture & Technical Audit (Phase 0)

Báo cáo đánh giá toàn diện dự án **AutoDubStudio v0.1** phục vụ quá trình nâng cấp v0.2 Dual-Engine System.

---

## 1. Overview & Repository Topology

- **Project Name**: AutoDubStudio
- **Target OS**: Windows (NVENC GPU Acceleration + CPU Fallback)
- **Target Hardware**: Intel i5-10300H, 16GB RAM, NVIDIA GTX 1650 Ti (4GB VRAM)
- **Directory Structure**:
  ```
  AutoDubStudio/
  ├── desktop/           # Tauri + React + TypeScript + Vite Desktop Frontend
  ├── engine/            # Python CLI & Core Engine Backend
  │   ├── autodub/
  │   │   ├── cli.py               # Main CLI Entrypoint
  │   │   ├── config.py            # Central Configuration & Hardware Profiles
  │   │   ├── exceptions.py        # Custom Exceptions
  │   │   ├── jobs/                # SQLite Job Queue & Lock Management
  │   │   ├── models/              # Project & Data DataModels
  │   │   ├── modules/             # Pipeline Core Modules (Extractor, Transcriber, Translator, TTS, Sync, Renderer)
  │   │   ├── orchestration/       # Batch Scheduler & Worker Pool
  │   │   └── pipeline/            # Pipeline Stage Manager, State & Validation
  │   └── tests/                   # 56 Unit & Integration Test Suites
  ├── models/            # Local Storage for Whisper & Ollama Models
  ├── projects/          # User Workspace Projects Storage
  ├── runtime/           # Standalone Binaries (FFmpeg, Piper)
  └── docs/              # Architectural Specs & Audit Documentation
  ```

---

## 2. Pipeline v0.1 Baseline Architecture (`MODE_DUBBING`)

Hệ thống v0.1 hiện tại hoạt động theo quy trình 6 giai đoạn nối tiếp (Sequential Stages):

```
Input Video (.mp4)
       │
       ▼
 [ 1. EXTRACT ]   ──► FFmpeg bóc tách audio/original.wav
       │
       ▼
 [ 2. TRANSCRIBE ]──► faster-whisper (float16/CUDA) ──► transcript/original.srt
       │
       ▼
 [ 3. TRANSLATE ] ──► Ollama / llama.cpp (Qwen2.5-3B) ──► transcript/translated.srt
       │
       ▼
 [ 4. TTS ]       ──► Piper Local ONNX (vi_VN-viss-low.onnx) ──► audio/tts/*.wav
       │
       ▼
 [ 5. SYNC ]      ──► Audio Time-stretching (atempo filter) ──► audio/synced/combined.wav
       │
       ▼
 [ 6. RENDER ]    ──► FFmpeg NVENC (h264_nvenc/hevc_nvenc) ──► output/final.mp4
```

### Module Responsibilities:
- `PipelineManager` (`engine/autodub/pipeline/manager.py`): Điều phối các stage, quản lý checkpointing (`pipeline.partial.json`), retry, pause, resume và cancel signal.
- `JobStore` (`engine/autodub/jobs/job_store.py`): SQLite WAL Database (`.autodub/jobs.db`) quản lý trạng thái FIFO Queue cho nhiều project.

---

## 3. Resource & VRAM Allocation Audit (4GB GTX 1650 Ti)

Toàn bộ các tác vụ AI trong v0.1 được tối ưu hóa cho giới hạn 4GB VRAM:

| Tác vụ AI | Engine / Model | VRAM tiêu thụ | CPU / System RAM |
| :--- | :--- | :--- | :--- |
| **STT** | `faster-whisper` (`small`, `float16`) | ~1,200 MB | ~1.5 GB RAM |
| **Translation** | `Qwen2.5-3B-Instruct` (Q4_K_M GGUF via llama.cpp CUDA) | ~2,200 MB | ~2.0 GB RAM |
| **TTS** | `Piper` (ONNX C++ runtime) | ~150 MB | ~300 MB RAM |
| **Render** | `FFmpeg NVENC` (`h264_nvenc`) | ~450 MB | ~500 MB RAM |
| **[V0.2 NEW] SD Image**| `Stable Diffusion 1.5 + LCM-LoRA` (`fp16` CPU offload) | ~2,200 MB | ~3.5 GB RAM |

> [!CAUTION]
> **Quy tắc An Toàn VRAM**: Với card 4GB VRAM, **tuyệt đối không chạy Qwen2.5 (2.2GB) và Stable Diffusion (2.2GB) đồng thời**. Hệ thống v0.2 bắt buộc phải nạp/giải phóng model tuần tự (Sequential Model Offloading).

---

## 4. Front-End Desktop Audit (`desktop/`)

- **Framework**: Tauri + React + TypeScript + Vite.
- **Styling**: TailwindCSS.
- **UI State**: Quản lý qua Custom Hooks & API Services kết nối với Python Engine CLI via Subprocess / RPC.
- **Cấu trúc hiện tại**: Có sẵn UI Dashboard hiển thị tiến trình Job, Log Viewer và Project Setup Manager.

---

## 5. Existing Test Suites Audit (`engine/tests/`)

Hệ thống có **56 file test unit & integration** bao phủ:
- Stage Extractors, Transcribers, Translators, TTS, Synchronizers, Renderers.
- Job Store, Job Lock, Job Queue, Continuous Dialogue, Pronunciation verification.
- Phase 9, Phase 21, Phase 23 E2E Render Integration test.

---

## CHECKPOINT 0 CONFIRMATION

- [x] Đã đọc toàn bộ cấu trúc mã nguồn backend & frontend.
- [x] Đã xác định vị trí Entry Point chính (`engine/autodub/cli.py`).
- [x] Đã hiểu rõ quy trình hoạt động của Pipeline v0.1 (`MODE_DUBBING`).
- [x] Đã nắm bắt bộ Test Suite hiện có (56 test files).
- [x] Đã xác định cơ chế chạy dự án và giới hạn phần cứng (GTX 1650 Ti 4GB VRAM).
- [x] Đã sẵn sàng thực hiện **Phase 1: Baseline Test**!
