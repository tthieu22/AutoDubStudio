import time
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add engine directory to path
engine_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(engine_dir))

from autodub.modules.ollama_client import OllamaClient, strip_think_tags

def test_single_sentence():
    print("========================================")
    print("TEST: QWEN3:4B SINGLE SENTENCE TRANSLATION")
    print("========================================")

    client = OllamaClient()
    available, err = client.check_availability("qwen3:4b")
    assert available, f"Qwen3:4b model not available: {err}"

    messages = [
        {"role": "system", "content": "You are a professional Chinese → Vietnamese subtitle translator. Translate the given Chinese subtitle to natural Vietnamese spoken dialogue. Return ONLY the translation, no explanation, no reasoning, no notes."},
        {"role": "user", "content": "[SUBTITLE_001]\n你好，你在干什么？"}
    ]

    t0 = time.time()
    response = client.chat(
        messages=messages,
        model="qwen3:4b",
        temperature=0.15,
        num_predict=256,
        timeout=120
    )
    elapsed = time.time() - t0

    print(f"Model:     qwen3:4b")
    print(f"think:     false")
    print(f"Elapsed:   {elapsed:.2f} seconds")
    print(f"Response:  {response}")

    assert response, "Response should not be empty"
    assert "<think>" not in response.lower(), "Response must not contain reasoning tags"
    print("PASS: Single sentence translation test succeeded.\n")

if __name__ == "__main__":
    test_single_sentence()
