"""Analytic/independent polygon consumer, not the face traversal as its oracle."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
import numpy as np
from shapely.geometry import LineString, Polygon

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('contacts',HERE/'road_water_contacts_ev112.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def data(n=4):
    return np.ones((n,n)), np.full((n-1,n-1),np.nan), np.full((n-1,n-1,4),np.nan)


def oracle(a,b,h,plane,field):
    """Clip each enumerated triangle by its linear wet half-plane, then by road.

    No grid cuts, barycentric routine or producer interval logic is used here.
    Per-face results deliberately preserve both sides of a shared edge.
    """
    road=LineString([a,b]); top=(len(h)-1)*6; out={}
    corners=((0,0),(0,1),(1,0),(1,1))
    for r in range(len(h)-1):
        for c in range(len(h)-1):
            for ti,ids in enumerate(((0,1,3),(0,2,3))):
                points=[(np.array([(c+corners[i][1])*6,top-(r+corners[i][0])*6],float),
                    h[r+corners[i][0],c+corners[i][1]]-(field[r,c,i] if np.isfinite(plane[r,c]) else .75)) for i in ids]
                clipped=[]
                for (p,dp),(q,dq) in zip(points,points[1:]+points[:1]):
                    if dp < 0: clipped.append(p)
                    if (dp < 0) != (dq < 0): clipped.append(p+(q-p)*dp/(dp-dq))
                if len(clipped) < 3: continue
                poly=Polygon(clipped)
                if not poly.is_valid or poly.area==0: continue
                hit=road.intersection(poly); geometries=list(hit.geoms) if hasattr(hit,'geoms') else [hit]
                vals=[]
                for g in geometries:
                    if g.geom_type=='LineString' and g.length>0:
                        from shapely.geometry import Point
                        t=[road.project(Point(g.coords[j]))/road.length for j in (0,-1)]
                        vals.append(sorted(t))
                if vals: out[(r,c,ti)]=vals
    return out


def merged(intervals):
    out=[]
    for lo,hi in sorted(intervals):
        if out and lo <= out[-1][1]+1e-12: out[-1][1]=max(out[-1][1],hi)
        else: out.append([lo,hi])
    return out


class ContactTests(unittest.TestCase):
    def compare(self,a,b,h,plane,field):
        result=m.edge_contacts(a,b,h,plane,field); expected=oracle(a,b,h,plane,field); actual={}
        for part in result['parts']:
            for f in part['faces']:
                if f['wet']: actual.setdefault((*f['cell'],f['triangle']),[]).extend(f['wet'])
        self.assertEqual(set(actual),set(expected))
        for key in actual:
            np.testing.assert_allclose(merged(actual[key]),merged(expected[key]),rtol=0,atol=1e-9/result['length_m'])
        return result

    def test_dry(self):
        self.compare([1,8],[17,8],*data())

    def test_fully_submerged_and_partial_endpoints(self):
        h,p,f=data(); h[:]=0
        self.compare([1,8],[17,8],h,p,f)
        h[:,0]=2
        for a,b in [([1,8],[17,8]),([7,8],[17,8]),([17,8],[1,8])]: self.compare(a,b,h,p,f)

    def test_narrow_river_between_samples(self):
        h,p,f=data();h[:]=100;h[:,1]=.70
        result=self.compare([1,8],[17,8],h,p,f)
        roots=[x for part in result['parts'] for face in part['faces'] for x in face['roots']]
        self.assertEqual(len(roots),2); self.assertLess((max(roots)-min(roots))*16,.01)

    def test_native_diagonal_and_outer_edge(self):
        h,p,f=data();h[:]=0
        self.compare([1,17],[17,1],h,p,f)
        self.compare([18,1],[18,17],h,p,f)

    def test_grid_edge_preserves_both_sides(self):
        h,p,f=data();p[:,0]=2;f[:,0,:]=2
        result=self.compare([6,1],[6,17],h,p,f)
        self.assertTrue(all(x['ambiguous_water_boundary'] for x in result['parts']))
        self.assertTrue(all(len(x['faces'])==2 for x in result['parts']))

    def test_water_step_without_root(self):
        h,p,f=data();p[:,0]=2;f[:,0,:]=2
        result=self.compare([1,8],[17,8],h,p,f)
        self.assertEqual(len(result['steps']),1)
        self.assertEqual(result['steps'][0]['water'],[2.,.75])
        self.assertFalse(any(f['roots'] for part in result['parts'] for f in part['faces']))

    def test_water_step_at_graph_node_and_chain_boundary(self):
        h,p,f=data();p[:,0]=2;f[:,0,:]=2
        left=m.edge_contacts([1,8],[6,8],h,p,f);right=m.edge_contacts([6,8],[17,8],h,p,f)
        observations={}
        self.assertFalse(m.observe_node(observations,7,[6,8],0,0,left['parts'][-1],1))
        events=m.observe_node(observations,7,[6,8],1,0,right['parts'][0],0)
        self.assertEqual(len(events),1);self.assertEqual(events[0]['kind'],'WATER_STEP_AT_CELL_CUT')
        self.assertEqual([events[0]['left']['water'],events[0]['right']['water']],[2.,.75])
        self.assertFalse(m.observe_node(observations,7,[6,8],1,0,right['parts'][0],0))

    def test_exact_root_at_cell_cut_is_retained(self):
        h,p,f=data();h[:,:]=np.array([0.,.75,2.,3.])
        result=self.compare([1,8],[17,8],h,p,f)
        self.assertTrue(any(0 in face['difference'] for part in result['parts'] for face in part['faces']))
        wet=[w for part in result['parts'] for face in part['faces'] for w in face['wet']]
        self.assertAlmostEqual(m.union_length(wet)*16,5.,places=9)

    def test_root_consumer_rejects_missing_and_shifted_shore(self):
        a=np.array([0.,0.]);b=np.array([2.,0.]);parts=[dict(faces=[dict(cell=[0,0],triangle=0,roots=[.5])])]
        good={(0,0,0):np.array([[1.,-1.],[1.,1.]])}
        self.assertEqual(m.check_roots(a,b,parts,good),(1,0.))
        with self.assertRaisesRegex(ValueError,'root_face_missing'):m.check_roots(a,b,parts,{})
        with self.assertRaisesRegex(ValueError,'root_not_on_native_shore'):m.check_roots(a,b,parts,{(0,0,0):good[(0,0,0)]+[.1,0]})

    def test_union_does_not_double_count_incident_faces(self):
        self.assertEqual(m.union_length([[0,.5],[0,.5],[.5,1],[.25,.75]]),1.)

    def test_ulp_slivers_retained_and_not_definite_steps(self):
        h,p,f=data();p[:,0]=2;f[:,0,:]=2
        result=m.edge_contacts([3.7,4.3],[9.7214,8.7506],h,p,f)
        tiny=[x for x in result['parts'] if x['hi']-x['lo']<1e-14]
        self.assertTrue(tiny);self.assertTrue(all(x['numerical_incidence_ambiguity'] for x in tiny))
        self.assertTrue(result['steps'])
        self.assertTrue(all(x['kind']=='NUMERICALLY_AMBIGUOUS_WATER_STEP' for x in result['steps']))

    def test_coplanar_contact_not_wet(self):
        h,p,f=data();h[:]=.75
        r=self.compare([1,8],[17,8],h,p,f)
        self.assertTrue(all(f['contact_interval'] and not f['wet'] for part in r['parts'] for f in part['faces']))

    def test_tangent_point_not_wet(self):
        h,p,f=data();h[1,1]=.75
        r=self.compare([1,12],[17,12],h,p,f)
        self.assertTrue(any(0 in f['difference'] for part in r['parts'] for f in part['faces']))
        self.assertFalse(any(f['wet'] for part in r['parts'] for f in part['faces']))

    def test_island_and_reverse(self):
        h,p,f=data(6);h[:]=0;h[2:4,2:4]=2
        for a,b in [([1,15],[29,15]),([29,15],[1,15])]: self.compare(a,b,h,p,f)

    def test_random_faces_against_polygon_clipping(self):
        rng=np.random.default_rng(2810);h,p,f=data(7);h[:]=rng.uniform(-2,3,h.shape)
        p[1:3,2:4]=1.2;f[1:3,2:4,:]=rng.uniform(.8,1.6,(2,2,4))
        for _ in range(16): self.compare(*rng.uniform(.1,35.9,(2,2)),h,p,f)

    def test_split_edge_invariance(self):
        h,p,f=data();h[:,1]=0;a=np.array([1.,8.]);b=np.array([17.,8.]);c=a+(b-a)*.413
        full=self.compare(a,b,h,p,f);left=self.compare(a,c,h,p,f);right=self.compare(c,b,h,p,f)
        def wet_length(result):
            intervals=[w for part in result['parts'] for face in part['faces'] for w in face['wet']]
            return sum(hi-lo for lo,hi in merged(intervals))*result['length_m']
        self.assertAlmostEqual(wet_length(full),wet_length(left)+wet_length(right),places=9)

    def test_invalid_road(self):
        for a,b,reason in [([0,0],[19,0],'road_outside_grid'),([0,0],[float('nan'),0],'road_nonfinite'),([1,1],[1,1],'zero_road_edge')]:
            with self.assertRaisesRegex(ValueError,reason): m.edge_contacts(a,b,*data())

    def test_missing_partition_end_rejected(self):
        with patch.object(m,'cuts',return_value=[0.,.5,.75]):
            with self.assertRaisesRegex(ValueError,'partition_gap'):m.edge_contacts([1,8],[2,8],*data())

    def test_invalid_pond_field(self):
        h,p,f=data();p[1,1]=2
        with self.assertRaisesRegex(ValueError,'face_domain_or_nonfinite'):m.edge_contacts([7,8],[11,8],h,p,f)

    def test_graph_omission_duplicate_and_shared_node(self):
        xy=np.array([[0,0],[1,0],[1,1]],float);edges=np.array([[0,1,1],[1,2,1]],float)
        self.assertEqual(m.graph_guard(xy,edges,[[0,1],[1,2]])['edges'],2)
        for chains in ([[0,1]],[[0,1],[1,2],[1,0]]):
            with self.assertRaisesRegex(ValueError,'edge_multiset'):m.graph_guard(xy,edges,chains)
        edges[0,2]=1.1
        with self.assertRaisesRegex(ValueError,'edge_length'):m.graph_guard(xy,edges,[[0,1,2]])


if __name__=='__main__':unittest.main(verbosity=2)
