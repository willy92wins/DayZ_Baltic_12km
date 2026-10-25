#!/usr/bin/env python
"""Small independent EV90 consumer fixtures; no candidate or author import."""
from __future__ import annotations

import importlib.util
import inspect
from pathlib import Path
from types import SimpleNamespace
import unittest

import numpy as np
from shapely.geometry import Polygon

SCRIPT = Path(__file__).with_name('verify_ev90.py')
SPEC = importlib.util.spec_from_file_location('ev90_consumer_under_test', SCRIPT)
ev90 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ev90)


def violation(area=0.1, excess=0.01, face=(0, 1, 2)):
    return {'kind':'physical','cell':[5,6],'triangle':0,'object':'fixture.p3d',
            'face_indices':list(face),'area_m2':area,'max_excess_m':excess}


class Ev90ConsumerFixtures(unittest.TestCase):
    def test_inward_float32_rounding(self):
        lo = ev90.inward32_lower(1.0 + 1e-8)
        hi = ev90.inward32_upper(1.0 - 1e-8)
        self.assertGreaterEqual(lo, 1.0 + 1e-8)
        self.assertLessEqual(hi, 1.0 - 1e-8)
        self.assertEqual(ev90.inward32_lower(1.0), 1.0)
        self.assertEqual(ev90.inward32_upper(1.0), 1.0)

    def test_F_absence_classes_are_not_imputed(self):
        self.assertEqual(ev90.classify_f_triangle([1.0, 2.0, 3.0]), 'known')
        self.assertEqual(ev90.classify_f_triangle([np.nan, np.nan, np.nan]), 'all_nan')
        self.assertEqual(ev90.classify_f_triangle([np.nan, 2.0, 3.0]), 'partial')

    def test_affine_burial_certificate_requires_valid_barycentric_weights(self):
        self.assertAlmostEqual(ev90.affine_clearance([1,1,1], [2,2,2], [0.2,0.3,0.5]), 1.0)
        with self.assertRaises(ValueError):
            ev90.affine_clearance([1,1,1], [2,2,2], [-0.1,0.6,0.5])

    def test_new_consumer_calls_bind_by_keyword_and_candidate_path(self):
        inspect.signature(ev90.certify_unknown_faces).bind(
            ev=None, geom=None, bundle={}, scan={}, domain={}, candidate=None)
        inspect.signature(ev90.coverage_contract_ev90).bind(
            ev=None, ev87=None, cv=None, hb=None, hh=None, bundle={}, changed_rc=[],
            source_hashes={}, frozen_cells=set())
        inspect.signature(ev90.affected_corridor_depth_report).bind(
            ev=None, ev87=None, bundle={}, h=None, changed_rc=[])
        b=np.zeros((2,2),dtype=np.float32)
        h=np.ones((2,2),dtype=np.float32)
        empty_scan={'unknown_records':{'physical':[],'visible':[]}}
        empty_domain={'variables_set':set(),'lower':np.zeros((2,2),dtype=np.float64)}
        got=ev90.certify_unknown_faces(ev=SimpleNamespace(CORE=(0,2,0,2)),geom=SimpleNamespace(),
            bundle={'B':{'heights':b}},scan=empty_scan,domain=empty_domain,candidate=h)
        self.assertEqual(got['unresolved'],[])
        self.assertEqual(got['by_kind'],{'physical':[],'visible':[]})

    def test_inherited_face_violation_is_open_but_must_not_worsen(self):
        same = ev90.compare_face_violations({'B':[violation()], 'candidate':[violation()]})
        improved = ev90.compare_face_violations({'B':[violation()], 'candidate':[]})
        self.assertTrue(same['pass'])
        self.assertEqual(same['baseline_count'], 1)
        self.assertTrue(improved['pass'])

    def test_new_or_worsened_face_violation_fails(self):
        new = ev90.compare_face_violations({'B':[], 'candidate':[violation()]})
        worse_area = ev90.compare_face_violations({'B':[violation()], 'candidate':[violation(area=0.11)]})
        worse_excess = ev90.compare_face_violations({'B':[violation()], 'candidate':[violation(excess=0.02)]})
        self.assertFalse(new['pass'])
        self.assertFalse(worse_area['pass'])
        self.assertFalse(worse_excess['pass'])

    def test_P9_unknown_area_and_triangle_vertex_changes_fail(self):
        clean={'corridors':[{'unknown_P_area_changed_between_pair_m2':0.0,
                             'unknown_P_max_triangle_vertex_delta_m':0.0}]}
        area_change={'corridors':[{'unknown_P_area_changed_between_pair_m2':0.25,
                                   'unknown_P_max_triangle_vertex_delta_m':0.0}]}
        vertex_change={'corridors':[{'unknown_P_area_changed_between_pair_m2':0.0,
                                     'unknown_P_max_triangle_vertex_delta_m':1e-7}]}
        self.assertTrue(ev90.p9_unknown_preserved(True,clean)['pass'])
        self.assertFalse(ev90.p9_unknown_preserved(True,area_change)['pass'])
        self.assertFalse(ev90.p9_unknown_preserved(True,vertex_change)['pass'])
        self.assertFalse(ev90.p9_unknown_preserved(False,clean)['pass'])

    def test_high_face_freeze_checks_all_four_cell_corners(self):
        b=np.zeros((2048,2048),dtype=np.float32);h=b.copy()
        pre={'scan':{'above':{'physical':{(840,370)},'visible':set()}}}
        helper=ev90.load_pinned('ev90_fixture_high_freeze',ev90.EV88_PATH,ev90.PINNED[str(ev90.EV88_PATH)])
        self.assertTrue(ev90.verify_high_cells_unchanged(helper,h,b,pre)['pass'])
        h[841,371]=np.float32(0.25)
        result=ev90.verify_high_cells_unchanged(helper,h,b,pre)
        self.assertFalse(result['pass'])
        self.assertEqual(result['changed_vertices'], [[841,371]])

    def test_affected_corridor_depth_known_and_unknown_P(self):
        geom=ev90.load_pinned('ev90_fixture_geometry',ev90.EV87_PATH,ev90.PINNED[str(ev90.EV87_PATH)])
        ev=ev90.load_pinned('ev90_fixture_helpers',ev90.EV88_PATH,ev90.PINNED[str(ev90.EV88_PATH)])
        r,c=840,370
        xy=geom.cell_xy(r,c)
        feature={'type':'Feature','properties':{'river':'fixture'},
            'geometry':{'type':'Polygon','coordinates':[[xy[[0,1,3,0]].tolist()] ]}}
        # Convert points into valid GeoJSON coordinate arrays, preserving first-triangle support.
        feature['geometry']['coordinates']=[[list(map(float,pt)) for pt in xy[[0,1,3,0]]]]
        h=np.zeros((2048,2048),dtype=np.float32)
        p=np.ones((2047,2047),dtype=np.float64)
        bundle={'P':p,'corridors':{'features':[feature]}}
        got=ev90.affected_corridor_depth_report(ev,geom,bundle,h,[(r,c)])
        self.assertTrue(got['pass'])
        self.assertGreater(got['tested_known_triangles'],0)
        p[r,c]=0.5
        shallow=ev90.affected_corridor_depth_report(ev,geom,bundle,h,[(r,c)])
        self.assertFalse(shallow['pass'])
        p[r,c]=1.0
        p[r,c]=np.nan
        got_unknown=ev90.affected_corridor_depth_report(ev,geom,bundle,h,[(r,c)])
        self.assertTrue(got_unknown['pass'])  # unknown is reported separately, not called a depth pass
        self.assertGreater(got_unknown['unknown_area_in_changed_corridor_support_m2'],0.0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
