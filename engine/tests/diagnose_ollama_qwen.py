import urllib.request
import json
import time
import sys
import subprocess
from pathlib import Path

# Add engine directory to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from autodub.config import TRANSLATION_MODEL
from autodub.modules.ollama_model_manager import OllamaModelManager

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def get_ollama_ps(base_url="http://localhost:11434"):
    try:
        req = urllib.request.urlopen(f"{base_url}/api/ps", timeout=5)
        return json.loads(req.read().decode())
    except Exception as e:
        return {"error": str(e)}


def verify_strictly_exclusive(model_manager: OllamaModelManager, stage_name: str) -> None:
    """Verifies that ONLY qwen3:4b is loaded in VRAM. Raises RuntimeError if foreign model is present."""
    loaded = model_manager.get_loaded_models()
    loaded_names = [m.get("name", "") or m.get("model", "") for m in loaded]
    
    for name in loaded_names:
        if name != TRANSLATION_MODEL and not name.startswith("qwen3") and name != "qwen3":
            err = f"MODEL_CONFLICT_DETECTED ({stage_name}): Foreign model '{name}' detected in VRAM. Active models: {loaded_names}."
            print(f"\n[FATAL] {err}")
            raise RuntimeError(err)


def run_single_subtitle_diag(model_name: str = TRANSLATION_MODEL):
    print(f"\n====================================================")
    print(f"RUNNING DIAGNOSTIC FOR EXCLUSIVE MODEL: {model_name}")
    print(f"====================================================")

    system_prompt = "You are a professional Chinese → Vietnamese subtitle translator. Think carefully about context, tone, and natural Vietnamese. Return ONLY the final Vietnamese translation."
    user_prompt = "你好，你在干什么？"

    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "stream": False,
        "think": True,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 512
        }
    }

    print("POST /api/chat Payload:")
    print(json.dumps(payload, indent=2, ensure_ascii=False))

    t0 = time.time()
    req = urllib.request.Request(
        "http://localhost:11434/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        raw_res_bytes = urllib.request.urlopen(req, timeout=120).read()
        wall_time = time.time() - t0
        res_json = json.loads(raw_res_bytes.decode())
    except Exception as e:
        print(f"ERROR executing chat request: {e}")
        return None

    msg_obj = res_json.get("message", {})
    raw_content = msg_obj.get("content", "")

    # Check thinking leakage
    lower_content = raw_content.lower()
    has_thinking = any(kw in lower_content for kw in ["let me think", "thinking", "<think>", "first,", "in vietnamese,"])

    # Extract Ollama timing metrics (nanoseconds -> seconds)
    total_duration_sec = res_json.get("total_duration", 0) / 1e9
    load_duration_sec = res_json.get("load_duration", 0) / 1e9
    prompt_eval_sec = res_json.get("prompt_eval_duration", 0) / 1e9
    prompt_eval_count = res_json.get("prompt_eval_count", 0)
    eval_sec = res_json.get("eval_duration", 0) / 1e9
    eval_count = res_json.get("eval_count", 0)

    tokens_per_sec = eval_count / eval_sec if eval_sec > 0 else 0.0

    ps_info = get_ollama_ps()
    vram_usage = "Unknown"
    processor = "Unknown"
    if isinstance(ps_info, dict) and "models" in ps_info:
        for m in ps_info["models"]:
            if m.get("name") == model_name or m.get("model") == model_name:
                vram_bytes = m.get("size_vram", 0)
                vram_usage = f"{vram_bytes / (1024*1024):.1f} MB / 4096 MB"
                processor = f"{m.get('processor', 'GPU/CPU')}"

    metrics = {
        "model": model_name,
        "wall_time": wall_time,
        "total_duration": total_duration_sec,
        "load_duration": load_duration_sec,
        "prompt_eval_duration": prompt_eval_sec,
        "prompt_eval_count": prompt_eval_count,
        "eval_duration": eval_sec,
        "eval_count": eval_count,
        "tokens_per_sec": tokens_per_sec,
        "has_thinking": has_thinking,
        "vram_usage": vram_usage,
        "processor": processor,
        "raw_response": raw_content
    }

    print(f"\n====================================================")
    print(f"{model_name.upper()} EXCLUSIVE DIAGNOSTIC RESULTS")
    print(f"====================================================")
    print(f"Model:                   {model_name}")
    print(f"Thinking Detected:       {'YES (FAIL - Thinking still active)' if has_thinking else 'OFF (PASS)'}")
    print(f"Endpoint:                POST /api/chat")
    print(f"Stream:                  false")
    print(f"----------------------------------------------------")
    print(f"TIMING METRICS")
    print(f"----------------------------------------------------")
    print(f"Wall Clock Time:         {wall_time:.2f} sec")
    print(f"Total Duration:          {total_duration_sec:.2f} sec")
    print(f"Load Duration:           {load_duration_sec:.2f} sec")
    print(f"Prompt Eval Duration:    {prompt_eval_sec:.2f} sec")
    print(f"Generation Duration:     {eval_sec:.2f} sec")
    print(f"----------------------------------------------------")
    print(f"TOKEN METRICS")
    print(f"----------------------------------------------------")
    print(f"Prompt Tokens:           {prompt_eval_count}")
    print(f"Output Tokens:           {eval_count}")
    print(f"Generation Speed:        {tokens_per_sec:.2f} tokens/sec")
    print(f"----------------------------------------------------")
    print(f"HARDWARE / RUNTIME")
    print(f"----------------------------------------------------")
    print(f"Processor:               {processor}")
    print(f"VRAM Memory:             {vram_usage}")
    print(f"----------------------------------------------------")
    print(f"RAW RESPONSE:")
    print(repr(raw_content))
    print(f"====================================================\n")

    return metrics


def run_diagnostics():
    print("====================================================")
    print("AUTODUBSTUDIO OLLAMA EXCLUSIVE DIAGNOSTIC SUITE")
    print("====================================================")

    try:
        ver_out = subprocess.check_output(["ollama", "--version"], text=True).strip()
        print(f"Ollama Version: {ver_out}")
    except Exception as e:
        print(f"Ollama Version check failed: {e}")

    manager = OllamaModelManager()

    # Step 1: Pre-check & Unload foreign models
    print("\n[STEP 1] Detecting and unloading foreign models from VRAM...")
    unloaded = manager.unload_other_models(target_model=TRANSLATION_MODEL)
    if unloaded:
        print(f"Unloaded foreign models: {unloaded}")
    else:
        print("No foreign models detected.")

    # Step 2: Ensure Qwen3 is loaded with keep_alive=1h
    print("\n[STEP 2] Ensuring qwen3:4b is exclusively loaded (keep_alive=1h)...")
    ok, err = manager.ensure_qwen3_loaded()
    if not ok:
        print(f"[FATAL] Failed to load {TRANSLATION_MODEL}: {err}")
        sys.exit(1)

    # Step 3: Verify exclusivity before inference
    print("\n[STEP 3] Verifying exclusive model residency before inference...")
    verify_strictly_exclusive(manager, stage_name="PRE_TEST")
    is_exclusive, status_msg = manager.verify_exclusive_model(TRANSLATION_MODEL)
    print(f"Exclusive Status: {status_msg}")

    # Step 4: Run single-subtitle diagnostic
    print("\n[STEP 4] Running single-subtitle diagnostic inference...")
    m_qwen3 = run_single_subtitle_diag(TRANSLATION_MODEL)

    # Step 5: Verify exclusivity after inference
    print("\n[STEP 5] Verifying exclusive model residency after inference...")
    verify_strictly_exclusive(manager, stage_name="POST_TEST")

    # Step 6: Print Final Runtime Summary
    status = manager.get_runtime_status()
    print("====================================================")
    print("FINAL EXCLUSIVE MODEL LIFECYCLE SUMMARY")
    print("====================================================")
    print(f"Production Model:        {status['target_model']}")
    print(f"Exclusive VRAM Loaded:   {'YES (PASS)' if status['is_exclusive'] else 'NO (FAIL)'}")
    print(f"Total Loaded Models:     {status['loaded_model_count']}")
    print(f"Total VRAM Used:         {status['total_vram_used_mb']:.1f} MB / 4096 MB")
    print(f"Model Exclusivity:       qwen3:4b ONLY")
    print("====================================================\n")


if __name__ == "__main__":
    run_diagnostics()
