import sys
import time
import os
import psutil
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir / "engine"))

from autodub.pipeline.manager import PipelineManager
from autodub.pipeline.state import PipelineStage
from autodub.utils.ffmpeg import FFmpegRunner

def run_benchmark():
    video_path = root_dir / "test_30min.mp4"
    if not video_path.exists():
        video_path = root_dir / "test_4min.mp4"

    print("=== PHASE 4 FASTER-WHISPER STT BENCHMARK ===")
    print(f"Target Video: {video_path.name}")

    project_name = "benchmark_p4"
    mgr = PipelineManager(project_name)

    # 1. Setup Source Video & Extract Audio
    src_dest = mgr.project_dir / "source" / "input.mp4"
    src_dest.parent.mkdir(parents=True, exist_ok=True)
    if not src_dest.exists():
        import shutil
        shutil.copy(video_path, src_dest)

    print("Executing Audio Extraction...")
    mgr.run_stage(PipelineStage.EXTRACT, force=True)

    audio_path = mgr.project_dir / "audio" / "original.wav"
    audio_meta = FFmpegRunner().validate_wav(audio_path)
    input_duration = audio_meta["duration"]
    print(f"Input Audio Duration: {input_duration:.2f}s ({input_duration/60:.2f} minutes)")

    # 2. Resource monitoring start
    process = psutil.Process(os.getpid())
    start_ram = process.memory_info().rss / (1024 * 1024)
    start_time = time.time()

    print("\nExecuting faster-whisper STT (model=small, compute_type=int8, device=auto)...")
    mgr.run_stage(PipelineStage.TRANSCRIBE, force=True)

    elapsed_time = time.time() - start_time
    end_ram = process.memory_info().rss / (1024 * 1024)
    cpu_percent = psutil.cpu_percent(interval=0.5)
    rtf = elapsed_time / input_duration if input_duration > 0 else 0.0

    # 3. Read metadata & segments
    trans_meta = mgr.project.data.get("metadata", {}).get("transcription", {})
    segments = mgr.project.data.get("segments", [])

    print("\n==========================================")
    print("         PHASE 4 BENCHMARK RESULTS         ")
    print("==========================================")
    print(f"Model:                {trans_meta.get('model', 'small')}")
    print(f"Device:               {trans_meta.get('device', 'auto')}")
    print(f"Compute Type:         {trans_meta.get('compute_type', 'int8')}")
    print(f"Detected Language:    {trans_meta.get('language', 'unknown')} (Prob: {trans_meta.get('language_probability', 0.0)})")
    print(f"Segments Count:       {len(segments)}")
    print(f"Input Duration:       {input_duration:.2f}s")
    print(f"Processing Time:      {elapsed_time:.2f}s")
    print(f"Real-Time Factor (RTF): {rtf:.4f}")
    print(f"RAM Usage:            {end_ram:.2f} MB")
    print(f"CPU Usage:            {cpu_percent}%")

    print("\n--- SAMPLE SUBTITLES (FIRST 10 SEGMENTS) ---")
    for seg in segments[:10]:
        text_safe = seg['text'].encode('ascii', errors='replace').decode('ascii')
        print(f"[{seg['id']}] {seg['start']:.2f}s -> {seg['end']:.2f}s: {text_safe}")

if __name__ == "__main__":
    run_benchmark()
