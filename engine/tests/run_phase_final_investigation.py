import json
import sys
import urllib.request
import urllib.error
import subprocess
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def run_cmd(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, encoding="utf-8", stderr=subprocess.STDOUT)
    except Exception as e:
        return str(e)

def http_post(endpoint, payload):
    url = f"http://localhost:11434{endpoint}"
    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            elapsed = time.time() - t0
            raw = json.loads(resp.read().decode("utf-8"))
            return True, elapsed, raw
    except Exception as e:
        elapsed = time.time() - t0
        return False, elapsed, {"error": str(e)}

def run_investigation():
    print("==================================================================", flush=True)
    print("   PHASE FINAL — QWEN3:4B NATIVE THINKING CONTROL INVESTIGATION   ", flush=True)
    print("==================================================================", flush=True)

    input_text = "你好，你在干什么？"
    results = {}

    # -------------------------------------------------------------
    # TEST 1: /api/generate with think=false
    # -------------------------------------------------------------
    print("\n[TEST 1] POST /api/generate (think=false)...", flush=True)
    payload1 = {
        "model": "qwen3:4b",
        "prompt": f"Translate Chinese into natural Vietnamese. Return only the final translation.\n\n{input_text}",
        "stream": False,
        "think": False,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 256
        }
    }
    s1, t1, r1 = http_post("/api/generate", payload1)
    results["TEST_1"] = {"success": s1, "time": t1, "raw": r1}
    print(f"Time: {t1:.2f}s | Done: {r1.get('done_reason')} | Eval: {r1.get('eval_count')} tokens")
    print("RAW JSON Dump:")
    print(json.dumps(r1, indent=2, ensure_ascii=False))

    # -------------------------------------------------------------
    # TEST 2: /api/generate with think=true
    # -------------------------------------------------------------
    print("\n[TEST 2] POST /api/generate (think=true)...", flush=True)
    payload2 = {
        "model": "qwen3:4b",
        "prompt": f"Translate Chinese into natural Vietnamese. Return only the final translation.\n\n{input_text}",
        "stream": False,
        "think": True,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 256
        }
    }
    s2, t2, r2 = http_post("/api/generate", payload2)
    results["TEST_2"] = {"success": s2, "time": t2, "raw": r2}
    print(f"Time: {t2:.2f}s | Done: {r2.get('done_reason')} | Eval: {r2.get('eval_count')} tokens")
    print("RAW JSON Dump:")
    print(json.dumps(r2, indent=2, ensure_ascii=False))

    # -------------------------------------------------------------
    # TEST 3: /api/chat with think=false
    # -------------------------------------------------------------
    print("\n[TEST 3] POST /api/chat (think=false)...", flush=True)
    payload3 = {
        "model": "qwen3:4b",
        "messages": [
            {"role": "system", "content": "Translate Chinese into natural Vietnamese. Return only the final translation."},
            {"role": "user", "content": input_text}
        ],
        "stream": False,
        "think": False,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 256
        }
    }
    s3, t3, r3 = http_post("/api/chat", payload3)
    results["TEST_3"] = {"success": s3, "time": t3, "raw": r3}
    print(f"Time: {t3:.2f}s | Done: {r3.get('done_reason')} | Eval: {r3.get('eval_count')} tokens")
    print("RAW JSON Dump:")
    print(json.dumps(r3, indent=2, ensure_ascii=False))

    # -------------------------------------------------------------
    # TEST 4: /api/chat with think=true
    # -------------------------------------------------------------
    print("\n[TEST 4] POST /api/chat (think=true)...", flush=True)
    payload4 = {
        "model": "qwen3:4b",
        "messages": [
            {"role": "system", "content": "Translate Chinese into natural Vietnamese. Return only the final translation."},
            {"role": "user", "content": input_text}
        ],
        "stream": False,
        "think": True,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 256
        }
    }
    s4, t4, r4 = http_post("/api/chat", payload4)
    results["TEST_4"] = {"success": s4, "time": t4, "raw": r4}
    print(f"Time: {t4:.2f}s | Done: {r4.get('done_reason')} | Eval: {r4.get('eval_count')} tokens")
    print("RAW JSON Dump:")
    print(json.dumps(r4, indent=2, ensure_ascii=False))

    # -------------------------------------------------------------
    # TEST 5, 6, 7: Metadata & Template Analysis
    # -------------------------------------------------------------
    print("\n[TEST 5, 6, 7] Model Show & Template...", flush=True)
    show_info = run_cmd("ollama show qwen3:4b")
    template_info = run_cmd("ollama show --template qwen3:4b")
    modelfile_info = run_cmd("ollama show --modelfile qwen3:4b")
    results["SHOW"] = show_info
    results["TEMPLATE"] = template_info
    results["MODELFILE"] = modelfile_info

    # -------------------------------------------------------------
    # TEST 8: /api/generate with minimal prompt & think=false
    # -------------------------------------------------------------
    print("\n[TEST 8] POST /api/generate Minimal Prompt (think=false)...", flush=True)
    payload8 = {
        "model": "qwen3:4b",
        "prompt": f"Translate to Vietnamese only:\n\n{input_text}",
        "stream": False,
        "think": False,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 256
        }
    }
    s8, t8, r8 = http_post("/api/generate", payload8)
    results["TEST_8"] = {"success": s8, "time": t8, "raw": r8}
    print(f"Time: {t8:.2f}s | Done: {r8.get('done_reason')} | Eval: {r8.get('eval_count')} tokens")
    print("RAW JSON Dump:")
    print(json.dumps(r8, indent=2, ensure_ascii=False))

    # -------------------------------------------------------------
    # TEST 9: /api/generate with minimal prompt & think=true
    # -------------------------------------------------------------
    print("\n[TEST 9] POST /api/generate Minimal Prompt (think=true)...", flush=True)
    payload9 = {
        "model": "qwen3:4b",
        "prompt": f"Translate to Vietnamese only:\n\n{input_text}",
        "stream": False,
        "think": True,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 256
        }
    }
    s9, t9, r9 = http_post("/api/generate", payload9)
    results["TEST_9"] = {"success": s9, "time": t9, "raw": r9}
    print(f"Time: {t9:.2f}s | Done: {r9.get('done_reason')} | Eval: {r9.get('eval_count')} tokens")
    print("RAW JSON Dump:")
    print(json.dumps(r9, indent=2, ensure_ascii=False))

    # Save to file
    out_file = BASE_DIR / "tests" / "phase_final_investigation_results.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n[INVESTIGATION COMPLETE] Results saved to {out_file}", flush=True)

if __name__ == "__main__":
    run_investigation()
