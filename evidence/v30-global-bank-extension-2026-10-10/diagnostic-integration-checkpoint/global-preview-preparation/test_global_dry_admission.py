import copy
import json
import unittest
from pathlib import Path

import numpy as np

import global_dry_build_common as common


def passing_report():
    pins = {
        str(common.RECOVERY_CANDIDATE.resolve()): common.RECOVERY_CANDIDATE_SHA,
        str(common.RECOVERY_RECEIPT.resolve()): common.RECOVERY_RECEIPT_SHA,
        str(common.V2_CONSUMER.resolve()): common.V2_CONSUMER_SHA,
        str(common.EV95_CANDIDATE.resolve()): common.EV95_CANDIDATE_SHA,
        str(common.EV95_DEPLOY.resolve()): common.EV95_DEPLOY_SHA,
        str(common.EV95_STAGE.resolve()): common.EV95_STAGE_SHA,
    }
    return {
        'schema': 'global-dry-rollback.independent-consumer.v1',
        'status': common.V2_STATUS,
        'gates': {name: True for name in common.V2_GATES},
        'candidate_path': str(common.RECOVERY_CANDIDATE),
        'candidate_sha256': common.RECOVERY_CANDIDATE_SHA,
        'recovery_receipt_path': str(common.RECOVERY_RECEIPT),
        'recovery_receipt_sha256': common.RECOVERY_RECEIPT_SHA,
        'source_readset_equal': True,
        'source_pins_start': pins,
        'source_pins_end': dict(pins),
        'domain': {'pass': True, 'changed_vertices': 5},
        'instrumentation': {'last_phase': 'complete_source_end_hash'},
    }


class AdmissionTests(unittest.TestCase):
    def test_valid_v2_report_accepts_only_exact_gate_and_identity_contract(self):
        accepted = common.validate_consumer_contract(passing_report(), 'a' * 64, 'a' * 64)
        self.assertEqual(accepted['candidate_sha256'], common.RECOVERY_CANDIDATE_SHA)
        self.assertEqual(accepted['recovery_receipt_sha256'], common.RECOVERY_RECEIPT_SHA)
        self.assertEqual(accepted['changed_vertices_vs_ev95'], 5)

    def test_rejects_current_real_error_report(self):
        failed_path = (common.G / 'global-operator-prototype/global-dry-rollback/postsolve-consumer/'
                       'instrumented-v2/runs/attempt-02/report.json')
        failed = json.loads(failed_path.read_text(encoding='utf-8'))
        digest = common.sha(failed_path)
        with self.assertRaises(ValueError):
            common.validate_consumer_contract(failed, digest, digest)
        with self.assertRaises(ValueError):
            common.load_accepted_inputs(failed_path, digest)

    def test_rejects_nonpass_status_and_missing_extra_or_false_gate(self):
        for mutate in (
            lambda x: x.update(status='ERROR_INDEPENDENT_CONSUMER'),
            lambda x: x['gates'].pop(next(iter(common.V2_GATES))),
            lambda x: x['gates'].update(unexpected=True),
            lambda x: x['gates'].update(domain_exact=False),
        ):
            report = passing_report()
            mutate(report)
            with self.assertRaises(ValueError):
                common.validate_consumer_contract(report, 'b' * 64, 'b' * 64)

    def test_rejects_candidate_receipt_source_and_report_sha_drift(self):
        mutators = (
            lambda x: x.update(candidate_sha256='0' * 64),
            lambda x: x.update(recovery_receipt_sha256='0' * 64),
            lambda x: x['source_pins_start'].update({str(common.V2_CONSUMER.resolve()): '0' * 64}),
            lambda x: x['source_pins_end'].update({'unpaired': '1' * 64}),
        )
        for mutate in mutators:
            report = passing_report()
            mutate(report)
            with self.assertRaises(ValueError):
                common.validate_consumer_contract(report, 'c' * 64, 'c' * 64)
        with self.assertRaises(ValueError):
            common.validate_consumer_contract(passing_report(), 'c' * 64, 'd' * 64)

    def test_rejects_missing_or_noninteger_domain_changed_count(self):
        for value in (None, 0, True, 2.0):
            report = passing_report()
            report['domain']['changed_vertices'] = value
            with self.assertRaises(ValueError):
                common.validate_consumer_contract(report, 'e' * 64, 'e' * 64)

    def test_nonheight_metadata_must_match_ev95_and_b_byte_exactly(self):
        base = {'heights': np.zeros((2, 2), dtype=np.float32),
                'mask': np.array([0.0, np.nan], dtype=np.float64)}
        common.require_metadata_exact(copy.deepcopy(base), copy.deepcopy(base), copy.deepcopy(base))
        changed = copy.deepcopy(base)
        changed['mask'][0] = 1.0
        with self.assertRaises(ValueError):
            common.require_metadata_exact(changed, base, base)
        wrong_dtype = copy.deepcopy(base)
        wrong_dtype['mask'] = wrong_dtype['mask'].astype(np.float32)
        with self.assertRaises(ValueError):
            common.require_metadata_exact(wrong_dtype, base, base)
        missing = {'heights': base['heights']}
        with self.assertRaises(ValueError):
            common.require_metadata_exact(missing, base, base)


if __name__ == '__main__':
    unittest.main(verbosity=2)
