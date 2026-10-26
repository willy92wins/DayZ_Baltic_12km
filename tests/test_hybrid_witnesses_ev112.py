import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'tools/terrain'), str(ROOT / 'tools/water')]
import repair_free_shapes_ev112 as solver
import census_pyramids_v31 as prominence_consumer
import census_creases_v31 as edge_consumer
from continuous_stream_pilot_v31 import fair_energy


class HybridWitnesses(unittest.TestCase):
    def test_rebased_previously_skipped_group_has_safe_hybrid_solution(self):
        path=ROOT/'tests/fixtures/feasible-witness-1171-190.npz'
        metadata=json.loads(path.with_suffix('.json').read_text())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),metadata['fixture_sha256'])
        with np.load(path) as data:fixture={key:data[key] for key in data.files}
        base,free=fixture['base'],fixture['free']
        with self.assertRaisesRegex(ValueError,'constrained native fairing failed'):
            solver.fair_native_patch(**fixture,bound_witnesses=True)
        result,receipt=solver.fair_native_patch(**fixture,bound_witnesses=True,preserve_satisfied_witnesses=True)
        self.assertEqual(receipt['witnesses'],'hybrid')
        result=result.astype(np.float32).astype(float)
        np.testing.assert_array_equal(result[~free],base[~free])
        self.assertTrue((result>=fixture['floor']-2e-6).all())
        self.assertTrue((result<=fixture['ceiling']+2e-6).all())
        peak,pit,*_=prominence_consumer.prominence(result)
        before_peak,before_pit,*_=prominence_consumer.prominence(base)
        self.assertLessEqual(peak[8,8],.3)
        self.assertTrue((peak<=np.maximum(before_peak,.3)+2e-6).all())
        self.assertTrue((pit<=np.maximum(before_pit,.3)+2e-6).all())
        before,after=edge_consumer.angles(base),edge_consumer.angles(result)
        self.assertTrue(all((after[k]<=np.maximum(before[k],20)+.01).all() for k in before))
        self.assertLess(fair_energy(result,fixture['prior'],0)[0],fair_energy(base,fixture['prior'],0)[0])

    def real_fixture(self):
        path = ROOT / 'tests/fixtures/hybrid-regression-cluster10.npz'
        metadata = json.loads(path.with_suffix('.json').read_text())
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), metadata['fixture_sha256'])
        with np.load(path) as data:
            return {key: data[key] for key in data.files}

    def test_previous_witness_choice_rejects_real_cluster(self):
        with self.assertRaisesRegex(ValueError, 'constrained native fairing failed'):
            solver.fair_native_patch(**self.real_fixture(), bound_witnesses=True)

    def test_hybrid_solves_real_cluster_under_independent_consumers(self):
        fixture = self.real_fixture()
        base, free = fixture['base'], fixture['free']
        result, receipt = solver.fair_native_patch(**fixture, bound_witnesses=True, preserve_satisfied_witnesses=True)
        result = result.astype(np.float32).astype(float)
        self.assertEqual(receipt['witnesses'], 'hybrid')
        self.assertTrue(np.any(result != base))
        np.testing.assert_array_equal(result[~free], base[~free])
        self.assertTrue((result[free] >= fixture['floor'][free] - 2e-6).all())
        self.assertTrue((result[free] <= fixture['ceiling'][free] + 2e-6).all())
        peak, pit, *_ = prominence_consumer.prominence(result)
        self.assertTrue((peak <= np.maximum(fixture['peak_cap'], .3) + 2e-6).all())
        self.assertTrue((pit <= np.maximum(fixture['pit_cap'], .3) + 2e-6).all())
        before, after = edge_consumer.angles(base), edge_consumer.angles(result)
        self.assertTrue(all((after[key] <= np.maximum(before[key], 20) + .01).all() for key in before))

    def test_hybrid_requires_bound_mode(self):
        with self.assertRaisesRegex(ValueError, 'require bound_witnesses'):
            solver.fair_native_patch(**self.real_fixture(), preserve_satisfied_witnesses=True)

    def test_satisfied_shapes_keep_default_constraints(self):
        base = np.full((9, 9), 2.)
        base[4, 4] += .1
        free = np.zeros(base.shape, bool)
        free[3:-3, 3:-3] = True
        args = (base, np.full_like(base, 2.), free, base - .5, base + .5,
                np.full_like(base, .3), np.full_like(base, .3))
        captured = []
        original = solver.minimize

        def record(*args, **kwargs):
            linear = kwargs['constraints'][-1]
            captured.append((linear.A.copy(), linear.ub.copy()))
            return original(*args, **kwargs)

        with patch.object(solver, 'minimize', side_effect=record):
            baseline, _ = solver.fair_native_patch(*args)
            hybrid, _ = solver.fair_native_patch(*args, bound_witnesses=True, preserve_satisfied_witnesses=True)
        np.testing.assert_array_equal(captured[0][0], captured[1][0])
        np.testing.assert_array_equal(captured[0][1], captured[1][1])
        np.testing.assert_array_equal(baseline, hybrid)


if __name__ == '__main__':
    unittest.main()
