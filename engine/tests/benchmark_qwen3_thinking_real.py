import json
import os
import sys
import time
import subprocess
from pathlib import Path

# Add engine directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from autodub.modules.ollama_client import OllamaClient
from autodub.modules.translator import RealTranslator
from autodub.modules.ollama_model_manager import OllamaModelManager

# Test Chinese Subtitle sentences for benchmarking
SAMPLE_SENTENCES = [
    "爸爸和妈妈去买菜。",
    "你好，你在干什么？",
    "你吃饭了吗？",
    "我们一起去公园散步吧。",
    "天气真好，阳光很明媚。",
    "今天的工作终于全部完成了。",
    "他在房间里认真地看书。",
    "老师，请问这个问题怎么解决？",
    "佩奇和乔治在泥坑里跳来跳去。",
    "明天早上八点我们在车站集合。",
    "事已至此，我们只能随机应变了。",
    "请帮我把桌子上的水杯拿过来。",
    "昨晚你看的那部电影好看吗？",
    "不要着急，一切都会好起来的。",
    "祝你生日快乐，心想事成！"
]


def get_gpu_vram():
    """Query nvidia-smi for current VRAM usage."""
    try:
        res = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total,utilization.gpu", "--format=csv,nounits,noheader"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if res.returncode == 0:
            lines = res.stdout.strip().splitlines()
            if lines:
                parts = [p.strip() for p in lines[0].split(",")]
                return {
                    "vram_used_mb": float(parts[0]),
                    "vram_total_mb": float(parts[1]),
                    "gpu_util_pct": float(parts[2])
                }
    except Exception as e:
        pass
    return {"vram_used_mb": 0.0, "vram_total_mb": 4096.0, "gpu_util_pct": 0.0}


def run_benchmark():
    print("==================================================================", flush=True)
    print("       AUTODUBSTUDIO — REAL QWEN3:4B THINKING MODE BENCHMARK     ", flush=True)
    print("==================================================================", flush=True)
    print("Hardware: NVIDIA GeForce GTX 1650 Ti (4GB VRAM)", flush=True)
    print("Model:    qwen3:4b (Thinking: ON)", flush=True)
    print("Concurrency: 1", flush=True)
    print("------------------------------------------------------------------\n", flush=True)

    client = OllamaClient()
    available, err = client.check_availability("qwen3:4b")
    if not available:
        print(f"[FATAL] Qwen3:4B is not available in Ollama: {err}", flush=True)
        sys.exit(1)

    # Ensure loaded
    print("[1/3] Ensuring qwen3:4b is exclusively loaded in VRAM...", flush=True)
    client.ensure_model_loaded()
    initial_gpu = get_gpu_vram()
    print(f"VRAM Used: {initial_gpu['vram_used_mb']:.0f} MB / {initial_gpu['vram_total_mb']:.0f} MB ({initial_gpu['gpu_util_pct']}% GPU Util)\n", flush=True)

    batch_sizes = [1, 3, 5]
    num_runs_per_batch = 5
    summary_results = {}

    for bs in batch_sizes:
        print(f"=== BENCHMARKING BATCH SIZE = {bs} (Concurrency = 1, Runs = {num_runs_per_batch}) ===", flush=True)
        translator = RealTranslator(batch_size=bs, client=client)
        latencies = []
        tokens_sec_list = []
        total_durations = []
        load_durations = []
        prompt_durations = []
        eval_durations = []
        success_count = 0

        for run_idx in range(1, num_runs_per_batch + 1):
            # Select bs sentences
            start_offset = ((run_idx - 1) * bs) % len(SAMPLE_SENTENCES)
            batch_texts = [SAMPLE_SENTENCES[(start_offset + j) % len(SAMPLE_SENTENCES)] for j in range(bs)]
            batch_items = [{"id_str": f"SUBTITLE_{j+1:03d}", "text": txt} for j, txt in enumerate(batch_texts)]

            print(f"  [Run {run_idx}/{num_runs_per_batch}] Batch of {bs} items: '{batch_texts[0]}' ...", end=" ", flush=True)

            t0 = time.time()
            try:
                res = translator.translate_batch(batch_items)
                elapsed = time.time() - t0
                success_count += 1
                latencies.append(elapsed)

                metrics = client.last_metrics
                tokens_sec_list.append(metrics.get("tokens_per_sec", 0.0))
                total_durations.append(metrics.get("total_duration_sec", 0.0))
                load_durations.append(metrics.get("load_duration_sec", 0.0))
                prompt_durations.append(metrics.get("prompt_eval_sec", 0.0))
                eval_durations.append(metrics.get("eval_sec", 0.0))

                gpu_now = get_gpu_vram()
                first_translated = res.get(batch_items[0]["id_str"], "")
                print(f"DONE in {elapsed:.2f}s | Speed: {metrics.get('tokens_per_sec', 0.0):.1f} t/s | Sample: \"{first_translated}\" | VRAM: {gpu_now['vram_used_mb']:.0f}MB", flush=True)
            except Exception as e:
                elapsed = time.time() - t0
                print(f"FAILED in {elapsed:.2f}s ({e})", flush=True)

        avg_lat = sum(latencies) / len(latencies) if latencies else 0.0
        min_lat = min(latencies) if latencies else 0.0
        max_lat = max(latencies) if latencies else 0.0
        avg_speed = sum(tokens_sec_list) / len(tokens_sec_list) if tokens_sec_list else 0.0
        avg_eval_dur = sum(eval_durations) / len(eval_durations) if eval_durations else 0.0
        avg_prompt_dur = sum(prompt_durations) / len(prompt_durations) if prompt_durations else 0.0
        avg_load_dur = sum(load_durations) / len(load_durations) if load_durations else 0.0
        sec_per_sub = avg_lat / bs if bs > 0 else 0.0

        summary_results[bs] = {
            "success_rate": (success_count / num_runs_per_batch) * 100.0,
            "avg_latency": avg_lat,
            "min_latency": min_lat,
            "max_latency": max_lat,
            "sec_per_subtitle": sec_per_sub,
            "tokens_per_sec": avg_speed,
            "load_duration": avg_load_dur,
            "prompt_duration": avg_prompt_dur,
            "eval_duration": avg_eval_dur,
            "vram_used_mb": get_gpu_vram()["vram_used_mb"]
        }
        print(f"  --> Batch {bs} Avg: {avg_lat:.2f}s ({sec_per_sub:.2f}s/sub) | Speed: {avg_speed:.1f} tok/s | Success: {summary_results[bs]['success_rate']:.0f}%\n", flush=True)

    print("\n==================================================================", flush=True)
    print("             OFFICIAL BENCHMARK RESULTS SUMMARY TABLE             ", flush=True)
    print("==================================================================", flush=True)
    print(f"{'Batch':<8}{'Latency (Avg)':<16}{'Sec/Subtitle':<16}{'Tokens/sec':<14}{'VRAM (MB)':<12}{'Success'}")
    print("------------------------------------------------------------------")
    for bs, data in summary_results.items():
        print(f"{bs:<8}{data['avg_latency']:.2f}s ({data['min_latency']:.2f}-{data['max_latency']:.2f}s)    {data['sec_per_subtitle']:.2f}s/sub        {data['tokens_per_sec']:.1f} tok/s     {data['vram_used_mb']:.0f} MB      {data['success_rate']:.0f}%")
    print("==================================================================\n", flush=True)

    # Save benchmark json output
    output_json_path = BASE_DIR / "tests" / "benchmark_qwen3_thinking_results.json"
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_results, f, indent=2, ensure_ascii=False)
    print(f"Benchmark results saved to: {output_json_path}")


if __name__ == "__main__":
    run_benchmark()
