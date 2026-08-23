import json
import os
import sys
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from autodub.modules.translator import RealTranslator, SubtitleDifficultyClassifier
from autodub.modules.output_sanitizer import TranslationOutputSanitizer

def get_vram_usage():
    try:
        output = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,nounits,noheader"],
            encoding="utf-8"
        )
        parts = [p.strip() for p in output.strip().split("\n")[0].split(",")]
        return int(parts[0]), int(parts[1]), float(parts[2])
    except Exception:
        return 0, 0, 0.0

def run_optimization_suite():
    print("==================================================================", flush=True)
    print("      AUTODUBSTUDIO — QWEN3:4B THINKING OPTIMIZATION SUITE        ", flush=True)
    print("==================================================================", flush=True)
    used, total, util = get_vram_usage()
    print(f"Hardware: NVIDIA GTX 1650 Ti ({total}MB VRAM) | Current VRAM: {used}MB ({util}%)", flush=True)
    print("Model:    qwen3:4b (Thinking: ON, Concurrency: 1)", flush=True)
    print("------------------------------------------------------------------\n", flush=True)

    translator = RealTranslator()

    # PHASE 1: 4 REQUIRED TEST CASES (Section 16)
    test_cases = [
        {"id": "TEST_1", "text": "爸爸和妈妈去买菜。", "style": "general", "desc": "Simple daily action"},
        {"id": "TEST_2", "text": "你好，你在干什么？", "style": "general", "desc": "Standard greeting"},
        {"id": "TEST_3", "text": "你吃饭了吗？", "style": "general", "desc": "Daily meal check"},
        {"id": "TEST_4", "text": "你这个时候还敢跟本王谈条件？", "style": "wuxia", "desc": "Complex historical tone (本王)"}
    ]

    print("=== PHASE 1: CORE TEST CASES (4 CASES) ===", flush=True)
    phase1_results = []
    for tc in test_cases:
        t0 = time.time()
        batch_items = [{"id_str": "SUBTITLE_001", "text": tc["text"]}]
        diff = SubtitleDifficultyClassifier.classify(tc["text"])
        
        try:
            res_dict = translator.translate_batch(
                batch_items=batch_items,
                translation_style=tc["style"]
            )
            elapsed = time.time() - t0
            m = getattr(translator.client, "last_metrics", {})
            vram_used, _, _ = get_vram_usage()
            translated = res_dict.get("SUBTITLE_001", "")
            
            rec = {
                "id": tc["id"],
                "input": tc["text"],
                "difficulty": diff,
                "style": tc["style"],
                "output": translated,
                "elapsed": elapsed,
                "tok_per_sec": m.get("tokens_per_sec", 0),
                "eval_count": m.get("eval_count", 0),
                "done_reason": m.get("done_reason", "stop"),
                "status": "PASS" if translated else "EMPTY",
                "vram_mb": vram_used
            }
        except Exception as e:
            elapsed = time.time() - t0
            rec = {
                "id": tc["id"],
                "input": tc["text"],
                "difficulty": diff,
                "style": tc["style"],
                "output": "",
                "elapsed": elapsed,
                "tok_per_sec": 0,
                "eval_count": 0,
                "done_reason": str(e),
                "status": "FAIL",
                "vram_mb": 0
            }
        phase1_results.append(rec)
        print(f"  [{rec['id']}] Input: '{rec['input']}' ({rec['difficulty']})")
        print(f"       Translation: \"{rec['output']}\"")
        print(f"       Time: {rec['elapsed']:.2f}s | Speed: {rec['tok_per_sec']:.1f} t/s | Status: {rec['status']}\n", flush=True)

    # PHASE 2: TOKEN BUDGET MATRIX ON SAMPLE INPUTS (512, 768, 1024, 1536, 2048)
    print("\n=== PHASE 2: TOKEN BUDGET MATRIX (Batch = 1) ===", flush=True)
    budgets = [512, 768, 1024, 1536, 2048]
    budget_results = {}

    for b in budgets:
        print(f"--- Testing Token Budget: {b} ---", flush=True)
        runs_data = []
        for prompt_text in ["你好，你在干什么？", "爸爸和妈妈去买菜。", "你这个时候还敢跟本王谈条件？"]:
            sys_prompt = translator._build_system_prompt()
            user_content = f"YOU MUST TRANSLATE ALL 1 SUBTITLES FROM SUBTITLE_001 TO SUBTITLE_001. DO NOT STOP UNTIL SUBTITLE_001 IS TRANSLATED.\n\nSUBTITLES TO TRANSLATE:\n\n[SUBTITLE_001]\n{prompt_text}"
            full_prompt = f"{sys_prompt}\n\n{user_content}"

            t0 = time.time()
            try:
                raw = translator.client.generate(
                    prompt=full_prompt,
                    model="qwen3:4b",
                    temperature=0.15,
                    num_predict=b,
                    timeout=120
                )
                elapsed = time.time() - t0
                m = getattr(translator.client, "last_metrics", {})
                status = "SUCCESS" if raw else "EMPTY"
                runs_data.append({
                    "prompt": prompt_text,
                    "elapsed": elapsed,
                    "speed": m.get("tokens_per_sec", 0),
                    "eval_count": m.get("eval_count", 0),
                    "done_reason": m.get("done_reason", "stop"),
                    "status": status,
                    "output": clean_translation(raw)[:60]
                })
            except Exception as e:
                elapsed = time.time() - t0
                runs_data.append({
                    "prompt": prompt_text,
                    "elapsed": elapsed,
                    "speed": 0,
                    "eval_count": 0,
                    "done_reason": str(e),
                    "status": "FAIL",
                    "output": ""
                })
        budget_results[str(b)] = runs_data

    # PHASE 3: BATCH SIZE MATRIX (Batch = 1, 3, 5)
    print("\n=== PHASE 3: BATCH SIZE MATRIX (Batches 1, 3, 5) ===", flush=True)
    batch_pool = [
        "你好，你在干什么？",
        "爸爸和妈妈去买菜。",
        "你吃饭了吗？",
        "这个世界上还有什么事情是我不知道的？",
        "你为什么要骗我？"
    ]
    batch_matrix_results = {}

    for bsize in [1, 3, 5]:
        print(f"--- Testing Batch Size = {bsize} ---", flush=True)
        items = [{"id_str": f"SUBTITLE_{i+1:03d}", "text": batch_pool[i]} for i in range(bsize)]
        batch_runs = []
        
        for run_idx in range(1, 4):
            t0 = time.time()
            try:
                res_dict = translator.translate_batch(batch_items=items)
                elapsed = time.time() - t0
                m = getattr(translator.client, "last_metrics", {})
                vram_used, _, _ = get_vram_usage()
                
                success_count = sum(1 for item in items if res_dict.get(item["id_str"]))
                is_full_success = (success_count == bsize)
                
                batch_runs.append({
                    "run": run_idx,
                    "batch_size": bsize,
                    "total_time": elapsed,
                    "sec_per_sub": elapsed / bsize,
                    "speed": m.get("tokens_per_sec", 0),
                    "eval_count": m.get("eval_count", 0),
                    "done_reason": m.get("done_reason", "stop"),
                    "success": is_full_success,
                    "vram_mb": vram_used
                })
                print(f"  [Batch {bsize} Run #{run_idx}] Total: {elapsed:.2f}s ({elapsed/bsize:.2f}s/sub) | Speed: {m.get('tokens_per_sec', 0):.1f} t/s | Success: {is_full_success}")
            except Exception as e:
                elapsed = time.time() - t0
                batch_runs.append({
                    "run": run_idx,
                    "batch_size": bsize,
                    "total_time": elapsed,
                    "sec_per_sub": elapsed / bsize,
                    "speed": 0,
                    "eval_count": 0,
                    "done_reason": str(e),
                    "success": False,
                    "vram_mb": 0
                })
                print(f"  [Batch {bsize} Run #{run_idx}] FAILED in {elapsed:.2f}s: {e}")
        batch_matrix_results[str(bsize)] = batch_runs

    # Save all results to json
    report_data = {
        "phase1_core_tests": phase1_results,
        "phase2_budget_matrix": budget_results,
        "phase3_batch_matrix": batch_matrix_results
    }
    
    out_file = BASE_DIR / "tests" / "optimization_benchmark_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report_data, f, indent=2, ensure_ascii=False)
    print(f"\nAll optimization benchmark data saved to: {out_file}", flush=True)

if __name__ == "__main__":
    run_optimization_suite()
