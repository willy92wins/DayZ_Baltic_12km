"""Analytic fixtures and corrupt consumer artifacts. No production sweep."""
import copy
import importlib.util
from pathlib import Path
import unittest
import numpy as np

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('census_under_test', HERE/'native_shore_census_ev112.py')
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)
verify = census.verify


def fixture():
    # 6 m square: NW=.25, other corners=1.25, water=.75. Hand-computed
    # intersections at edge midpoints: top (3,6), left (0,3), diagonal (3,3).
    h = np.array([[.25, 1.25], [1.25, 1.25]])
    plane = np.full((1, 1), np.nan)
    field = np.full((1, 1, 4), np.nan)  # Valid absence of pond.
    segments = dict(p=np.array([[[3., 6.], [3., 3.]], [[0., 3.], [3., 3.]]]),
                    key=np.array([[1, 3], [2, 3]], np.int64), cell=np.array([[0, 0], [0, 0]]),
                    tri=np.array([0, 1]), pond=np.array([False, False]), lev=np.array([.75, .75]))
    return h, plane, field, segments


class NativeCensusTests(unittest.TestCase):
    def setUp(self):
        self.h, self.plane, self.field, self.seg = fixture()

    def check(self):
        return verify.segments(self.h, self.plane, self.field, self.seg)

    def test_known_midpoint_geometry(self):
        result = self.check()
        self.assertEqual(result['segments'], 2)
        self.assertEqual(result['maximum_water_height_residual_m'], 0.)

    def test_producer_agrees_with_hand_computed_fixture(self):
        producer = census.module('isolated_fixture_producer', HERE.parent/'water/shore_ramp_v31.py')
        producer.N, producer.NC, producer.ZTOP = 2, 1, 6.
        water, pond = producer.corner_water(self.plane, self.field)
        actual = producer.extract_segments(self.h, water, pond, self.plane, r0=0, r1=1, c0=0, c1=1)
        for key in self.seg:
            np.testing.assert_array_equal(actual[key], self.seg[key])
        verify.chains(actual, producer.chain(actual))

    def test_sloped_pond_field(self):
        # Keep intersections at hand-computed midpoints with a nonconstant W.
        self.plane[:] = 2.
        self.field[:] = [1., 2., 3., 4.]
        self.h = np.array([[.5, 2.5], [3.5, 4.5]])
        self.seg['pond'][:] = True
        self.seg['lev'][:] = 2.
        self.assertEqual(self.check()['maximum_water_height_residual_m'], 0.)

    def test_nan_height_rejected(self):
        self.h[0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, '^height_nonfinite$'): self.check()

    def test_nan_in_active_water_field_rejected(self):
        self.plane[:] = .75
        self.field[:] = .75
        self.field[0, 0, 0] = np.nan
        with self.assertRaisesRegex(ValueError, '^pond_field_nonfinite$'): self.check()

    def test_incomplete_water_field_rejected(self):
        self.field = self.field[:, :, :3]
        with self.assertRaisesRegex(ValueError, '^field_shape$'): self.check()

    def test_missing_segment_rejected(self):
        self.seg = {key: value[:1] for key, value in self.seg.items()}
        with self.assertRaisesRegex(ValueError, '^mixed_face_coverage$'): self.check()

    def test_duplicate_segment_rejected(self):
        self.seg = {key: np.concatenate([value, value[:1]]) for key, value in self.seg.items()}
        with self.assertRaisesRegex(ValueError, '^duplicate_face$'): self.check()

    def test_duplicate_pair_rejected(self):
        self.seg['key'][1] = self.seg['key'][0]
        with self.assertRaisesRegex(ValueError, '^duplicate_edge_pair$'): self.check()

    def test_shift_along_edge_rejected_by_surface(self):
        self.seg['p'][0, 0, 0] += .1
        with self.assertRaisesRegex(ValueError, '^water_height_residual$'): self.check()

    def test_same_edge_twice_rejected(self):
        self.seg['key'][0, 1] = self.seg['key'][0, 0]
        self.seg['p'][0, 1] = self.seg['p'][0, 0]
        with self.assertRaisesRegex(ValueError, '^repeated_endpoint_edge$'): self.check()

    def test_all_zero_edge_cannot_replace_crossing_edge(self):
        self.h[:] = [[.25, .75], [1.25, .75]]
        self.seg['p'][:] = [[[6., 3.], [6., 0.]], [[0., 3.], [6., 0.]]]
        self.seg['key'][0] = [7, 3]
        with self.assertRaisesRegex(ValueError, '^edge_not_straddling$'): self.check()

    def test_shift_off_edge_rejected(self):
        self.seg['p'][0, 0, 1] += .1
        with self.assertRaisesRegex(ValueError, '^point_off_edge$'): self.check()

    def test_chain_missing_assignment_rejected(self):
        with self.assertRaisesRegex(ValueError, '^chain_assignment_coverage$'):
            verify.chains(self.seg, [])

    def test_chain_duplicate_assignment_rejected(self):
        chain = census.shore.chain(self.seg)
        with self.assertRaisesRegex(ValueError, '^chain_assignment_coverage$'):
            verify.chains(self.seg, chain+copy.deepcopy(chain))

    def test_chain_wrong_geometry_rejected(self):
        chain = census.shore.chain(self.seg)
        chain[0]['pts'][1, 0] += .1
        with self.assertRaisesRegex(ValueError, '^chain_geometry_or_key$'):
            verify.chains(self.seg, chain)

    def test_exact_vertex_degeneracy_is_not_pass(self):
        producer = census.module('isolated_equal_vertex_producer', HERE.parent/'water/shore_ramp_v31.py')
        producer.N, producer.NC, producer.ZTOP = 2, 1, 6.
        self.h = np.array([[.75, .25], [1.25, .25]])
        water, pond = producer.corner_water(self.plane, self.field)
        seg = producer.extract_segments(self.h, water, pond, self.plane, r0=0, r1=1, c0=0, c1=1)
        result = verify.segments(self.h, self.plane, self.field, seg)
        self.assertEqual(result['zero_length_segments'], 1)
        self.assertEqual(result['exact_water_vertex_faces'], 2)
        chains = producer.chain(seg)
        verify.chains(seg, chains)
        self.assertIn('DEGENERATE', [row['status'] for row in census.screen(chains)])

    def test_cross_key_coincident_endpoints_inventoried(self):
        chain = census.shore.chain(self.seg)
        other = copy.deepcopy(chain[0])
        other['keys'] = other['keys'] + 100
        found = census.cross_key_endpoints(chain+[other])
        self.assertEqual(len(found), 2)

    def test_closed_chain_closure_not_claimed(self):
        item = dict(pts=np.array([[0., 0.], [20., 0.], [20., 20.], [0., 0.]]),
                    order=np.arange(3), closed=True)
        result = census.screen([item])[0]
        self.assertTrue(result['closed'])
        self.assertFalse(result['closure_turn_evaluated'])

    def test_large_chain_cost_explicit(self):
        x = np.arange(2200, dtype=float)
        item = dict(pts=np.column_stack([x, x % 2]), order=np.arange(2199), closed=False)
        self.assertEqual(census.screen([item])[0]['status'], 'NOT_EVALUATED_COST')


if __name__ == '__main__':
    unittest.main(verbosity=2)
