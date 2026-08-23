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

def call_raw_generate(
    prompt: str,
    system: str,
    num_predict: int,
    timeout: int = 300
) -> Dict[str, Any]:
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen3:4b",
        "prompt": prompt,
        "system": system,
        "stream": False,
        "think": True,
        "keep_alive": "1h",
        "options": {
            "num_predict": num_predict,
            "temperature": 0.3
        }
    }
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
            
            response_txt = raw.get("response", "")
            thinking_txt = raw.get("thinking", "")
            done = raw.get("done", False)
            done_reason = raw.get("done_reason", "stop")
            eval_count = raw.get("eval_count", 0)
            eval_duration_ns = raw.get("eval_duration", 0)
            total_duration_ns = raw.get("total_duration", 0)
            prompt_eval_duration_ns = raw.get("prompt_eval_duration", 0)
            prompt_eval_count = raw.get("prompt_eval_count", 0)
            load_duration_ns = raw.get("load_duration", 0)

            speed = (eval_count / (eval_duration_ns / 1e9)) if eval_duration_ns > 0 else 0.0

            # Classification
            # Estimate response tokens vs thinking tokens
            resp_words = len(response_txt.split())
            est_resp_tokens = max(1, int(resp_words * 1.3)) if response_txt.strip() else 0
            est_think_tokens = max(0, eval_count - est_resp_tokens)

            if done_reason == "length" and not response_txt.strip():
                classification = "TOKEN_BUDGET_EXHAUSTED"
            elif done_reason == "length" and response_txt.strip():
                classification = "PARTIAL_RESPONSE"
            elif not response_txt.strip() and thinking_txt.strip():
                classification = "THINKING_ONLY"
            elif not response_txt.strip():
                classification = "EMPTY_RESPONSE"
            else:
                classification = "SUCCESS"

            return {
                "success": (classification == "SUCCESS"),
                "classification": classification,
                "elapsed": elapsed,
                "response": response_txt.strip(),
                "thinking_length_chars": len(thinking_txt),
                "response_length_chars": len(response_txt),
                "eval_count": eval_count,
                "prompt_eval_count": prompt_eval_count,
                "total_duration_s": total_duration_ns / 1e9,
                "eval_duration_s": eval_duration_ns / 1e9,
                "prompt_eval_duration_s": prompt_eval_duration_ns / 1e9,
                "load_duration_s": load_duration_ns / 1e9,
                "speed": speed,
                "done_reason": done_reason,
                "thinking_tokens_est": est_think_tokens,
                "response_tokens_est": est_resp_tokens
            }
    except Exception as e:
        elapsed = time.time() - t0
        return {
            "success": False,
            "classification": "ERROR",
            "elapsed": elapsed,
            "response": "",
            "thinking_length_chars": 0,
            "response_length_chars": 0,
            "eval_count": 0,
            "prompt_eval_count": 0,
            "total_duration_s": elapsed,
            "eval_duration_s": 0,
            "prompt_eval_duration_s": 0,
            "load_duration_s": 0,
            "speed": 0.0,
            "done_reason": str(e),
            "thinking_tokens_est": 0,
            "response_tokens_est": 0
        }

def run_benchmark():
    print("==================================================================", flush=True)
    print("       AUTODUBSTUDIO — QWEN3:4B MINIMUM THINKING BUDGET TEST     ", flush=True)
    print("==================================================================", flush=True)
    v_used, v_total, v_util = get_vram()
    print(f"Hardware: NVIDIA GTX 1650 Ti ({v_total}MB) | VRAM: {v_used}MB | GPU Util: {v_util}%", flush=True)
    print("Model:    qwen3:4b (Thinking: ON, Concurrency: 1, Keep-Alive: 1h, Retries: 0)", flush=True)
    print("Endpoint: /api/generate\n", flush=True)

    default_system = "Translate Chinese into natural Vietnamese.\nThink briefly.\nReturn only the Vietnamese translation."

    test_sentences = [
        ("TEST_SIMPLE", "爸爸和妈妈去买菜。"),
        ("TEST_SIMPLE_2", "你好，你在干什么？"),
        ("TEST_COMPLEX", "你这个时候还敢跟本王谈条件？")
    ]

    budget_levels = [256, 384, 512, 640, 768, 896, 1024, 1152, 1280, 1408, 1536, 1664, 1792, 2048]

    budget_matrix_results = {}

    print("==================================================================", flush=True)
    print("                    PHASE 1: NUM_PREDICT MATRIX                  ", flush=True)
    print("==================================================================", flush=True)

    min_safe_budget = None

    for budget in budget_levels:
        print(f"\n>>> TESTING NUM_PREDICT = {budget} <<<", flush=True)
        budget_summary = []
        
        all_passed = True
        for tag, text in test_sentences:
            print(f"  Sentence [{tag}]: \"{text}\"", flush=True)
            runs = []
            for r_idx in range(1, 4): # 3 runs
                res = call_raw_generate(
                    prompt=text,
                    system=default_system,
                    num_predict=budget,
                    timeout=240
                )
                runs.append(res)
                print(f"    Run #{r_idx}: {res['elapsed']:.2f}s | Tokens: {res['eval_count']} (Think: ~{res['thinking_tokens_est']}, Final: {res['response_tokens_est']}) | Speed: {res['speed']:.1f} t/s | Output: \"{res['response']}\" | [{res['classification']}]", flush=True)
                if res["classification"] != "SUCCESS":
                    all_passed = False
                time.sleep(0.5)
            budget_summary.append({"tag": tag, "runs": runs})
        
        budget_matrix_results[budget] = budget_summary
        
        # Check if this budget achieved 100% success across all 3 sentences
        if all_passed and min_safe_budget is None:
            min_safe_budget = budget
            print(f"\n[FOUND CANDIDATE MINIMUM_SAFE_NUM_PREDICT = {min_safe_budget}]", flush=True)
            # If we find a reliable minimum safe budget, we continue to 1536 to observe the scaling curve
            if budget >= 1536:
                break

    if min_safe_budget is None:
        min_safe_budget = 1536

    print("\n==================================================================", flush=True)
    print(f"     PHASE 2: CONFIRMATION TEST ON MIN SAFE BUDGET ({min_safe_budget})", flush=True)
    print("==================================================================", flush=True)
    print(f"Running 10 confirmation runs on \"爸爸和妈妈去买菜。\" with num_predict={min_safe_budget}...\n", flush=True)

    confirm_runs = []
    for c_idx in range(1, 11):
        c_res = call_raw_generate(
            prompt="爸爸和妈妈去买菜。",
            system=default_system,
            num_predict=min_safe_budget,
            timeout=240
        )
        confirm_runs.append(c_res)
        print(f"  Confirm Run #{c_idx:02d}: {c_res['elapsed']:.2f}s | Tokens: {c_res['eval_count']} (Think: ~{c_res['thinking_tokens_est']}, Final: {c_res['response_tokens_est']}) | Output: \"{c_res['response']}\" | [{c_res['classification']}]", flush=True)
        time.sleep(0.5)

    # ====================================================================
    # PHASE 3: SECOND TEST — PROMPT EFFECT (5 prompts x 5 runs)
    # ====================================================================
    print("\n==================================================================", flush=True)
    print("                 PHASE 3: PROMPT EFFECT BENCHMARK                ", flush=True)
    print("==================================================================", flush=True)

    prompts = {
        "PROMPT_A": "Translate Chinese into natural Vietnamese.\nReturn only the final translation.",
        "PROMPT_B": "Translate Chinese into natural Vietnamese.\nUse minimal reasoning necessary.\nReturn only the final translation.",
        "PROMPT_C": "Translate Chinese into natural Vietnamese.\nThink briefly and efficiently.\nReturn only the final translation.",
        "PROMPT_D": "Translate Chinese into natural Vietnamese.\nFor simple sentences, use concise reasoning.\nReturn only the final translation.",
        "PROMPT_E": "Professional Chinese-Vietnamese subtitle translation.\nPreserve meaning, tone and natural Vietnamese.\nAvoid unnecessary analysis.\nReturn only the final translation."
    }

    prompt_results = {}

    for p_name, p_body in prompts.items():
        print(f"\n--- Testing [{p_name}] (5 runs, num_predict={min_safe_budget}) ---", flush=True)
        p_runs = []
        for pr_idx in range(1, 6):
            pr_res = call_raw_generate(
                prompt="爸爸和妈妈去买菜。",
                system=p_body,
                num_predict=min_safe_budget,
                timeout=240
            )
            p_runs.append(pr_res)
            print(f"  Run #{pr_idx}: {pr_res['elapsed']:.2f}s | Tokens: {pr_res['eval_count']} (Think: ~{pr_res['thinking_tokens_est']}, Final: {pr_res['response_tokens_est']}) | Speed: {pr_res['speed']:.1f} t/s | Output: \"{pr_res['response']}\" | [{pr_res['classification']}]", flush=True)
            time.sleep(0.5)
        prompt_results[p_name] = p_runs

    # Save all raw results to JSON
    full_output = {
        "hardware": "NVIDIA GTX 1650 Ti 4GB",
        "model": "qwen3:4b",
        "min_safe_budget": min_safe_budget,
        "budget_matrix": budget_matrix_results,
        "confirmation_runs": confirm_runs,
        "prompt_effect": prompt_results
    }
    out_file = BASE_DIR / "tests" / "minimum_thinking_budget_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(full_output, f, indent=2, ensure_ascii=False)
    print(f"\n[BENCHMARK COMPLETED] All results recorded in: {out_file}", flush=True)

if __name__ == "__main__":
    run_benchmark()
