"""Independent polygon/plane tests and failure controls for deployed road overlay."""
import importlib.util,hashlib,tempfile,unittest,json
from types import SimpleNamespace
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon,LineString
P=Path(__file__).with_name('road_surface_overlay_ev112.py');s=importlib.util.spec_from_file_location('overlay',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def quad(x0=2,x1=6,z0=-2,z1=2,y=3):return np.array([[x0,y,z0],[x1,y,z0],[x1,y,z1],[x0,y,z1]],float)
def water(lo=.2,hi=.6,y=2,uncertain=False):return dict(lo=lo,hi=hi,y=[y,y],uncertain=uncertain,ref=['water'])
def bridge(lo=.2,hi=.6,y=3,uncertain=False):return dict(lo=lo,hi=hi,y=None if uncertain else [y,y],uncertain=uncertain,ref=['bridge'])


class Clipping(unittest.TestCase):
    def test_polygon_oracle_many_rotated_translated_faces(self):
        rng=np.random.default_rng(17)
        for _ in range(100):
            theta=rng.uniform(-3,3);rot=np.array([[np.cos(theta),-np.sin(theta)],[np.sin(theta),np.cos(theta)]])
            p=quad()[:,[0,2]]@rot+np.array([10000,5000]);a,b=np.array([9990,5000]),np.array([10010,5001])
            got=m.clip(a,b,m.hull(p));want=Polygon(p).intersection(LineString([a,b]))
            if want.is_empty:self.assertIsNone(got)
            else:
                self.assertAlmostEqual((got[1]-got[0])*np.linalg.norm(b-a),want.length,delta=1e-9)
                ts=(np.asarray(want.coords)-a)@(b-a)/np.dot(b-a,b-a)
                np.testing.assert_allclose(got,[ts.min(),ts.max()],atol=1e-9/np.linalg.norm(b-a),rtol=0)

    def test_small_water_between_samples(self):
        got=m.face_span([0,0],[10,0],quad(x0=2.123,x1=2.124));self.assertAlmostEqual(got['hi']-got['lo'],.0001)

    def test_tangent_and_collinear_boundary(self):
        p=np.array([[2,0],[4,2],[6,0]])
        self.assertEqual(m.clip([0,2],[10,2],m.hull(p)),(.4,.4))
        self.assertEqual(m.clip([0,0],[10,0],m.hull(p)),(.2,.6))

    def test_canonical_shared_edge_no_sliver(self):
        v=quad(x0=1234.123,x1=1248.432,z0=5321.2,z1=5338.321);a=np.array([1230.,5325.777]);b=np.array([1251.,5332.998]);cache={}
        f=m.face_span(a,b,v[[0,1,2]],cache=cache);g=m.face_span(a,b,v[[3,2,0]],cache=cache)
        spans=sorted([(f['lo'],f['hi']),(g['lo'],g['hi'])]);self.assertEqual(spans[0][1],spans[1][0])
        self.assertEqual(len(m.union(spans)),1)

    def test_real_gap_preserved(self):
        self.assertEqual(len(m.union([(0,.5),(.500000000000001,1)])),2)

    def test_vertical_segment_interval(self):
        v=np.array([[2,0,0],[6,0,0],[6,7,0],[2,7,0]])
        r=m.face_span([0,0],[10,0],v);self.assertEqual((r['lo'],r['hi']),(.2,.6));self.assertIsNone(r['y']);self.assertEqual(r['height_bounds'],[0,7]);self.assertTrue(r['uncertain'])

    def test_vertical_transverse_and_point(self):
        self.assertEqual(m.clip([4,-1],[4,1],np.array([[2,0],[6,0]])),(.5,.5))
        self.assertEqual(m.clip([0,0],[4,0],np.array([[2,0]])),(.5,.5))
        self.assertIsNone(m.clip([0,1],[4,1],np.array([[2,0]])))

    def test_analytic_height_plane(self):
        v=quad();v[:,1]=2*v[:,0]+3*v[:,2]+7;r=m.face_span([0,0],[10,0],v)
        self.assertEqual(r['y'],[11,19])

    def test_ambiguous_quad_retains_both_fans(self):
        v=quad();v[2,1]=4;r=m.face_span([0,0],[10,0],v,m.surface.AMBIGUOUS_FACE)
        self.assertTrue(r['uncertain']);self.assertIsNone(r['y']);self.assertEqual({x['fan'] for x in r['fans']},{0,1});self.assertEqual(r['height_bounds'],[3,4])

    def test_reverse_axis(self):
        p=m.hull(quad()[:,[0,2]]);a=m.clip([0,0],[10,0],p);b=m.clip([10,0],[0,0],p)
        np.testing.assert_allclose(b,[1-a[1],1-a[0]],atol=1e-15)


class Exposure(unittest.TestCase):
    def test_buried_plate_under_bank(self):
        q=water();q['height_bounds']=[2,2]
        result=m.exposure(q,[dict(lo=0,hi=1,y=[3,3],face=[0,0,0])]);self.assertTrue(all(x['exposure'].startswith('BURIED') for x in result))

    def test_crossing_terrain_inside_interval(self):
        q=water(0,1,y=2);r=m.exposure(q,[dict(lo=0,hi=1,y=[0,4],face=[0,0,0])])
        self.assertEqual([(x['lo'],x['hi']) for x in r],[(0,.5),(.5,1)]);self.assertTrue(r[0]['exposure'].startswith('EXPOSED'));self.assertTrue(r[1]['exposure'].startswith('BURIED'))

    def test_exact_contact_is_not_wet(self):
        q=water();r=m.exposure(q,[dict(lo=0,hi=1,y=[2,2],face=[0,0,0])]);self.assertTrue(r[0]['exposure'].startswith('CONTACT'))

    def test_terrain_analytic_plane_across_cells(self):
        h=np.array([[36+2*c-3*r for c in range(4)] for r in range(4)],float)
        a,b=np.array([1.,1.]),np.array([17.,16.]);parts=m.terrain_parts(a,b,h)
        for p in parts:
            for t,y in zip((p['lo'],p['hi']),p['y']):
                x,z=a+(b-a)*t;self.assertAlmostEqual(y,27+x/3+z/2,delta=1e-12)

    def test_conditional_proxy_not_certified(self):
        r=m.face_span([0,0],[10,0],quad(),m.surface.PROXY_CONDITIONAL)
        self.assertTrue(r['uncertain']);r['ref']=[1];self.assertEqual(m.overlay(r,[])[0]['status'],'INCONCLUSIVE_WATER')


class Classification(unittest.TestCase):
    def test_removed_bridge(self):self.assertEqual(m.overlay(water(),[])[0]['status'],'WET_AXIS_WITHOUT_BRIDGE_ROADWAY')
    def test_present_bridge(self):self.assertEqual(m.overlay(water(),[bridge()])[0]['status'],'ROADWAY_ABOVE_WATER')
    def test_submerged_or_level_bridge(self):
        for y in (0,2):self.assertEqual(m.overlay(water(),[bridge(y=y)])[0]['status'],'ROADWAY_AT_OR_BELOW_WATER')
    def test_unknown_bridge_prevents_absence(self):self.assertEqual(m.overlay(water(),[bridge(uncertain=True)])[0]['status'],'INCONCLUSIVE_BRIDGE_GEOMETRY')
    def test_gap_and_displacement(self):
        a,b=bridge(0,.3),bridge(.7,1);a['ref']=[1];b['ref']=[2];r=m.overlay(water(0,1),[a,b])
        self.assertEqual([x['status'] for x in r],['ROADWAY_ABOVE_WATER','WET_AXIS_WITHOUT_BRIDGE_ROADWAY','ROADWAY_ABOVE_WATER'])
        self.assertEqual((r[1]['lo'],r[1]['hi']),(.3,.7))
    def test_deck_crosses_water(self):
        b=bridge(0,1);b['y']=[1,3];r=m.overlay(water(0,1),[b]);self.assertEqual(r[0]['hi'],.5);self.assertEqual(r[1]['status'],'ROADWAY_ABOVE_WATER')
    def test_overlaid_water_layers_preserved(self):
        self.assertEqual(m.overlay(water(y=4),[bridge()])[0]['status'],'ROADWAY_AT_OR_BELOW_WATER');self.assertEqual(m.overlay(water(y=1),[bridge()])[0]['status'],'ROADWAY_ABOVE_WATER')
    def test_water_roadway_never_bridge(self):
        self.assertEqual(m.roadway_role('bridge','dz\\surfaces\\data\\roadway\\water_ext.paa'),'water_roadway')
        self.assertEqual(m.roadway_role('custom_pilot',''),'custom_pilot_roadway');self.assertEqual(m.roadway_role('bridge',''),'bridge')
    def test_rotated_bridge_geometry_changes_coverage(self):
        v=quad(x0=2,x1=8,z0=-.25,z1=.25);a=np.array([0.,0]);b=np.array([10.,0]);first=m.face_span(a,b,v)
        v[:,[0,2]]=(v[:,[0,2]]-[5,0])@np.array([[0,1],[-1,0]])+[5,0];second=m.face_span(a,b,v)
        self.assertGreater(first['hi']-first['lo'],second['hi']-second['lo'])
    def test_native_tangent_end_is_retained(self):
        c=dict(parts=[dict(lo=0,hi=1,ambiguous_water_boundary=False,numerical_incidence_ambiguity=False,faces=[dict(wet=[],roots=[],contact_interval=False,difference=[0,1],water=[.75,.75],cell=[0,0],triangle=0)])])
        r=m.native_water(c);self.assertEqual(len(r),1);self.assertEqual((r[0]['lo'],r[0]['hi']),(0,0))
    def test_reference_edge_omission_fails(self):
        with self.assertRaisesRegex(ValueError,'edge_multiset'):m.native.graph_guard(np.array([[0,0],[2,0],[4,0]]),np.array([[0,1,2],[1,2,2]]),[[0,1]])
    def test_instance_omission_fails(self):
        with self.assertRaisesRegex(ValueError,'instance_coverage'):m.surface.instance_guard(np.array([1]),np.array([0]),np.array([[1,0,0,0,1,0,0,0,1,0,0,0]]),[dict(index=0,instances=2,group='bridge')])
    def test_input_hash_fails_before_consumption(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data';p.write_bytes(b'wrong')
            with self.assertRaisesRegex(ValueError,'input_hash'):m.sealed(p,hashlib.sha256(b'right').hexdigest(),{})

    def test_intramesh_gap_is_inconclusive_without_welding(self):
        r=m.overlay(water(0,1),[bridge(0,.5),bridge(.500000000000001,1)])
        self.assertEqual(r[1]['status'],'INCONCLUSIVE_INTRAMESH_GAP');self.assertGreater(r[1]['hi']-r[1]['lo'],0)

    def test_layer_difference_keeps_buried_and_nominal_provenance(self):
        n=water();q=water(y=4);q['height_bounds']=[4,4];q['ref']=[3]
        r=m.layer_differences([n],[q]);self.assertEqual(r[0]['model_minus_native'],[2,2])


class Orchestration(unittest.TestCase):
    def fixture(self,conditional):
        v=np.array([quad(x0=1,x1=11,z0=1,z1=3,y=2),quad(x0=1,x1=11,z0=1,z1=3,y=4)])
        meta=np.array([(0,0,0,0,0,2 if conditional else 1,4,1 if conditional else 0,-1,0.),(1,1,0,0,0,0,4,0,-1,0.)],m.surface.META)
        I=[1,0,0,0,1,0,0,0,1,0,0,0]
        return dict(v=v,m=meta,ids=np.array([10,20]),mi=np.array([0,1]),poses=np.array([I,I]),catalog={0:dict(group='custom_pilot'),1:dict(group='bridge')},
                    sections={0:dict(lods=[dict(sections=[dict(texture='')])]),1:dict(lods=[dict(sections=[dict(texture='water_ext.paa')])])},h=np.full((4,4),3 if conditional else 0),plane=np.full((3,3),np.nan),
                    xy=np.array([[1,2],[6,2],[11,2],[1,14],[11,14]],float),road_rows=[(0,0,0,1,0,5),(1,0,1,2,0,5),(2,0,3,4,0,10)],coverage=dict(edges=3),contacts={})

    def run_fixture(self,conditional):
        data=self.fixture(conditional);bm,candidates,cost=m.broad_phase(data)
        self.assertEqual(cost['candidate_edges'],2);self.assertEqual(cost['bbox_pairs'],4);self.assertNotIn(2,candidates)
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);meter=SimpleNamespace(dump=lambda p,x:p.write_text(json.dumps(x,allow_nan=False),encoding='utf-8'))
            report=m.census(data,bm,candidates,p,meter);rows=json.loads((p/'contacts.json').read_text());nodes=json.loads((p/'nodes.json').read_text())
            node=next(n for n in nodes if n['node']==1)
            self.assertEqual(len(node['observations']),4);self.assertEqual({x['chain'] for x in node['observations']},{0,1})
            with np.load(p/'edge-coverage.npz') as z:self.assertEqual(len(z['rows']),3)
            return rows,report

    def test_buried_proxy_remains_inconclusive_and_nodes_not_duplicated(self):
        rows,report=self.run_fixture(True)
        self.assertTrue(any(s['exposure'].startswith('BURIED') for r in rows for s in r['surfaces'] if s['role']=='model_water'))
        self.assertEqual(set(report['finding_pieces']),{'INCONCLUSIVE_WATER'})

    def test_water_roadway_does_not_cover_exposed_water(self):
        rows,report=self.run_fixture(False);self.assertEqual(set(report['finding_pieces']),{'WET_AXIS_WITHOUT_BRIDGE_ROADWAY'})


if __name__=='__main__':unittest.main()
