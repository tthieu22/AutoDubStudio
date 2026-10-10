import json
import sys
import urllib.request
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def test_stop_and_format(sentence):
    url = "http://localhost:11434/api/generate"
    
    prompt_raw = f"""<|im_start|>system
You are a direct subtitle translator. Translate Chinese directly to Vietnamese.
Output format:
[VIETNAMESE]
<translated text><|im_end|>
<|im_start|>user
[CHINESE]
{sentence}<|im_end|>
<|im_start|>assistant
<think>
</think>
[VIETNAMESE]
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
            "stop": ["<|im_end|>", "\n[", "<|im_start|>", "\n\n"]
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
            speed = eval_count / elapsed if elapsed > 0 else 0
            print(f"Input:    {sentence}")
            print(f"Output:   \"{resp_txt}\"")
            print(f"Tokens:   {eval_count} tokens | Time: {elapsed:.2f}s | Speed: {speed:.1f} tok/s | Done: {raw.get('done_reason')}\n")
            return raw
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
    for s in sentences:
        test_stop_and_format(s)
