import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from dry_road_native_consumer_ev112 import evaluate
SHAPE='baltic_stream_pilot\\cs_kit_118_0000.p3d'
class NativeChannels(unittest.TestCase):
    def setUp(self):
        self.p=[dict(id=0,x=1.,z=2.,ground=10.,effective_bed=9.8,water_ext=None,roadway=10.,expect='dry',uncertain=[],bed_shapes=[SHAPE])]
        self.r={0:dict(ground=10.,road=10.,pond=False,sea=False,depth=0.,surface=0.,rv=True,rv_pos=[1.,10.,2.],rv_shapes='',bullet=True,bullet_pos=[1.,9.84,2.],bullet_normal=[0.,1.,0.],bullet_shape=SHAPE)}
        self.c=dict(margin_m=.04)
    def result(self):return evaluate(self.p,self.r,self.c)
    def test_buried_rv_is_terrain_bullet_is_bed(self):self.assertEqual(self.result()['status'],'SERVER_PROBE_PASS')
    def test_exposed_and_water_positive(self):
        self.p[0].update(ground=9.,water_ext=10.,roadway=10.,expect='wet')
        self.r[0].update(ground=9.,pond=True,depth=1.,surface=10.,rv_pos=[1.,9.8,2.],rv_shapes=SHAPE+'|')
        self.assertEqual(self.result()['status'],'SERVER_PROBE_PASS')
    def test_bad_bullet_not_compared_to_terrain(self):
        self.r[0]['bullet_pos'][1]=10.04
        self.assertIn('bullet',[x['channel'] for x in self.result()['failures']])
    def test_bad_ground_not_hidden_by_uncertainty(self):
        self.p[0]['uncertain']=['water_boundary_numeric'];self.r[0]['ground']=10.02
        self.assertEqual(self.result()['status'],'FAIL')
    def test_boundary_never_passes(self):
        self.p[0]['uncertain']=['water_boundary_numeric'];q=self.result()
        self.assertEqual(q['status'],'INCONCLUSIVE_COVERAGE');self.assertEqual(q['coverage']['ground'],{'PASS':1})
    def test_missing_id(self):
        with self.assertRaisesRegex(ValueError,'coverage_count'):evaluate(self.p,{},self.c)
    def test_wrong_id(self):
        self.r[1]=self.r.pop(0)
        with self.assertRaisesRegex(ValueError,'coverage_ids'):self.result()
    def test_unknown_boundary(self):
        self.p[0]['uncertain']=['skip_failure']
        with self.assertRaisesRegex(ValueError,'unknown_uncertainty'):self.result()
    def test_water_negative(self):
        self.r[0].update(pond=True,depth=.2);self.assertEqual(self.result()['coverage']['water'],{'FAIL':1})
    def test_roadway_negative(self):
        self.r[0]['road']=10.04;self.assertEqual(self.result()['coverage']['roadway'],{'FAIL':1})
    def test_foreign_occluder_negative(self):
        self.r[0]['rv_shapes']='other.p3d|';self.assertEqual(self.result()['coverage']['rv'],{'FAIL':1})
    def test_wrong_bullet_identity(self):
        self.r[0]['bullet_shape']='other.p3d';self.assertEqual(self.result()['coverage']['bullet'],{'FAIL':1})
    def test_ray_xz_negative(self):
        self.r[0]['bullet_pos'][0]+=.02;self.assertEqual(self.result()['coverage']['bullet'],{'FAIL':1})
    def test_calibration_negative(self):
        self.c['margin_m']=.06
        with self.assertRaisesRegex(ValueError,'vanilla_margin'):self.result()
    def test_outside_points_remain_visible(self):
        self.p[0]['uncertain']=['outside_changed_model_after_roundtrip'];q=self.result()
        self.assertEqual(q['points'],1);self.assertEqual(q['coverage']['bullet'],{'INCONCLUSIVE':1});self.assertEqual(q['coverage']['roadway'],{'INCONCLUSIVE':1})
        self.assertEqual(q['coverage']['water'],{'PASS':1})
    def test_shallow_water_uncertainty_is_separate(self):
        self.p[0]['uncertain']=['water_depth_numeric'];q=self.result()
        self.assertEqual(q['coverage']['water'],{'INCONCLUSIVE':1});self.assertEqual(q['coverage']['roadway'],{'PASS':1})
    def test_foreign_unproved_geometry(self):
        self.p[0]['uncertain']=['foreign_bed_support'];q=self.result()
        self.assertEqual(q['coverage']['bullet'],{'INCONCLUSIVE':1});self.assertEqual(q['coverage']['roadway'],{'PASS':1})
    def test_flagged_surface(self):
        self.p[0]['uncertain']=['flagged_surface'];self.assertEqual(self.result()['coverage']['rv'],{'INCONCLUSIVE':1})
    def test_bad_normal(self):
        for n in ([0.,2.,0.],[0.,-1.,0.]):
            self.r[0]['bullet_normal']=n;self.assertEqual(self.result()['coverage']['bullet'],{'FAIL':1})
    def test_nearly_coincident_identity(self):
        self.p[0]['effective_bed']=10.;self.r[0]['bullet_pos'][1]=10.04
        for identity in ('',SHAPE+'|'):
            self.r[0]['rv_shapes']=identity;self.assertEqual(self.result()['status'],'SERVER_PROBE_PASS')
    def test_wet_with_buried_bed(self):
        self.p[0].update(water_ext=10.3,roadway=10.3,expect='wet')
        self.r[0].update(road=10.3,pond=True,depth=.29,surface=10.3)
        self.assertEqual(self.result()['status'],'SERVER_PROBE_PASS')
    def test_missing_bed_identity(self):
        del self.p[0]['bed_shapes']
        with self.assertRaisesRegex(ValueError,'bed_without_identity'):self.result()

if __name__=='__main__':unittest.main()
