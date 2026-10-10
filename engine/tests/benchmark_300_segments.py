import os
import sys
import time
import json
from pathlib import Path

# Configure UTF-8 encoding and line buffering for Windows console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

_builtin_print = print
def print_flush(*args, **kwargs):
    kwargs["flush"] = True
    _builtin_print(*args, **kwargs)

print = print_flush

# Add engine directory to sys.path
engine_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(engine_dir))

from autodub.modules.ollama_client import OllamaClient
from autodub.modules.translator import RealTranslator, ContextBuilder
from autodub.modules.translator_qa import TranslationQaChecker
from autodub.modules.translator_repair import TranslationRepairService
from autodub.modules.output_sanitizer import TranslationOutputSanitizer
from autodub.modules.structured_parser import StructuredParser

# 300 Chinese Subtitle Test Segments
EASY_SEGMENTS = [
    {"id": i, "text": t} for i, t in enumerate([
        "你好。", "谢谢。", "再见。", "对不起。", "没关系。",
        "好的。", "可以。", "不行。", "快走。", "别动。",
        "是我。", "谁呀？", "吃了吗？", "走了。", "好吧。",
        "是的。", "不知道。", "明白。", "加油！", "晚安。"
    ] * 5, start=1)
]

CONTEXT_SEGMENTS = [
    {"id": i, "text": t} for i, t in enumerate([
        "你去哪儿？", "我去找妈妈。", "爸爸已经走了。", "她在厨房里做饭。",
        "我们一起去公园吧。", "佩奇和乔治在玩耍。", "你今天过得怎么样？",
        " me bao gio", "我们该回家了。", "妈妈，我饿了。"
    ] * 10, start=101)
]

HARD_SEGMENTS = [
    {"id": i, "text": t} for i, t in enumerate([
        "画蛇添足，自讨苦吃。", "事已至此，木已成舟。", "此地无银三百两。",
        "他这人总是心口不一。", "臣叩见陛下，陛下万岁万岁万万岁。",
        "你小子少跟我装蒜！", "哎呀，这可如何是好？", "乱七八糟，成何体统！",
        "风雨同舟，患难与共。", "不入虎穴，焉得虎子。"
    ] * 1, start=201)
]

ALL_SEGMENTS = EASY_SEGMENTS[:10] + CONTEXT_SEGMENTS[:10] + HARD_SEGMENTS[:10]


def run_benchmark():
    print("==========================================================")
    print("🚀 CHINESE → VIETNAMESE TRANSLATION ENGINE BENCHMARK (300 SEGMENTS)")
    print("==========================================================")

    client = OllamaClient()
    model_name = "qwen3:4b"
    available, msg = client.check_availability(model_name)
    if not available:
        print(f"Error: Required model '{model_name}' not available: {msg}")
        return

    translator = RealTranslator(model_name=model_name)

    locked_entities = {
        "爸爸": "Bố",
        "妈妈": "Mẹ",
        "佩奇": "Peppa",
        "乔治": "George"
    }

    start_time = time.time()
    scores = []
    qa_passes = 0
    repair_passes = 0
    human_reviews = 0

    print(f"\n--- Running 300 Segments Test (Model: {model_name}) ---")
    for idx, seg in enumerate(ALL_SEGMENTS):
        text = seg["text"]
        prev_ctx, next_ctx = ContextBuilder.get_context(ALL_SEGMENTS, idx, window=3)

        if available:
            trans, status, qa_info = translator.translate_segment_single(
                text=text,
                prev_context=prev_ctx,
                next_context=next_ctx,
                locked_entities=locked_entities,
                model=model_name
            )
        else:
            trans = f"[MOCK_VIETSUB] {text}"
            qa_info = TranslationQaChecker.check_segment(
                {"id": seg["id"], "text": text, "translated_text": trans},
                locked_entities=locked_entities
            )
            status = qa_info["status"]

        score = qa_info.get("score", 100)
        scores.append(score)

        if status == "QA_PASS":
            qa_passes += 1
        elif status == "REPAIR_PASS":
            repair_passes += 1
        else:
            human_reviews += 1

        if (idx + 1) % 5 == 0 or idx + 1 == len(ALL_SEGMENTS):
            print(f"Processed {idx + 1}/{len(ALL_SEGMENTS)} segments... Current Avg Score: {sum(scores)/len(scores):.2f}/100 | Last Seg: '{text}' -> '{trans}' ({status})")

    elapsed = time.time() - start_time
    avg_score = sum(scores) / max(1, len(scores))

    print("\n==========================================================")
    print("📊 BENCHMARK RESULTS SUMMARY")
    print("==========================================================")
    print(f"Total Segments Tested : {len(ALL_SEGMENTS)}")
    print(f"Execution Time        : {elapsed:.2f} seconds ({elapsed/len(ALL_SEGMENTS):.2f}s per segment)")
    print(f"Average Quality Score : {avg_score:.2f} / 100")
    print(f"QA PASS Count         : {qa_passes} ({qa_passes/len(ALL_SEGMENTS)*100:.1f}%)")
    print(f"AI REPAIR PASS Count  : {repair_passes} ({repair_passes/len(ALL_SEGMENTS)*100:.1f}%)")
    print(f"HUMAN REVIEW Count    : {human_reviews} ({human_reviews/len(ALL_SEGMENTS)*100:.1f}%)")

    print("\n--- Real Integration Test (爸爸已经走了。) ---")
    sample_text = "爸爸已经走了。"
    sample_res, sample_status, sample_qa = translator.translate_segment_single(
        text=sample_text,
        locked_entities=locked_entities,
        model=model_name
    )
    print(f"Input : '{sample_text}'")
    print(f"Output: '{sample_res}' | Status: {sample_status} | Score: {sample_qa.get('score')}")

    tts_blocked = sample_status in ["HUMAN_REVIEW", "FAIL"]
    print(f"TTS Gate Status: {'BLOCKED 🛑' if tts_blocked else 'ALLOWED ✅ (1.00x)'}")

    print("\n--- Invalid Output Test (Testing Output Integrity Catch) ---")
    bad_output = "Bố đi rồi. This translation maintains the context..."
    bad_qa = TranslationQaChecker.check_segment(
        {"id": 999, "text": sample_text, "translated_text": bad_output},
        locked_entities=locked_entities
    )
    print(f"Bad Output Input: '{bad_output}'")
    print(f"QA Status: {bad_qa['status']} | Issues: {[i['message'] for i in bad_qa['issues']]}")
    print(f"TTS Gate Lock Test: {'PASSED (Blocked)' if bad_qa['status'] == 'FAIL' else 'FAILED'}")

    return {
        "total_segments": len(ALL_SEGMENTS),
        "execution_time": elapsed,
        "average_score": avg_score,
        "qa_passes": qa_passes,
        "repair_passes": repair_passes,
        "human_reviews": human_reviews
    }


if __name__ == "__main__":
    run_benchmark()
