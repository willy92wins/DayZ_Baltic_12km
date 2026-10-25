"""Counterexamples from the 2026-10-24 council, independent analytic terrain."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools/terrain'),str(ROOT/'tools/water')]
import verify_roads_v30 as roads
import eval_visual_probe_v31 as probe

class RoadContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.h=np.full((2048,2048),5.)
        cls.water=np.zeros_like(cls.h,dtype=bool)
        cls.chain=np.array([[100.,100.],[120.,100.],[140.,100.],[160.,100.]])

    def evaluate(self,h=None,water=None,coverage=None):
        with patch.object(roads,'road_chains',return_value=[self.chain]):
            return roads.evaluate(self.h if h is None else h,self.water if water is None else water,coverage)

    def test_flat_pass_and_frozen_coverage(self):
        r=self.evaluate();self.assertEqual(r['status'],'PASS')
        self.assertEqual(r['samples'],23)
        self.assertEqual(self.evaluate(coverage=r['coverage_sha256'])['status'],'PASS')
        self.assertEqual(self.evaluate(coverage='0'*64)['status'],'FAIL')

    def test_no_eligible_samples_is_not_pass(self):
        r=self.evaluate(water=np.ones_like(self.water));self.assertEqual(r['samples'],0)
        self.assertEqual(r['status'],'FAIL')

    def test_nonfinite_and_shape_rejected(self):
        for value in (np.nan,np.inf,-np.inf):
            bad=self.h.copy();bad[0,0]=value
            with self.assertRaises(ValueError):self.evaluate(h=bad)
        with self.assertRaises(ValueError):self.evaluate(h=self.h[:20])
        with self.assertRaises(ValueError):self.evaluate(water=self.water.astype(float))

    def test_real_crossfall_is_rejected(self):
        r=np.arange(2048)[:,None]
        h=np.broadcast_to(5+r*.06,(2048,2048)).copy()
        self.assertGreater(self.evaluate(h=h)['cross_fail'],0)
        self.assertEqual(self.evaluate(h=h)['status'],'FAIL')

    def test_longitudinal_grade_and_chord_location(self):
        h=np.broadcast_to(np.arange(2048)*.6,(2048,2048)).copy()
        r=self.evaluate(h=h);self.assertGreater(r['grade_fail'],0);self.assertEqual(r['cross_fail'],0)
        # A roof ridge at x=132: the centre of the 6m chord is station32.
        profile=5+.02*np.abs(np.arange(2048)*6-132)
        r=self.evaluate(h=np.broadcast_to(profile,(2048,2048)).copy())
        self.assertGreater(r['chord_fail'],0);self.assertAlmostEqual(r['worst']['chord']['station_m'],32.)
        self.assertEqual(r['worst']['chord']['x'],132.)
        self.assertTrue(any(f['check']=='chord' and f['station_m']==32 for f in r['fail_list']))

class ProbeContract(unittest.TestCase):
    def fixture(self):
        p=dict(id=0,kind='control',x=100.,z=100.,ground=5.,bed=4.,expect='dry')
        r={0:dict(ground=5.,sea_refs_valid=True,sea_refs=[.75]*3,pond=False,sea=False,depth=-4.,road=5.)}
        return p,r

    def test_dry_positive(self):
        p,r=self.fixture();self.assertEqual(probe.judge([p],r,.04)['status'],'SERVER_PROBE_PASS')

    def test_ground_is_explicit_height_only_control(self):
        p,r=self.fixture();p['expect']='ground';p.pop('bed')
        # Import-height controls intentionally make no water assertion.
        r[0].update(pond=True,depth=1.)
        self.assertEqual(probe.judge([p],r,.04)['status'],'SERVER_PROBE_PASS')

    def test_unknown_missing_nonfinite_duplicate_expected(self):
        p,r=self.fixture();p['expect']='TYPO'
        with self.assertRaises(ValueError):probe.judge([p],r,.04)
        for key in ('x','z','ground','bed'):
            p,r=self.fixture();p[key]=float('nan')
            with self.assertRaises(ValueError):probe.judge([p],r,.04)
        p,r=self.fixture()
        with self.assertRaises(ValueError):probe.judge([p,p],r,.04)
        with self.assertRaises(ValueError):probe.judge([],{},.04)

if __name__=='__main__':unittest.main()
