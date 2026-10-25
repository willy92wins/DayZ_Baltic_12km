from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/water'))
from diagnose_compiled_contact_v31 import classify


class ContactDiagnosticTests(unittest.TestCase):
    def test_interior_edge_vertex_and_outside(self):
        triangles = [[[8192, 5, 0], [8194, 5, 0], [8192, 5, 2]]]
        for x, z, expected in [(8192.5,.5,'interior_one_ulp'), (8193,1,'boundary_or_sub_ulp'),
                               (8192,0,'boundary_or_sub_ulp'), (8194,2,'outside')]:
            self.assertEqual(classify(triangles,x,z)['classification'], expected)

    def test_lower_interior_cannot_hide_upper_edge(self):
        triangles = [[[8192,5,0],[8194,5,0],[8192,5,2]],
                     [[8191,4,-1],[8195,4,-1],[8191,4,3]]]
        result = classify(triangles,8192,0)
        self.assertEqual(result['classification'], 'boundary_or_sub_ulp')
        self.assertEqual(result['top_y_m'],5)

    def test_positive_clearance_smaller_than_world_ulp(self):
        result = classify([[[8192,5,0],[8194,5,0],[8192,5,2]]],8193,.99951171875)
        self.assertEqual(result['classification'],'boundary_or_sub_ulp')
        self.assertGreater(result['top_triangle_best_edge_clearance_m'],0)
        self.assertLess(result['top_triangle_best_edge_clearance_m'],result['world_ulp_m'])

    def test_almost_vertical_face_does_not_supply_height(self):
        result = classify([[[0,0,0],[1,1e12,0],[0,0,1]]],.25,.25)
        self.assertEqual(result['classification'],'outside')


if __name__ == '__main__':
    unittest.main()
