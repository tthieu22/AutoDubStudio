class AutoDubError(Exception):
    """Base exception class for AutoDubStudio."""
    pass

class ProjectValidationError(AutoDubError):
    """Raised when project validation fails."""
    pass

class StateTransitionError(AutoDubError):
    """Raised when an invalid state transition is attempted."""
    pass

class StageDependencyError(AutoDubError):
    """Raised when a stage dependency constraint is violated."""
    pass

class PipelineCancelledError(AutoDubError):
    """Raised when pipeline execution is cancelled by the user."""
    pass

class OllamaUnavailableError(AutoDubError):
    """Raised when local Ollama server is unreachable."""
    pass

class OllamaModelNotFoundError(AutoDubError):
    """Raised when requested LLM model is not installed in Ollama."""
    pass

class OllamaTimeoutError(AutoDubError):
    """Raised when Ollama request times out."""
    pass

class TranslationFailedError(AutoDubError):
    """Raised when translation fails after maximum retries."""
    pass

class PiperUnavailableError(AutoDubError):
    """Raised when Piper TTS executable is not found."""
    pass

class PiperVoiceNotFoundError(AutoDubError):
    """Raised when requested Piper voice model is missing."""
    pass

class PiperSynthesisError(AutoDubError):
    """Raised when Piper fails to synthesize audio."""
    pass

class PiperInvalidOutputError(AutoDubError):
    """Raised when output WAV file from Piper is invalid or corrupted."""
    pass

class PiperTimeoutError(AutoDubError):
    """Raised when Piper synthesis process times out."""
    pass

class TTSSynthesisFailedError(AutoDubError):
    """Raised when TTS stage fails after retries."""
    pass

class SyncError(AutoDubError):
    """Base exception class for Audio Synchronization module."""
    pass

class SyncInputError(SyncError):
    """Raised when input data for synchronization is invalid."""
    pass

class SyncTTSMissingError(SyncError):
    """Raised when expected TTS WAV file is missing."""
    pass

class SyncInvalidAudioError(SyncError):
    """Raised when input or output audio file is corrupted/invalid."""
    pass

class SyncFFmpegError(SyncError):
    """Raised when FFmpeg process fails during synchronization."""
    pass

class SyncDurationMismatchError(SyncError):
    """Raised when output duration exceeds tolerance after correction pass."""
    pass

class SyncExtremeSpeedError(SyncError):
    """Raised when required speed factor exceeds limits under REJECT policy."""
    pass

class SyncOverlapError(SyncError):
    """Raised when subtitle overlap occurs under FAIL policy."""
    pass

class SyncCancelledError(SyncError):
    """Raised when synchronization stage is cancelled."""
    pass

class AudioMixError(AutoDubError):
    """Raised when audio mixing fails."""
    pass

class AudioValidationError(AutoDubError):
    """Raised when input/output audio validation fails."""
    pass

class RenderError(AutoDubError):
    """Base exception class for Video Renderer module."""
    pass

class RenderValidationError(RenderError):
    """Raised when rendering configuration or stream validation fails."""
    pass

class RenderFFmpegError(RenderError):
    """Raised when FFmpeg process fails during rendering."""
    pass

class EncoderUnavailableError(RenderError):
    """Raised when requested video encoder is unavailable."""
    pass

class NvencUnavailableError(EncoderUnavailableError):
    """Raised when NVIDIA NVENC encoder is requested but unavailable."""
    pass

class SubtitleValidationError(RenderError):
    """Raised when subtitle file validation fails."""
    pass

class OutputValidationError(RenderError):
    """Raised when rendered output file validation fails."""
    pass

class RenderCancelledError(RenderError):
    """Raised when rendering stage is cancelled."""
    pass

class JobError(AutoDubError):
    """Base exception class for Job Management module."""
    pass

class JobStateError(JobError):
    """Raised when job state operations fail."""
    pass

class InvalidJobStateTransitionError(JobStateError):
    """Raised when an invalid job state transition is attempted."""
    pass

class JobAlreadyExistsError(JobError):
    """Raised when attempting to create a job with a duplicate ID."""
    pass

class JobNotFoundError(JobError):
    """Raised when requested job ID is not found."""
    pass

class JobLockError(JobError):
    """Raised when acquiring or releasing a job lock fails."""
    pass

class QueueError(JobError):
    """Raised when queue operations fail."""
    pass

class WorkerError(JobError):
    """Raised when worker execution fails."""
    pass

class PipelineRecoveryError(JobError):
    """Raised when job or pipeline recovery fails."""
    pass

class StageExecutionError(JobError):
    """Raised when stage execution fails."""
    pass

class RetryExhaustedError(JobError):
    """Raised when maximum retries are exhausted for a job."""
    pass

class ArtifactValidationError(JobError):
    """Raised when stage output artifact validation fails."""
    pass



