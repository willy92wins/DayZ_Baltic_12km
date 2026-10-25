import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import unittest

import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools/terrain'),str(ROOT/'tools/water'),str(ROOT/'tools/quality')]
from repair_free_shapes_ev112 import fair_native_patch,curvature_constraint
from shape_patterns_ev112 import rectangle_components
import census_pyramids_v31 as prominence
import census_creases_v31 as crease


class RectanglePilot(unittest.TestCase):
    def test_omitted_curvature_matches_frozen_e_solver(self):
        path=ROOT/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/hybrid-relief-20261025/replay/solver-used.py'
        self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),'821ed14a97ae2886db32c0d2cff646a0891aa10072bddda35aad5c9186741bef')
        spec=importlib.util.spec_from_file_location('frozen_e_solver',path)
        old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
        with np.load(ROOT/'tests/fixtures/hybrid-regression-cluster10.npz') as z:f={k:z[k] for k in z.files}
        before,rb=old.fair_native_patch(**f,bound_witnesses=True,preserve_satisfied_witnesses=True)
        after,ra=fair_native_patch(**f,bound_witnesses=True,preserve_satisfied_witnesses=True)
        np.testing.assert_array_equal(before,after);self.assertEqual(rb,ra)

    def fixture(self):
        p=ROOT/'tests/fixtures/rectangle-narva.npz'
        meta=json.loads(p.with_suffix('.json').read_text())
        self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),meta['fixture_sha256'])
        with np.load(p) as z:return {k:z[k] for k in z.files}

    def test_real_rectangle_removed_with_fixed_domain_and_native_guards(self):
        f=self.fixture();target=f.pop('target');lower=f.pop('curvature_lower');upper=f.pop('curvature_upper')
        base=f['base'];free=f['free']
        self.assertEqual(len(rectangle_components(base)),1)
        h,_=fair_native_patch(**f,bound_witnesses=True,preserve_satisfied_witnesses=True,curvature_bounds=(lower,upper))
        h=h.astype(np.float32).astype(float)
        self.assertEqual(rectangle_components(h),[])
        np.testing.assert_array_equal(h[~free],base[~free])
        self.assertLessEqual(abs(h-base).max(),.750002)
        for axis in (0,1):
            d=h[1:-1,1:-1]-(h[1:-1,:-2]+h[1:-1,2:])/2 if axis==0 else h[1:-1,1:-1]-(h[:-2,1:-1]+h[2:,1:-1])/2
            self.assertLessEqual(abs(d[target[1:-1,1:-1]]).max(),.3)
            self.assertTrue((d>=lower[axis,1:-1,1:-1]-2e-6).all())
            self.assertTrue((d<=upper[axis,1:-1,1:-1]+2e-6).all())
        pk,pt,*_=prominence.prominence(h)
        self.assertTrue((pk<=np.maximum(f['peak_cap'],.3)+2e-6).all())
        self.assertTrue((pt<=np.maximum(f['pit_cap'],.3)+2e-6).all())
        before,after=crease.angles(base),crease.angles(h)
        self.assertTrue(all((after[k]<=np.maximum(before[k],20)+.01).all() for k in before))

    def test_fixed_target_cannot_be_reported_as_solved(self):
        f=self.fixture()
        with self.assertRaisesRegex(ValueError,'Fixed curvature stencil'):
            curvature_constraint(f['base'],np.zeros_like(f['free']),(f['curvature_lower'],f['curvature_upper']))

    def test_fixed_centre_with_free_neighbour_is_constrained(self):
        base=np.zeros((9,9));free=np.zeros_like(base,bool);free[4,5]=True
        limits=np.full((2,9,9),10.);lower=-limits.copy();upper=limits.copy()
        lower[0,4,4]=-.1;upper[0,4,4]=.1
        con=curvature_constraint(base,free,(lower,upper))
        # The free neighbour at +1 creates a -.5 residual at fixed centre.
        value=con.A@np.array([1.])
        self.assertTrue(((value<con.lb)|(value>con.ub)).any())
        value=con.A@np.array([.1])
        self.assertTrue(((value>=con.lb)&(value<=con.ub)).all())

    def test_signed_limits_reject_reversed_large_fault(self):
        base=np.zeros((9,9));free=np.zeros_like(base,bool);free[4,4]=True
        lower=np.full((2,9,9),-10.);upper=np.full((2,9,9),10.)
        lower[0,4,4]=-.2999;upper[0,4,4]=.8
        con=curvature_constraint(base,free,(lower,upper))
        value=con.A@np.array([-.8])
        self.assertTrue((value<con.lb).any())

    def test_malformed_bounds_fail_closed(self):
        base=np.zeros((9,9));free=np.ones_like(base,bool)
        with self.assertRaisesRegex(ValueError,'shape'):
            curvature_constraint(base,free,(base,base))
        lo=np.zeros((2,9,9));hi=np.ones((2,9,9));lo[0,3,3]=np.nan
        with self.assertRaisesRegex(ValueError,'finite ordered'):
            curvature_constraint(base,free,(lo,hi))
        lo[0,3,3]=2.
        with self.assertRaisesRegex(ValueError,'finite ordered'):
            curvature_constraint(base,free,(lo,hi))


if __name__=='__main__':unittest.main()
