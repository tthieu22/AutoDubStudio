import time
import sys
import json
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add engine directory to path
engine_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(engine_dir))

from autodub.modules.translator import RealTranslator, format_subtitle_id
from autodub.modules.ollama_client import OllamaClient

REALISTIC_SUBTITLES_20 = [
    "王爷，您怎么亲自来了？",
    "我不放心你，过来看看。",
    "林婉多谢王爷关心。",
    "跟我回府吧，这里不安全。",
    "是，王爷。",
    "你听说今天城里发生的事了吗？",
    "听说了，听说刺客已经被抓住了。",
    "事情没那么简单，背后的主谋还在。",
    "那我们现在该怎么办？",
    "静观其变，切勿打草惊蛇。",
    "你为什么不早点告诉我？",
    "我也是刚刚接到密报。",
    "有人在暗中监视我们府邸。",
    "看来他们要动手了。",
    "放心，有本王在，没人能伤你。",
    "今晚就在这里休息吧。",
    "好的，一切听从王爷安排。",
    "明早我们要进宫面圣。",
    "皇上会相信我们吗？",
    "清者自清，真相终会大白。"
]

def run_qwen3_batch_benchmark():
    print("====================================================================")
    print("AUTODUBSTUDIO QWEN3:4B CLEAN BATCH BENCHMARK (GTX 1650 Ti 4GB)")
    print("====================================================================")

    client = OllamaClient()
    available, err = client.check_availability("qwen3:4b")
    if not available:
        print(f"ERROR: qwen3:4b model not available: {err}")
        return

    # Build 20 realistic test items
    test_items = []
    for i in range(20):
        test_items.append({
            "id_num": i + 1,
            "id_str": format_subtitle_id(i + 1),
            "text": REALISTIC_SUBTITLES_20[i]
        })

    batch_sizes = [1, 5, 10, 15, 20]
    results_summary = []

    for bs in batch_sizes:
        print(f"\n--------------------------------------------------------------------")
        print(f"[BENCHMARK] Testing Qwen3:4b Batch Size = {bs} subtitles...")
        sub_slice = test_items[:bs]
        translator = RealTranslator(model_name="qwen3:4b", batch_size=bs)

        t0 = time.time()
        res_dict = translator.translate_batch(
            batch_items=sub_slice,
            translation_style="general",
            locked_entities={"王爷": "Vương gia", "林婉": "Lâm Uyển"}
        )
        elapsed = time.time() - t0
        per_sub_latency = elapsed / bs if bs > 0 else 0.0

        missing = [item["id_str"] for item in sub_slice if item["id_str"] not in res_dict]
        valid = (len(missing) == 0)
        status_str = "PASS (100% Complete)" if valid else f"FAIL ({len(missing)} missing)"

        print(f"  Result: {bs} subtitles in {elapsed:.2f}s | {per_sub_latency:.2f}s/sub | {status_str}")
        if valid:
            print("  Sample translations:")
            for item in sub_slice[:min(3, bs)]:
                id_str = item["id_str"]
                print(f"    [{id_str}] {item['text']} -> {res_dict.get(id_str, '')}")

        results_summary.append({
            "batch_size": bs,
            "total_time": elapsed,
            "count": len(res_dict),
            "expected_count": bs,
            "per_sub": per_sub_latency,
            "status": status_str,
            "is_pass": valid
        })

    print("\n====================================================================")
    print("             QWEN3:4B CLEAN BATCH BENCHMARK SUMMARY TABLE            ")
    print("====================================================================")
    print(f"{'Batch Size':<12} | {'Total Time (s)':<16} | {'Subtitles':<12} | {'Sec/Subtitle':<14} | {'Status'}")
    print("-" * 75)

    max_reliable_batch = 0
    optimal_bs = None
    min_per_sub = float("inf")

    for r in results_summary:
        parsed_fmt = f"{r['count']}/{r['expected_count']}"
        print(f"{r['batch_size']:<12} | {r['total_time']:<16.2f} | {parsed_fmt:<12} | {r['per_sub']:<14.2f} | {r['status']}")
        if r["is_pass"]:
            max_reliable_batch = r["batch_size"]
            if r["per_sub"] < min_per_sub:
                min_per_sub = r["per_sub"]
                optimal_bs = r["batch_size"]

    print("--------------------------------------------------------------------")
    print(f"MODEL:                       qwen3:4b")
    print(f"THINKING:                    OFF / Controlled")
    print(f"CONCURRENCY:                 1")
    print(f"HARDWARE:                    NVIDIA GeForce GTX 1650 Ti (4GB VRAM)")
    print(f"MAXIMUM RELIABLE BATCH SIZE: {max_reliable_batch} subtitles/batch")
    print(f"OPTIMAL BATCH SIZE:          {optimal_bs} subtitles/batch ({min_per_sub:.2f}s/subtitle)")
    print("====================================================================\n")

if __name__ == "__main__":
    run_qwen3_batch_benchmark()
