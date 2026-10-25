"""Focused tests for EV94 consumer dynamic-artifact readset closure."""
import tempfile
import unittest
from pathlib import Path

import verify_ev94_rebase as consumer


class ArtifactReadsetClosureTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.paths = [root / name for name in (
            "preflight.json", "prepared.npz", "solve-result.json",
            "solver-state.npz", "candidate.npz")]
        for i, path in enumerate(self.paths):
            path.write_bytes((f"artifact-{i}\n").encode("ascii"))

    def tearDown(self):
        self.tmp.cleanup()

    def readset(self):
        return consumer.artifact_readset(*self.paths, "test artifact readset")

    def test_exact_five_artifact_set_closes_without_static_source(self):
        start = self.readset()
        end = self.readset()
        self.assertEqual(len(start), 5)
        self.assertNotIn(str(Path(consumer.__file__).resolve()), start)
        consumer.require_same_readset(start, end, "test closure")

    def test_same_members_with_changed_content_is_rejected(self):
        start = self.readset()
        self.paths[2].write_bytes(b"changed solve result\n")
        end = self.readset()
        with self.assertRaises(consumer.Reject):
            consumer.require_same_readset(start, end, "test content drift")

    def test_changed_member_set_is_rejected_separately(self):
        start = self.readset()
        end = dict(start)
        extra = Path(consumer.__file__).resolve()
        end[str(extra)] = consumer.sha(extra)
        with self.assertRaisesRegex(consumer.Reject, "member set changed"):
            consumer.require_same_readset(start, end, "test set drift")

    def test_duplicate_dynamic_path_is_rejected(self):
        with self.assertRaisesRegex(consumer.Reject, "duplicate dynamic artifact path"):
            consumer.artifact_readset(*([*self.paths[:4], self.paths[0]]), "duplicate test")


if __name__ == "__main__":
    unittest.main(verbosity=2)
