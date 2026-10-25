import sys,unittest
from pathlib import Path
import numpy as np
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'tools/terrain'),str(Path(__file__).resolve().parents[1]/'tools/water')]
from shape_repair_constraints_ev112 import road_vertex_guard
from continuous_stream_pilot_v31 import axis_for
from review_continuous_stream_pilot_v31 import require_authored_support
from repair_free_shapes_ev112 import fair_native_patch
from native_crease_constraints_ev112 import crease_constraint
import census_creases_v31 as census


class ShapeRepairConstraints(unittest.TestCase):
    def test_baseline_cannot_replace_authored_support(self):
        baseline=np.ones((8,8));authored=baseline.copy();authored[3,3]=.9
        require_authored_support(authored,baseline,authored)
        with self.assertRaisesRegex(ValueError,'authored pilot support'):require_authored_support(authored,baseline,baseline)
        merged=authored.copy();merged[6,6]=1.1
        require_authored_support(authored,baseline,merged)
        with self.assertRaises(ValueError):require_authored_support(baseline,baseline,baseline)

    def test_guard_contains_triangle_vertices_of_rotated_road_ribbons(self):
        # Consumer points between metre stations and at both ribbon borders.
        # Explicit triangle corners are recovered independently of the guard.
        for degrees in (0,13,45,79,90):
            angle=np.radians(degrees);t=np.array([np.cos(angle),np.sin(angle)])
            n=np.array([-t[1],t[0]]);a=np.array([150.,150.])-t*80;b=a+t*160
            guard=road_vertex_guard([np.array([a,b])],shape=(64,64),zmax=378.)
            q=np.array([a+t*s+n*offset for s in np.linspace(0,160,731) for offset in (-4,-1.7,0,2.3,4)])
            x=q[:,0]/6;y=(378-q[:,1])/6;c=x.astype(int);r=y.astype(int);u=x-c;v=y-r
            self.assertTrue(guard[r,c].all());self.assertTrue(guard[r+1,c+1].all())
            self.assertTrue(guard[np.where(u>=v,r,r+1),np.where(u>=v,c+1,c)].all())
            self.assertFalse(guard[0,0])
            # Counterexample: removing a required support corner is detected.
            corrupted=guard.copy();corrupted[r[20],c[20]]=False
            self.assertFalse(corrupted[r,c].all())

    def test_invalid_reference_fails_closed(self):
        for chains in ([],[np.array([[1.,1.]])],[np.array([[1.,1.],[1.,1.]])],[np.array([[0.,0.],[np.nan,1.]])]):
            with self.assertRaises(ValueError):road_vertex_guard(chains,shape=(8,8),zmax=42.)

    def test_pond_road_bridge_or_unknown_end_is_not_treated_as_natural(self):
        for end in ('pond','road','bridge',None):
            site=dict(id='fixture',mode='reach',ends=dict(up='natural',dn=end))
            with self.assertRaisesRegex(ValueError,'two natural ends'):axis_for(site,None,None,None)
        with self.assertRaises(ValueError):axis_for(dict(id='fixture',extend={'dn':{'partner':'other'}}),None,None,None)

    def test_constrained_fairing_removes_peak_without_moving_boundary(self):
        h=np.full((13,13),2.);h[6,6]=2.6;free=np.zeros(h.shape,bool);free[3:-3,3:-3]=True
        corrected,receipt=fair_native_patch(h,np.full_like(h,2.),free,h-.75,h+.75,np.full_like(h,.29999),np.full_like(h,.29999))
        self.assertTrue(receipt['success']);self.assertTrue(np.array_equal(corrected[~free],h[~free]))
        self.assertLess(corrected[6,6]-max(corrected[5,6],corrected[6,5],corrected[6,7],corrected[7,6]),.3)
        self.assertLess(float(np.max(np.abs(corrected-2))),.1)

    def test_crease_constraints_match_independent_native_edge_consumer(self):
        rng=np.random.default_rng(12);base=rng.normal(3,.3,(9,9));free=np.zeros(base.shape,bool);free[3:-3,3:-3]=True
        candidate=base.copy();candidate[free]+=rng.normal(0,.3,int(free.sum()))
        constraint=crease_constraint(base,free);before=census.angles(base);after=census.angles(candidate)
        mask=census.pair_union(*census.tri_any(free))
        expected=np.concatenate([(np.cos(np.radians(after[k]))-np.minimum(np.cos(np.radians(before[k])),np.cos(np.radians(20))))[mask[k]] for k in ('diagonal','east','south')])
        np.testing.assert_allclose(constraint['fun'](candidate[free]),expected,atol=1e-12)

    def test_crease_constraint_detects_introduced_pyramid(self):
        h=np.full((9,9),3.);free=np.zeros(h.shape,bool);free[3:-3,3:-3]=True
        constraint=crease_constraint(h,free);candidate=h.copy();candidate[4,4]+=3.
        self.assertGreaterEqual(float(constraint['fun'](h[free]).min()),0.)
        self.assertLess(float(constraint['fun'](candidate[free]).min()),0.)

    def test_crease_derivative_matches_finite_difference(self):
        rng=np.random.default_rng(12);h=rng.normal(3,.3,(9,9));free=np.zeros(h.shape,bool);free[3:-3,3:-3]=True
        constraint=crease_constraint(h,free);x=h[free]+rng.normal(0,.05,int(free.sum()))
        numeric=np.column_stack([(constraint['fun'](x+np.eye(len(x))[i]*1e-5)-constraint['fun'](x-np.eye(len(x))[i]*1e-5))/2e-5 for i in range(len(x))])
        np.testing.assert_allclose(constraint['jac'](x),numeric,atol=1e-8)


if __name__=='__main__':unittest.main()
