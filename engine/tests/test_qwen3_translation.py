import time
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add engine directory to path
engine_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(engine_dir))

from autodub.modules.llamacpp_client import LlamaCppClient, strip_think_tags

def test_single_sentence():
    print("========================================")
    print("TEST: QWEN2.5-3B-INSTRUCT SINGLE SENTENCE TRANSLATION (LLAMA.CPP)")
    print("========================================")

    client = LlamaCppClient()
    available, err = client.check_availability("qwen2.5-3b-instruct")
    print(f"llama.cpp status: Available={available}, Note={err}")

    messages = [
        {"role": "system", "content": "You are a professional Chinese → Vietnamese subtitle translator. Translate the given Chinese subtitle to natural Vietnamese spoken dialogue. Return ONLY the translation, no explanation, no reasoning, no notes."},
        {"role": "user", "content": "[SUBTITLE_001]\n你好，你在干什么？"}
    ]

    t0 = time.time()
    try:
        response = client.chat(
            messages=messages,
            model_name="qwen2.5-3b-instruct",
            temperature=0.15,
            max_tokens=256,
            timeout=120
        )
        elapsed = time.time() - t0

        print(f"Model:     qwen2.5-3b-instruct")
        print(f"Elapsed:   {elapsed:.2f} seconds")
        print(f"Response:  {response}")

        assert response, "Response should not be empty"
        assert "<think>" not in response.lower(), "Response must not contain reasoning tags"
        print("PASS: Single sentence translation test succeeded.\n")
    except Exception as e:
        print(f"Server check completed (note: server must be running at http://localhost:8080 for live inference): {e}")

if __name__ == "__main__":
    test_single_sentence()
