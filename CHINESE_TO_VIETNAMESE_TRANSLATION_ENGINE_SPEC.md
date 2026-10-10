# 📋 THIẾT KẾ & QUY CHUẨN KỸ THUẬT: CHINESE → VIETNAMESE TRANSLATION ENGINE

**Dự án:** AutoDubStudio (Local AI Video Translation & Dubbing Application)  
**Thiết bị đích (Target Hardware):** Intel i5-10300H (4C/8T), RAM 16GB, GPU GTX 1650 Ti (4GB VRAM), Windows, Local Ollama.

---

## 🎯 1. TỔNG QUAN MỤC TIÊU & QUY TẮC NGUYÊN TẮC

1. **Nâng cấp Translation Engine:** Dịch phụ đề phim/video dài 1–3 giờ từ **Tiếng Trung (zh) $\rightarrow$ Tiếng Việt (vi)**.
2. **Local 100% via Ollama:** Không phụ thuộc Cloud API, không chi phí, bảo mật dữ liệu.
3. **Model mặc định có thể cấu hình (Central Config):** 
   - `TRANSLATION_MODEL = "qwen3:4b"`
   - `TRANSLATION_LANGUAGE = "zh-vi"`
   - Kiến trúc động cho phép thay đổi model (ví dụ `qwen3:8b`, `gemma3:4b`) thông qua **System Settings UI** mà không hard-code trong source.
4. **Tham số dịch thuật:** `temperature = 0.15`, `thinking = OFF` (Tối ưu tốc độ, khóa sáng tạo, tránh giải thích dài dòng).
5. **CẤM HARD-CODE RULE:** Không sử dụng `.replace()` hay các mảng từ/câu cố định (ví dụ `爸爸 -> Bố`, `Good night -> ...`) để vá lỗi dịch thuật. Tất cả dựa vào **Context + Entity Memory + Glossary + LLM + QA Loop**.
6. **TTS Gate Lock:** Tốc độ TTS luôn cố định **`1.00x`**. Âm thanh lồng tiếng TTS **chỉ được phép trigger** sau khi phụ đề đạt **`QA PASS`** hoặc qua 1 vòng **`AI REPAIR QA PASS #2`**.

---

## 🏗️ 2. KIẾN TRÚC TRANSLATION ENGINE TOÀN DIỆN

```text
                     CHINESE SRT (1–3h)
                             │
                             ▼
                     Context Builder
                       (±3 lines)
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
       Entity Memory                    Glossary
      (Locked Entity)             (Data-driven Memory)
              │                             │
              └──────────────┬──────────────┘
                             ▼
                      Ollama Client
            (Model: Configurable | Temp: 0.15 | Thinking: OFF)
                             │
                             ▼
                    Structured Parser
                             │
                       JSON VALID?
                        /         \
                      YES          NO
                       │            │
                       │          RETRY (Max 2)
                       │            │
                       │        FAIL → HUMAN_REVIEW
                       ▼
                  Output Sanitizer
             (Format Lọc Markdown/Quotes)
                             │
                             ▼
                7-Point Translation QA
                             │
                  ┌──────────┴──────────┐
                  ▼                     ▼
                PASS                   FAIL
                  │                     │
                  │                 AI REPAIR (Vòng 1 duy nhất)
                  │                     │
                  │                     ▼
                  │                  QA #2
                  │                 /     \
                  │               PASS    FAIL
                  │                │        │
                  └────────┬───────┘        ▼
                           ▼           HUMAN_REVIEW
                     FINAL VIETSUB
                           │
                           ▼
                    TTS GATE CHECK
                           │
                       QA PASS?
                      /       \
                    YES        NO
                     │          │
                     ▼          ▼
                    TTS       BLOCK
                  (1.00x)
```

---

## 📋 3. QUY TRÌNH 7-POINT TRANSLATION QA VERIFICATION

Mỗi dòng dịch bắt buộc chạy qua **7 chỉ số đánh giá tự động** trước khi phê duyệt:

1. **Meaning Preservation (Nghĩa cốt lõi):** Đảm bảo giữ đúng ý chính và thông điệp ban đầu.
2. **Entity Preservation (Tên thực thể & Nhân vật):** Giữ đúng các danh từ riêng, tên nhân vật theo Entity Memory đã được xác nhận.
3. **Pronoun & Relationship (Xưng hô & Quan hệ):** Chuẩn xác đại từ xưng hô dựa trên ngữ cảnh 3 câu trước và 3 câu sau.
4. **Number Preservation (Con số & Thời gian):** Khớp chính xác 100% các con số, thời gian, số lượng.
5. **Hallucination Protection (Chống ảo giác AI):** Loại bỏ việc tự bịa ra nhân vật, sự kiện, đồ vật không tồn tại trong bản gốc.
6. **Natural Vietnamese (Văn phong thuần Việt):** Đảm bảo câu thoại tự nhiên, mượt mà khi đọc lồng tiếng.
7. **Output Integrity (Tính toàn vẹn đầu ra):** 
   - Không chứa tiếng Anh đệm/giải thích (`This translation maintains...`).
   - Không dính Markdown (`**...**`).
   - Không bị rò rỉ System Instruction hay rác JSON.
   - Không trả về nhiều bản dịch mâu thuẫn trong cùng một kết quả.

---

## 🗂️ 4. PHÂN CHIA TRÁCH NHIỆM RÕ RÀNG TRONG CODE PIPELINE

- **Structured Parser:** Kiểm tra cấu trúc JSON `{"translation": "..."}` từ raw Ollama response. Nếu sai JSON $\rightarrow$ Retry. Nếu Retry thất bại $\rightarrow$ Đẩy sang status `HUMAN_REVIEW`.
- **Output Sanitizer:** Chỉ làm nhiệm vụ **Format Correction** (Loại bỏ quotes thừa, strip space, xóa bớt markdown remnants). **TUYỆT ĐỐI KHÔNG SỬA NGHĨA CỦA TỪ**.
- **Translation QA:** Đánh giá tính toàn vẹn ngữ nghĩa và định dạng qua **7-Point QA Check**.
- **AI Repair:** Chạy **tối đa 1 vòng duy nhất**. Nhận Original Chinese + Current Vietnamese + QA Error List + Context ±3 + Entity Memory + Glossary để tạo bản sửa mới. Nếu QA lần 2 vẫn FAIL $\rightarrow$ Chuyển sang `HUMAN_REVIEW`.

---

## 📊 5. BỘ TIÊU CHÍ BENCHMARK 300 SEGMENTS (CHINESE → VIETNAMESE)

Không benchmark bằng mock random, sử dụng 300 dòng subtitle Tiếng Trung thực tế từ ứng dụng phân làm 3 nhóm:
- **100 câu Dễ (Easy):** Chào hỏi, câu ngắn độc lập (`你好`, `谢谢`, `快走`).
- **100 câu Ngữ cảnh (Contextual):** Câu thoại phụ thuộc đại từ và hội thoại liên tiếp (`你去哪儿？`, `爸爸已经走了。`).
- **100 câu Khó (Hard):** Thành ngữ, câu thiếu chủ ngữ, từ cổ trang, từ lóng, xưng hô phức tạp nhiều nhân vật.

### 📐 Thang điểm Chấm Benchmark (/100 điểm):
- **Meaning:** 20 điểm
- **Natural Vietnamese:** 20 điểm
- **Entity:** 15 điểm
- **Context Consistency:** 15 điểm
- **Hallucination Free:** 15 điểm
- **Output Integrity:** 10 điểm
- **Overall Consistency:** 5 điểm

---

## 🚀 6. LỘ TRÌNH TRIỂN KHAI 4 PHASE (ROADMAP)

### 🔹 Phase A — Core Architecture
- Central Config (`TRANSLATION_MODEL=qwen3:4b`, `TRANSLATION_LANGUAGE=zh-vi`).
- Context Builder (±3 câu subtitle).
- Data-driven Entity Memory (Ưu tiên Locked Entity hơn LLM) & Glossary System.

### 🔹 Phase B — Safety & Quality Pipeline
- Structured Output Parser (Khóa JSON & Retry mechanism).
- Dedicated Output Sanitizer (Chỉ xử lý Format).
- Engine 7-point Translation QA.
- Controlled AI Repair Loop (Tối đa 1 lần retry) & TTS Gate Lock (1.00x).

### 🔹 Phase C — UI Modernization
- Cập nhật SubtitleEditor UI: Bảng điều khiển 7 chỉ số QA, Nút kích hoạt AI Repair thủ công/tự động, Khóa TTS khi QA FAIL.
- Cập nhật SystemSettings UI: Cho phép đổi linh hoạt model Ollama (`Qwen3:4b`, `Qwen3:8b`, `Gemma3:4b`).

### 🔹 Phase D — Verification & Benchmark
- Chạy 15+ Unit tests backend.
- Integration test thực tế kết nối Ollama với câu mẫu `爸爸已经走了。` $\rightarrow$ `Bố đi rồi.`.
- Thực thi Benchmark 300 segments trên GPU GTX 1650 Ti 4GB và xuất báo cáo chi tiết.
- Kiểm tra toàn bộ Frontend Build & Python Engine Runtime.
