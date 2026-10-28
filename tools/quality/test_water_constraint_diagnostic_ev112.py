import importlib.util
from pathlib import Path
import unittest
import numpy as np

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE/(name+'.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


d = load('water_constraint_diagnostic_ev112')
v = load('verify_small_native_water_pilot_ev112')


class Constraints(unittest.TestCase):
    def test_index_against_explicit_sets(self):
        rng = np.random.default_rng(2128); n = 17
        cells = rng.integers(0, n-1, size=(80, 2)); owner = rng.integers(0, 7, 80)
        low, high = d.ownership(cells, owner, n)
        reference = [[set() for _ in range(n)] for _ in range(n)]
        for (r, c), cid in zip(cells, owner):
            corners = {(r, c), (r, c+1), (r+1, c), (r+1, c+1)}
            vertices = corners.copy()
            for a, b in corners:
                vertices.update(((a-1, b), (a+1, b), (a, b-1), (a, b+1), (a-1, b-1), (a+1, b+1)))
            for a, b in vertices:
                if 0 <= a < n and 0 <= b < n: reference[a][b].add(int(cid))
        for cid in range(8):
            expected = np.array([[bool(s-{cid}) for s in row] for row in reference])
            np.testing.assert_array_equal(d.foreign(low, high, cid), expected)

    def test_duplicate_cell_retains_both_owners(self):
        low, high = d.ownership([[2, 2], [2, 2]], [4, 8], 8)
        self.assertTrue(d.foreign(low, high, 4)[2, 2]); self.assertTrue(d.foreign(low, high, 8)[2, 2])

    def test_no_self_protection_or_border_reflection(self):
        low, high = d.ownership([[0, 0]], [0], 8)
        self.assertFalse(d.foreign(low, high, 0).any())
        self.assertFalse(d.foreign(low, high, 1)[7].any())
        self.assertFalse(d.foreign(low, high, 1)[:, 7].any())

    def test_empty_index(self):
        low, high = d.ownership(np.empty((0, 2), int), [], 5)
        self.assertFalse(d.foreign(low, high, 0).any())

    def test_fixed_square_is_conflict_not_permission(self):
        square = np.array([[0, 0], [20, 0], [20, 20], [0, 20], [0, 0]], float)
        r = d.classify(square, True, True, True, True, v.closed_screen)
        self.assertEqual(r['status'], 'FROZEN_SCREEN_CONFLICT')
        self.assertIn('no permission', r['conditions'])

    def test_fixed_smooth_ring_compatible(self):
        t = np.linspace(0, 2*np.pi, 101); p = np.column_stack([25*np.cos(t), 14*np.sin(t)]); p[-1] = p[0]
        self.assertEqual(d.classify(p, True, True, True, True, v.closed_screen)['status'], 'FROZEN_SCREEN_COMPATIBLE')

    def test_partial_ring_never_impossible(self):
        square = np.array([[0, 0], [20, 0], [20, 20], [0, 20], [0, 0]], float)
        self.assertEqual(d.classify(square, True, False, True, True, v.closed_screen)['status'], 'PARTIAL_CONSTRAINTS_INCONCLUSIVE')

    def test_exclusions_are_not_passes(self):
        p = np.zeros((514, 2))
        for closed, fixed, degree, sea, expected in ((False, True, True, True, 'NOT_EVALUATED_OPEN'),
                (True, True, True, False, 'OUT_OF_SCOPE_POND'),
                (True, True, False, True, 'INCONCLUSIVE_EDGE_INCIDENCE'),
                (True, True, True, True, 'NOT_EVALUATED_COST')):
            self.assertEqual(d.classify(p, closed, fixed, degree, sea, v.closed_screen)['status'], expected)

    def test_local_peak_support(self):
        h = np.zeros((11, 11), np.float32); h[5, 5] = 2
        r = d.support_at(h, 5, 5, 'peak'); self.assertEqual(r['value'], 2)
        self.assertTrue(any(w['shape_id'] == 0 for w in r['witnesses']))

    def test_global_screen_cost_is_not_pass(self):
        p = np.array([[0, 0], [20, 0], [20, 20], [0, 20], [0, 0]], float)
        budget = dict(pairs_left=16)
        self.assertEqual(d.classify(p, True, True, True, True, v.closed_screen, budget)['status'], 'FROZEN_SCREEN_CONFLICT')
        self.assertEqual(d.classify(p, True, True, True, True, v.closed_screen, budget)['status'], 'NOT_EVALUATED_COST')

    def test_degenerate_not_certified(self):
        self.assertEqual(d.classify(np.zeros((4, 2)), True, True, True, True, v.closed_screen)['status'], 'INCONCLUSIVE_DEGENERATE')

    def test_support_against_production_prominence(self):
        native = d.module('native_prominence', HERE.parent/'terrain/despike_v31.py')
        rng = np.random.default_rng(2128)
        h = rng.uniform(-2, 2, (native.N, native.N)).astype(np.float32)
        peak, pit = native.prominence(h)
        coords = [(0, 0), (0, native.N-1), (native.N-1, 0), (native.N-1, native.N-1), (1, 1)]
        coords += list(map(tuple, rng.integers(0, native.N, (32, 2))))
        for r, c in coords:
            self.assertEqual(d.support_at(h, r, c, 'peak')['value'], float(peak[r, c]))
            self.assertEqual(d.support_at(h, r, c, 'pit')['value'], float(pit[r, c]))

    def test_unedited_pair_becomes_pit(self):
        old = np.zeros((11, 11), np.float32); new = old.copy(); new[3:8, 3:8] = 1
        new[5, 5:7] = 0
        for c in (5, 6):
            self.assertEqual(old[5, c], new[5, c])
            self.assertEqual(d.support_at(old, 5, c, 'pit')['value'], 0)
            self.assertEqual(d.support_at(new, 5, c, 'pit')['value'], 1)


if __name__ == '__main__': unittest.main(verbosity=2)
