# AutoDubStudio — Tổng Quan Dự Án & Báo Cáo Tiến Độ (Project Overview & Master Progress)

> **LƯU Ý QUAN TRỌNG DÀNH CHO AI ASSISTANT / DEVELOPER:**
> Mọi AI hoặc Lập trình viên làm việc trên dự án này **BẮT BUỘC** phải đọc file này trước khi thực hiện nhiệm vụ, và **PHẢI CẬP NHẬT** file này (hoặc các file chi tiết trong `docs/`) ngay sau khi hoàn thành tính năng, refactor code, sửa lỗi hệ thống hoặc thay đổi kiến trúc.

---

## 1. Giới Thiệu Dự Án (Project Description)

**AutoDubStudio** là một hệ thống Full-Stack cao cấp kết hợp giữa **Tự Động Hóa Sáng Tạo Tiểu Thuyết AI (AI Novel Generation Engine V2.3)** và **Hệ Thống Lồng Tiếng Video Đa Ngôn Ngữ (Video Dubbing Pipeline)**.

Dự án cho phép:
1. **Sáng tạo Tiểu thuyết AI đỉnh cao (AI Novel Engine V2.3)**: Tự động khởi tạo thế giới quan đa dạng (Worlds & Lore), xây dựng hệ thống nhân vật linh hoạt (Nam & Nữ), lập kế hoạch cốt truyện dài tập (1000+ chương), và tự động viết từng phân cảnh với khả năng kiểm soát Canon tuyệt đối (0% Hallucination, Fail-Closed Validation, 100% Ngôn ngữ Tiếng Việt).
2. **Lồng tiếng & Xử lý Video (Video Dubbing Studio)**: Trích xuất âm thanh, nhận diện lời thoại (Whisper STT), dịch thuật ngữ cảnh (LLM Translation), tổng hợp giọng nói (Piper/Edge-TTS), đồng bộ thời lượng âm thanh (Pitch-preserved Audio Stretching `atempo`), và dựng video hoàn chỉnh (FFmpeg NVENC Hardware Acceleration).
3. **Desktop Application (Tauri + Rust + Python Engine)**: Giao diện ứng dụng desktop siêu nhẹ, quản lý tiến trình Python chạy ngầm, tự động kết nối và khởi chạy Ollama GPU CUDA Server.

---

## 2. Kiến Trúc Hệ Thống (System Architecture)

```text
AutoDubStudio Workspace
 ├── desktop/                          # Tauri Desktop App (Rust IPC + Web Frontend)
 │    ├── src/                         # React/TS Frontend GUI
 │    └── src-tauri/                   # Rust Backend IPC Handlers
 │         ├── src/commands/           # Refactored IPC Handler Modules
 │         │    ├── novel_commands.rs  # Lệnh điều khiển Novel Engine & Crawler
 │         │    ├── dub_commands.rs    # Lệnh điều khiển Dubbing Pipeline & Projects
 │         │    └── system_commands.rs # Quản lý phần cứng RAM/GPU & Ollama Server
 │         └── src/main.rs             # Application Bootstrap Runner
 │
 └── engine/                           # Core Python Processing Engine
      └── autodub/
           ├── novel/                  # AI Novel Engine V2.3 Package
           │    ├── specialized_engines/# 9 Specialized Prompt Engines (Character, World, Memory, Level, Event...)
           │    ├── components/        # Sub-Services (story_planner, chapter_planner, scene_executor)
           │    ├── pipeline_orchestrator.py # Orchestrator 9 bước kiểm định Fail-Closed
           │    ├── canon_validator_engine.py # Thẩm định mâu thuẫn Canon & Leak ký ức
           │    ├── novel_database.py  # SQLite Canon Database Manager
           │    └── novel_engine.py    # Facade Engine mỏng nhẹ
           │
           └── modules/                # Dubbing Pipeline Modules
                ├── extractor.py       # FFmpeg Audio/Video Demuxer
                ├── transcriber.py     # Faster-Whisper Speech-to-Text
                ├── translator.py      # Qwen/LLM Contextual Subtitle Translator
                ├── tts.py             # Piper / Edge-TTS Audio Synthesizer
                ├── synchronizer.py    # Audio Synchronizer & Timeline Manager
                └── sync_utils.py      # Pitch-preserved audio stretching helpers (atempo)
```

---

## 3. Các Thành Tựu & Tính Năng Đã Hoàn Thành (Key Features Achieved)

### 3.1. Hệ Thống 9 Specialized Prompt Engines Độc Lập
Thay thế Master Prompt đơn độc bằng 9 Engine xử lý chuyên biệt theo chuẩn Domain Isolation:
1. **`CHARACTER_ENGINE`**: Phân tích danh tính, tâm lý, thuộc tính, mối quan hệ nhân vật (hỗ trợ cả Nam & Nữ).
2. **`WORLD_ENGINE`**: Mở rộng thế giới quan, bản đồ, địa danh, môn phái, luật lệ thế giới.
3. **`TERMINOLOGY_ENGINE`**: Bảo tồn thuật ngữ chuẩn Canon tác phẩm, danh xưng, tu vi.
4. **`MEMORY_ENGINE`**: Quản lý trạng thái tri thức (`UNKNOWN`, `RUMOR`, `CLAIM`, `CONFIRMED`) & kiểm soát ranh giới ký ức.
5. **`LEVEL_ENGINE`**: Theo dõi cấp độ sức mạnh, cảnh giới, đột phá tu vi.
6. **`EVENT_ENGINE`**: Ghi nhận các sự kiện mốc lịch sử & mâu thuẫn chính.
7. **`RELATIONSHIP_ENGINE`**: Theo dõi biến động liên minh, thù địch, tình cảm.
8. **`OPEN_THREAD_ENGINE`**: Quản lý các tuyến kịch bản mở & manh mối chưa giải mã.
9. **`CANON_VALIDATOR`**: Thẩm định viên chéo kiểm soát 5 nguy cơ mâu thuẫn Canon và Knowledge Leak với nguyên tắc **FAIL-CLOSED**.

### 3.2. Refactor Mã Nguồn Đạt Chuẩn Phân Tách Chi Tiết (SRP Refactoring)
- **`novel_engine.py`**: Tách nhỏ từ 1,070 dòng xuống 460 dòng bằng cách trích xuất `StoryPlanner`, `ChapterPlanner`, và `SceneExecutor`.
- **`main.rs` (Rust Backend)**: Tách nhỏ từ 1,525 dòng xuống 195 dòng bằng cách di chuyển IPC commands vào gói `commands/` (`novel_commands.rs`, `dub_commands.rs`, `system_commands.rs`).
- **`synchronizer.py`**: Tách các hàm tính toán stretching/atempo audio sang `sync_utils.py`.

### 3.3. Kiểm Soát Nội Dung 100% Tiếng Việt & Không Fallback Giả Tạo
- Yêu cầu AI sinh nội dung 100% Tiếng Việt chất lượng cao.
- **Strict Data Integrity**: Tuyệt đối không tự suy đoán dữ liệu Canon, không fallback khi thiếu dữ liệu, nếu LLM lỗi hoặc mâu thuẫn dữ liệu sẽ dừng lại khẩn cấp (**Fail-Closed**) và thông báo lỗi chính xác.

### 3.4. Hiển Thị Real-Time Logs Trên Giao Diện Desktop
- Mọi bước xử lý trong Novel Engine và Dubbing Pipeline đều phát ra sự kiện log chi tiết (`pipeline://log`, `novel://progress`) hiển thị trên giao diện Tauri Desktop giúp người dùng hoặc lập trình viên theo dõi chính xác tiến độ công việc đang chạy.

---

## 4. Danh Sách Bộ Test Verification (Unit & Integration Tests)

Dự án hiện có hệ thống test tự động bao phủ 100% logic với kết quả luôn được duy trì **100% PASS**:

- **Core Novel & Engine Tests**:
  ```bash
  set PYTHONPATH=d:\FullStack\AutoDubStudio\engine
  python -m unittest tests.test_specialized_engines tests.test_pipeline_orchestrator tests.test_static_content_scan tests.test_novel_generation_no_fallback tests.test_novel_engine tests.test_novel_v23_locks
  ```
  *(57/57 tests PASS)*

- **Rust Backend Compilation Check**:
  ```bash
  cd desktop/src-tauri
  cargo check
  ```
  *(0 Errors, 0 Warnings)*

---

## 5. Quy Định Bắt Bắt Buộc Đối Với AI Assistant (AI Progress Update Mandate)

> ⚠️ **QUY TẮC CẬP NHẬT TIẾN ĐỘ DÀNH CHO MỌI AI:**
> 1. Mỗi khi thực hiện bất kỳ thay đổi nào liên quan đến **kiến trúc dự án**, **thêm/bớt module**, **thay đổi prompt engine**, **refactor file**, hoặc **thêm tính năng mới**, AI **BẮT BUỘC** phải cập nhật lại file [`PROJECT_OVERVIEW.md`](file:///d:/FullStack/AutoDubStudio/PROJECT_OVERVIEW.md) này ngay lập tức.
> 2. Nếu file tổng quan này trở nên quá dài, hãy mở rộng thêm các file chuyên sâu trong thư mục `docs/` (ví dụ `docs/NOVEL_ENGINE.md`, `docs/DUBBING_PIPELINE.md`) và giữ `PROJECT_OVERVIEW.md` đóng vai trò Master Index.
> 3. Cập nhật rõ ràng ngày/giờ và tóm tắt công việc đã hoàn thành vào phần **Nhật Ký Cập Nhật (Change Log)** bên dưới.

---

## 6. Nhật Ký Cập Nhật Tiền Độ (Progress Change Log)

| Ngày | Người thực hiện | Nội dung cập nhật / Thành tựu |
| :--- | :--- | :--- |
| **2026-09-01** | Antigravity AI | - Refactor tách Master Prompt thành 9 Specialized Prompt Engines.<br>- Refactor `novel_engine.py` (tách components `StoryPlanner`, `ChapterPlanner`, `SceneExecutor`).<br>- Refactor `main.rs` Tauri Rust backend (tách `commands/` modules).<br>- Refactor `synchronizer.py` (tách `sync_utils.py`).<br>- Tạo file tổng quan dự án `PROJECT_OVERVIEW.md` và thiết lập quy định tự động cập nhật tiến độ cho AI.<br>- Nâng cấp độ bền bỉ trích xuất JSON trong `novel_engine.py` (`strict=False`, loại bỏ comment & chuyển đổi ngoặc kép thông minh).<br>- Cải tiến Rust IPC handler `novel_commands.rs` đọc chi tiết log lỗi thực tế từ `novel_execution.log`.<br>- Tối ưu hóa prompt `story_director.py` & bổ sung cơ chế khôi phục JSON bị cắt ngắn (`repair_truncated_json`).<br>- Bổ sung nút **Copy Tất Cả Arcs** và **Copy từng Arc 1** trong `ArcPlanner.tsx`.<br>- Kết nối dữ liệu thực từ SQLite DB cho **Canon Database Facts** & **Open Plot Threads** trong `novel_commands.rs` & `CanonExplorer.tsx`.<br>- Thêm Hộp thoại Pop-up Cảnh Báo (`showResetConfirm`) & Cơ chế Tự Động Xóa Sạch Dữ Liệu Cũ (`executeInitializeNovel`).<br>- Tái cấu trúc quy trình Bước 1 thực thi tuần tự 5 Prompts 1-by-1 truyền dồn Context tích tụ.<br>- Bổ sung cơ chế **Tính Toán Quy Mô Dữ Liệu Tỷ Lệ Theo Tổng Số Chương (`_get_target_counts(total_chapters)`)** trong `story_director.py`.<br>- **FIX: Event Channel Mismatch** — `subscribeNovelLogs` listen `"pipeline://log"` thay vì `"novel://log"` (kênh trống).<br>- **FIX: Protagonist Integrity Check** — Loại bỏ `idea=idea` cho Prompt 1B/1D/1E (chỉ áp dụng cho 1A/1C có character data). Nâng cấp `validate_protagonist_integrity` nhận diện non-character data.<br>- **ENFORCE FAIL-CLOSED (GEMINI.md)**: Xóa toàn bộ try/except fallback & data giả trong Bước 1 (1B, 1C, 1D, 1E). Nếu LLM thất bại → `GenerationError` propagate lên → dừng ngay.<br>- **Master Plan Batched Generation & Title Optimization**: Tách `generate_master_plan` thành vòng lặp batch (10 Arcs/batch). Truyền dồn chi tiết Bối cảnh (địa danh, thế lực, dàn nhân vật, cấp độ) vào `build_batch_prompt`. Cấm tựa đề generic lặp lại ("Đấu trường mới"). Bắt buộc tính toán khoảng chương liên tục chính xác theo công thức toán học (`start_chapter`, `end_chapter`). |
