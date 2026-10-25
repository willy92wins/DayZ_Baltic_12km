"""Small offline fixtures for EV93 preview readiness and point serialization."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from ev93_build_common import load_accepted_inputs
from prepare_probe import barycentric_height_independent, recalibrated_points, reference_with_points
import numpy as np


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class ReadinessFixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.candidate = self.root / 'candidate.npz'
        self.candidate.write_bytes(b'fixture-candidate')
        self.input_file = self.root / 'pinned-input.json'
        self.input_file.write_text('{"fixture":true}\n', encoding='utf-8')
        self.receipt_path = self.root / 'authoring.json'
        self.report_path = self.root / 'consumer.json'
        self.receipt = {
            'status': 'AUTHORED_PENDING_GLOBAL_CONSUMER',
            'candidate_path': str(self.candidate),
            'candidate_sha256': sha(self.candidate),
            'prepared_sha256': 'a' * 64,
            'ledger_sha256': 'b' * 64,
            'index_manifest_sha256': 'c' * 64,
            'index_verification_sha256': 'd' * 64,
            'changed_vertices': 4,
        }
        self.receipt_path.write_text(json.dumps(self.receipt), encoding='utf-8')
        self.report = {
            'status': 'PASS_INCREMENTAL_NONREGRESSION',
            'gates': {'geometry': True, 'water': True},
            'information': {
                'candidate_sha256': self.receipt['candidate_sha256'],
                'prepared_sha256': self.receipt['prepared_sha256'],
                'authoring_receipt_sha256': sha(self.receipt_path),
                'global_contract_status': 'OPEN_INHERITED_MAP_DEFECTS',
                'changed_vertices': 4,
                'ledger_sha256': self.receipt['ledger_sha256'],
                'index_manifest_sha256': self.receipt['index_manifest_sha256'],
                'index_verification_sha256': self.receipt['index_verification_sha256'],
                'input_hashes': {str(self.input_file): sha(self.input_file)},
            },
        }
        self.report_path.write_text(json.dumps(self.report), encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def test_exact_receipt_and_pass_are_accepted(self):
        result = load_accepted_inputs(self.receipt_path, self.report_path)
        self.assertEqual(result['candidate_sha256'], self.receipt['candidate_sha256'])
        self.assertEqual(result['changed_vertices'], 4)

    def test_consumer_wrong_receipt_hash_fails_closed(self):
        self.report['information']['authoring_receipt_sha256'] = '0' * 64
        self.report_path.write_text(json.dumps(self.report), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'exact authoring receipt'):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_consumer_input_drift_fails_closed(self):
        self.input_file.write_text('changed\n', encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'input changed after PASS'):
            load_accepted_inputs(self.receipt_path, self.report_path)

    def test_nonpass_and_false_gate_fail_closed(self):
        self.report['gates']['water'] = False
        self.report_path.write_text(json.dumps(self.report), encoding='utf-8')
        with self.assertRaisesRegex(ValueError, 'gates'):
            load_accepted_inputs(self.receipt_path, self.report_path)


class NativeReferenceFixtures(unittest.TestCase):
    def test_point_overlay_serializes_new_ground_and_preserves_water(self):
        baseline = [
            {'id': 0, 'x': 3.0, 'z': 12279.0, 'cls': 1, 'expected_ground': 4.0, 'expected_water': 0.25},
            {'id': 1, 'x': 9.0, 'z': 12273.0, 'cls': 2, 'expected_ground': 6.0},
        ]
        updated = recalibrated_points(baseline, [5.0, 7.0])
        reference = reference_with_points({'points': baseline, 'other': 'kept'}, updated)
        self.assertEqual([p['expected_ground'] for p in reference['points']], [5.0, 7.0])
        self.assertEqual(reference['points'][0]['expected_water'], 0.25)
        self.assertNotIn('expected_water', reference['points'][1])
        self.assertEqual(reference['other'], 'kept')
        self.assertEqual(baseline[0]['expected_ground'], 4.0)

    def test_independent_triangle_plane_for_both_sides_of_diagonal(self):
        rr, cc = np.mgrid[0:2, 0:2]
        heights = (1.0 + 2.0 * rr + 3.0 * cc).astype(np.float64)
        # On the diagonal both triangles agree; nearby points exercise both branches.
        self.assertAlmostEqual(barycentric_height_independent(heights, 3.0, 12279.0), 3.5)
        self.assertAlmostEqual(barycentric_height_independent(heights, 4.5, 12279.0), 4.25)
        self.assertAlmostEqual(barycentric_height_independent(heights, 1.5, 12280.5), 2.25)


if __name__ == '__main__':
    unittest.main(verbosity=2)
