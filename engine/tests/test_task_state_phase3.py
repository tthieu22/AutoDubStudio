import unittest
from autodub.pipeline.task_state import TaskStatus, TaskRecord, TaskStateMachine
from autodub.exceptions import StateTransitionError

class TestPhase3TaskStateMachine(unittest.TestCase):
    def setUp(self):
        self.task = TaskRecord(
            task_id="task_scene_001_image",
            project_id="proj_001",
            stage="IMAGE_GEN",
            artifact_path="assets/images/scene_001.png"
        )

    def test_01_initial_task_state(self):
        self.assertEqual(self.task.status, TaskStatus.PENDING)
        self.assertEqual(self.task.attempt, 1)
        self.assertEqual(self.task.max_attempts, 3)

    def test_02_valid_review_approval_flow(self):
        # PENDING -> PROCESSING
        TaskStateMachine.transition(self.task, TaskStatus.PROCESSING)
        self.assertEqual(self.task.status, TaskStatus.PROCESSING)

        # PROCESSING -> GENERATED
        TaskStateMachine.transition(self.task, TaskStatus.GENERATED)
        self.assertEqual(self.task.status, TaskStatus.GENERATED)

        # GENERATED -> REVIEW_REQUIRED
        TaskStateMachine.transition(self.task, TaskStatus.REVIEW_REQUIRED)
        self.assertEqual(self.task.status, TaskStatus.REVIEW_REQUIRED)

        # REVIEW_REQUIRED -> APPROVED
        TaskStateMachine.approve(self.task)
        self.assertEqual(self.task.status, TaskStatus.APPROVED)

    def test_03_rejection_flow(self):
        TaskStateMachine.transition(self.task, TaskStatus.PROCESSING)
        TaskStateMachine.transition(self.task, TaskStatus.GENERATED)
        TaskStateMachine.transition(self.task, TaskStatus.REVIEW_REQUIRED)

        # Reject
        TaskStateMachine.reject(self.task, reason="Image quality low")
        self.assertEqual(self.task.status, TaskStatus.REJECTED)
        self.assertEqual(self.task.error, "Image quality low")

        # Re-process
        TaskStateMachine.transition(self.task, TaskStatus.PROCESSING)
        self.assertEqual(self.task.status, TaskStatus.PROCESSING)
        self.assertIsNone(self.task.error)

    def test_04_failure_and_retry_limit(self):
        TaskStateMachine.transition(self.task, TaskStatus.PROCESSING)
        TaskStateMachine.fail(self.task, "CUDA out of memory")
        self.assertEqual(self.task.status, TaskStatus.FAILED)

        # Retry 1 (attempt becomes 2)
        TaskStateMachine.retry(self.task)
        self.assertEqual(self.task.attempt, 2)
        self.assertEqual(self.task.status, TaskStatus.PROCESSING)

        # Fail again
        TaskStateMachine.fail(self.task, "CUDA OOM 2")

        # Retry 2 (attempt becomes 3)
        TaskStateMachine.retry(self.task)
        self.assertEqual(self.task.attempt, 3)

        # Fail third time
        TaskStateMachine.fail(self.task, "CUDA OOM 3")

        # Retry 3 should raise error exceeding max_attempts=3
        with self.assertRaises(StateTransitionError):
            TaskStateMachine.retry(self.task)

    def test_05_approved_protection(self):
        TaskStateMachine.transition(self.task, TaskStatus.PROCESSING)
        TaskStateMachine.transition(self.task, TaskStatus.GENERATED)
        TaskStateMachine.approve(self.task)

        # Cannot modify approved task without force
        with self.assertRaises(StateTransitionError):
            TaskStateMachine.transition(self.task, TaskStatus.PROCESSING, force=False)

        # Can modify with force
        TaskStateMachine.transition(self.task, TaskStatus.PROCESSING, force=True)
        self.assertEqual(self.task.status, TaskStatus.PROCESSING)

    def test_06_serialization(self):
        d = self.task.to_dict()
        self.assertEqual(d["task_id"], "task_scene_001_image")
        self.assertEqual(d["status"], "pending")

        restored = TaskRecord.from_dict(d)
        self.assertEqual(restored.task_id, self.task.task_id)
        self.assertEqual(restored.status, TaskStatus.PENDING)

if __name__ == "__main__":
    unittest.main()
