import sys
import time
import os
import psutil
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "engine"))

from autodub.pipeline.manager import PipelineManager  # type: ignore
from autodub.pipeline.state import PipelineStage  # type: ignore
from autodub.modules.tts import RealTTS, PiperClient  # type: ignore

def run_benchmark():
    print("=== PHASE 6 LOCAL TEXT-TO-SPEECH (PIPER TTS) BENCHMARK ===")

    project_name = "benchmark_p6"
    mgr = PipelineManager(project_name)

    # 1. Prepare video & preceding stages (Extract, Transcribe, Translate)
    video_path = root_dir / "test_30min.mp4"
    if not video_path.exists():
        video_path = root_dir / "test_4min.mp4"

    src_dest = mgr.project_dir / "source" / "input.mp4"
    src_dest.parent.mkdir(parents=True, exist_ok=True)
    if not src_dest.exists():
        import shutil
        shutil.copy(video_path, src_dest)

    print("Running pipeline up to Translate stage if needed...")
    if mgr.project.get_stage_info("extract").get("status") != "completed":
        mgr.run_stage(PipelineStage.EXTRACT)
    if mgr.project.get_stage_info("transcribe").get("status") != "completed":
        mgr.run_stage(PipelineStage.TRANSCRIBE)
    if mgr.project.get_stage_info("translate").get("status") != "completed":
        from autodub.modules.translator import RealTranslator, OllamaClient
        from tests.test_translator_phase5 import MockOllamaClient
        client_ollama = OllamaClient()
        avail, _ = client_ollama.check_availability("qwen3:4b")
        if avail:
            translator = RealTranslator(model_name="qwen3:4b", client=client_ollama)
        else:
            translator = RealTranslator(model_name="qwen3:4b", client=MockOllamaClient())
        translator.run(mgr.project)

    segments = mgr.project.data.get("segments", [])
    total_segments = len(segments)
    total_chars = sum(len(s.get("translation", s.get("text", ""))) for s in segments)
    print(f"Total Segments to Synthesize: {total_segments}")
    print(f"Total Vietnamese Characters:   {total_chars}")

    # 2. Check Piper Availability
    client_piper = PiperClient()
    voice_name = "vi_VN-viss-low"
    available, err_msg, sample_rate = client_piper.check_availability(voice_name)

    if not available:
        print(f"\n[NOTICE] Local Piper TTS status: {err_msg}")
        print("Switching to MockPiperClient benchmark demonstration mode...")
        from tests.test_tts_phase6 import MockPiperClient
        tts = RealTTS(client=MockPiperClient())
    else:
        print(f"\n[SUCCESS] Connected to Piper TTS binary at {client_piper.executable_path}")
        tts = RealTTS(client=client_piper)

    # 3. Resource Monitoring & Run
    process = psutil.Process(os.getpid())
    start_ram = process.memory_info().rss / (1024 * 1024)
    start_time = time.time()

    print("\nExecuting Piper TTS stage...")
    tts.run(mgr.project, force=True, voice_name=voice_name)

    elapsed_time = time.time() - start_time
    end_ram = process.memory_info().rss / (1024 * 1024)
    cpu_percent = psutil.cpu_percent(interval=0.5)

    tts_data = mgr.project.data.get("tts", {})
    gen_audio_duration = tts_data.get("total_audio_duration", 0.0)
    rtf = elapsed_time / gen_audio_duration if gen_audio_duration > 0 else 0.0
    sec_per_segment = elapsed_time / total_segments if total_segments > 0 else 0.0

    print("\n==========================================")
    print("         PHASE 6 BENCHMARK RESULTS         ")
    print("==========================================")
    print(f"Engine:               Piper Local TTS")
    print(f"Voice Model:          {voice_name}")
    print(f"Language:             vi")
    print(f"Segments Count:       {total_segments}")
    print(f"Total Characters:     {total_chars}")
    print(f"Generated Audio:      {gen_audio_duration:.2f} seconds")
    print(f"Processing Time:      {elapsed_time:.2f}s")
    print(f"Real-Time Factor:     {rtf:.4f} (RTF)")
    print(f"Average sec/segment:  {sec_per_segment:.4f}s")
    print(f"RAM Usage:            {end_ram:.2f} MB")
    print(f"CPU Usage:            {cpu_percent}%")

    print("\n--- SAMPLE TTS AUDIO FILES (FIRST 5 SEGMENTS) ---")
    audio_tts_dir = mgr.project_dir / "audio" / "tts"
    for seg in segments[:5]:
        seg_id = seg.get("id", 1)
        wav_file = audio_tts_dir / f"{seg_id:06d}.wav"
        text_safe = seg.get("translation", "").encode("ascii", errors="replace").decode("ascii")
        print(f"[{seg_id:06d}.wav] Exists: {wav_file.exists()} | Duration: {seg.get('tts', {}).get('duration', 0.0)}s | Text: {text_safe}")

if __name__ == "__main__":
    run_benchmark()
