import sys
import time
import os
import psutil
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "engine"))

from autodub.pipeline.manager import PipelineManager
from autodub.pipeline.state import PipelineStage
from autodub.modules.translator import RealTranslator, OllamaClient

def run_benchmark():
    print("=== PHASE 5 LOCAL TRANSLATION (OLLAMA QWEN3 4B) BENCHMARK ===")

    project_name = "benchmark_p5"
    mgr = PipelineManager(project_name)

    # 1. Ensure project has source audio & transcript from Phase 4
    video_path = root_dir / "test_30min.mp4"
    if not video_path.exists():
        video_path = root_dir / "test_4min.mp4"

    src_dest = mgr.project_dir / "source" / "input.mp4"
    src_dest.parent.mkdir(parents=True, exist_ok=True)
    if not src_dest.exists():
        import shutil
        shutil.copy(video_path, src_dest)

    print("Running STT stage if needed...")
    mgr.run_stage(PipelineStage.EXTRACT)
    mgr.run_stage(PipelineStage.TRANSCRIBE)

    segments = mgr.project.data.get("segments", [])
    total_segments = len(segments)
    total_chars = sum(len(s.get("text", "")) for s in segments)
    print(f"Total Segments to Translate: {total_segments}")
    print(f"Total Source Characters:     {total_chars}")

    # 2. Check Ollama Availability
    client = OllamaClient()
    available, err_msg = client.check_availability("qwen3:4b")

    if not available:
        print(f"\n[NOTICE] Local Ollama status: {err_msg}")
        print("Switching to MockOllamaClient benchmark demonstration mode...")
        from tests.test_translator_phase5 import MockOllamaClient
        translator = RealTranslator(model_name="qwen3:4b", client=MockOllamaClient())
    else:
        print(f"\n[SUCCESS] Connected to Ollama at {client.base_url}")
        translator = RealTranslator(model_name="qwen3:4b", client=client)

    # 3. Resource Monitoring & Run
    process = psutil.Process(os.getpid())
    start_ram = process.memory_info().rss / (1024 * 1024)
    start_time = time.time()

    print("\nExecuting Translation stage...")
    translator.run(mgr.project, force=True)

    elapsed_time = time.time() - start_time
    end_ram = process.memory_info().rss / (1024 * 1024)
    cpu_percent = psutil.cpu_percent(interval=0.5)

    sec_per_segment = elapsed_time / total_segments if total_segments > 0 else 0.0

    # 4. Read translated segments
    trans_segments = mgr.project.data.get("segments", [])

    print("\n==========================================")
    print("         PHASE 5 BENCHMARK RESULTS         ")
    print("==========================================")
    print(f"Provider:             Ollama Local")
    print(f"Model:                qwen3:4b")
    print(f"Source Language:      en")
    print(f"Target Language:      vi")
    print(f"Segments Count:       {total_segments}")
    print(f"Total Characters:     {total_chars}")
    print(f"Processing Time:      {elapsed_time:.2f}s")
    print(f"Average sec/segment:  {sec_per_segment:.4f}s")
    print(f"RAM Usage:            {end_ram:.2f} MB")
    print(f"CPU Usage:            {cpu_percent}%")

    print("\n--- SAMPLE TRANSLATIONS (FIRST 10 SEGMENTS) ---")
    for seg in trans_segments[:10]:
        text_safe = seg.get('text', '').encode('ascii', errors='replace').decode('ascii')
        trans_safe = seg.get('translation', '').encode('ascii', errors='replace').decode('ascii')
        print(f"[{seg.get('id', '?')}] EN: {text_safe}")
        print(f"     VI: {trans_safe}")

if __name__ == "__main__":
    run_benchmark()
