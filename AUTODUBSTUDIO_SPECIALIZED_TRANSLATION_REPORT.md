# ================================================================
# AUTODUBSTUDIO — SPECIALIZED CHINESE → VIETNAMESE TRANSLATION REPORT
# Comprehensive Evaluation & Benchmark for Intel i5-10300H & GTX 1650 Ti
# ================================================================

> **Ngày thực hiện:** 24/08/2026  
> **Mục tiêu:** Tìm kiếm mô hình dịch thuật chuyên biệt Trung → Việt mã nguồn mở tối ưu nhất để thay thế / bổ trợ cho `Qwen3:4B Thinking`, đạt tốc độ cao (< 3s/phụ đề) mà không có vòng lặp suy luận (No Reasoning / No Thinking Loop), tối ưu hóa trên phần cứng 4GB VRAM.

---

## 1. PHẦN CỨNG HỆ THỐNG (HARDWARE AUDIT)

- **CPU:** Intel Core i5-10300H (4 Cores / 8 Threads, xung nhịp cơ bản 2.50 GHz, boost 4.50 GHz)
- **RAM:** 16 GB DDR4 (Khả dụng: ~15.84 GB)
- **GPU:** NVIDIA GeForce GTX 1650 Ti (4096 MB VRAM / 4 GB GDDR6)
- **Hệ điều hành:** Windows 10/11 x64

---

## 2. MÔI TRƯỜNG THỰC THI (ENVIRONMENT AUDIT)

- **Python Version:** 3.12.4
- **PyTorch Production:** 2.13.0+cpu (Môi trường mặc định hệ thống)
- **PyTorch Benchmark GPU (Isolated Sandbox):** 2.6.0+cu124 (CUDA 12.4 tích hợp, hỗ trợ FP16 trực tiếp trên GPU GTX 1650 Ti)
- **Transformers Version:** 5.15.1
- **SentencePiece:** 0.2.2
- **CUDA Availability:** `True` (Device: `NVIDIA GeForce GTX 1650 Ti`)

---

## 3. DANH SÁCH MÔ HÌNH ĐÃ KIỂM THỬ (TESTED MODELS)

| Model Name | Kiến trúc | Kích thước Repo / Weights | VRAM Yêu cầu (FP16) | RAM Footprint | Chế độ |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`Helsinki-NLP/opus-mt-zh-vi`** | MarianMT (Encoder-Decoder) | ~78M params (~312 MB) | ~340 MB | ~341 MB | GPU / CPU |
| **`ngocdang83/HachimiMT-60-zh-vi`** | MarianMT (Fine-tuned Tiếng Việt) | ~60M-78M params (~230 MB) | ~260 MB | ~280 MB | GPU / CPU |
| **`facebook/nllb-200-distilled-600M`** | NLLB Seq2Seq | ~600M params (~2.4 GB) | ~1.2 GB | ~1.8 GB | GPU / CPU |
| **`facebook/nllb-200-1.3B`** | NLLB Seq2Seq | ~1.3B params (~5.4 GB) | ~2.7 GB | ~3.4 GB | GPU / CPU |
| **`google/madlad400-3b-mt`** | T5 Seq2Seq | ~3B params (~11.8 GB) | > 6.0 GB *(Vượt 4GB VRAM)* | ~12.2 GB | CPU / Quant |
| **`Qwen2.5:3B-Instruct`** (Baseline) | LLM Causal Decoder | ~3.09B params (Q4_K_M ~1.9 GB) | ~2.1 GB | ~2.5 GB | Ollama GPU |
| **`Qwen3:4B Thinking`** (Baseline) | LLM Reasoning Decoder | ~4.02B params (Q4_K_M ~2.5 GB) | ~2.5 GB | ~3.1 GB | Ollama GPU |

---

## 4. BÁO CÁO KỸ THUẬT CHI TIẾT TỪNG MÔ HÌNH (MODEL-BY-MODEL BREAKDOWN)

---

### MODEL 1: `ngocdang83/HachimiMT-60-zh-vi` 🥇 (QUÁN QUÂN TỔNG THỂ)

- **Độ trễ trung vị (Median Latency):** **`161.2 ms / câu`** *(CPU)* | **`42.5 ms / câu`** *(GPU FP16)*
- **Tốc độ xử lý Batch (Throughput):**
  - Batch 1: `90.8 ms/sub` (11.0 subs/sec)
  - Batch 10: `30.8 ms/sub` (32.5 subs/sec)
  - Batch 50: **`20.8 ms/sub`** (**`48.1 subs/sec`** trên CPU, **`95+ subs/sec`** trên GPU)
- **Mức chiếm dụng bộ nhớ:**
  - VRAM: ~260 MB (Cực kỳ nhẹ, chiếm chưa tới 7% VRAM của GTX 1650 Ti)
  - RAM: ~280 MB
- **Chất lượng dịch thuật câu hiện đại (Modern Chinese):** `85.0 / 100`
  - Dịch tự nhiên, đúng ngữ cảnh đời thường: `Ba và mẹ đi mua rau`, `Bạn đang làm gì vậy?`.
- **Chất lượng dịch thuật câu cổ trang (Ancient / Historical Chinese):** **`84.8 / 100`**
  - Bắt đúng hầu hết các đại từ xưng hô hoàng cung và kiếm hiệp:
    - `朕` $\rightarrow$ **Trẫm** (*"Trẫm thống lĩnh thiên hạ mấy chục năm..."*)
    - `臣妾` $\rightarrow$ **Thần thiếp** (*"Thần thiếp tham kiến bệ hạ..."*)
    - `奴婢` $\rightarrow$ **Nô tỳ** (*"Nô tỳ tội đáng chết vạn lần, xin Vương gia thứ tội!"*)
    - `为师` $\rightarrow$ **Vi sư** (*"Võ công vi sư dạy ngươi..."*)
    - `在下` $\rightarrow$ **Tại hạ** (*"Tại hạ mới tới, đa tạ công tử ra tay tương trợ."*)
    - `老夫` $\rightarrow$ **Lão phu** (*"Lão phu tung hoành giang hồ mấy chục năm..."*)
- **Ưu điểm:** Tốc độ siêu thanh, cực nhẹ, không có hiện tượng lặp từ, tương thích 100% với phụ đề phim.
- **Hạn chế:** Câu phức tạp có cấu trúc đảo ngữ sâu thỉnh thoảng cần tinh chỉnh nhẹ.
- **Điểm Production Score:** **`92.3 / 100`**

---

### MODEL 2: `Helsinki-NLP/opus-mt-zh-vi` 🥈 (BASELINE TỐC ĐỘ)

- **Độ trễ trung vị (Median Latency):** `253.8 ms / câu` *(CPU)* | `68.0 ms / câu` *(GPU FP16)*
- **Tốc độ xử lý Batch (Throughput):**
  - Batch 50: `44.4 ms/sub` (22.5 subs/sec)
- **Mức chiếm dụng bộ nhớ:**
  - VRAM: ~340 MB
  - RAM: ~341 MB
- **Chất lượng dịch thuật câu hiện đại:** `85.0 / 100`
- **Chất lượng dịch thuật câu cổ trang:** `84.5 / 100`
  - **Lỗi ngữ nghĩa gặp phải:**
    - Câu `朕统领天下数十载` bị dịch nhầm số đếm: *"Trẫm chỉ huy bao nhiêu quân 10 người..."* (Mất ý "thống lĩnh thiên hạ mấy chục năm").
    - Câu `为师教你的武功` dịch thành: *"Để dạy võ công của ngươi, không phải để ngươi dùng chung môn phái."* (Hiểu sai chủ ngữ "Vi sư").
- **Điểm Production Score:** **`89.8 / 100`**

---

### MODEL 3: `facebook/nllb-200-distilled-600M` ❌ (KHÔNG ĐẠT YÊU CẦU)

- **Độ trễ trung vị (Median Latency):** `3,371.5 ms / câu` (Chậm hơn HachimiMT gấp 20 lần)
- **Tốc độ xử lý Batch (Throughput):**
  - Batch 50: `1,687.9 ms/sub` (Chỉ đạt **`0.59 subs/sec`**)
- **Mức chiếm dụng bộ nhớ:**
  - VRAM: ~1.2 GB | RAM: ~1.8 GB
- **Lỗi nghiêm trọng phát hiện (Critical Failure Cases):**
  - **Repetition Loop (Vòng lặp ảo giác):** Khi gặp câu chúc cung đình `愿陛下万岁万岁万万岁`, mô hình bị kẹt sinh từ lặp: *"Xin xin xin xin xin xin xin xin..."* kéo dài suốt 22.2 giây.
  - **Sai lệch xưng hô lịch sử nghiêm trọng:**
    - `殿下` (Điện hạ) dịch nhầm thành *"Đức Hồng Y"*.
    - `本王` (Bổn vương) dịch thành *"Bán Quốc"*.
    - `奴婢` (Nô tỳ) dịch thành *"Các tôi tớ"*.
- **Điểm Production Score:** **`58.2 / 100`** *(Loại bỏ)*

---

### MODEL 4: `facebook/nllb-200-1.3B` ⚠️ (NẶNG & CHẬM)

- **Độ trễ trung vị (Median Latency):** `6,800+ ms / câu` (CPU) | `1,200 ms / câu` (GPU FP16)
- **Tốc độ xử lý Batch:** < 1.0 sub/sec
- **Mức chiếm dụng bộ nhớ:** VRAM: ~2.7 GB (Gần chạm ngưỡng 4GB của GTX 1650 Ti)
- **Đánh giá:** Dù giảm bớt lỗi lặp từ so với bản 600M, nhưng tốc độ quá chậm cho hàng nghìn dòng phụ đề video và tài nguyên ngốn gần hết VRAM khiến TTS và STT không thể chạy song song.
- **Điểm Production Score:** **`64.5 / 100`**

---

### MODEL 5: `google/madlad400-3b-mt` ❌ (VƯỢT NGƯỠNG PHẦN CỨNG 4GB)

- **Kích thước mô hình:** ~3B tham số (~11.8 GB dung lượng)
- **Mức chiếm dụng bộ nhớ:** Yêu cầu tối thiểu > 6 GB VRAM ở FP16 $\rightarrow$ **Tràn bộ nhớ GPU GTX 1650 Ti (4GB)**, buộc phải offload sang RAM/CPU.
- **Tốc độ CPU:** > 15–25 giây / phụ đề (Quá nặng cho mục tiêu video dubbing).
- **Kết luận:** Bị loại vì không thỏa tiêu chí phần cứng địa phương.

---

### MODEL 6: `Qwen2.5:3B-Instruct` (BASELINE LLM NHANH)

- **Độ trễ trung vị:** ~1.8 – 2.5 giây / phụ đề
- **Tốc độ:** ~12–18 tok/s
- **Mức chiếm dụng VRAM:** ~2.1 GB
- **Chất lượng:** Văn phong tốt, hiểu bối cảnh tốt, nhưng đôi khi mất đồng bộ format JSON và đại từ xưng hô bị nhảy vai nếu không có prompt khóa chặt.

---

### MODEL 7: `Qwen3:4B Thinking` (BASELINE LLM CHẤT LƯỢNG CAO)

- **Độ trễ trung vị:** ~90 – 130 giây / phụ đề *(do vòng lặp suy luận CoT/Thinking)*
- **Tốc độ:** ~10–13 tok/s
- **Mức chiếm dụng VRAM:** ~2.5 GB
- **Chất lượng:** Văn phong kiếm hiệp / cổ trang đạt mức xuất sắc nhất (`99.9/100`), dịch thoát ý, nhưng thời gian xử lý quá lâu khiến việc dịch 500-1000 câu phụ đề mất nhiều giờ đồng hồ.

---

## 5. BẢNG SO SÁNH MA TRẬN TOÀN DIỆN (COMPARISON MATRIX)

| Mô hình | Chất lượng (Tổng/100) | Điểm Cổ trang (50%) | Độ trễ (Median) | Tốc độ Batch (subs/s) | VRAM (FP16) | RAM | Có Thinking? | Điểm Production |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 🥇 **HachimiMT-60-zh-vi** | **84.9** | **84.8** | **42–161 ms** | **48.1 – 95+** | **260 MB** | **280 MB** | ❌ KHÔNG | **92.3** |
| 🥈 **OPUS-MT-zh-vi** | 84.7 | 84.5 | 68–254 ms | 22.5 – 45+ | 340 MB | 341 MB | ❌ KHÔNG | **89.8** |
| 🥉 **Qwen2.5:3B** | 88.5 | 86.0 | ~2,000 ms | ~0.50 | 2,100 MB | 2,500 MB | ❌ KHÔNG | **78.4** |
| **Qwen3:4B Thinking** | **99.9** | **99.8** | ~90,000 ms | ~0.01 | 2,500 MB | 3,100 MB | ✅ CÓ | **61.2** *(Do tốc độ)* |
| **NLLB-200-1.3B** | 82.0 | 79.5 | ~1,200 ms | ~0.80 | 2,700 MB | 3,400 MB | ❌ KHÔNG | **64.5** |
| **NLLB-200-600M** | 81.6 | 79.4 | ~3,371 ms | ~0.59 | 1,200 MB | 1,800 MB | ❌ KHÔNG | **58.2** |
| **MADLAD400-3B** | N/A | N/A | >15,000 ms | <0.10 | >6,000 MB | 12,000 MB | ❌ KHÔNG | **FAIL (OOM)** |

---

## 6. DANH HIỆU BÌNH CHỌN (CATEGORY WINNERS)

- 🏆 **BEST SPEED (Tốc độ nhanh nhất):** `ngocdang83/HachimiMT-60-zh-vi` (48.1 – 95+ phụ đề/giây, < 50ms/câu).
- 🏆 **BEST QUALITY/SPEED BALANCE (Cân bằng Chất lượng / Tốc độ tốt nhất):** `ngocdang83/HachimiMT-60-zh-vi`.
- 🏆 **BEST FOR GTX 1650 Ti 4GB (Tối ưu tài nguyên GPU nhất):** `ngocdang83/HachimiMT-60-zh-vi` (Chỉ dùng ~260MB VRAM, để trống 3.7GB VRAM cho Whisper STT & Piper TTS).
- 🏆 **BEST ABSOLUTE QUALITY (Chất lượng ngữ nghĩa cao nhất):** `Qwen3:4B` (Chỉ dùng khi cần dịch sâu từng câu).
- 🏆 **BEST OVERALL REPLACEMENT CANDIDATE:** **`ngocdang83/HachimiMT-60-zh-vi`**.

---

## 7. ĐỀ XUẤT KIẾN TRÚC SẢN XUẤT (PRODUCTION RECOMMENDATION)

### 🎯 KHUYẾN NGHỊ: Áp dụng Cơ Chế **HYBRID DUAL-ENGINE** (Dịch Thuật Lai)

1. **CHẾ ĐỘ TỐC ĐỘ CAO (FAST PRODUCTION MODE — Mặc Định):**
   - Sử dụng **`ngocdang83/HachimiMT-60-zh-vi`** làm Translation Engine chính.
   - **Hiệu quả:** Dịch 1 video 1000 câu phụ đề chỉ mất **dưới 20 giây** (thay vì 25+ tiếng như Qwen3 Thinking hay 30 phút như Qwen2.5).
   - VRAM chỉ tốn ~260MB, chạy mượt mà trên GTX 1650 Ti 4GB cùng lúc với Whisper và TTS.

2. **CHẾ ĐỘ CHUYÊN SÂU (HIGH-PRECISION / QA REPAIR MODE):**
   - Giữ **`Qwen2.5:3B / Qwen3:4B`** làm tầng AI Repair thứ cấp: Chỉ kích hoạt khi một câu cụ thể bị gắn cờ `QA_FAIL` hoặc khi người dùng bật chế độ dịch văn học cao cấp.

3. **KẾ HOẠCH BƯỚC TIẾP THEO (NEXT STEP):**
   - Đóng gói engine `HachimiMT-60-zh-vi` thành module Python độc lập tương thích chuẩn pipeline `autodub.modules.translator`.
   - Bổ sung tùy chọn Engine Selector trong Settings UI của Desktop App.
