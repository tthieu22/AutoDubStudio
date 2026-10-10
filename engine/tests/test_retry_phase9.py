import unittest
from autodub.orchestration.retry_policy import RetryPolicy, ErrorCategory
from autodub.exceptions import (
    PipelineCancelledError,
    ProjectValidationError,
    PiperSynthesisError,
    OllamaUnavailableError,
    AudioMixError
)


class TestPhase9RetryPolicy(unittest.TestCase):

    def setUp(self):
        self.policy = RetryPolicy(max_retries=3, base_delay_sec=0.1, max_delay_sec=1.0)

    def test_01_classify_errors(self):
        self.assertEqual(self.policy.classify_error(PipelineCancelledError("msg")), ErrorCategory.CANCELLED)
        self.assertEqual(self.policy.classify_error(OllamaUnavailableError("msg")), ErrorCategory.RESOURCE)
        self.assertEqual(self.policy.classify_error(ProjectValidationError("msg")), ErrorCategory.VALIDATION)
        self.assertEqual(self.policy.classify_error(AudioMixError("msg")), ErrorCategory.TRANSIENT)

    def test_02_should_retry_transient_error(self):
        err = AudioMixError("temporary ffmpeg glitch")
        self.assertTrue(self.policy.should_retry(err, current_attempt=1))
        self.assertTrue(self.policy.should_retry(err, current_attempt=2))
        self.assertFalse(self.policy.should_retry(err, current_attempt=3))  # Max retries reached

    def test_03_non_retryable_errors(self):
        cancelled = PipelineCancelledError("cancelled")
        validation = ProjectValidationError("invalid schema")
        self.assertFalse(self.policy.should_retry(cancelled, current_attempt=1))
        self.assertFalse(self.policy.should_retry(validation, current_attempt=1))

    def test_04_exponential_backoff_calculation(self):
        self.assertEqual(self.policy.calculate_backoff_delay(1), 0.1)
        self.assertEqual(self.policy.calculate_backoff_delay(2), 0.2)
        self.assertEqual(self.policy.calculate_backoff_delay(3), 0.4)


if __name__ == "__main__":
    unittest.main()
