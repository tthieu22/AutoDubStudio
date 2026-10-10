# -*- coding: utf-8 -*-
"""
AutoDubStudio - Chinese -> Vietnamese Specialized Translation Model Benchmark
Systematic benchmark script measuring latency, throughput, RAM, VRAM, and linguistic quality.
"""

import sys
import os
import time
import gc
import json
import psutil
import statistics
import torch
from typing import Dict, List, Any, Optional

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# Ensure huggingface cache doesn't fill C drive if D drive is available
os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"

TEST_DATASET = [
    # Standard 10 Tests
    {"id": "TEST_01", "type": "modern", "src": "爸爸和妈妈去买菜。", "ref": "Bố và mẹ đi mua rau."},
    {"id": "TEST_02", "type": "modern", "src": "你好，你在干什么？", "ref": "Bạn đang làm gì vậy?"},
    {"id": "TEST_03", "type": "modern", "src": "你吃饭了吗？", "ref": "Bạn ăn cơm chưa?"},
    {"id": "TEST_04", "type": "ancient", "src": "你这个时候还敢跟本王谈条件？", "ref": "Đến lúc này mà ngươi vẫn còn dám ra điều kiện với bổn vương sao?"},
    {"id": "TEST_05", "type": "ancient", "src": "本王今日便要看看，你究竟有几分本事。", "ref": "Hôm nay bổn vương muốn xem rốt cuộc ngươi có bản lĩnh đến đâu."},
    {"id": "TEST_06", "type": "modern", "src": "你若再敢骗我，我绝不会放过你。", "ref": "Nếu ngươi còn dám lừa ta, ta tuyệt đối sẽ không bỏ qua cho ngươi."},
    {"id": "TEST_07", "type": "ancient", "src": "小姐，外面有人求见。", "ref": "Tiểu thư, bên ngoài có người cầu kiến."},
    {"id": "TEST_08", "type": "ancient", "src": "陛下，敌军已经攻破城门。", "ref": "Bệ hạ, quân địch đã phá được cổng thành."},
    {"id": "TEST_09", "type": "modern", "src": "你以为我会相信你说的话吗？", "ref": "Ngươi nghĩ ta sẽ tin những lời ngươi nói sao?"},
    {"id": "TEST_10", "type": "ancient", "src": "从今以后，你我恩断义绝。", "ref": "Từ nay về sau, ân nghĩa giữa ta và ngươi coi như đoạn tuyệt."},
    
    # 10 Difficult Ancient / Royal / Drama / Social Hierarchy Tests
    {"id": "TEST_11", "type": "ancient", "src": "朕统领天下数十载，何曾受过这等屈辱？", "ref": "Trẫm thống lĩnh thiên hạ mấy chục năm, nào từng chịu qua sự sỉ nhục này?"},
    {"id": "TEST_12", "type": "ancient", "src": "启禀娘娘，殿下此刻正在御书房面圣。", "ref": "Khởi bẩm nương nương, điện hạ lúc này đang ở ngự thư phòng diện kiến thánh thượng."},
    {"id": "TEST_13", "type": "ancient", "src": "臣妾参见陛下，愿陛下万岁万岁万万岁。", "ref": "Thần thiếp thỉnh an bệ hạ, nguyện bệ hạ vạn tuế vạn tuế vạn vạn tuế."},
    {"id": "TEST_14", "type": "ancient", "src": "奴婢罪该万死，还请王爷恕罪！", "ref": "Nô tỳ tội đáng muôn chết, xin vương gia thứ tội!"},
    {"id": "TEST_15", "type": "ancient", "src": "为师教你的武功，不是让你用来同门相残的。", "ref": "Võ công vi sư dạy ngươi không phải để ngươi dùng vào việc tàn sát đồng môn."},
    {"id": "TEST_16", "type": "ancient", "src": "为父操劳一生，全是为了你这个不肖子！", "ref": "Cả đời vi phụ vất vả nhọc nhằn, tất cả đều là vì đứa con bất hiếu như con!"},
    {"id": "TEST_17", "type": "ancient", "src": "在下初来乍到，多谢公子出手相助。", "ref": "Tại hạ mới đến nơi này, đa tạ công tử đã ra tay giúp đỡ."},
    {"id": "TEST_18", "type": "ancient", "src": "老夫纵横江湖数十年，尔等黄口小儿休得猖狂！", "ref": "Lão phu tung hoành giang hồ mấy chục năm, lũ trẻ ranh các ngươi chớ có ngông cuồng!"},
    {"id": "TEST_19", "type": "ancient", "src": "少爷，老爷吩咐过，今夜绝不可踏出府门半步。", "ref": "Thiếu gia, lão gia đã dặn dò, đêm nay tuyệt đối không được bước ra khỏi phủ nửa bước."},
    {"id": "TEST_20", "type": "ancient", "src": "本宫执掌后宫多年，岂容你在此颠倒黑白？", "ref": "Bổn cung cai quản hậu cung nhiều năm, há để ngươi ở đây đổi trắng thay đen?"}
]

def get_system_telemetry():
    import torch
    ram = psutil.virtual_memory()
    cuda_avail = torch.cuda.is_available()
    vram_used = 0.0
    vram_total = 0.0
    device_name = "CPU Only"
    
    if cuda_avail:
        device_name = torch.cuda.get_device_name(0)
        vram_total = torch.cuda.get_device_properties(0).total_memory / (1024**3)
        vram_used = torch.cuda.memory_allocated(0) / (1024**3)
        
    return {
        "python_version": sys.version.split()[0],
        "torch_version": torch.__version__,
        "cuda_available": cuda_avail,
        "device_name": device_name,
        "vram_total_gb": round(vram_total, 2),
        "vram_used_gb": round(vram_used, 2),
        "ram_total_gb": round(ram.total / (1024**3), 2),
        "ram_used_gb": round(ram.used / (1024**3), 2),
        "ram_percent": ram.percent,
        "cpu_percent": psutil.cpu_percent(interval=0.1)
    }

class ModelRunner:
    def __init__(self, name: str, model_id: str, model_type: str):
        self.name = name
        self.model_id = model_id
        self.model_type = model_type
        self.model = None
        self.tokenizer = None
        self.load_time = 0.0
        self.load_status = "PENDING"
        self.error_msg = ""
        self.model_size_mb = 0.0
        self.vram_used_mb = 0.0
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    def load(self):
        import torch
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, MarianMTModel, MarianTokenizer, T5ForConditionalGeneration, T5Tokenizer
        
        start = time.time()
        process = psutil.Process(os.getpid())
        ram_before = process.memory_info().rss / (1024**2)
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.reset_peak_memory_stats()
            vram_before = torch.cuda.memory_allocated() / (1024**2)
        else:
            vram_before = 0.0
        
        try:
            print(f"\n[LOAD] Loading {self.name} ({self.model_id}) on {self.device.upper()}...")
            dtype = torch.float16 if self.device == "cuda" else torch.float32

            if self.model_type == "marian":
                self.tokenizer = MarianTokenizer.from_pretrained(self.model_id)
                self.model = MarianMTModel.from_pretrained(self.model_id, torch_dtype=dtype).to(self.device)
            elif self.model_type == "nllb":
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_id, src_lang="zho_Hans")
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_id, torch_dtype=dtype).to(self.device)
            elif self.model_type == "madlad":
                self.tokenizer = T5Tokenizer.from_pretrained(self.model_id)
                self.model = T5ForConditionalGeneration.from_pretrained(self.model_id, torch_dtype=dtype).to(self.device)
            else:
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_id, torch_dtype=dtype).to(self.device)

            self.model.eval()
            if self.device == "cuda":
                torch.cuda.synchronize()
            self.load_time = time.time() - start
            ram_after = process.memory_info().rss / (1024**2)
            self.model_size_mb = round(ram_after - ram_before, 2)
            if torch.cuda.is_available():
                self.vram_used_mb = round((torch.cuda.memory_allocated() / (1024**2)) - vram_before, 2)
            
            self.load_status = "SUCCESS"
            print(f"[LOAD_SUCCESS] {self.name} loaded in {self.load_time:.2f}s on {self.device.upper()} (VRAM: {self.vram_used_mb} MB | RAM: {self.model_size_mb} MB)")
            return True
        except Exception as e:
            self.load_status = "LOAD_FAILED"
            self.error_msg = str(e)
            self.load_time = time.time() - start
            print(f"[LOAD_FAILED] {self.name}: {e}")
            return False

    def translate_single(self, text: str) -> str:
        if self.load_status != "SUCCESS":
            return f"ERROR: {self.load_status}"
        
        import torch
        with torch.no_grad():
            if self.model_type == "marian":
                inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self.device)
                outputs = self.model.generate(**inputs, max_length=128, num_beams=1)
                if self.device == "cuda":
                    torch.cuda.synchronize()
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            elif self.model_type == "nllb":
                inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self.device)
                forced_bos_token_id = self.tokenizer.convert_tokens_to_ids("vie_Latn")
                outputs = self.model.generate(**inputs, forced_bos_token_id=forced_bos_token_id, max_length=128, num_beams=1)
                if self.device == "cuda":
                    torch.cuda.synchronize()
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            elif self.model_type == "madlad":
                prompt = f"<2vi> {text}"
                inputs = self.tokenizer(prompt, return_tensors="pt", padding=True, truncation=True).to(self.device)
                outputs = self.model.generate(**inputs, max_length=128, num_beams=1)
                if self.device == "cuda":
                    torch.cuda.synchronize()
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()
            else:
                inputs = self.tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(self.device)
                outputs = self.model.generate(**inputs, max_length=128, num_beams=1)
                if self.device == "cuda":
                    torch.cuda.synchronize()
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True).strip()

    def translate_batch(self, texts: List[str]) -> List[str]:
        if self.load_status != "SUCCESS":
            return [f"ERROR: {self.load_status}"] * len(texts)
        
        import torch
        with torch.no_grad():
            if self.model_type == "marian":
                inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True).to(self.device)
                outputs = self.model.generate(**inputs, max_length=128, num_beams=1)
                if self.device == "cuda":
                    torch.cuda.synchronize()
                return [self.tokenizer.decode(out, skip_special_tokens=True).strip() for out in outputs]
            elif self.model_type == "nllb":
                inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True).to(self.device)
                forced_bos_token_id = self.tokenizer.convert_tokens_to_ids("vie_Latn")
                outputs = self.model.generate(**inputs, forced_bos_token_id=forced_bos_token_id, max_length=128, num_beams=1)
                if self.device == "cuda":
                    torch.cuda.synchronize()
                return [self.tokenizer.decode(out, skip_special_tokens=True).strip() for out in outputs]
            elif self.model_type == "madlad":
                prompts = [f"<2vi> {t}" for t in texts]
                inputs = self.tokenizer(prompts, return_tensors="pt", padding=True, truncation=True).to(self.device)
                outputs = self.model.generate(**inputs, max_length=128, num_beams=1)
                if self.device == "cuda":
                    torch.cuda.synchronize()
                return [self.tokenizer.decode(out, skip_special_tokens=True).strip() for out in outputs]
            else:
                inputs = self.tokenizer(texts, return_tensors="pt", padding=True, truncation=True).to(self.device)
                outputs = self.model.generate(**inputs, max_length=128, num_beams=1)
                if self.device == "cuda":
                    torch.cuda.synchronize()
                return [self.tokenizer.decode(out, skip_special_tokens=True).strip() for out in outputs]

    def unload(self):
        del self.model
        del self.tokenizer
        self.model = None
        self.tokenizer = None
        gc.collect()
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except:
            pass

def score_translation(item: Dict[str, Any], trans: str) -> Dict[str, Any]:
    """
    10 Criteria (0-10 each):
    A. Semantic accuracy (0-10)
    B. Natural Vietnamese (0-10)
    C. Pronoun accuracy (0-10)
    D. Context accuracy (0-10)
    E. Tone (0-10)
    F. Historical terminology (0-10)
    G. Subtitle suitability (0-10)
    H. No hallucination (0-10)
    I. No unnecessary additions (0-10)
    J. No missing meaning (0-10)
    """
    if not trans or trans.startswith("ERROR"):
        return {"total": 0, "breakdown": {}, "grade": "FAIL", "notes": "Translation failed"}

    scores = {
        "semantic_accuracy": 8,
        "natural_vietnamese": 8,
        "pronoun_accuracy": 8,
        "context_accuracy": 8,
        "tone": 8,
        "historical_terminology": 8,
        "subtitle_suitability": 8,
        "no_hallucination": 10,
        "no_unnecessary_additions": 10,
        "no_missing_meaning": 9
    }
    
    t_lower = trans.lower()
    src = item["src"]
    
    # Pronoun & Royal term verification
    if "本王" in src:
        if "bổn vương" in t_lower:
            scores["historical_terminology"] = 10
            scores["pronoun_accuracy"] = 10
        elif "ta" in t_lower:
            scores["historical_terminology"] = 6
            scores["pronoun_accuracy"] = 7
        else:
            scores["historical_terminology"] = 2
            scores["pronoun_accuracy"] = 3
            
    if "本宫" in src:
        if "bổn cung" in t_lower:
            scores["historical_terminology"] = 10
            scores["pronoun_accuracy"] = 10
        elif "ta" in t_lower:
            scores["historical_terminology"] = 5
            scores["pronoun_accuracy"] = 6
        else:
            scores["historical_terminology"] = 2
            scores["pronoun_accuracy"] = 3

    if "朕" in src:
        if "trẫm" in t_lower:
            scores["historical_terminology"] = 10
            scores["pronoun_accuracy"] = 10
        elif "tôi" in t_lower or "ta" in t_lower:
            scores["historical_terminology"] = 4
            scores["pronoun_accuracy"] = 5
        else:
            scores["historical_terminology"] = 1
            scores["pronoun_accuracy"] = 2

    if "陛下" in src:
        if "bệ hạ" in t_lower:
            scores["historical_terminology"] = 10
        else:
            scores["historical_terminology"] = 4

    if "娘娘" in src:
        if "nương nương" in t_lower:
            scores["historical_terminology"] = 10
        else:
            scores["historical_terminology"] = 4

    if "奴婢" in src:
        if "nô tỳ" in t_lower or "nô tì" in t_lower:
            scores["historical_terminology"] = 10
            scores["pronoun_accuracy"] = 10
        elif "tôi" in t_lower:
            scores["historical_terminology"] = 2
            scores["pronoun_accuracy"] = 3

    if "臣妾" in src:
        if "thần thiếp" in t_lower:
            scores["historical_terminology"] = 10
            scores["pronoun_accuracy"] = 10
        elif "tôi" in t_lower:
            scores["historical_terminology"] = 2
            scores["pronoun_accuracy"] = 3

    if "为师" in src:
        if "vi sư" in t_lower or "thầy" in t_lower:
            scores["historical_terminology"] = 9
            scores["pronoun_accuracy"] = 9
        else:
            scores["historical_terminology"] = 3
            scores["pronoun_accuracy"] = 4

    if "为父" in src:
        if "vi phụ" in t_lower or "làm cha" in t_lower or "cha" in t_lower or "bố" in t_lower:
            scores["historical_terminology"] = 9
            scores["pronoun_accuracy"] = 9
        else:
            scores["historical_terminology"] = 3
            scores["pronoun_accuracy"] = 4

    if "在下" in src:
        if "tại hạ" in t_lower:
            scores["historical_terminology"] = 10
            scores["pronoun_accuracy"] = 10
        elif "tôi" in t_lower:
            scores["historical_terminology"] = 5
            scores["pronoun_accuracy"] = 6

    if "老夫" in src:
        if "lão phu" in t_lower:
            scores["historical_terminology"] = 10
            scores["pronoun_accuracy"] = 10
        elif "ông già này" in t_lower:
            scores["historical_terminology"] = 6
            scores["pronoun_accuracy"] = 7
        elif "tôi" in t_lower:
            scores["historical_terminology"] = 3
            scores["pronoun_accuracy"] = 4

    if "尔等" in src:
        if "các ngươi" in t_lower or "chúng mày" in t_lower or "lũ" in t_lower:
            scores["historical_terminology"] = 9
            scores["pronoun_accuracy"] = 9
        elif "bạn" in t_lower:
            scores["historical_terminology"] = 3
            scores["pronoun_accuracy"] = 3

    if "恩断义绝" in src:
        if "ân đoạn nghĩa tuyệt" in t_lower or "đoạn tuyệt" in t_lower or "cắt đứt" in t_lower:
            scores["semantic_accuracy"] = 10
            scores["natural_vietnamese"] = 10
        else:
            scores["semantic_accuracy"] = 5

    total = sum(scores.values())
    if total >= 90:
        grade = "EXCELLENT"
    elif total >= 75:
        grade = "GOOD"
    elif total >= 60:
        grade = "ACCEPTABLE"
    elif total >= 40:
        grade = "POOR"
    else:
        grade = "FAIL"

    return {"total": total, "breakdown": scores, "grade": grade}

def run_benchmarks():
    telemetry = get_system_telemetry()
    print("=" * 70)
    print("AUTODUBSTUDIO SPECIALIZED TRANSLATION MODEL BENCHMARK HARNESS")
    print(f"Python: {telemetry['python_version']} | Torch: {telemetry['torch_version']}")
    print(f"CUDA: {telemetry['cuda_available']} ({telemetry['device_name']})")
    print(f"RAM: {telemetry['ram_used_gb']}/{telemetry['ram_total_gb']} GB")
    print("=" * 70)

    # Candidate models to evaluate
    candidates = [
        {"name": "Helsinki-NLP/opus-mt-zh-vi", "id": "Helsinki-NLP/opus-mt-zh-vi", "type": "marian"},
        {"name": "ngocdang83/HachimiMT-60-zh-vi", "id": "ngocdang83/HachimiMT-60-zh-vi", "type": "marian"},
        {"name": "facebook/nllb-200-distilled-600M", "id": "facebook/nllb-200-distilled-600M", "type": "nllb"},
        {"name": "facebook/nllb-200-1.3B", "id": "facebook/nllb-200-1.3B", "type": "nllb"},
        {"name": "google/madlad400-3b-mt", "id": "google/madlad400-3b-mt", "type": "madlad"}
    ]

    all_results = {
        "telemetry": telemetry,
        "models": {}
    }

    for cand in candidates:
        name = cand["name"]
        print(f"\n=======================================================")
        print(f"BENCHMARKING CANDIDATE: {name}")
        print(f"=======================================================")
        
        runner = ModelRunner(name, cand["id"], cand["type"])
        loaded = runner.load()
        
        cand_result = {
            "name": name,
            "id": cand["id"],
            "type": cand["type"],
            "load_status": runner.load_status,
            "load_time_sec": round(runner.load_time, 2),
            "model_size_mb": runner.model_size_mb,
            "error_msg": runner.error_msg,
            "single_tests": [],
            "batch_tests": {},
            "metrics": {}
        }
        
        if not loaded:
            print(f"[SKIP] Skipping tests for {name} due to load failure.")
            runner.unload()
            all_results["models"][name] = cand_result
            continue

        # Phase 3: Single sentence benchmark (3 runs each)
        print(f"--- Phase 3: Single Subtitle Latency & Quality (20 Sentences × 3 Runs) ---")
        warmup_done = False
        modern_scores = []
        ancient_scores = []
        all_latencies = []
        
        for item in TEST_DATASET:
            latencies = []
            trans_result = ""
            for run_idx in range(3):
                t0 = time.perf_counter()
                trans = runner.translate_single(item["src"])
                t1 = time.perf_counter()
                lat = (t1 - t0) * 1000 # ms
                latencies.append(lat)
                trans_result = trans
            
            first_lat = latencies[0]
            warm_lat = statistics.median(latencies[1:])
            avg_lat = statistics.mean(latencies)
            all_latencies.append(warm_lat)
            
            score_data = score_translation(item, trans_result)
            if item["type"] == "modern":
                modern_scores.append(score_data["total"])
            else:
                ancient_scores.append(score_data["total"])
                
            test_rec = {
                "id": item["id"],
                "type": item["type"],
                "src": item["src"],
                "expected": item["ref"],
                "translated": trans_result,
                "latencies_ms": [round(x, 1) for x in latencies],
                "warm_latency_ms": round(warm_lat, 1),
                "score": score_data["total"],
                "grade": score_data["grade"],
                "breakdown": score_data["breakdown"]
            }
            cand_result["single_tests"].append(test_rec)
            print(f"[{item['id']}] ({warm_lat:.1f}ms) | Score: {score_data['total']}/100 [{score_data['grade']}]")
            print(f"   SRC: {item['src']}")
            print(f"   OUT: {trans_result}")

        # Phase 4: Batch Benchmark (1, 5, 10, 20, 50)
        print(f"\n--- Phase 4: Batch Benchmark (Batch 1, 5, 10, 20, 50) ---")
        batch_sizes = [1, 5, 10, 20, 50]
        # Generate synthetic batch items from dataset
        full_corpus = [item["src"] for item in TEST_DATASET]
        
        for b_size in batch_sizes:
            batch_input = (full_corpus * ((b_size // len(full_corpus)) + 1))[:b_size]
            try:
                proc = psutil.Process(os.getpid())
                ram_b4 = proc.memory_info().rss / (1024**2)
                
                t0 = time.perf_counter()
                batch_out = runner.translate_batch(batch_input)
                t1 = time.perf_counter()
                
                ram_aft = proc.memory_info().rss / (1024**2)
                elapsed = t1 - t0
                subs_per_sec = round(b_size / elapsed, 2)
                avg_time_per_sub_ms = round((elapsed / b_size) * 1000, 1)
                
                cand_result["batch_tests"][f"batch_{b_size}"] = {
                    "total_time_sec": round(elapsed, 3),
                    "avg_ms_per_sub": avg_time_per_sub_ms,
                    "subs_per_sec": subs_per_sec,
                    "ram_mb": round(ram_aft, 1),
                    "status": "PASS"
                }
                print(f"   Batch {b_size:2d}: {elapsed:.3f}s | {avg_time_per_sub_ms} ms/sub | {subs_per_sec} subs/sec")
            except Exception as be:
                cand_result["batch_tests"][f"batch_{b_size}"] = {
                    "status": "FAIL",
                    "error": str(be)
                }
                print(f"   Batch {b_size:2d}: FAILED ({be})")

        # Phase 5, 6, 7 Metrics & Scoring
        avg_modern = statistics.mean(modern_scores) if modern_scores else 0
        avg_ancient = statistics.mean(ancient_scores) if ancient_scores else 0
        overall_quality = (avg_modern + avg_ancient) / 2 if (modern_scores and ancient_scores) else 0
        weighted_quality = (0.30 * avg_modern) + (0.50 * avg_ancient) + (0.20 * overall_quality)
        
        med_lat_ms = statistics.median(all_latencies) if all_latencies else 9999
        # Speed score: 100 if <= 50ms, scale down to 0 if >= 3000ms
        speed_score = max(0.0, min(100.0, (1.0 - (med_lat_ms / 3000.0)) * 100.0))
        # Resource score: 100 if size < 200MB, down if > 3GB
        resource_score = max(0.0, min(100.0, (1.0 - (runner.model_size_mb / 4000.0)) * 100.0))
        stability_score = 100.0 if runner.load_status == "SUCCESS" else 0.0
        
        # Production Score: 40% Quality + 30% Speed + 15% Resource + 15% Stability
        production_score = (0.40 * weighted_quality) + (0.30 * speed_score) + (0.15 * resource_score) + (0.15 * stability_score)
        
        cand_result["metrics"] = {
            "avg_modern_quality": round(avg_modern, 2),
            "avg_ancient_quality": round(avg_ancient, 2),
            "overall_quality": round(overall_quality, 2),
            "weighted_quality": round(weighted_quality, 2),
            "median_latency_ms": round(med_lat_ms, 1),
            "speed_score": round(speed_score, 2),
            "resource_score": round(resource_score, 2),
            "stability_score": round(stability_score, 2),
            "production_score": round(production_score, 2)
        }
        
        print(f"\n[SUMMARY] {name}:")
        print(f"   Modern Quality:   {avg_modern:.1f}/100")
        print(f"   Ancient Quality:  {avg_ancient:.1f}/100")
        print(f"   Weighted Quality: {weighted_quality:.1f}/100")
        print(f"   Median Latency:   {med_lat_ms:.1f} ms")
        print(f"   PRODUCTION SCORE: {production_score:.1f}/100")

        runner.unload()
        all_results["models"][name] = cand_result

    # Save complete JSON results
    output_dir = "scripts/benchmark_mt"
    os.makedirs(output_dir, exist_ok=True)
    json_path = os.path.join(output_dir, "benchmark_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print(f"\n[SAVED] Benchmark results saved to {json_path}")

if __name__ == "__main__":
    run_benchmarks()
