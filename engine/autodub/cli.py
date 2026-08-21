import argparse
import json
import os
import sys
from pathlib import Path
from typing import List

# Add NVIDIA CUDA DLL paths from pip-installed packages to OS PATH
# This is required for ctranslate2/faster-whisper to find cublas64_12.dll, cudnn, etc.
_venv_site = Path(sys.prefix) / "Lib" / "site-packages" / "nvidia"
if _venv_site.exists():
    for _dll_dir in _venv_site.rglob("bin"):
        if _dll_dir.is_dir():
            os.add_dll_directory(str(_dll_dir))
            os.environ["PATH"] = str(_dll_dir) + os.pathsep + os.environ.get("PATH", "")

from autodub.pipeline.manager import PipelineManager
from autodub.pipeline.state import PipelineStage
from autodub.jobs.job_manager import JobManager
from autodub.workers.worker_pool import WorkerPool
from autodub.exceptions import AutoDubError, PipelineCancelledError


def main():
    parser = argparse.ArgumentParser(description="AutoDubStudio Production Engine CLI (Phase 9)")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create <name> [--source <path>]
    create_sp = subparsers.add_parser("create", help="Create a new project")
    create_sp.add_argument("name", help="Project name")
    create_sp.add_argument("--source", default="source/input.mp4", help="Relative or absolute path to source video")

    # status <project_or_job_id> [--json]
    status_sp = subparsers.add_parser("status", help="Get status of project or job")
    status_sp.add_argument("target", help="Project name/path or Job ID")
    status_sp.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # list [--status <status>] [--limit <limit>] [--json]
    list_sp = subparsers.add_parser("list", help="List jobs in database")
    list_sp.add_argument("--status", default=None, help="Filter by job status")
    list_sp.add_argument("--limit", type=int, default=100, help="Maximum jobs to list")
    list_sp.add_argument("--json", action="store_true", help="Output machine-readable JSON")

    # batch <input_paths...> [--output <dir>] [--workers <n>] [--priority <p>] [--force] [--json]
    batch_sp = subparsers.add_parser("batch", help="Batch process multiple video files")
    batch_sp.add_argument("inputs", nargs="+", help="Input video file(s) or directory")
    batch_sp.add_argument("--output", default="output", help="Output directory path")
    batch_sp.add_argument("--workers", type=int, default=2, help="Number of concurrent worker threads")
    batch_sp.add_argument("--priority", type=int, default=5, help="Job priority (higher runs first)")
    batch_sp.add_argument("--force", action="store_true", help="Force re-processing duplicate jobs")
    batch_sp.add_argument("--json", action="store_true", help="Output machine-readable JSON results")

    # run <project_or_job> [--force]
    run_sp = subparsers.add_parser("run", help="Run full pipeline for a project or job")
    run_sp.add_argument("target", help="Project name/path or Job ID")
    run_sp.add_argument("--force", action="store_true", help="Force re-running completed stages")

    # resume <target>
    resume_sp = subparsers.add_parser("resume", help="Resume pipeline/job from checkpoint")
    resume_sp.add_argument("target", help="Project name/path or Job ID")

    # pause <job_id>
    pause_sp = subparsers.add_parser("pause", help="Pause a running job")
    pause_sp.add_argument("job_id", help="Job ID to pause")

    # retry <target> [<stage>] [--force]
    retry_sp = subparsers.add_parser("retry", help="Retry a job or stage")
    retry_sp.add_argument("target", help="Project name/path or Job ID")
    retry_sp.add_argument("stage", nargs="?", choices=[s.value for s in PipelineStage], help="Stage to retry")
    retry_sp.add_argument("--force", action="store_true", help="Force re-running a COMPLETED stage")

    # cancel <target>
    cancel_sp = subparsers.add_parser("cancel", help="Cancel running pipeline or job")
    cancel_sp.add_argument("target", help="Project name/path or Job ID")

    # recover
    subparsers.add_parser("recover", help="Recover interrupted jobs from crash/restart")

    # clean [--status <status>]
    clean_sp = subparsers.add_parser("clean", help="Clean completed or failed jobs from database")
    clean_sp.add_argument("--status", default=None, help="Specific job status to clean (default: all)")

    # validate <project>
    val_sp = subparsers.add_parser("validate", help="Validate project integrity and dependencies")
    val_sp.add_argument("project", help="Project name or path")

    # individual stage runners
    for stage_enum in PipelineStage:
        sp = subparsers.add_parser(stage_enum.value, help=f"Execute {stage_enum.value} stage")
        sp.add_argument("project", help="Project name or path")
        sp.add_argument("--force", action="store_true", help="Force re-execution if completed")
        if stage_enum == PipelineStage.TRANSCRIBE:
            sp.add_argument("--model", default="small", choices=["tiny", "base", "small", "medium", "large-v3"], help="Whisper model size")
            sp.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"], help="Device type")
            sp.add_argument("--compute-type", default="int8", choices=["int8", "float16", "float32"], help="Compute type")
            sp.add_argument("--language", default="en", help="Language code or 'auto'")
            sp.add_argument("--chunk-duration", type=int, default=600, help="Chunk duration in seconds")
        elif stage_enum == PipelineStage.TRANSLATE:
            sp.add_argument("--source-language", default="en", help="Source language code")
            sp.add_argument("--target-language", default="vi", help="Target language code")
            sp.add_argument("--model", default="qwen2.5:3b", help="Ollama LLM model name")
        elif stage_enum == PipelineStage.TTS:
            sp.add_argument("--voice", default=None, help="Piper voice model name")
            sp.add_argument("--language", default="vi", help="Target TTS language code")
        elif stage_enum == PipelineStage.SYNC:
            sp.add_argument("--speed-min", type=float, default=0.5, help="Minimum speed factor limit")
            sp.add_argument("--speed-max", type=float, default=2.0, help="Maximum speed factor limit")
            sp.add_argument("--tolerance", type=float, default=0.05, help="Duration tolerance in seconds")
            sp.add_argument("--overlap-policy", default="TRIM", choices=["TRIM", "SHIFT", "ALLOW", "FAIL"], help="Overlap resolution policy")
            sp.add_argument("--extreme-policy", default="CLAMP", choices=["CLAMP", "REJECT", "FALLBACK"], help="Extreme speed policy")
        elif stage_enum == PipelineStage.RENDER:
            sp.add_argument("--audio-mode", default="DUCK_ORIGINAL", choices=["DUB_ONLY", "ORIGINAL_ONLY", "MIX", "DUCK_ORIGINAL"], help="Audio mixing mode")
            sp.add_argument("--tts-volume", type=float, default=1.0, help="TTS audio volume scale")
            sp.add_argument("--original-volume", type=float, default=0.15, help="Original video audio volume scale")
            sp.add_argument("--codec", default="H264", choices=["H264", "H265"], help="Target video codec")
            sp.add_argument("--encoder", default="AUTO", choices=["AUTO", "CPU", "NVENC"], help="Target video encoder")
            sp.add_argument("--quality", default="MEDIUM", choices=["FAST", "MEDIUM", "HIGH"], help="Encoding quality preset")
            sp.add_argument("--subtitle-mode", default="BURN_IN", choices=["NONE", "COPY", "BURN_IN"], help="Subtitle processing mode")

    args = parser.parse_args()

    try:
        job_mgr = JobManager()

        if args.command == "create":
            mgr = PipelineManager(args.name)
            mgr.project.data["source"]["path"] = args.source
            mgr.project.save()
            print(f"Project '{args.name}' created successfully.")
            return

        elif args.command == "list":
            jobs = job_mgr.list_jobs(status=args.status, limit=args.limit)
            if args.json:
                print(json.dumps([j.to_dict() for j in jobs], indent=2))
            else:
                print(f"{'JOB ID':<18} | {'STATUS':<12} | {'STAGE':<12} | {'PROGRESS':<8} | {'INPUT'}")
                print("-" * 75)
                for j in jobs:
                    print(f"{j.job_id:<18} | {j.status:<12} | {j.current_stage:<12} | {j.progress:>6.1f}% | {j.input_path}")
            return

        elif args.command == "batch":
            # Expand directory inputs if any
            input_files: List[Path] = []
            for item in args.inputs:
                p = Path(item)
                if p.is_dir():
                    input_files.extend(list(p.glob("*.mp4")) + list(p.glob("*.mkv")) + list(p.glob("*.avi")))
                elif p.exists():
                    input_files.append(p)

            if not input_files:
                print("No input video files found.")
                return

            created_jobs = []
            out_base = Path(args.output)
            out_base.mkdir(parents=True, exist_ok=True)

            for idx, inp in enumerate(input_files, 1):
                proj_name = f"projects/{inp.stem}"
                out_path = out_base / f"{inp.stem}_dubbed.mp4"
                job = job_mgr.create_job(
                    project_id=proj_name,
                    input_path=str(inp),
                    output_path=str(out_path),
                    priority=args.priority,
                    force_duplicate=args.force,
                )
                created_jobs.append(job)

            pool = WorkerPool(job_manager=job_mgr, max_workers=args.workers)
            pool.start()

            # Wait for all jobs to complete or fail
            while pool.active_worker_count > 0 or job_mgr.queue.get_queue_length() > 0:
                import time
                time.sleep(0.5)

            pool.stop()

            final_jobs = [job_mgr.get_job(j.job_id) for j in created_jobs]
            if args.json:
                print(json.dumps([j.to_dict() for j in final_jobs if j], indent=2))
            else:
                print("\nBatch Processing Completed:")
                for j in final_jobs:
                    if j:
                        print(f"[{j.status}] Job '{j.job_id}' -> Output: '{j.output_path}'")
            return

        elif args.command == "pause":
            job = job_mgr.pause_job(args.job_id)
            print(f"Job '{job.job_id}' paused successfully.")
            return

        elif args.command == "recover":
            recovered = job_mgr.recover_jobs()
            print(f"Recovered {len(recovered)} interrupted jobs.")
            return

        elif args.command == "clean":
            count = job_mgr.clean_jobs(status=args.status)
            print(f"Cleaned {count} jobs from database.")
            return

        # Commands supporting both job_id and project_id target
        target = getattr(args, "target", None)
        job = job_mgr.get_job(target) if target else None

        if args.command == "status":
            if job:
                if args.json:
                    print(json.dumps(job.to_dict(), indent=2))
                else:
                    print(f"Job ID: {job.job_id}")
                    print(f"Status: {job.status}")
                    print(f"Stage: {job.current_stage}")
                    print(f"Progress: {job.progress:.1f}%")
                    print(f"Input: {job.input_path}")
            else:
                mgr = PipelineManager(target)
                if args.json:
                    print(json.dumps(mgr.project.data, indent=2))
                else:
                    print(mgr.get_status_formatted())

        elif args.command == "run":
            if job:
                pool = WorkerPool(job_manager=job_mgr, max_workers=1)
                job_mgr.enqueue_job(job.job_id)
                pool.start()
                while pool.active_worker_count > 0:
                    import time
                    time.sleep(0.2)
                pool.stop()
            else:
                mgr = PipelineManager(target)
                mgr.run_all(force=getattr(args, "force", False))

        elif args.command == "resume":
            if job:
                job_mgr.resume_job(job.job_id)
                print(f"Job '{job.job_id}' resumed.")
            else:
                mgr = PipelineManager(target)
                mgr.resume()

        elif args.command == "cancel":
            if job:
                job_mgr.cancel_job(job.job_id)
                print(f"Job '{job.job_id}' cancelled.")
            else:
                mgr = PipelineManager(target)
                mgr.cancel()
                print(f"Cancellation signal sent to project '{target}'.")

        elif args.command == "retry":
            if job and not getattr(args, "stage", None):
                job_mgr.retry_job(job.job_id)
                print(f"Job '{job.job_id}' scheduled for retry.")
            else:
                mgr = PipelineManager(target)
                st = PipelineStage(args.stage) if getattr(args, "stage", None) else PipelineStage.RENDER
                mgr.retry(st, force=getattr(args, "force", False))

        elif args.command == "validate":
            mgr = PipelineManager(target)
            if mgr.validate():
                print(f"Project '{target}' is VALID.")

        else:
            # Individual stage command
            mgr = PipelineManager(args.project)
            stage_enum = PipelineStage(args.command)
            stage_kwargs = {}
            if stage_enum == PipelineStage.TRANSCRIBE:
                if getattr(args, "model", None): stage_kwargs["model_name"] = args.model
                if getattr(args, "device", None): stage_kwargs["device"] = args.device
                if getattr(args, "compute_type", None): stage_kwargs["compute_type"] = args.compute_type
                if getattr(args, "chunk_duration", None): stage_kwargs["chunk_duration"] = args.chunk_duration
            elif stage_enum == PipelineStage.TRANSLATE:
                if getattr(args, "model", None): stage_kwargs["model_name"] = args.model
                if getattr(args, "source_language", None): stage_kwargs["source_language"] = args.source_language
                if getattr(args, "target_language", None): stage_kwargs["target_language"] = args.target_language
            elif stage_enum == PipelineStage.TTS:
                if getattr(args, "voice", None): stage_kwargs["voice_name"] = args.voice
                if getattr(args, "language", None): stage_kwargs["language"] = args.language
            elif stage_enum == PipelineStage.SYNC:
                if getattr(args, "speed_min", None) is not None: stage_kwargs["speed_min"] = args.speed_min
                if getattr(args, "speed_max", None) is not None: stage_kwargs["speed_max"] = args.speed_max
                if getattr(args, "tolerance", None) is not None: stage_kwargs["tolerance"] = args.tolerance
                if getattr(args, "overlap_policy", None): stage_kwargs["overlap_policy"] = args.overlap_policy
                if getattr(args, "extreme_policy", None): stage_kwargs["extreme_policy"] = args.extreme_policy
            elif stage_enum == PipelineStage.RENDER:
                from autodub.modules.render_config import RenderConfig
                cfg = RenderConfig(
                    audio_mode=args.audio_mode,
                    tts_volume=args.tts_volume,
                    original_volume=args.original_volume,
                    video_codec=args.codec,
                    encoder=args.encoder,
                    quality=args.quality,
                    subtitle_mode=args.subtitle_mode
                )
                stage_kwargs["render_config"] = cfg

            mgr.run_stage(stage_enum, force=getattr(args, "force", False), **stage_kwargs)

    except PipelineCancelledError as e:
        print(f"Cancelled: {e}", file=sys.stderr)
        sys.exit(5)
    except AutoDubError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unhandled Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
