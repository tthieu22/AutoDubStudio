import json
import math
import os
import sys
import time
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Setup environment
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

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

def calc_stats(values: List[float]) -> Dict[str, float]:
    if not values:
        return {"avg": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "p95": 0.0}
    s = sorted(values)
    n = len(s)
    avg = sum(s) / n
    median = s[n // 2] if n % 2 != 0 else (s[n // 2 - 1] + s[n // 2]) / 2.0
    p95_idx = min(n - 1, math.ceil(0.95 * n) - 1)
    return {
        "avg": round(avg, 2),
        "median": round(median, 2),
        "min": round(s[0], 2),
        "max": round(s[-1], 2),
        "p95": round(s[p95_idx], 2)
    }

def call_ollama(
    endpoint: str = "/api/generate",
    prompt: Optional[str] = None,
    system: Optional[str] = None,
    messages: Optional[List[Dict[str, str]]] = None,
    num_predict: int = 1536,
    timeout: int = 240
) -> Dict[str, Any]:
    url = f"http://localhost:11434{endpoint}"
    payload: Dict[str, Any] = {
        "model": "qwen3:4b",
        "stream": False,
        "think": True,
        "keep_alive": "1h",
        "options": {
            "num_predict": num_predict,
            "temperature": 0.3
        }
    }
    if endpoint == "/api/generate":
        payload["prompt"] = prompt or ""
        if system:
            payload["system"] = system
    else: # /api/chat
        payload["messages"] = messages or []

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )

    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            elapsed = time.time() - t0
            raw = json.loads(resp.read().decode("utf-8"))
            
            # Extract fields
            if endpoint == "/api/chat":
                msg = raw.get("message", {})
                content = msg.get("content", "")
                thinking = msg.get("thinking", "")
            else:
                content = raw.get("response", "")
                thinking = raw.get("thinking", "")
            
            eval_count = raw.get("eval_count", 0)
            eval_duration_ns = raw.get("eval_duration", 0)
            total_duration_ns = raw.get("total_duration", 0)
            prompt_eval_duration_ns = raw.get("prompt_eval_duration", 0)
            prompt_eval_count = raw.get("prompt_eval_count", 0)
            done_reason = raw.get("done_reason", "stop")
            
            speed = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns > 0 else 0.0

            # Approximate token division if API doesn't split eval_count
            resp_words = len(content.split())
            approx_resp_tokens = max(1, int(resp_words * 1.3)) if content else 0
            approx_think_tokens = max(0, eval_count - approx_resp_tokens)

            return {
                "success": True,
                "elapsed": elapsed,
                "content": content.strip(),
                "thinking": thinking.strip(),
                "eval_count": eval_count,
                "prompt_eval_count": prompt_eval_count,
                "total_duration_s": total_duration_ns / 1e9,
                "eval_duration_s": eval_duration_ns / 1e9,
                "prompt_eval_duration_s": prompt_eval_duration_ns / 1e9,
                "speed": speed,
                "done_reason": done_reason,
                "thinking_tokens_est": approx_think_tokens,
                "response_tokens_est": approx_resp_tokens
            }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "success": False,
            "elapsed": elapsed,
            "content": "",
            "thinking": "",
            "eval_count": 0,
            "prompt_eval_count": 0,
            "total_duration_s": elapsed,
            "eval_duration_s": 0,
            "prompt_eval_duration_s": 0,
            "speed": 0,
            "done_reason": str(e),
            "thinking_tokens_est": 0,
            "response_tokens_est": 0
        }

def run_suite():
    print("==================================================================", flush=True)
    print("  AUTODUBSTUDIO — QWEN3:4B THINKING LATENCY OPTIMIZATION SUITE    ", flush=True)
    print("==================================================================", flush=True)
    used, total, util = get_vram()
    print(f"Hardware: NVIDIA GTX 1650 Ti ({total}MB) | VRAM: {used}MB | GPU Util: {util}%", flush=True)
    print("Model:    qwen3:4b (Thinking: ON, Concurrency: 1, Keep-Alive: 1h)\n", flush=True)

    all_results = {}

    # Helper to run N iterations
    def run_benchmark_series(name: str, config_fn, num_runs: int = 5):
        print(f"--- RUNNING [{name}] ({num_runs} runs) ---", flush=True)
        runs = []
        for i in range(1, num_runs + 1):
            v_used, _, _ = get_vram()
            res = config_fn()
            res["run_index"] = i
            res["vram_mb"] = v_used
            runs.append(res)
            status_str = "PASS" if (res["success"] and res["content"]) else f"FAIL ({res['done_reason']})"
            print(f"  Run #{i}: {res['elapsed']:.2f}s | Tokens: {res['eval_count']} (Think: ~{res['thinking_tokens_est']}, Final: {res['response_tokens_est']}) | Speed: {res['speed']:.1f} t/s | Output: \"{res['content']}\" | [{status_str}]", flush=True)
            time.sleep(1) # brief thermal buffer
        
        latencies = [r["elapsed"] for r in runs if r["success"]]
        tokens = [r["eval_count"] for r in runs if r["success"]]
        speeds = [r["speed"] for r in runs if r["success"]]
        pass_count = sum(1 for r in runs if r["success"] and r["content"])
        
        stats = {
            "name": name,
            "runs": runs,
            "pass_rate": f"{pass_count}/{num_runs}",
            "latency": calc_stats(latencies),
            "tokens": calc_stats(tokens),
            "speed": calc_stats(speeds)
        }
        all_results[name] = stats
        print(f"  ==> Summary [{name}]: Avg Latency={stats['latency']['avg']}s, Median={stats['latency']['median']}s, P95={stats['latency']['p95']}s, Avg Tokens={stats['tokens']['avg']}, Pass Rate={stats['pass_rate']}\n", flush=True)
        return stats

    # ====================================================================
    # 1. BASELINE CONTROL (5 runs each)
    # ====================================================================
    base_sys = "You are a professional Chinese-to-Vietnamese subtitle translator.\nTranslate naturally and accurately.\nReturn ONLY the Vietnamese translation."
    
    run_benchmark_series(
        "BASELINE_SENTENCE_1 (爸爸和妈妈去买菜。)",
        lambda: call_ollama(
            endpoint="/api/generate",
            prompt="[SUBTITLE_001]\n爸爸和妈妈去买菜。",
            system=base_sys,
            num_predict=1536
        ),
        num_runs=5
    )

    run_benchmark_series(
        "BASELINE_SENTENCE_2 (你好，你在干什么？)",
        lambda: call_ollama(
            endpoint="/api/generate",
            prompt="[SUBTITLE_001]\n你好，你在干什么？",
            system=base_sys,
            num_predict=1536
        ),
        num_runs=5
    )

    # ====================================================================
    # 2. TEST B — PROMPT MINIMIZATION MATRIX (4 prompts x 5 runs)
    # Target sentence: 爸爸和妈妈去买菜。
    # ====================================================================
    p1 = "You are a Chinese to Vietnamese subtitle translator.\nTranslate naturally and accurately.\nThink briefly.\nReturn only the final Vietnamese translation."
    p2 = "Translate Chinese into natural Vietnamese.\nThink briefly.\nReturn only the Vietnamese translation."
    p3 = "Translate the Chinese subtitle into natural Vietnamese.\nUse context when necessary.\nAvoid unnecessary analysis.\nReturn only the final translation."
    p4 = "Professional Chinese-Vietnamese subtitle translation.\nPreserve meaning, tone and natural Vietnamese.\nReturn only the final translation."

    for idx, p_text in enumerate([p1, p2, p3, p4], 1):
        run_benchmark_series(
            f"TEST_B_PROMPT_{idx}",
            lambda p=p_text: call_ollama(
                endpoint="/api/generate",
                prompt="爸爸和妈妈去买菜。",
                system=p,
                num_predict=1536
            ),
            num_runs=5
        )

    # ====================================================================
    # 3. TEST C — THINKING INSTRUCTION MATRIX (5 instructions x 5 runs)
    # ====================================================================
    c_instructions = [
        ("C1", "Think briefly and efficiently."),
        ("C2", "Use minimal reasoning necessary to produce an accurate translation."),
        ("C3", "Do not over-analyze simple sentences."),
        ("C4", "Reason only about ambiguity, context and character relationships."),
        ("C5", "For simple sentences, use concise reasoning. For complex sentences, reason more deeply.")
    ]
    for c_id, c_text in c_instructions:
        sys_c = f"Translate Chinese to Vietnamese naturally.\n{c_text}\nReturn only the final translation."
        run_benchmark_series(
            f"TEST_C_INSTRUCTION_{c_id}",
            lambda s=sys_c: call_ollama(
                endpoint="/api/generate",
                prompt="爸爸和妈妈去买菜。",
                system=s,
                num_predict=1536
            ),
            num_runs=5
        )

    # ====================================================================
    # 4. TEST D — TOKEN BUDGET MATRIX (512, 768, 1024, 1280, 1536)
    # ====================================================================
    for budget in [512, 768, 1024, 1280, 1536]:
        run_benchmark_series(
            f"TEST_D_BUDGET_{budget}",
            lambda b=budget: call_ollama(
                endpoint="/api/generate",
                prompt="爸爸和妈妈去买菜。",
                system=p2,
                num_predict=b
            ),
            num_runs=5
        )

    # ====================================================================
    # 5. TEST F — API ENDPOINT COMPARISON (/api/generate vs /api/chat)
    # ====================================================================
    run_benchmark_series(
        "TEST_F_ENDPOINT_GENERATE",
        lambda: call_ollama(
            endpoint="/api/generate",
            prompt="爸爸和妈妈去买菜。",
            system=p2,
            num_predict=1536
        ),
        num_runs=5
    )

    chat_msgs = [
        {"role": "system", "content": p2},
        {"role": "user", "content": "爸爸和妈妈去买菜。"}
    ]
    run_benchmark_series(
        "TEST_F_ENDPOINT_CHAT",
        lambda: call_ollama(
            endpoint="/api/chat",
            messages=chat_msgs,
            num_predict=1536
        ),
        num_runs=5
    )

    # ====================================================================
    # 6. TEST G — SYSTEM PROMPT VS SINGLE DIRECT PROMPT
    # ====================================================================
    single_direct = "Translate this Chinese subtitle into natural Vietnamese. Think briefly. Return only the final Vietnamese translation.\n\nSubtitle: 爸爸和妈妈去买菜。"
    run_benchmark_series(
        "TEST_G_SINGLE_DIRECT_PROMPT",
        lambda: call_ollama(
            endpoint="/api/generate",
            prompt=single_direct,
            system=None,
            num_predict=1536
        ),
        num_runs=5
    )

    # ====================================================================
    # 7. TEST I — SIMPLE VS COMPLEX
    # ====================================================================
    simple_cases = ["你好。", "谢谢。", "你在干什么？", "你吃饭了吗？", "快走。"]
    for s_idx, s_text in enumerate(simple_cases, 1):
        run_benchmark_series(
            f"TEST_I_SIMPLE_{s_idx} ({s_text})",
            lambda t=s_text: call_ollama(
                endpoint="/api/generate",
                prompt=t,
                system=p2,
                num_predict=1536
            ),
            num_runs=3
        )

    complex_cases = [
        ("WUXIA_KING", "你这个时候还敢跟本王谈条件？"),
        ("HISTORICAL_WAR", "若不是当年师父救我一命，我早已死在那场战乱之中。"),
        ("PALACE_QUEEN", "你以为凭借你现在的身份，就能命令本宫吗？")
    ]
    for c_tag, c_text in complex_cases:
        run_benchmark_series(
            f"TEST_I_COMPLEX_{c_tag}",
            lambda t=c_text: call_ollama(
                endpoint="/api/generate",
                prompt=t,
                system=p2,
                num_predict=1536
            ),
            num_runs=3
        )

    # ====================================================================
    # 8. TEST K — BATCH SIZE MATRIX (Batch 1, Batch 3, Batch 5)
    # ====================================================================
    batch_1_txt = "[SUBTITLE_001]\n爸爸和妈妈去买菜。"
    batch_3_txt = "[SUBTITLE_001]\n你好。\n\n[SUBTITLE_002]\n你在干什么？\n\n[SUBTITLE_003]\n你吃饭了吗？"
    batch_5_txt = "[SUBTITLE_001]\n你好。\n\n[SUBTITLE_002]\n你在干什么？\n\n[SUBTITLE_003]\n你吃饭了吗？\n\n[SUBTITLE_004]\n快走。\n\n[SUBTITLE_005]\n谢谢。"

    run_benchmark_series(
        "TEST_K_BATCH_1",
        lambda: call_ollama(
            endpoint="/api/generate",
            prompt=batch_1_txt,
            system=p2,
            num_predict=1536
        ),
        num_runs=3
    )

    run_benchmark_series(
        "TEST_K_BATCH_3",
        lambda: call_ollama(
            endpoint="/api/generate",
            prompt=batch_3_txt,
            system=p2,
            num_predict=1792
        ),
        num_runs=3
    )

    run_benchmark_series(
        "TEST_K_BATCH_5",
        lambda: call_ollama(
            endpoint="/api/generate",
            prompt=batch_5_txt,
            system=p2,
            num_predict=2048,
            timeout=300
        ),
        num_runs=3
    )

    # Save complete JSON
    out_file = BASE_DIR / "tests" / "latency_optimization_matrix_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"\n==================================================================", flush=True)
    print(f"BENCHMARK COMPLETE. Results saved to: {out_file}", flush=True)
    print(f"==================================================================", flush=True)

if __name__ == "__main__":
    run_suite()
