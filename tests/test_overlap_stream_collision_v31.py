import itertools
from pathlib import Path
import sys
import unittest
from types import SimpleNamespace

import numpy as np
from scipy.spatial import ConvexHull, QhullError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/water'))
from overlap_stream_collision_v31 import expanded_component, selected_components


class OverlapCollisionTests(unittest.TestCase):
    def test_cube_has_analytic_dimensions_and_volume(self):
        original = np.array(list(itertools.product((-1., 1.), repeat=3)))
        result = expanded_component(original)
        eps = 1 / 512
        np.testing.assert_array_equal(result['points'].min(0), [-1-eps, -1, -1-eps])
        np.testing.assert_array_equal(result['points'].max(0), [1+eps, 1, 1+eps])
        self.assertAlmostEqual(result['volume'], (2+2*eps)**2 * 2, places=10)

    def test_sloping_prism_contains_original_and_has_bounded_support(self):
        top = np.array([[0, 0, 0], [3, .75, 0], [.5, .625, 1]])
        original = np.vstack((top, top-[0, .4, 0]))
        result = expanded_component(original)
        hull = ConvexHull(result['points'])
        # A convex body's half-spaces independently test containment of the input.
        signed = original @ hull.equations[:, :3].T + hull.equations[:, 3]
        self.assertLessEqual(float(signed.max()), 1e-10)
        directions = np.array(list(itertools.product((-2., -.3, 1.), repeat=3)))
        before = (original @ directions.T).max(0)
        after = (result['points'] @ directions.T).max(0)
        expected_extension = (abs(directions[:, 0]) + abs(directions[:, 2])) / 512
        np.testing.assert_allclose(after-before, expected_extension, rtol=0, atol=1e-12)

    def test_degenerate_or_nonfinite_geometry_cannot_be_accepted(self):
        for data in (np.zeros((3, 3)), np.full((8, 3), np.nan), np.zeros((3, 2))):
            with self.assertRaises((ValueError, QhullError)):
                expanded_component(data)

    def test_local_selection_preserves_bbox_anchors_without_expanding_other_interior(self):
        selections = {}
        for name, x, z in [('low',-10,-10),('high',10,10),('contact',0,0),('other',5,5)]:
            points = [SimpleNamespace(coords=(x+dx,y,z+dz))
                      for dx,y,dz in itertools.product((-1.,1.),repeat=3)]
            selections[name] = SimpleNamespace(points=points)
        lod = SimpleNamespace(points=[p for s in selections.values() for p in s.points], selections=selections)
        selected = selected_components(lod,[dict(x=8192,z=9000)],[8192,0,9000])
        self.assertEqual(set(selected), {'low','high','contact'})
        self.assertEqual(selected['contact'], ['contact_footprint'])
        self.assertEqual(selected['low'], ['bbox_extremum'])

    def test_distinct_components_hold_each_bbox_extremum(self):
        selections = {}
        for name,x,z in [('left',-10,0),('right',10,0),('front',0,-10),('back',0,10),('contact',0,0),('other',5,5)]:
            selections[name] = SimpleNamespace(points=[SimpleNamespace(coords=(x+dx,y,z+dz))
                                for dx,y,dz in itertools.product((-1.,1.),repeat=3)])
        lod = SimpleNamespace(points=[p for s in selections.values() for p in s.points], selections=selections)
        self.assertEqual(set(selected_components(lod,[dict(x=0,z=0)],[0,0,0])),
                         {'left','right','front','back','contact'})


if __name__ == '__main__':
    unittest.main()
