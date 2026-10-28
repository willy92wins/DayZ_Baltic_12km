"""Analytic fixtures and adversarial saved-MLOD consumers, no DayZ needed."""
import io
from pathlib import Path
import struct
import sys
import tempfile
import unittest
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from prism_contact_b3_ev112 import author, dilate
from verify_prism_contact_b3_ev112 import verify, original_controls
from review_compact_collision_v31 import load, py3d
from compact_stream_collision_v31 import add_component
from scipy.spatial import ConvexHull

ORIGIN = [8262., 7., 8934.]
TARGETS = [dict(id=700, x=8262., z=8934.)]

def fixture(path, slope=(0., 0.)):
    model = py3d.P3D()
    visual, geo, memory, road = [py3d.LOD() for _ in range(4)]
    visual.resolution, geo.resolution, memory.resolution, road.resolution = 0., 1e13, 1e15, 3e15
    for idx, xz in enumerate(([[0, 0], [1, 0], [0, 1]],
                              [[-20, -20], [-10, -20], [-20, -10]],
                              [[10, 10], [20, 10], [10, 20]]), 1):
        q = np.asarray(xz, float)
        top = np.column_stack((q[:, 0], q @ slope, q[:, 1]))
        points = np.vstack((top, top - [0, 180/512, 0]))
        hull = ConvexHull(points)
        add_component(py3d, geo, dict(points=points, faces=hull.simplices, volume=hull.volume), idx)
        start = len(visual.points)
        for v in top:
            p = py3d.Point()
            p.coords = tuple(v)
            visual.points.append(p)
        normal = np.cross(top[1]-top[0], top[2]-top[0])
        normal /= np.linalg.norm(normal)
        ni = len(visual.facenormals)
        visual.facenormals.append(tuple(normal))
        face = py3d.Face(visual.points, visual.facenormals)
        for i in range(3):
            v = py3d.Vertex(visual.points, visual.facenormals)
            v.point_index, v.normal_index, v.uv = start+i, ni, (0., 0.)
            face.vertices.append(v)
        visual.faces.append(face)
    model.lods = [visual, geo, memory, road]
    with path.open('wb') as f:
        model.write(f)

class B3(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name)/'source.p3d'
        self.candidate = Path(self.tmp.name)/'candidate.p3d'
        fixture(self.source)
        blob, _ = author(self.source, TARGETS, ORIGIN)
        self.candidate.write_bytes(blob)

    def check(self, **kw):
        return verify(self.source, self.candidate, TARGETS, ORIGIN, ['Component0001'], **kw)

    def mutate(self, fn):
        h, lods, blobs = load(self.candidate)
        fn(lods)
        m = py3d.P3D()
        m.lods = lods
        stream = io.BytesIO()
        m.write(stream)
        self.candidate.write_bytes(stream.getvalue())

    def test_flat_full_overlay(self):
        r = self.check()
        self.assertEqual(r['status'], 'OFFLINE_CANDIDATE_ONLY')
        self.assertGreater(r['contacts'][0]['world_float32_margin_m'], 0)
        self.assertLess(r['contacts'][0]['margin_ulps'], 2)

    def test_known_tilted_planes(self):
        for slopes in ((.125, -.25), (-.25, .125)):
            with self.subTest(slopes=slopes):
                fixture(self.source, slopes)
                blob, _ = author(self.source, TARGETS, ORIGIN)
                self.candidate.write_bytes(blob)
                self.assertEqual(self.check()['status'], 'OFFLINE_CANDIDATE_ONLY')

    def test_identity_is_not_a_repair(self):
        self.candidate.write_bytes(self.source.read_bytes())
        with self.assertRaisesRegex(ValueError, 'no_strict_expansion'):
            self.check()

    def test_inverted_face(self):
        self.mutate(lambda l: l[1].faces[0].vertices.reverse())
        with self.assertRaises(ValueError):
            self.check()

    def test_missing_face(self):
        def edit(l):
            face = l[1].faces.pop()
            for sel in l[1].selections.values():
                sel.faces.pop(face, None)
        self.mutate(edit)
        with self.assertRaises(ValueError):
            self.check()

    def test_wrong_normal(self):
        self.mutate(lambda l: l[1].facenormals.__setitem__(0, (1., 0., 0.)))
        with self.assertRaisesRegex(ValueError, 'normal_error'):
            self.check()

    def test_wrong_plane(self):
        def edit(l):
            p = l[1].points[0]
            p.coords = (p.coords[0], p.coords[1]+.01, p.coords[2])
        self.mutate(edit)
        with self.assertRaises(ValueError):
            self.check()

    def test_unauthorized_other_component(self):
        self.mutate(lambda l: setattr(l[1].points[-1], 'mass', 2.))
        with self.assertRaisesRegex(ValueError, 'unauthorized_bytes_changed'):
            self.check()

    def test_visual_mutation(self):
        self.mutate(lambda l: setattr(l[0].points[0], 'coords', (0., .01, 0.)))
        with self.assertRaisesRegex(ValueError, 'non_geometry_changed'):
            self.check()

    def test_roadway_mutation(self):
        self.mutate(lambda l: l[3].properties.__setitem__('unexpected', 'yes'))
        with self.assertRaisesRegex(ValueError, 'non_geometry_changed'):
            self.check()

    def test_extra_target_fails_selection(self):
        with self.assertRaisesRegex(ValueError, 'selection_mismatch'):
            verify(self.source, self.candidate, TARGETS+[dict(id=999, x=8272., z=8944.)], ORIGIN, ['Component0001'])

    def test_contraction_rejected(self):
        def edit(l):
            for p in l[1].selections['Component0001'].points:
                x, y, z = p.coords
                p.coords = ((x-1/3)*.99+1/3, y, (z-1/3)*.99+1/3)
        self.mutate(edit)
        with self.assertRaises(ValueError):
            self.check()

    def test_nonradial_deformation_rejected(self):
        def edit(l):
            for p in l[1].selections['Component0001'].points:
                x, y, z = p.coords
                if x > 1:
                    p.coords = (x, y, z+.0001)
        self.mutate(edit)
        with self.assertRaises(ValueError):
            self.check()

    def test_wrong_family_rejected(self):
        with self.assertRaisesRegex(ValueError, 'prism_shape'):
            dilate(np.zeros((8, 3)))

    def controls(self):
        targets = TARGETS + [dict(id=723, x=8262.7578125, z=8938.232421875)]
        rows = [dict(id=t['id'], expected=dict(**t, expect=('dry' if t['id']==700 else 'wet'))) for t in targets]
        return dict(rows=rows), targets

    def test_original_mixed_water_labels_retained(self):
        original, targets = self.controls()
        original_controls(original, targets, ORIGIN)

    def test_original_wet_not_relabelled_dry(self):
        original, targets = self.controls()
        original['rows'][1]['expected']['expect'] = 'dry'
        with self.assertRaisesRegex(ValueError, 'original_controls_changed'):
            original_controls(original, targets, ORIGIN)

    def test_original_target_not_moved(self):
        original, targets = self.controls()
        targets[1] = dict(targets[1], x=targets[1]['x']+.001)
        with self.assertRaisesRegex(ValueError, 'original_controls_changed'):
            original_controls(original, targets, ORIGIN)

if __name__ == '__main__':
    unittest.main()
