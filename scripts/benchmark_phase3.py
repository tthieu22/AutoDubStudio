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
    root_dir = Path(__file__).resolve().parent.parent
    video_path = root_dir / "test_30min.mp4"
    if not video_path.exists():
        video_path = root_dir / "test_4min.mp4"

    print(f"--- Phase 3 Real Benchmark ---")
    print(f"Target Video: {video_path.name}")

    runner = FFmpegRunner()
    input_meta = runner.probe(video_path)
    input_duration = input_meta["duration"]
    print(f"Input Duration: {input_duration:.2f}s ({input_duration/60:.2f} minutes)")

    project_name = "benchmark_p3"
    mgr = PipelineManager(project_name)
    
    # Copy video to project source
    src_dest = mgr.project_dir / "source" / "input.mp4"
    src_dest.parent.mkdir(parents=True, exist_ok=True)
    if not src_dest.exists():
        import shutil
        shutil.copy(video_path, src_dest)

    # Process resource tracking
    process = psutil.Process(os.getpid())
    start_ram = process.memory_info().rss / (1024 * 1024)
    start_time = time.time()

    mgr.run_stage(PipelineStage.EXTRACT, force=True)

    elapsed_time = time.time() - start_time
    end_ram = process.memory_info().rss / (1024 * 1024)
    cpu_percent = psutil.cpu_percent(interval=0.5)

    output_wav = mgr.project_dir / "audio" / "original.wav"
    output_meta = runner.validate_wav(output_wav)
    output_duration = output_meta["duration"]

    rtf = elapsed_time / input_duration if input_duration > 0 else 0.0

    print("\n=== BENCHMARK RESULTS ===")
    print(f"Input Duration: {input_duration:.2f}s")
    print(f"Output Duration: {output_duration:.2f}s (Diff: {abs(input_duration - output_duration):.4f}s)")
    print(f"Processing Time: {elapsed_time:.2f}s")
    print(f"Real-Time Factor (RTF): {rtf:.4f}")
    print(f"RAM Usage: {end_ram:.2f} MB")
    print(f"CPU Usage: {cpu_percent}%")
    print(f"Codec: {output_meta['audio_codec']} | Sample Rate: {output_meta['audio_sample_rate']} | Channels: {output_meta['audio_channels']}")

if __name__ == "__main__":
    run_benchmark()
