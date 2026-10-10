import urllib.request
import json
import time

payload = {
    "model": "qwen3:4b",
    "prompt": "Translate this to Vietnamese: 爸爸和妈妈去买菜。",
    "stream": False,
    "options": {
        "num_predict": 1024
    }
}

t0 = time.time()
req = urllib.request.Request(
    "http://localhost:11434/api/generate",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

try:
    with urllib.request.urlopen(req, timeout=120) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        elapsed = time.time() - t0
        print("=== RAW RESPONSE KEYS ===")
        print(list(res.keys()))
        print(f"Elapsed: {elapsed:.2f}s")
        print(f"Total tokens: {res.get('eval_count', 0)}")
        print("=== RESPONSE VALUE ===")
        print(repr(res.get("response", "")))
        if "thinking" in res:
            print("=== THINKING VALUE ===")
            print(repr(res.get("thinking", "")))
except Exception as e:
    print("Error:", e)
