"""Independent analytic and negative controls for the incremental pilot gates."""
import importlib.util
from pathlib import Path
import unittest
import numpy as np

HERE = Path(__file__).resolve().parent


def load(name):
    spec = importlib.util.spec_from_file_location(name, HERE/(name+'.py'))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


v = load('verify_small_native_water_pilot_ev112')
a = load('small_native_water_pilot_ev112')


class Gates(unittest.TestCase):
    def test_native_diagonal_positive(self):
        m = np.eye(7, dtype=bool)
        self.assertEqual(v.topology(m, m)['wet']['before'], 1)
        # Opposite diagonal is not a native edge and has seven components.
        self.assertEqual(v.topology(m[:, ::-1], m[:, ::-1])['wet']['before'], 7)

    def test_shifted_component_survives(self):
        old = np.zeros((12, 12), bool); old[3:7, 3:7] = True
        new = np.zeros_like(old); new[4:8, 4:8] = True
        self.assertEqual(v.topology(old, new)['wet']['after'], 1)

    def test_water_removed(self):
        old = np.zeros((12, 12), bool); old[3:7, 3:7] = True
        with self.assertRaisesRegex(ValueError, 'component_bijection_wet'): v.topology(old, np.zeros_like(old))

    def test_water_added(self):
        new = np.zeros((12, 12), bool); new[3:7, 3:7] = True
        with self.assertRaisesRegex(ValueError, 'component_bijection_wet'): v.topology(np.zeros_like(new), new)

    def test_island_submerged(self):
        old = np.zeros((15, 15), bool); old[2:13, 2:13] = True; old[7:9, 7:9] = False
        new = old.copy(); new[7:9, 7:9] = True
        with self.assertRaisesRegex(ValueError, 'component_bijection_dry'): v.topology(old, new)

    def test_merge_plus_new_body_same_count(self):
        old = np.zeros((20, 20), bool); old[3:6, 3:6] = True; old[3:6, 8:11] = True
        new = old.copy(); new[4, 6:8] = True; new[14:16, 14:16] = True
        from scipy.ndimage import label
        self.assertEqual(label(old, v.S6)[1], label(new, v.S6)[1])
        with self.assertRaisesRegex(ValueError, 'component_bijection_wet'): v.topology(old, new)

    def test_split_plus_deleted_body_same_count(self):
        separate = np.zeros((20, 20), bool); separate[3:6, 3:6] = True; separate[3:6, 8:11] = True
        joined = separate.copy(); joined[4, 6:8] = True; joined[14:16, 14:16] = True
        with self.assertRaisesRegex(ValueError, 'component_bijection_wet'): v.topology(joined, separate)

    def state(self):
        before = dict(heights=np.ones((9, 9), np.float32), protected=np.zeros((9, 9), bool))
        after = {k:x.copy() for k, x in before.items()}; after['heights'][4, 4] += .1
        after[v.MASK] = after['heights'] != before['heights']
        d = dict(allowed=np.ones((9, 9), bool), fixed=np.zeros((9, 9), bool), side=np.zeros((9, 9), np.int8))
        return before, after, d

    def test_nontrivial_delta_positive(self):
        self.assertEqual(v.delta_guard(*self.state())['changed'], 1)

    def test_protected_height_rejected(self):
        b, c, d = self.state(); d['fixed'][4, 4] = True
        with self.assertRaisesRegex(ValueError, 'protected_height'): v.delta_guard(b, c, d)

    def test_external_delta_rejected(self):
        b, c, d = self.state(); d['allowed'][4, 4] = False
        with self.assertRaisesRegex(ValueError, 'outside_allowed'): v.delta_guard(b, c, d)

    def test_old_mask_rejected(self):
        b, c, d = self.state(); c['protected'][0, 0] = True
        with self.assertRaisesRegex(ValueError, 'array_changed'): v.delta_guard(b, c, d)

    def test_unchanged_candidate_rejected(self):
        b, c, d = self.state(); c['heights'] = b['heights'].copy(); c[v.MASK][:] = False
        with self.assertRaisesRegex(ValueError, 'unchanged_candidate'): v.delta_guard(b, c, d)

    def test_change_mask_cannot_hide_delta(self):
        b, c, d = self.state(); c[v.MASK][:] = False
        with self.assertRaisesRegex(ValueError, 'change_mask'): v.delta_guard(b, c, d)

    def test_current_and_potential_pond_corner(self):
        b, c, _ = self.state(); plane = np.full((8, 8), np.nan); env = plane.copy()
        v.footprint_guard(b['heights'], c['heights'], plane, env)
        for slot in (plane, env):
            slot[3, 3] = 5
            with self.assertRaisesRegex(ValueError, 'pond_corner_changed'):
                v.footprint_guard(b['heights'], c['heights'], plane, env)
            slot[3, 3] = np.nan

    def test_native_side_conflict_unconstrained(self):
        h = np.full((5, 5), .75); p = np.zeros((5, 5), bool)
        h[1, 1] = 1.; p[1, 1] = True
        self.assertEqual(a.side_requirements(h, p)[2, 2], 1)
        h[3, 3] = .5; p[3, 3] = True
        self.assertEqual(a.side_requirements(h, p)[2, 2], 0)

    def test_side_is_checked_on_saved_heights(self):
        b, c, d = self.state(); c['heights'][4, 4] = np.float32(.79); d['side'][4, 4] = 1
        with self.assertRaisesRegex(ValueError, 'side_dry'): v.delta_guard(b, c, d)

    def test_curved_analytic_contour_positive(self):
        t = np.linspace(0, 2*np.pi, 161); p = np.column_stack([25*np.cos(t), 14*np.sin(t)]); p[-1] = p[0]
        m = v.closed_screen(p)
        self.assertEqual(m['maximum_abrupt_turns'], 0); self.assertEqual(m['maximum_long_straights'], 0)
        # This is a curvature control, never universal naturalness acceptance.

    def test_closure_corner_detected_all_starts(self):
        p = np.array([[0, 0], [8, 0], [12, 4], [12, 12], [4, 12], [0, 8]], float)
        for i in range(len(p)):
            q = np.roll(p, i, axis=0); result = v.closed_screen(np.vstack([q, q[:1]]))
            self.assertGreaterEqual(result['maximum_turn_deg'], 90)

    def test_empty_and_duplicate_contour_rejected(self):
        for p in (np.empty((0, 2)), np.zeros((5, 2))):
            with self.assertRaises(ValueError): v.closed_screen(p)

    def test_native_slopes_positive_and_negative(self):
        r, c = np.mgrid[:9, :9]; plane = (r*.1+c*.2).astype(np.float32)
        v.slope_guard(plane, plane+.1)
        bad = plane.copy(); bad[4, 4] += 20
        with self.assertRaisesRegex(ValueError, 'slope_regression'): v.slope_guard(plane, bad)


if __name__ == '__main__': unittest.main(verbosity=2)
