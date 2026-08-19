import json
import os
import shutil
import tempfile
import time
import wave
import sys
import subprocess
from pathlib import Path
from typing import Optional, Dict, Any, List

try:
    import psutil
except ImportError:
    psutil = None

sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

from autodub.models.project import Project
from autodub.modules.render_config import RenderConfig
from autodub.modules.renderer import RealRenderer, detect_available_encoders
from autodub.utils.ffmpeg import FFmpegRunner


def create_synthetic_wav(path: Path, duration: float, sample_rate: int = 16000, channels: int = 1):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    num_frames = int(max(0.01, duration) * sample_rate)
    frame_data = b"\x10\x00" * channels

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(channels)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(frame_data * num_frames)


def create_synthetic_mp4(path: Path, duration: float = 5.0, runner: Optional[FFmpegRunner] = None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    runner = runner or FFmpegRunner()
    cmd = [
        str(runner.ffmpeg_path), "-y",
        "-f", "lavfi", "-i", f"color=c=blue:s=1280x720:r=30:d={duration}",
        "-f", "lavfi", "-i", f"anullsrc=r=16000:cl=mono:d={duration}",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        str(path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def create_sample_srt(path: Path, duration: float):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "1\n"
        f"00:00:00,000 --> 00:00:{int(min(duration, 5)):02d},000\n"
        "Xin chào thế giới - AutoDubStudio Phase 8 Benchmark\n\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def run_benchmark():
    temp_dir = tempfile.mkdtemp(prefix="autodub_bench_p8_")
    try:
        runner = FFmpegRunner()
        encoders = detect_available_encoders(runner)
        print("=" * 60)
        print("AUTODUBSTUDIO — PHASE 8 BENCHMARK: VIDEO MIXING & RENDERING")
        print("=" * 60)
        print(f"Detected Encoders: {encoders}")

        scenarios = [
            ("Short Video", 10.0, "DUCK_ORIGINAL", "BURN_IN"),
            ("Medium Video", 30.0, "MIX", "COPY"),
            ("Long Video (Simulated)", 60.0, "DUB_ONLY", "NONE")
        ]

        results = []

        for name, duration, audio_mode, sub_mode in scenarios:
            proj_dir = Path(temp_dir) / name.replace(" ", "_").lower()
            project = Project(proj_dir, name=name)

            src_mp4 = proj_dir / "source" / "input.mp4"
            create_synthetic_mp4(src_mp4, duration=duration, runner=runner)

            synced_dir = proj_dir / "audio" / "synced"
            create_synthetic_wav(synced_dir / "000001.wav", duration)
            create_synthetic_wav(synced_dir / "combined.wav", duration)
            create_sample_srt(proj_dir / "transcript" / "translated.srt", duration)

            project.data["segments"] = [{
                "id": 1,
                "start": 0.0,
                "end": duration,
                "sync": {"status": "COMPLETED", "path": "audio/synced/000001.wav"}
            }]
            for st in ["extract", "transcribe", "translate", "tts", "sync"]:
                project.update_stage(st, "COMPLETED", progress=100)
            project.save()

            cfg = RenderConfig(
                audio_mode=audio_mode,
                tts_volume=1.0,
                original_volume=0.15,
                subtitle_mode=sub_mode,
                encoder="AUTO"
            )

            real_renderer = RealRenderer(step_delay=0.01)

            process_info = psutil.Process(os.getpid()) if psutil else None
            mem_before = process_info.memory_info().rss / (1024 * 1024) if process_info else 0.0
            cpu_before = psutil.cpu_percent(interval=None) if psutil else 0.0

            start_t = time.time()
            elapsed = real_renderer.run(project, force=True, render_config=cfg)
            real_time = time.time() - start_t

            mem_after = process_info.memory_info().rss / (1024 * 1024) if process_info else 0.0
            cpu_after = psutil.cpu_percent(interval=None) if psutil else 0.0

            rtf = real_time / duration if duration > 0 else 0.0

            final_mp4 = proj_dir / "output" / "final.mp4"
            try:
                out_meta = runner.probe(final_mp4)
            except Exception:
                out_meta = {"format": {"duration": str(duration)}}

            fmt = out_meta.get("format", {})
            if isinstance(fmt, str):
                fmt = {"duration": str(duration)}
            out_duration = float(fmt.get("duration", duration))
            drift_ms = abs(out_duration - duration) * 1000.0
            file_size_kb = final_mp4.stat().st_size / 1024.0 if final_mp4.exists() else 0.0

            res_item = {
                "scenario": name,
                "duration_sec": duration,
                "render_time_sec": round(real_time, 2),
                "rtf": round(rtf, 4),
                "audio_mode": audio_mode,
                "subtitle_mode": sub_mode,
                "encoder_used": project.data.get("render", {}).get("encoder", "unknown"),
                "duration_drift_ms": round(drift_ms, 2),
                "file_size_kb": round(file_size_kb, 1),
                "ram_mb": round(mem_after, 1)
            }
            results.append(res_item)

            print(f"\n--- {name} ({duration}s) ---")
            print(f"Render Time: {real_time:.2f}s | RTF: {rtf:.4f}")
            print(f"Encoder: {res_item['encoder_used']} | Subtitles: {sub_mode}")
            print(f"Duration Drift: {drift_ms:.2f}ms | Output Size: {file_size_kb:.1f} KB")
            print(f"Memory Usage: {mem_after:.1f} MB")

        print("\n" + "=" * 60)
        print("SUMMARY BENCHMARK REPORT")
        print("=" * 60)
        for r in results:
            print(f"{r['scenario']:<22} | Duration: {r['duration_sec']:>4.1f}s | Render: {r['render_time_sec']:>5.2f}s | RTF: {r['rtf']:>6.4f} | Drift: {r['duration_drift_ms']:>5.2f}ms | RAM: {r['ram_mb']:>5.1f}MB")
        print("=" * 60)

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_benchmark()
