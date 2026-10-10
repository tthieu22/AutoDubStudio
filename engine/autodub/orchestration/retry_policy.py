from enum import Enum
import logging
from typing import Type, Tuple

from autodub.exceptions import (
    AutoDubError,
    PipelineCancelledError,
    RenderCancelledError,
    SyncCancelledError,
    ProjectValidationError,
    JobStateError,
    InvalidJobStateTransitionError,
    OllamaUnavailableError,
    PiperUnavailableError,
    EncoderUnavailableError,
    NvencUnavailableError,
    ArtifactValidationError,
    OutputValidationError,
    SubtitleValidationError,
)

logger = logging.getLogger("autodub.orchestration.retry")


class ErrorCategory(Enum):
    TRANSIENT = "TRANSIENT"
    PERMANENT = "PERMANENT"
    CANCELLED = "CANCELLED"
    RESOURCE = "RESOURCE"
    VALIDATION = "VALIDATION"


NON_RETRYABLE_EXCEPTIONS: Tuple[Type[Exception], ...] = (
    PipelineCancelledError,
    RenderCancelledError,
    SyncCancelledError,
    ProjectValidationError,
    JobStateError,
    InvalidJobStateTransitionError,
    OllamaUnavailableError,
    PiperUnavailableError,
    EncoderUnavailableError,
    NvencUnavailableError,
    ArtifactValidationError,
    OutputValidationError,
    SubtitleValidationError,
)


class RetryPolicy:
    """Configurable retry policy with error classification and exponential backoff."""

    def __init__(self, max_retries: int = 3, base_delay_sec: float = 1.0, max_delay_sec: float = 30.0):
        self.max_retries = max_retries
        self.base_delay_sec = base_delay_sec
        self.max_delay_sec = max_delay_sec

    def classify_error(self, exc: Exception) -> ErrorCategory:
        if isinstance(exc, (PipelineCancelledError, RenderCancelledError, SyncCancelledError)):
            return ErrorCategory.CANCELLED
        if isinstance(exc, (OllamaUnavailableError, PiperUnavailableError, EncoderUnavailableError, NvencUnavailableError)):
            return ErrorCategory.RESOURCE
        if isinstance(exc, (ProjectValidationError, ArtifactValidationError, OutputValidationError, SubtitleValidationError)):
            return ErrorCategory.VALIDATION
        if isinstance(exc, NON_RETRYABLE_EXCEPTIONS):
            return ErrorCategory.PERMANENT
        return ErrorCategory.TRANSIENT

    def should_retry(self, exc: Exception, current_attempt: int) -> bool:
        if current_attempt >= self.max_retries:
            return False
        category = self.classify_error(exc)
        if category in (ErrorCategory.PERMANENT, ErrorCategory.CANCELLED, ErrorCategory.VALIDATION):
            return False
        return True

    def calculate_backoff_delay(self, current_attempt: int) -> float:
        delay = self.base_delay_sec * (2 ** (max(1, current_attempt) - 1))
        return min(delay, self.max_delay_sec)
