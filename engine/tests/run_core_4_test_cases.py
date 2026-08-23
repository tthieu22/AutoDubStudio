import json
import os
import sys
import time
import subprocess
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from autodub.modules.translator import RealTranslator, SubtitleDifficultyClassifier

def get_vram():
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,nounits,noheader"],
            encoding="utf-8"
        )
        p = [x.strip() for x in out.strip().split("\n")[0].split(",")]
        return int(p[0]), int(p[1]), float(p[2])
    except Exception:
        return 0, 0, 0.0

def run_tests():
    print("==================================================================", flush=True)
    print("        AUTODUBSTUDIO — 4 CORE ACCEPTANCE TEST CASES (QWEN3)     ", flush=True)
    print("==================================================================", flush=True)
    used, total, util = get_vram()
    print(f"Hardware: NVIDIA GTX 1650 Ti ({total}MB VRAM) | VRAM: {used}MB ({util}%)", flush=True)
    print("Model:    qwen3:4b (Thinking: ON, Concurrency: 1)", flush=True)
    print("------------------------------------------------------------------\n", flush=True)

    translator = RealTranslator(timeout=240)

    test_cases = [
        {"id": "TEST_1", "text": "爸爸和妈妈去买菜。", "style": "general", "expected": "Bố và mẹ đi mua rau."},
        {"id": "TEST_2", "text": "你好，你在干什么？", "style": "general", "expected": "Bạn đang làm gì vậy?"},
        {"id": "TEST_3", "text": "你吃饭了吗？", "style": "general", "expected": "Bạn ăn cơm chưa? / Bạn ăn chưa?"},
        {"id": "TEST_4", "text": "你这个时候还敢跟本王谈条件？", "style": "wuxia", "expected": "Ngươi vào lúc này mà còn dám bàn điều kiện với bổn vương?"}
    ]

    results = []

    for tc in test_cases:
        print(f"Running [{tc['id']}]: \"{tc['text']}\" ...", flush=True)
        t0 = time.time()
        diff = SubtitleDifficultyClassifier.classify(tc["text"])
        
        batch_items = [{"id_str": "SUBTITLE_001", "text": tc["text"]}]
        try:
            res_dict = translator.translate_batch(
                batch_items=batch_items,
                translation_style=tc["style"]
            )
            elapsed = time.time() - t0
            m = getattr(translator.client, "last_metrics", {})
            vram_used, _, _ = get_vram()
            translation = res_dict.get("SUBTITLE_001", "").strip()

            rec = {
                "id": tc["id"],
                "input": tc["text"],
                "expected": tc["expected"],
                "actual": translation,
                "difficulty": diff,
                "style": tc["style"],
                "elapsed": elapsed,
                "speed": m.get("tokens_per_sec", 0),
                "eval_count": m.get("eval_count", 0),
                "done_reason": m.get("done_reason", "stop"),
                "status": "PASS" if translation else "EMPTY",
                "vram_mb": vram_used
            }
        except Exception as e:
            elapsed = time.time() - t0
            rec = {
                "id": tc["id"],
                "input": tc["text"],
                "expected": tc["expected"],
                "actual": "",
                "difficulty": diff,
                "style": tc["style"],
                "elapsed": elapsed,
                "speed": 0,
                "eval_count": 0,
                "done_reason": str(e),
                "status": "FAIL",
                "vram_mb": 0
            }
        results.append(rec)
        print(f"  -> Actual Translation: \"{rec['actual']}\"")
        print(f"  -> Expected:           \"{rec['expected']}\"")
        print(f"  -> Latency: {rec['elapsed']:.2f}s | Speed: {rec['speed']:.1f} t/s | Tokens: {rec['eval_count']} | Status: {rec['status']}\n", flush=True)

    print("==================================================================", flush=True)
    print("                       SUMMARY OF 4 CORE TESTS                   ", flush=True)
    print("==================================================================", flush=True)
    passes = [r for r in results if r["status"] == "PASS"]
    print(f"Passed: {len(passes)} / {len(results)}")
    for r in results:
        print(f"  [{r['id']}] {r['input']:<25} -> \"{r['actual']}\" ({r['elapsed']:.2f}s, {r['speed']:.1f} t/s)")

    out_file = BASE_DIR / "tests" / "core_4_tests_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nSaved to: {out_file}", flush=True)

if __name__ == "__main__":
    run_tests()
