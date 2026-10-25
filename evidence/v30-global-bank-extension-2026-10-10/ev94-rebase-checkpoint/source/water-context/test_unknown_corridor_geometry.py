import importlib.util
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name('audit_unknown_corridors.py')
spec = importlib.util.spec_from_file_location('unknown_corridor_audit_test_subject', SCRIPT)
subject = importlib.util.module_from_spec(spec)
spec.loader.exec_module(subject)


class UnknownCorridorGeometryTests(unittest.TestCase):
    def test_positive_negative_controls_use_audit_helpers(self):
        result = subject.self_test()
        self.assertTrue(result['positive_two_layer_half_coverage'])
        self.assertTrue(result['negative_bbox_only_exact_clip'])
        self.assertTrue(result['positive_clearance_control'])
        self.assertTrue(result['negative_buried_clearance_control'])

    def test_native_cell_coordinate_and_diagonal_contract(self):
        import numpy as np
        from shapely.geometry import Polygon

        h = np.zeros((subject.GRID_N, subject.GRID_N), dtype=np.float32)
        r, c = 17, 23
        tris = subject.cell_triangles(r, c, h)
        self.assertEqual(len(tris), 2)
        self.assertAlmostEqual(tris[0][1].area, 18.0)
        self.assertAlmostEqual(tris[1][1].area, 18.0)
        self.assertTrue(tris[0][1].intersection(tris[1][1]).area == 0.0)
        self.assertAlmostEqual(tris[0][1].union(tris[1][1]).area, 36.0)
        self.assertEqual(tris[0][1].bounds, (c * 6.0, 12282.0 - (r + 1) * 6.0, (c + 1) * 6.0, 12282.0 - r * 6.0))

    def test_json_patch_key_roundtrip_and_legacy_failure(self):
        import json

        key = ('Narva_23', 117, 204, 1)
        patch_map = {key: {'sentinel': 7}}
        serialized = json.loads(json.dumps({'patch_keys': [list(key)]}))['patch_keys'][0]
        with self.assertRaises(TypeError):
            patch_map[serialized]
        self.assertEqual(subject.lookup_serialized_patch(patch_map, serialized), {'sentinel': 7})


if __name__ == '__main__':
    unittest.main()
