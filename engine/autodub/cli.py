import argparse
import sys
from pathlib import Path
from autodub.pipeline.manager import PipelineManager
from autodub.pipeline.state import PipelineStage
from autodub.exceptions import AutoDubError

def main():
    parser = argparse.ArgumentParser(description="AutoDubStudio CLI Engine")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # create <name> [--source <path>]
    create_sp = subparsers.add_parser("create", help="Create a new project")
    create_sp.add_argument("name", help="Project name")
    create_sp.add_argument("--source", default="source/input.mp4", help="Relative or absolute path to source video")

    # status <project>
    status_sp = subparsers.add_parser("status", help="Get project status")
    status_sp.add_argument("project", help="Project name or path")

    # run <project>
    run_sp = subparsers.add_parser("run", help="Run full pipeline from start")
    run_sp.add_argument("project", help="Project name or path")

    # resume <project>
    resume_sp = subparsers.add_parser("resume", help="Resume pipeline from checkpoint")
    resume_sp.add_argument("project", help="Project name or path")

    # retry <project> <stage> [--force]
    retry_sp = subparsers.add_parser("retry", help="Retry a specific stage")
    retry_sp.add_argument("project", help="Project name or path")
    retry_sp.add_argument("stage", choices=[s.value for s in PipelineStage], help="Stage to retry")
    retry_sp.add_argument("--force", action="store_true", help="Force re-running a COMPLETED stage")

    # cancel <project>
    cancel_sp = subparsers.add_parser("cancel", help="Cancel running pipeline")
    cancel_sp.add_argument("project", help="Project name or path")

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
        if args.command == "create":
            mgr = PipelineManager(args.name)
            mgr.project.data["source"]["path"] = args.source
            mgr.project.save()
            print(f"Project '{args.name}' created successfully.")
            return

        mgr = PipelineManager(args.project)

        if args.command == "status":
            print(mgr.get_status_formatted())

        elif args.command == "run":
            mgr.run_all()

        elif args.command == "resume":
            mgr.resume()

        elif args.command == "retry":
            mgr.retry(PipelineStage(args.stage), force=args.force)

        elif args.command == "cancel":
            mgr.cancel()
            print(f"Cancellation signal sent to project '{args.project}'.")

        elif args.command == "validate":
            if mgr.validate():
                print(f"Project '{args.project}' is VALID.")

        else:
            # Stage command
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

    except AutoDubError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unhandled Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
