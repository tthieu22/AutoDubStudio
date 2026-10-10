import time
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Add engine directory to path
engine_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(engine_dir))

from autodub.modules.translator import RealTranslator

def test_continuous_dialogue():
    print("========================================")
    print("TEST: QWEN3:4B CONTINUOUS DIALOGUE TEST")
    print("========================================")

    translator = RealTranslator(model_name="qwen3:4b", batch_size=6)
    
    dialogue_items = [
        {"id_num": 1, "id_str": "SUBTITLE_001", "text": "你来了。"},
        {"id_num": 2, "id_str": "SUBTITLE_002", "text": "我等你好久了。"},
        {"id_num": 3, "id_str": "SUBTITLE_003", "text": "你为什么不告诉我？"},
        {"id_num": 4, "id_str": "SUBTITLE_004", "text": "我不能说。"},
        {"id_num": 5, "id_str": "SUBTITLE_005", "text": "为什么？"},
        {"id_num": 6, "id_str": "SUBTITLE_006", "text": "เพราะ (因为)有人在监视我们。"}
    ]

    print("Sending batch request (6 subtitles) to Qwen3:4b (think=false)...", flush=True)
    t0 = time.time()
    res = translator.translate_batch(
        batch_items=dialogue_items,
        translation_style="ancient",
        locked_entities={"男主": "Tần Vương", "女主": "Lâm Uyển"}
    )
    elapsed = time.time() - t0

    print(f"Elapsed Time: {elapsed:.2f}s")
    print("Results:")
    for item in dialogue_items:
        id_str = item["id_str"]
        trans = res.get(id_str, "")
        print(f"  {id_str} | Source: {item['text']} -> Vietsub: {trans}")
        assert trans, f"Translation for {id_str} should not be empty"
        assert "<think>" not in trans.lower(), f"Reasoning leakage detected in {id_str}"

    assert len(res) == 6, f"Expected 6 translations, got {len(res)}"
    print("\nPASS: Continuous dialogue context test succeeded.\n")

if __name__ == "__main__":
    test_continuous_dialogue()
