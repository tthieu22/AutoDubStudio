import sys
import os
import time
import shutil
import tempfile
import json
import wave
from pathlib import Path

# Add engine directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

from autodub.models.project import Project
from autodub.modules.synchronizer import RealSynchronizer, probe_audio_duration

def create_synthetic_wav(path: Path, duration: float, sample_rate: int = 16000):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    num_frames = int(max(0.01, duration) * sample_rate)
    frame_data = b"\x10\x00"

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frame_data * num_frames)

def run_benchmark():
    print("=" * 60)
    print("AUTODUBSTUDIO — PHASE 7 REAL AUDIO SYNCHRONIZATION BENCHMARK")
    print("=" * 60)

    temp_dir = tempfile.mkdtemp(prefix="autodub_bm_sync_")
    try:
        project_dir = Path(temp_dir) / "benchmark_proj"
        project = Project(project_dir, name="Benchmark Phase 7")

        # Generate 63 synthetic segments matching Phase 6 benchmark
        segments = []
        tts_dir = project_dir / "audio" / "tts"
        tts_dir.mkdir(parents=True, exist_ok=True)

        current_time = 5.0
        for i in range(1, 64):
            # Target duration varies between 1.5s and 8.0s
            target_dur = 1.5 + (i * 0.1) % 6.5
            start_t = current_time
            end_t = start_t + target_dur
            current_time = end_t + 0.5  # 0.5s gap between segments

            # Generated TTS duration varies (some faster, some slower)
            # Speed ratio between 0.7x and 1.6x
            ratio = 0.7 + ((i * 17) % 90) / 100.0
            tts_dur = round(target_dur * ratio, 2)

            wav_path = tts_dir / f"{i:06d}.wav"
            create_synthetic_wav(wav_path, tts_dur)

            segments.append({
                "id": i,
                "start": round(start_t, 2),
                "end": round(end_t, 2),
                "text": f"Benchmark segment {i} sample text",
                "translated_text": f"Đoạn mã hóa điểm chuẩn {i} văn bản mẫu",
                "tts": {
                    "path": f"audio/tts/{i:06d}.wav",
                    "duration": tts_dur,
                    "status": "COMPLETED"
                }
            })

        project.data["segments"] = segments
        project.save()

        total_target_duration = sum(s["end"] - s["start"] for s in segments)
        print(f"\nBenchmark dataset:")
        print(f"- Total segments: {len(segments)}")
        print(f"- Total audio speech duration: {total_target_duration:.2f}s")
        print(f"- Total timeline duration: {current_time:.2f}s")
        print("-" * 60)

        # Run RealSynchronizer
        synchronizer = RealSynchronizer(step_delay=0.0)
        t0 = time.time()
        proc_time = synchronizer.run(project, force=True)
        t1 = time.time()

        wall_time = t1 - t0
        rtf = wall_time / total_target_duration if total_target_duration > 0 else 0.0

        sync_meta = project.data.get("sync", {})
        combined_wav = project_dir / "audio" / "synced" / "combined.wav"
        combined_dur = probe_audio_duration(combined_wav)

        print("\n" + "=" * 60)
        print("BENCHMARK RESULTS SUMMARY")
        print("=" * 60)
        print(f"Total Segments Processed   : {sync_meta.get('total_segments', 0)}")
        print(f"Completed Segments          : {sync_meta.get('total_segments', 0) - sync_meta.get('skipped_segments', 0)}")
        print(f"Skipped Segments            : {sync_meta.get('skipped_segments', 0)}")
        print(f"Clamped Speed Segments      : {sync_meta.get('clamped_segments', 0)}")
        print(f"Total Target Audio Duration : {sync_meta.get('total_audio_duration', 0.0):.2f}s")
        print(f"Combined Output Audio Dur  : {combined_dur:.2f}s")
        print(f"Wall Clock Execution Time   : {wall_time:.4f}s")
        print(f"Engine Processing Time      : {proc_time:.4f}s")
        print(f"Real-Time Factor (RTF)      : {rtf:.4f}")
        print(f"Maximum Duration Error      : {sync_meta.get('max_duration_error', 0.0):.4f}s")
        print(f"Average Duration Error      : {sync_meta.get('average_duration_error', 0.0):.4f}s")
        print(f"Combined Wav File Exists    : {combined_wav.exists()} ({combined_wav.stat().st_size / 1024:.1f} KB)")
        print("=" * 60)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    run_benchmark()
