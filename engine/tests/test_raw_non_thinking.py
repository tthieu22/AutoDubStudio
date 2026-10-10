import json
import sys
import urllib.request
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def test_generate_non_thinking():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "qwen3:4b",
        "prompt": "Translate this Chinese subtitle into natural Vietnamese.\nReturn ONLY the final Vietnamese translation.\n\n你好，你在干什么？",
        "stream": False,
        "think": False,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 128
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            elapsed = time.time() - t0
            raw = json.loads(resp.read().decode("utf-8"))
            print("=== RAW /api/generate (think: False) ===")
            print(json.dumps(raw, indent=2, ensure_ascii=False))
            print(f"\nElapsed: {elapsed:.2f}s")
            return raw
    except Exception as e:
        print(f"Error: {e}")
        return {}

def test_chat_non_thinking():
    url = "http://localhost:11434/api/chat"
    payload = {
        "model": "qwen3:4b",
        "messages": [
            {"role": "system", "content": "Translate Chinese subtitles into natural Vietnamese.\nReturn ONLY the final translation."},
            {"role": "user", "content": "你好，你在干什么？"}
        ],
        "stream": False,
        "think": False,
        "keep_alive": "1h",
        "options": {
            "temperature": 0.15,
            "num_predict": 128
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
        with urllib.request.urlopen(req, timeout=120) as resp:
            elapsed = time.time() - t0
            raw = json.loads(resp.read().decode("utf-8"))
            print("\n=== RAW /api/chat (think: False) ===")
            print(json.dumps(raw, indent=2, ensure_ascii=False))
            print(f"\nElapsed: {elapsed:.2f}s")
            return raw
    except Exception as e:
        print(f"Error: {e}")
        return {}

if __name__ == "__main__":
    test_generate_non_thinking()
    test_chat_non_thinking()
