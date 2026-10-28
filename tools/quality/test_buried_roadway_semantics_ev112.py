import copy,hashlib,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from buried_roadway_semantics_ev112 import observe,parse,verify_frozen,verify_package_set

class ConsumerTests(unittest.TestCase):
    def setUp(self):
        groups=['buried_changed']*4+['buried_unchanged']*4+['exposed_unchanged']*8
        self.points=[dict(id=i,group=g,x=1.,z=2.,ground=10.,bed=9.8 if g.startswith('buried') else 10.2) for i,g in enumerate(groups)]
        self.rows={i:dict(ground=10.,road=10. if i<8 else 10.2,sea=False,pond=False,depth=0.,rv=True,rv_pos=[1.,10.2,2.],rv_shapes='baltic_stream_pilot\\cs_kit_118_0000.p3d|') for i in range(16)}
    def test_ground_and_bed_are_observations(self):
        self.assertEqual(observe(self.points,self.rows)['status'],'SEMANTICS_OBSERVED_AT_SAMPLES')
        for i in range(8):self.rows[i]['road']=9.8
        q=observe(self.points,self.rows);self.assertEqual(q['observed_by_group']['buried_changed'],{'BED':4})
    def test_missing_id(self):
        del self.rows[15]
        with self.assertRaisesRegex(ValueError,'measurement_universe'):observe(self.points,self.rows)
    def test_manifest_strata(self):
        self.points[0]['group']='exposed_unchanged'
        with self.assertRaisesRegex(ValueError,'sample_strata'):observe(self.points,self.rows)
    def test_wet_dry_control(self):
        self.rows[0]['pond']=True;self.assertEqual(observe(self.points,self.rows)['status'],'FAIL_DIAGNOSTIC_CONTROLS')
    def test_ground(self):
        self.rows[0]['ground']+=.02;self.assertEqual(observe(self.points,self.rows)['status'],'FAIL_DIAGNOSTIC_CONTROLS')
    def test_exposed_roadway(self):
        self.rows[8]['road']=10.;self.assertEqual(observe(self.points,self.rows)['status'],'FAIL_DIAGNOSTIC_CONTROLS')
    def test_no_unique_prediction(self):
        self.rows[0]['road']=9.9;self.assertEqual(observe(self.points,self.rows)['status'],'INCONCLUSIVE_SEMANTICS')
    def test_duplicate_log(self):
        row='P;0;10;false;false;0;0;10;1;true;<1,10,2>;x;false;<0,0,0>;;0.75;0.75;0.75;true;1;<0,1,0>;<0,1,0>'
        with self.assertRaises(AssertionError):parse('BALTIC_VISUAL_PROBE_V3;BalticTrial\nBEGIN;2\n'+row+'\n'+row+'\nEND;2',2)
    def test_manifest_bytes(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'points.json';path.write_text('{"id":0}')
            pins={str(path):hashlib.sha256(path.read_bytes()).hexdigest()};verify_frozen(pins);path.write_text('{"id":1}')
            with self.assertRaisesRegex(ValueError,'input_drift'):verify_frozen(pins)
    def test_package_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'test.pbo';path.write_bytes(b'payload');pins={str(path):hashlib.sha256(path.read_bytes()).hexdigest()};verify_package_set(pins,pins)
            with self.assertRaisesRegex(ValueError,'package_binding'):verify_package_set(pins,{str(path):'bad'})

if __name__=='__main__':unittest.main()
