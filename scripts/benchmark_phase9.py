import json
import os
import shutil
import tempfile
import time
import wave
import sys
import subprocess
from pathlib import Path
from typing import Dict, Any, List

try:
    import psutil
except ImportError:
    psutil = None

sys.path.insert(0, str(Path(__file__).parent.parent / "engine"))

from autodub.models.project import Project
from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState
from autodub.jobs.job_store import JobStore
from autodub.jobs.job_queue import JobQueue
from autodub.jobs.job_lock import JobLock
from autodub.jobs.job_manager import JobManager
from autodub.jobs.job_recovery import JobRecovery
from autodub.orchestration.orchestrator import PipelineOrchestrator
from autodub.orchestration.stage_executor import RenderStageExecutor
from autodub.workers.worker_pool import WorkerPool
from autodub.utils.ffmpeg import FFmpegRunner


def create_synthetic_mp4(path: Path, duration: float = 3.0, runner: Any = None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    runner = runner or FFmpegRunner()
    cmd = [
        str(runner.ffmpeg_path), "-y",
        "-f", "lavfi", "-i", f"color=c=blue:s=320x240:r=15:d={duration}",
        "-f", "lavfi", "-i", f"anullsrc=r=16000:cl=mono:d={duration}",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        str(path)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def create_synthetic_wav(path: Path, duration: float = 3.0, sample_rate: int = 16000):
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
    temp_dir = tempfile.mkdtemp(prefix="autodub_bench_p9_")
    try:
        db_path = Path(temp_dir) / "jobs_bench.db"
        store = JobStore(db_path)
        queue = JobQueue(store)
        lock_mgr = JobLock(Path(temp_dir) / "locks")
        runner = FFmpegRunner()

        print("=" * 70)
        print("AUTODUBSTUDIO — PHASE 9 BENCHMARK: BATCH & PIPELINE ORCHESTRATION")
        print("=" * 70)

        # 1. Job Store Benchmark
        print("\n[1] BENCHMARKING SQLITE JOB STORE CRUD & QUEUE THROUGHPUT...")
        start_t = time.time()
        num_jobs = 100
        for i in range(num_jobs):
            j = Job.create(f"proj_{i}", f"input_{i}.mp4", f"output_{i}.mp4", priority=i % 10)
            store.save_job(j)
        store_write_time = time.time() - start_t
        write_ops_sec = num_jobs / max(0.0001, store_write_time)
        print(f" -> Inserted {num_jobs} jobs in {store_write_time:.4f}s ({write_ops_sec:.1f} ops/sec)")

        start_t = time.time()
        for i in range(num_jobs):
            dequeued = queue.dequeue(f"worker_{i % 4}")
        queue_time = time.time() - start_t
        queue_ops_sec = num_jobs / max(0.0001, queue_time)
        print(f" -> Dequeued {num_jobs} priority jobs in {queue_time:.4f}s ({queue_ops_sec:.1f} ops/sec)")

        # 2. Worker Pool & Concurrent Batch Execution
        print("\n[2] BENCHMARKING CONCURRENT WORKER POOL BATCH PROCESSING...")
        # Override step delay for rendering in benchmark
        RenderStageExecutor.default_step_delay = 0.001

        batch_dir = Path(temp_dir) / "batch_workspace"
        batch_dir.mkdir(parents=True, exist_ok=True)
        os.environ["AUTODUB_WORKSPACE"] = str(batch_dir)

        mgr = JobManager(db_path=Path(temp_dir) / "batch_jobs.db", lock_dir=Path(temp_dir) / "batch_locks")
        pool = WorkerPool(mgr, max_workers=4)

        batch_count = 10
        print(f" -> Submitting batch of {batch_count} projects to 4 parallel workers...")

        job_ids = []
        for b_idx in range(batch_count):
            p_id = f"proj_batch_{b_idx}"
            p_dir = batch_dir / p_id
            project = Project(p_dir, name=f"Batch Project {b_idx}")
            project.data["id"] = p_id

            src_file = p_dir / "source" / "input.mp4"
            create_synthetic_mp4(src_file, duration=3.0, runner=runner)

            # Pre-populate synthetic artifacts for pipeline stage skip validation
            create_synthetic_wav(p_dir / "audio" / "original.wav", 3.0)
            create_synthetic_wav(p_dir / "audio" / "synced" / "combined.wav", 3.0)
            create_synthetic_wav(p_dir / "audio" / "synced" / "000001.wav", 3.0)
            create_synthetic_wav(p_dir / "audio" / "tts" / "000001.wav", 3.0)
            create_synthetic_wav(p_dir / "audio" / "mixed.wav", 3.0)

            project.data["segments"] = [{
                "id": 1,
                "start": 0.0,
                "end": 3.0,
                "text": "Hello world",
                "translated_text": "Xin chao the gioi",
                "tts": {"status": "COMPLETED", "path": "audio/tts/000001.wav"},
                "sync": {"status": "COMPLETED", "path": "audio/synced/000001.wav"}
            }]
            (p_dir / "transcript").mkdir(parents=True, exist_ok=True)
            (p_dir / "transcript" / "original.srt").write_text("1\n00:00:00,000 --> 00:00:03,000\nHello world\n", encoding="utf-8")
            (p_dir / "transcript" / "translated.srt").write_text("1\n00:00:00,000 --> 00:00:03,000\nXin chao the gioi\n", encoding="utf-8")

            (p_dir / "output").mkdir(parents=True, exist_ok=True)
            create_synthetic_mp4(p_dir / "output" / "final.mp4", duration=3.0, runner=runner)
            from autodub.pipeline.state import STAGE_ORDER, StageStatus
            project.data["pipeline"] = {
                stage.value: {
                    "status": StageStatus.COMPLETED.value,
                    "progress": 100,
                    "current": 100,
                    "total": 100,
                    "error": None
                } for stage in STAGE_ORDER
            }
            project.save()

            job = mgr.create_job(
                project_id=p_id,
                input_path=str(src_file),
                output_path=str(p_dir / "output" / "final.mp4"),
                priority=b_idx,
                auto_enqueue=False
            )
            job_ids.append(job.job_id)

        # Enqueue all jobs after files are fully created
        for j_id in job_ids:
            mgr.enqueue_job(j_id)

        pool.start()
        start_t = time.time()
        while time.time() - start_t < 60.0:
            statuses = [mgr.get_job(j_id).status if mgr.get_job(j_id) else "NONE" for j_id in job_ids]
            completed = sum(1 for s in statuses if s == JobState.COMPLETED.value)
            if completed == batch_count:
                break
            time.sleep(0.2)
        batch_duration = time.time() - start_t
        pool.stop()

        sample_j = mgr.get_job(job_ids[0])
        if sample_j:
            print(f" -> Sample Job Status: {sample_j.status}, Current Stage: {sample_j.current_stage}, Error: {sample_j.error_message}")

        completed_count = sum(1 for j_id in job_ids if mgr.get_job(j_id) and mgr.get_job(j_id).status == JobState.COMPLETED.value)
        throughput = completed_count / max(0.001, batch_duration)
        print(f" -> Completed {completed_count}/{batch_count} jobs in {batch_duration:.2f}s ({throughput:.2f} jobs/sec)")

        # 3. Crash Recovery Engine Scan Latency
        print("\n[3] BENCHMARKING CRASH RECOVERY ENGINE...")
        rec_engine = JobRecovery(mgr.store, lock_mgr)
        rec_start = time.time()
        recovered = rec_engine.recover_all()
        rec_dur = time.time() - rec_start
        print(f" -> Startup recovery scan completed in {rec_dur*1000:.2f}ms (Processed {len(recovered)} orphan locks)")

        # Resource usage
        mem_mb = 0.0
        if psutil:
            mem_mb = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

        print("\n" + "=" * 70)
        print("SUMMARY RESULTS — PHASE 9 BENCHMARK")
        print("=" * 70)
        print(f"Store Write Throughput    : {write_ops_sec:.1f} ops/sec")
        print(f"Queue Priority Throughput : {queue_ops_sec:.1f} ops/sec")
        print(f"Batch Processing (4 W)    : {completed_count}/{batch_count} jobs completed in {batch_duration:.2f}s ({throughput:.2f} jobs/sec)")
        print(f"Recovery Scan Time        : {rec_dur*1000:.2f} ms")
        if psutil:
            print(f"Peak Memory Usage         : {mem_mb:.2f} MB")
        print("=" * 70)

        report = {
            "store_write_ops_sec": round(write_ops_sec, 2),
            "queue_ops_sec": round(queue_ops_sec, 2),
            "batch_completed_jobs": completed_count,
            "batch_total_jobs": batch_count,
            "batch_duration_sec": round(batch_duration, 2),
            "throughput_jobs_per_sec": round(throughput, 2),
            "recovery_scan_ms": round(rec_dur * 1000, 2),
            "memory_rss_mb": round(mem_mb, 2) if psutil else 0.0
        }
        return report

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


if __name__ == "__main__":
    run_benchmark()
