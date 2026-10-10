import json
import sys
import urllib.request
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def test_clean_non_thinking(sentence):
    url = "http://localhost:11434/api/generate"
    
    prompt_raw = f"""<|im_start|>system
You are a professional Chinese to Vietnamese subtitle translator.
Translate directly and naturally into Vietnamese. Output ONLY the Vietnamese translation.<|im_end|>
<|im_start|>user
[SUBTITLE_001]
{sentence}<|im_end|>
<|im_start|>assistant
<think>
</think>
[SUBTITLE_001]
"""

    payload = {
        "model": "qwen3:4b",
        "prompt": prompt_raw,
        "raw": True,
        "stream": False,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.1,
            "num_predict": 64,
            "stop": ["<|im_end|>", "\n[", "<|im_start|>", "\n\n", "</think>"]
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            elapsed = time.time() - t0
            raw = json.loads(resp.read().decode("utf-8"))
            resp_txt = raw.get("response", "").strip()
            eval_count = raw.get("eval_count", 0)
            thinking_txt = raw.get("thinking", "")
            speed = eval_count / elapsed if elapsed > 0 else 0
            
            # Check for any leakage of reasoning
            has_think_leak = "<think>" in resp_txt or "</think>" in resp_txt or "Okay" in resp_txt or "Let me think" in resp_txt
            status = "PASS" if (resp_txt and not has_think_leak) else "FAIL"
            
            print(f"Input:    {sentence}")
            print(f"Output:   \"{resp_txt}\"")
            print(f"Thinking Field: {'EMPTY' if not thinking_txt else thinking_txt}")
            print(f"Tokens:   {eval_count} tokens | Time: {elapsed:.2f}s | Speed: {speed:.1f} tok/s | Status: {status}\n")
            return {
                "input": sentence,
                "output": resp_txt,
                "tokens": eval_count,
                "elapsed": elapsed,
                "speed": speed,
                "status": status
            }
    except Exception as e:
        print(f"Error: {e}")
        return {}

if __name__ == "__main__":
    sentences = [
        "你好，你在干什么？",
        "爸爸和妈妈去买菜。",
        "你吃饭了吗？",
        "谢谢你。",
        "快走！",
        "我不知道。",
        "你为什么骗我？",
        "今天我们一起回家。",
        "我真的没有骗你。",
        "你这个时候还敢跟本王谈条件？"
    ]
    results = []
    for s in sentences:
        r = test_clean_non_thinking(s)
        if r:
            results.append(r)
            
    print("==================================================")
    print(f"TOTAL RUNS: {len(results)}/10 PASS")
    avg_time = sum(r['elapsed'] for r in results)/len(results)
    avg_tokens = sum(r['tokens'] for r in results)/len(results)
    print(f"Average Latency: {avg_time:.2f}s")
    print(f"Average Tokens:  {avg_tokens:.1f}")
    print("==================================================")
