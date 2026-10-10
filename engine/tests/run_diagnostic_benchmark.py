import json
import os
import sys
import time
import urllib.request
import urllib.error
import re
from pathlib import Path

# Setup paths
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from autodub.modules.translator import RealTranslator
from autodub.modules.output_sanitizer import TranslationOutputSanitizer
from autodub.modules.ollama_client import strip_think_tags

PROMPTS = [
    "爸爸和妈妈去买菜。",
    "你好，你在干什么？",
    "你吃饭了吗？",
    "这个世界上还有什么事情是我不知道的？",
    "你为什么要骗我？"
]

def run_diagnostic():
    print("==================================================================", flush=True)
    print("      AUTODUBSTUDIO — QWEN3:4B THINKING BENCHMARK DIAGNOSTIC      ", flush=True)
    print("==================================================================", flush=True)
    print("Model:            qwen3:4b", flush=True)
    print("Thinking Mode:    ON (think=True)", flush=True)
    print("Max Retries:      0 (Single shot, zero retries)", flush=True)
    print("Concurrency:      1", flush=True)
    
    # Calculate exact num_predict used in current RealTranslator for batch=1
    sample_batch = [{"id_str": "SUBTITLE_001", "text": "test"}]
    num_predict = min(2048, max(1024, len(sample_batch) * 400))
    print(f"num_predict:      {num_predict}", flush=True)
    print("------------------------------------------------------------------\n", flush=True)

    translator = RealTranslator()
    base_url = "http://localhost:11434"

    results = []

    for idx, prompt_text in enumerate(PROMPTS, start=1):
        print(f"==================== RUN #{idx} / {len(PROMPTS)} ====================", flush=True)
        print(f"Input: \"{prompt_text}\"", flush=True)

        batch_items = [{"id_str": "SUBTITLE_001", "text": prompt_text}]
        expected_ids = ["SUBTITLE_001"]

        # Build prompt using RealTranslator
        subtitles_input = f"[SUBTITLE_001]\n{prompt_text}"
        user_content = f"YOU MUST TRANSLATE ALL 1 SUBTITLES FROM SUBTITLE_001 TO SUBTITLE_001. DO NOT STOP UNTIL SUBTITLE_001 IS TRANSLATED.\n\nSUBTITLES TO TRANSLATE:\n\n{subtitles_input}"
        system_prompt = translator._build_system_prompt()
        full_prompt = f"{system_prompt}\n\n{user_content}"

        payload = {
            "model": "qwen3:4b",
            "prompt": full_prompt,
            "stream": False,
            "think": True,
            "keep_alive": "1h",
            "options": {
                "temperature": 0.15,
                "num_predict": num_predict
            }
        }

        raw_json_res = None
        status = "UNKNOWN"
        error_msg = ""
        t0 = time.time()

        try:
            req = urllib.request.Request(
                f"{base_url}/api/generate",
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json", "User-Agent": "AutoDubStudio"}
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                raw_bytes = resp.read()
                raw_json_res = json.loads(raw_bytes.decode("utf-8"))
        except (urllib.error.URLError, TimeoutError) as e:
            if "timed out" in str(e).lower() or isinstance(e, TimeoutError):
                status = "TIMEOUT"
            else:
                status = "API_ERROR"
            error_msg = str(e)
        except Exception as e:
            status = "API_ERROR"
            error_msg = str(e)

        wall_duration = time.time() - t0

        if raw_json_res is not None:
            # Extract fields per Section 1
            model = raw_json_res.get("model", None)
            created_at = raw_json_res.get("created_at", None)
            response_val = raw_json_res.get("response", None)
            thinking_val = raw_json_res.get("thinking", None)
            message_val = raw_json_res.get("message", None)
            done = raw_json_res.get("done", None)
            done_reason = raw_json_res.get("done_reason", None)
            total_duration = raw_json_res.get("total_duration", None)
            load_duration = raw_json_res.get("load_duration", None)
            prompt_eval_count = raw_json_res.get("prompt_eval_count", None)
            prompt_eval_duration = raw_json_res.get("prompt_eval_duration", None)
            eval_count = raw_json_res.get("eval_count", None)
            eval_duration = raw_json_res.get("eval_duration", None)

            # Compute seconds
            total_sec = (total_duration / 1e9) if total_duration else wall_duration
            load_sec = (load_duration / 1e9) if load_duration else 0.0
            prompt_sec = (prompt_eval_duration / 1e9) if prompt_eval_duration else 0.0
            eval_sec = (eval_duration / 1e9) if eval_duration else 0.0
            tok_per_sec = (eval_count / eval_sec) if (eval_count and eval_sec > 0) else 0.0

            # Log Complete Raw Ollama JSON Fields
            print("\n[RAW OLLAMA RESPONSE JSON METADATA]")
            print(f"  model:                {model}")
            print(f"  created_at:           {created_at}")
            print(f"  done:                 {done}")
            print(f"  done_reason:          {done_reason}")
            print(f"  total_duration:       {total_duration} ({total_sec:.2f}s)")
            print(f"  load_duration:        {load_duration} ({load_sec:.2f}s)")
            print(f"  prompt_eval_count:    {prompt_eval_count}")
            print(f"  prompt_eval_duration: {prompt_eval_duration} ({prompt_sec:.2f}s)")
            print(f"  eval_count:           {eval_count}")
            print(f"  eval_duration:        {eval_duration} ({eval_sec:.2f}s)")
            print(f"  thinking field:       {repr(thinking_val)}")
            print(f"  message field:        {repr(message_val)}")
            print(f"  response length:      {len(response_val) if response_val else 0} chars")

            # Check if response has thinking tags embedded
            has_think_tags = bool(re.search(r'<think>[\s\S]*?</think>', response_val or "", re.IGNORECASE))
            has_unclosed_think = bool(re.search(r'^<think>', (response_val or "").strip(), re.IGNORECASE)) and not has_think_tags

            # Extract reasoning text vs final text
            stripped_text = strip_think_tags(response_val or "")
            sanitized_text = TranslationOutputSanitizer.sanitize(stripped_text)

            print("\n[RESPONSE PAYLOAD]")
            print(f"  raw response:         {repr(response_val)}")
            print(f"  stripped text:        {repr(stripped_text)}")
            print(f"  sanitized text:       {repr(sanitized_text)}")

            # Count approximate thinking vs final response tokens
            # If Ollama returns <think> in response:
            think_match = re.search(r'<think>([\s\S]*?)</think>', response_val or "", re.IGNORECASE)
            if think_match:
                thinking_content = think_match.group(1)
                # rough char-to-token ratio ~ 4 chars/token
                thinking_token_est = max(1, len(thinking_content) // 4)
                final_token_est = max(0, (eval_count or 0) - thinking_token_est)
            elif has_unclosed_think or (thinking_val and not response_val):
                thinking_token_est = eval_count or 0
                final_token_est = 0
            else:
                thinking_token_est = 0
                final_token_est = eval_count or 0

            # Classification per Section 3 & 7
            if sanitized_text and not any(kw in sanitized_text.lower() for kw in ["let me think", "okay, let's", "analyzing"]):
                status = "SUCCESS_TRANSLATION"
            elif (response_val == "" or not response_val) and thinking_val:
                status = "THINKING_ONLY"
            elif (response_val == "" or not response_val) and not thinking_val:
                status = "EMPTY_RESPONSE"
            elif has_unclosed_think or (not sanitized_text and (has_think_tags or thinking_val)):
                status = "THINKING_ONLY"
            elif any(kw in (response_val or "").lower() for kw in ["let me think", "okay, let's", "first, i need"]) and not sanitized_text:
                status = "INVALID_REASONING_OUTPUT"
            else:
                status = "INVALID_REASONING_OUTPUT"

            res_record = {
                "run": idx,
                "input": prompt_text,
                "status": status,
                "total_sec": total_sec,
                "load_sec": load_sec,
                "prompt_sec": prompt_sec,
                "eval_sec": eval_sec,
                "eval_count": eval_count or 0,
                "tok_per_sec": tok_per_sec,
                "thinking_tokens_est": thinking_token_est,
                "final_tokens_est": final_token_est,
                "raw_response": response_val,
                "sanitized_translation": sanitized_text,
                "done_reason": done_reason
            }
        else:
            res_record = {
                "run": idx,
                "input": prompt_text,
                "status": status,
                "total_sec": wall_duration,
                "load_sec": 0,
                "prompt_sec": 0,
                "eval_sec": 0,
                "eval_count": 0,
                "tok_per_sec": 0,
                "thinking_tokens_est": 0,
                "final_tokens_est": 0,
                "raw_response": None,
                "sanitized_translation": "",
                "done_reason": error_msg
            }

        results.append(res_record)

        # Print Performance Metrics per Section 8
        print("\n[PERFORMANCE & CLASSIFICATION]")
        print(f"  Run:                    #{idx}")
        print(f"  Input:                  {prompt_text}")
        print(f"  Status:                 {res_record['status']}")
        print(f"  Total:                  {res_record['total_sec']:.2f}s")
        print(f"  Load:                   {res_record['load_sec']:.2f}s")
        print(f"  Prompt:                 {res_record['prompt_sec']:.2f}s")
        print(f"  Generation:             {res_record['eval_sec']:.2f}s")
        print(f"  Eval tokens:            {res_record['eval_count']}")
        print(f"  Tokens/sec:             {res_record['tok_per_sec']:.2f} tok/s")
        print(f"  Thinking tokens (est):  {res_record['thinking_tokens_est']}")
        print(f"  Final response tokens:  {res_record['final_tokens_est']}")
        print(f"  Final Translation:      \"{res_record['sanitized_translation']}\"")
        print("------------------------------------------------------------------\n", flush=True)

    # Final Summary per Section 10
    print("\n==================================================================", flush=True)
    print("                     FINAL DIAGNOSTIC SUMMARY                     ", flush=True)
    print("==================================================================", flush=True)

    successes = [r for r in results if r["status"] == "SUCCESS_TRANSLATION"]
    empty_res = [r for r in results if r["status"] == "EMPTY_RESPONSE"]
    thinking_only = [r for r in results if r["status"] == "THINKING_ONLY"]
    invalid_reasoning = [r for r in results if r["status"] == "INVALID_REASONING_OUTPUT"]
    timeouts = [r for r in results if r["status"] == "TIMEOUT"]
    api_errors = [r for r in results if r["status"] == "API_ERROR"]

    print(f"Successful translations:    {len(successes)} / {len(PROMPTS)}")
    print(f"Empty responses:            {len(empty_res)}")
    print(f"Thinking-only:              {len(thinking_only)}")
    print(f"Invalid reasoning outputs:  {len(invalid_reasoning)}")
    print(f"Timeouts:                   {len(timeouts)}")
    print(f"API errors:                 {len(api_errors)}")

    avg_success_lat = (sum(r["total_sec"] for r in successes) / len(successes)) if successes else 0.0
    avg_speed = (sum(r["tok_per_sec"] for r in results if r["tok_per_sec"] > 0) / len([r for r in results if r["tok_per_sec"] > 0])) if any(r["tok_per_sec"] > 0 for r in results) else 0.0
    avg_thinking_tok = (sum(r["thinking_tokens_est"] for r in results) / len(results)) if results else 0.0
    avg_final_tok = (sum(r["final_tokens_est"] for r in results) / len(results)) if results else 0.0

    print(f"\nAverage successful latency: {avg_success_lat:.2f}s")
    print(f"Average generation speed:   {avg_speed:.2f} tok/s")
    print(f"Average thinking tokens:    {avg_thinking_tok:.1f}")
    print(f"Average final resp tokens:  {avg_final_tok:.1f}")

    print("\n------------------------------------------------------------------")
    print("Detailed Run Breakdown:")
    for r in results:
        print(f"  #{r['run']} | {r['input']:<25} | Status: {r['status']:<22} | Time: {r['total_sec']:>6.2f}s | Speed: {r['tok_per_sec']:>5.1f} t/s | DoneReason: {r['done_reason']}")
        if r['sanitized_translation']:
            print(f"      Translation: \"{r['sanitized_translation']}\"")
    print("==================================================================\n", flush=True)

    # Save to diagnostic json artifact
    diag_file = BASE_DIR / "tests" / "diagnostic_results.json"
    with open(diag_file, "w", encoding="utf-8") as f:
        json.dump({
            "num_predict": num_predict,
            "results": results,
            "summary": {
                "total_prompts": len(PROMPTS),
                "success_count": len(successes),
                "empty_response_count": len(empty_res),
                "thinking_only_count": len(thinking_only),
                "invalid_reasoning_count": len(invalid_reasoning),
                "timeout_count": len(timeouts),
                "api_error_count": len(api_errors),
                "avg_success_lat": avg_success_lat,
                "avg_speed": avg_speed,
                "avg_thinking_tokens": avg_thinking_tok,
                "avg_final_tokens": avg_final_tok
            }
        }, f, indent=2, ensure_ascii=False)
    print(f"Diagnostic results saved to: {diag_file}", flush=True)


if __name__ == "__main__":
    run_diagnostic()
