"""Readiness and contract-boundary fixtures for the EV94 focal build adapter."""
import argparse
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

import focal_build_common as common
from stage import B, COMPILE_RUNNER_SHA256, verify_compile_runner

COMPOSITION = common.FOCUS / 'composition-run-01/review.json'
SUPPLEMENT = common.FOCUS / 'consumer-run-01/acceptance-supplement.json'

class FocalBuildContractTests(unittest.TestCase):
    def test_real_composition_and_supplement_are_accepted_read_only(self):
        accepted = common.load_accepted_inputs(COMPOSITION, SUPPLEMENT)
        self.assertEqual(accepted['candidate_sha256'], common.CANDIDATE_SHA)
        self.assertEqual(accepted['base_candidate_sha256'], common.COMPOSED_BASE_SHA)
        self.assertEqual(accepted['retained_units'], 499)
        self.assertEqual(accepted['changed_vertices'], 30067)
        self.assertEqual(accepted['readset_files'], 48)
        self.assertEqual(accepted['supplement_readset_files'], 43)

    def test_acceptance_manifest_is_focal_and_never_claims_selection_receipt(self):
        accepted = common.load_accepted_inputs(COMPOSITION, SUPPLEMENT)
        out = common.add_acceptance_manifest({}, accepted)
        self.assertEqual(out['ev94_composition_report_sha256'], accepted['composition_report_sha256'])
        self.assertEqual(out['ev94_focal_supplement_sha256'], common.SUPPLEMENT_SHA)
        self.assertEqual(out['ev94_candidate_sha256'], common.CANDIDATE_SHA)
        self.assertNotIn('ev93_selection_receipt', out)
        self.assertNotIn('ev94_selection_receipt', out)

    def test_old_ev93_selection_cli_is_not_accepted(self):
        parser = argparse.ArgumentParser()
        common.acceptance_args(parser)
        with self.assertRaises(SystemExit):
            parser.parse_args(['--selection-receipt', 'selection.json', '--consumer-report', 'consumer.json'])

    def test_unknown_composition_status_fails_closed(self):
        with self.assertRaises(FileNotFoundError):
            common.load_accepted_inputs(COMPOSITION.with_name('not-a-composition.json'), SUPPLEMENT)

    def test_stage_runner_verification_is_read_only_and_pinned(self):
        runner = B / 'compile_native_world.ps1'
        before = hashlib.sha256(runner.read_bytes()).hexdigest()
        self.assertEqual(before, COMPILE_RUNNER_SHA256)
        self.assertEqual(verify_compile_runner(), before)
        self.assertEqual(hashlib.sha256(runner.read_bytes()).hexdigest(), before)
        stage_source = (B / 'stage.py').read_text(encoding='utf-8')
        self.assertNotIn("(B / 'compile_native_world.ps1').write_text", stage_source)
        with tempfile.TemporaryDirectory() as directory:
            changed = Path(directory) / runner.name
            changed.write_bytes(runner.read_bytes() + b'\n# altered')
            with self.assertRaisesRegex(ValueError, 'reviewed EV94 pin'):
                verify_compile_runner(changed)

if __name__ == '__main__':
    unittest.main(verbosity=2)
