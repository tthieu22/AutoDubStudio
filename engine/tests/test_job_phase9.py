import unittest
import time
from autodub.jobs.job import Job
from autodub.jobs.job_state import JobState, validate_job_state_transition, is_terminal_job_state
from autodub.exceptions import InvalidJobStateTransitionError


class TestPhase9JobModel(unittest.TestCase):

    def test_01_job_creation(self):
        job = Job.create(
            project_id="test_project",
            input_path="input/video.mp4",
            output_path="output/final.mp4",
            priority=8
        )
        self.assertTrue(job.job_id.startswith("job_"))
        self.assertEqual(job.project_id, "test_project")
        self.assertEqual(job.status, JobState.PENDING.value)
        self.assertEqual(job.priority, 8)
        self.assertEqual(job.progress, 0.0)

    def test_02_job_serialization(self):
        job = Job.create(
            project_id="test_proj",
            input_path="in.mp4",
            output_path="out.mp4"
        )
        data = job.to_dict()
        self.assertEqual(data["job_id"], job.job_id)
        self.assertEqual(data["status"], JobState.PENDING.value)

        reconstituted = Job.from_dict(data)
        self.assertEqual(reconstituted.job_id, job.job_id)
        self.assertEqual(reconstituted.project_id, job.project_id)
        self.assertEqual(reconstituted.input_path, job.input_path)

    def test_03_valid_state_transitions(self):
        job = Job.create("p1", "in.mp4", "out.mp4")
        job.transition_to(JobState.QUEUED.value)
        self.assertEqual(job.status, JobState.QUEUED.value)

        job.transition_to(JobState.RUNNING.value)
        self.assertEqual(job.status, JobState.RUNNING.value)
        self.assertIsNotNone(job.started_at)

        job.transition_to(JobState.COMPLETED.value)
        self.assertEqual(job.status, JobState.COMPLETED.value)
        self.assertIsNotNone(job.completed_at)

    def test_04_invalid_state_transition(self):
        job = Job.create("p1", "in.mp4", "out.mp4")
        with self.assertRaises(InvalidJobStateTransitionError):
            job.transition_to(JobState.COMPLETED.value)

    def test_05_terminal_state_detection(self):
        self.assertTrue(is_terminal_job_state("COMPLETED"))
        self.assertTrue(is_terminal_job_state("CANCELLED"))
        self.assertFalse(is_terminal_job_state("RUNNING"))
        self.assertFalse(is_terminal_job_state("QUEUED"))


if __name__ == "__main__":
    unittest.main()
