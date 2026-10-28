"""Analytic positive/negative fixtures independent of Baltic generator output."""
import itertools
import json
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
import collision_scene_b2a_ev112 as c


def cube():
    return np.array(list(itertools.product((-1., 1.), repeat=3)))


def matrix():
    return np.r_[np.eye(3).ravel(), [0., 0., 0.]]


def pbo(path, prefix, name, body):
    props = b'\0'+struct.pack('<5I', 0x56657273, 0, 0, 0, 0)
    props += b'prefix\0'+prefix.encode()+b'\0\0'
    header = name.encode()+b'\0'+struct.pack('<5I', 0, 0, 0, 0, len(body))
    path.write_bytes(props+header+b'\0'+bytes(20)+body)


class GeometryTests(unittest.TestCase):
    def test_cube_inside_is_possible_not_proved_solid(self):
        self.assertEqual(c.separation(cube(), [0, 0, 0])['state'], 'POSSIBLE_OCCUPANCY')

    def test_cube_face_contact_not_clear(self):
        self.assertNotEqual(c.separation(cube(), [1, 0, 0])['state'], 'SEPARATED')

    def test_cube_outside_certificate(self):
        s = c.separation(cube(), [2, 0, 0])
        self.assertEqual(s['state'], 'SEPARATED')
        self.assertGreater(s['lower_margin'], .9999999)
        self.assertEqual(s['vertices_verified'], 8)

    def test_tetra_diagonal_separation_not_aabb(self):
        v = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 1]], float)
        self.assertEqual(c.separation(v, [.8, .8, .8])['state'], 'SEPARATED')
        self.assertEqual(c.separation(v, [.1, .1, .1])['state'], 'POSSIBLE_OCCUPANCY')

    def test_degenerate_plane_contact_and_far(self):
        v = np.array([[0, 0, 0], [1, 0, 0], [0, 0, 1], [1, 0, 1]], float)
        self.assertEqual(c.separation(v, [.5, 0, .5])['state'], 'INCONCLUSIVE_DEGENERATE')
        self.assertEqual(c.separation(v, [.5, 1, .5])['state'], 'SEPARATED')

    def test_pose_translation_rotation_nonuniform_scale(self):
        m = np.r_[[0, 2, 0, -3, 0, 0, 0, 0, .5], [100, 200, 300]]
        v = c.inv.transform(cube(), m)
        lo, hi = c.aabb_world(cube(), m[None])
        self.assertTrue((lo[0] <= v.min(0)).all() and (hi[0] >= v.max(0)).all())
        self.assertEqual(c.separation(v, [100, 200, 300])['state'], 'POSSIBLE_OCCUPANCY')
        self.assertEqual(c.separation(v, [104, 200, 300])['state'], 'SEPARATED')

    def test_far_center_volume_reaches_ray(self):
        v = cube()*np.array([100, 1, 1])
        m = matrix(); m[9] = 80
        lo, hi = c.aabb_world(v, m[None])
        self.assertTrue(lo[0, 0] < 0 < hi[0, 0])

    def test_component_missing_vertex_and_face_residual(self):
        v = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0], [10, 0, 0]], float)
        selection = NS(name='component01', selected_faces=[0], selected_vertices=[0])
        fs, groups = c.components(v, [[0, 1, 2], [1, 2, 3]], [selection])
        self.assertEqual(set(groups[0][1]), {0, 1, 2})
        self.assertEqual(set(groups[1][1]), {1, 2, 3})

    def test_unassigned_vertex_not_silently_empty(self):
        self.assertEqual(c.components(cube(), [], [])[1][0][0], 'unassigned_vertices')

    def test_bad_index_rejected(self):
        with self.assertRaisesRegex(ValueError, 'face_indices'):
            c.components(cube(), [[0, 1, 999]], [])

    def test_nan_rejected(self):
        with self.assertRaises(ValueError):
            c.separation(cube(), [np.nan, 0, 0])

    def test_roundoff_does_not_create_clearance(self):
        self.assertNotEqual(c.separation(cube(), [1+1e-15, 0, 0])['state'], 'SEPARATED')

    def test_transform_error_blocks_separation(self):
        self.assertNotEqual(c.separation(cube(), [1.001, 0, 0], .01)['state'], 'SEPARATED')

    def test_ray_high_blocked_low_clear(self):
        v = np.array([[-2, 10, -2], [2, 10, -2], [0, 10, 2]], float)
        self.assertEqual(c.vertical_hits(v, [[0, 1, 2]], 0, 0, 0, 100)[0]['height'], 10)
        self.assertEqual(c.vertical_hits(v, [[0, 1, 2]], 0, 0, 0, 2), [])

    def test_ray_edge_retained_ambiguous(self):
        v = np.array([[0, 5, 0], [1, 5, 0], [0, 5, 1]], float)
        self.assertEqual(c.vertical_hits(v, [[0, 1, 2]], 0, 0, 0, 10)[0]['state'], 'AMBIGUOUS_EDGE_OR_FACE')

    def test_vertical_face_not_silently_missed(self):
        v = np.array([[0, 0, 0], [0, 10, 0], [0, 10, 1]], float)
        self.assertEqual(c.vertical_hits(v, [[0, 1, 2]], 0, .5, 0, 100)[0]['state'],
                         'INCONCLUSIVE_VERTICAL_OR_DEGENERATE')

    def test_overlapping_faces_not_deduplicated(self):
        v = np.array([[-1, 5, -1], [1, 5, -1], [0, 5, 1]], float)
        self.assertEqual(len(c.vertical_hits(v, [[0, 1, 2], [0, 1, 2]], 0, 0, 0, 10)), 2)

    def test_quad_contact_conditional(self):
        v = np.array([[-1, 5, -1], [1, 5, -1], [1, 5, 1], [-1, 5, 1]], float)
        self.assertTrue(all(h['quad_fan_conditional'] for h in c.vertical_hits(v, [[0, 1, 2, 3]], 0, .5, 0, 10)))

    def test_fire_geometry_not_geometry(self):
        l = NS(resolution=float(np.float32(1e15)), lod_end_ok=True)
        self.assertIsNone(c.geometry_lod(NS(lods=[l], resolutions=[l.resolution], lod_errors=[])))

    def test_duplicate_geometry_rejected(self):
        l = NS(resolution=c.GEOMETRY, lod_end_ok=True)
        with self.assertRaisesRegex(ValueError, 'duplicate_geometry'):
            c.geometry_lod(NS(lods=[l, l], resolutions=[l.resolution]*2, lod_errors=[]))

    def test_unknown_model_blocks_all_origins(self):
        self.assertEqual(c.origin_state([dict(state='SEPARATED')], ['missing'], 2), 'INCONCLUSIVE_COVERAGE')

    def test_unknown_proxy_blocks_clearance(self):
        empty, rows = c.empty_proxy_tree('absent.p3d', {}, None)
        self.assertFalse(empty)
        self.assertEqual(c.origin_state([], rows, 2), 'INCONCLUSIVE_COVERAGE')

    def test_nonempty_proxy_blocks_output_coverage(self):
        geometry = (cube(), [[0, 1, 2]], [], np.zeros(3), dict(proxies=[]))
        with patch.object(c, 'model_geometry', return_value=geometry):
            unknown, evidence = c.proxy_coverage('parent.p3d', ['child.p3d'], 7, {}, None)
        self.assertEqual(unknown, [dict(name='parent.p3d', child='child.p3d', instances=7,
                                       reason='nonempty_or_unresolved_proxy_frame')])
        self.assertEqual(c.origin_state([], unknown, 2), 'INCONCLUSIVE_COVERAGE')

    def test_union_of_frame_bounds_cannot_drop_second_frame(self):
        v = np.concatenate([cube(), cube()+[500, 0, 0]])
        lo, hi = c.aabb_world(v, matrix()[None])
        self.assertTrue((lo[0] <= [-1, -1, -1]).all())
        self.assertTrue((hi[0] >= [501, 1, 1]).all())
        self.assertTrue(((np.array([500, 0, 0]) >= lo[0]) &
                         (np.array([500, 0, 0]) <= hi[0])).all())

    def test_snapshot_matches_far_full_scene_instance(self):
        m = np.stack([matrix(), matrix()]);m[1, 9] = 100
        scene = dict(names=['tree.p3d'], ids=np.array([4, 9]), mat=m)
        snap = [dict(id=349, round=0, measured=dict(objects=[
                dict(shape='tree.p3d', pos=[100, 0, 0], valid=True)]))]
        rows = c.compare_snapshots(scene, np.array([0, 1]), np.array([0, 2]), snap)
        self.assertEqual(rows[0]['matching_float32_instance_ids'], [9])
        self.assertEqual(rows[0]['searched_instances'], 2)
        self.assertEqual(rows[0]['state'], 'MATCHED_FLOAT32_POSITION')

    def test_snapshot_position_duplicates_remain_ambiguous(self):
        scene = dict(names=['tree.p3d'], ids=np.array([4, 9]), mat=np.stack([matrix(), matrix()]))
        snap = [dict(id=349, round=0, measured=dict(objects=[
                dict(shape='tree.p3d', pos=[0, 0, 0], valid=True)]))]
        rows = c.compare_snapshots(scene, np.array([0, 1]), np.array([0, 2]), snap)
        self.assertEqual(rows[0]['state'], 'AMBIGUOUS_FLOAT32_POSITION')

    def test_snapshot_unmatched_not_a_pose_mismatch_claim(self):
        scene = dict(names=['tree.p3d'], ids=np.array([4]), mat=matrix()[None])
        snap = [dict(id=349, round=0, measured=dict(objects=[
                dict(shape='tree.p3d', pos=[100, 0, 0], valid=True)]))]
        rows = c.compare_snapshots(scene, np.array([0]), np.array([0, 1]), snap)
        self.assertEqual(rows[0]['state'], 'NO_FLOAT32_POSITION_MATCH')
        self.assertEqual(rows[0]['matching_float32_instance_ids'], [])

    def test_central_comparison_retains_all_hits_and_both_native_channels(self):
        measured = dict(ground=0, rv=True, rv_pos=[0, 10, 0], rv_shapes='tree',
                        rv_normal=[0, 1, 0], bullet=True, bullet_pos=[0, 11, 0],
                        bullet_shape='tree', bullet_normal=[0, 1, 0])
        native = {i:dict(states={'rv':'FAIL'}, expected=dict(x=0, z=0, ground=0,
                       effective_bed=1), measured=measured) for i in c.IDS}
        hits = [dict(id=349, slot=0, height=y, frame='raw') for y in (10, 1, 1)]
        hits += [dict(id=349, slot=0, frame='plus_bounding_center', state='INCONCLUSIVE')]
        result = c.central_comparison(native, hits)
        self.assertEqual(len(result['rows']), 10)
        self.assertEqual(result['rows'][0]['model_contacts'], hits)
        self.assertEqual(result['rows'][0]['native']['bullet_pos'][1], 11)

    def test_terrain_blocks_origin(self):
        self.assertEqual(c.origin_state([], [], -1), 'INCONCLUSIVE_TERRAIN')

    def test_clear_is_explicitly_conditional(self):
        self.assertEqual(c.origin_state([], [], 2), 'CLEAR_UNDER_FRAME_HYPOTHESES')

    def test_different_pbo_same_path_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp)/'a.pbo', Path(tmp)/'b.pbo'
            pbo(a, 'dz/tree', 'tree.p3d', b'first')
            pbo(b, 'dz/tree', 'tree.p3d', b'second')
            with self.assertRaisesRegex(ValueError, 'ambiguous_package_path'):
                c.bind_packages([a, b])

    def test_payload_bound_to_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            a = Path(tmp)/'a.pbo'
            pbo(a, 'dz/tree', 'tree.p3d', b'first')
            bindings, pins = c.bind_packages([a])
            self.assertEqual(c.payload(bindings['dz/tree/tree.p3d']), b'first')
            self.assertEqual(pins[0]['sha256'], c.sha(a))


class PointTests(unittest.TestCase):
    def setUp(self):
        self.original = [dict(id=i, states={'rv':'FAIL'}, expected=dict(id=i, x=8247.453125,
                         z=8938.498046875, ground=8., effective_bed=8.5)) for i in c.IDS]
        self.a = [dict(id=x['id'], expected=x['expected'].copy(), original_states=x['states'].copy())
                  for x in self.original]
        self.H = np.zeros((2048, 2048), np.float32)

    def test_centrals_preserved_90_stimuli(self):
        pts = c.select_points(self.a, self.original, self.H)
        self.assertEqual(len(pts), 90)
        self.assertEqual([p['id'] for p in pts if p['slot'] == 0], list(c.IDS))
        self.assertEqual(set(p['low_y'] for p in pts), {10.5})
        self.assertNotEqual(pts[1]['effective_offset'], pts[1]['nominal_offset'])

    def test_missing_point(self):
        with self.assertRaisesRegex(ValueError, 'missing_central_id'):
            c.select_points(self.a[:-1], self.original, self.H)

    def test_duplicate_point(self):
        with self.assertRaisesRegex(ValueError, 'duplicate_source_id'):
            c.select_points(self.a+[self.a[0]], self.original, self.H)

    def test_replaced_central(self):
        self.a[0]['expected']['x'] += .02
        with self.assertRaisesRegex(ValueError, 'original_central_changed'):
            c.select_points(self.a, self.original, self.H)

    def test_changed_original_labels(self):
        self.a[0]['original_states']['rv'] = 'PASS'
        with self.assertRaisesRegex(ValueError, 'original_central_changed'):
            c.select_points(self.a, self.original, self.H)


if __name__ == '__main__':
    unittest.main()
