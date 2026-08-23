import json
import sys
import urllib.request
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def test_raw_assistant_prompt(prefill=""):
    url = "http://localhost:11434/api/generate"
    # Format standard ChatML without <think>
    system_text = "You are a professional Chinese-to-Vietnamese subtitle translator. Output ONLY the Vietnamese translation."
    user_text = "你好，你在干什么？"
    
    if prefill:
        prompt_raw = f"<|im_start|>system\n{system_text}<|im_end|>\n<|im_start|>user\n{user_text}<|im_end|>\n<|im_start|>assistant\n{prefill}"
    else:
        prompt_raw = f"<|im_start|>system\n{system_text}<|im_end|>\n<|im_start|>user\n{user_text}<|im_end|>\n<|im_start|>assistant\n"

    payload = {
        "model": "qwen3:4b",
        "prompt": prompt_raw,
        "raw": True,
        "stream": False,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 128,
            "stop": ["<|im_end|>", "<|endoftext|>"]
        }
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST"
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            elapsed = time.time() - t0
            raw = json.loads(resp.read().decode("utf-8"))
            print(f"=== TEST RAW (prefill='{prefill}') ===")
            print(f"Response: {json.dumps(raw.get('response', ''), ensure_ascii=False)}")
            print(f"Done Reason: {raw.get('done_reason')}")
            print(f"Eval Count: {raw.get('eval_count')} tokens in {elapsed:.2f}s ({raw.get('eval_count')/elapsed:.1f} tok/s)\n")
            return raw
    except Exception as e:
        print(f"Error: {e}")
        return {}

if __name__ == "__main__":
    # Test 1: ChatML ending with <|im_start|>assistant\n
    test_raw_assistant_prompt(prefill="")
    # Test 2: ChatML ending with <|im_start|>assistant\n<think>\n</think>\n (closed think tag)
    test_raw_assistant_prompt(prefill="<think>\n</think>\n")
    # Test 3: ChatML with direct Vietnamese subtitle prefix
    test_raw_assistant_prompt(prefill="Chào, ")
