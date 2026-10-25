"""Analytic observations and corrupt evidence for the new server gate."""
import copy,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/water'))
from eval_visual_probe_v31 import judge,parse,calibrate


class VisualProbeGate(unittest.TestCase):
    def setUp(self):
        self.points=[dict(id=i,kind='sea_reference',x=i,z=0,ground=-1,expect='sea') for i in range(3)]
        self.points.append(dict(id=3,kind='original_endpoint',site='fixture',x=3,z=0,ground=2,expect='wet',water_ext=3,bed=2.6,collision_pilot=True))
        self.points.append(dict(id=4,kind='dry_bank',site='fixture',x=4,z=0,ground=3.2,expect='dry',water_ext=None,bed=3.4,collision_pilot=True))
        shape=r'baltic_stream_pilot\fixture.p3d'
        self.log='BALTIC_VISUAL_PROBE_V3;BalticTrial\nBEGIN;5\n'
        for i in range(3):self.log+=f'P;{i};-1;true;false;0.75;1.75;-1;0;true;<0,-1,0>;;false;<0,0,0>;\n'
        self.log+=f'P;3;2;false;true;3;1;3;1;true;<3,2.6,0>;{shape}|;true;<3,2.64,0>;{shape}\n'
        self.log+=f'P;4;3.2;false;false;0.75;0;3.4;1;true;<4,3.4,0>;{shape}|;true;<4,3.44,0>;{shape}\nEND;5\n'
        lines=self.log.splitlines()
        for i in range(5):lines[i+2]+=';0.75;0.75;0.75;true;'+str(1000+i*100)+';<0,1,0>;<0,1,0>'
        self.log='\n'.join(lines)+'\n'
        self.rows=parse(self.log,5)

    def test_analytic_positive(self):self.assertEqual(judge(self.points,self.rows,.04)['status'],'SERVER_PROBE_PASS')

    def test_independent_failures(self):
        cases=[(3,'pond',False),(3,'surface',3.25),(3,'ground',2.1),(3,'road',2.6),
               (3,'rv',False),(3,'rv_shapes','other.p3d'),(3,'rv_pos',[3,2.1,0]),
               (3,'bullet',False),(3,'bullet_shape','other.p3d'),(3,'bullet_pos',[3,2.1,0]),
               (4,'pond',True),(4,'depth',.1),(0,'sea',False),(0,'sea_refs_valid',False),(0,'sea_refs',[.75,.75,.9])]
        for ident,key,value in cases:
            with self.subTest(field=key,value=value):
                rows=copy.deepcopy(self.rows);rows[ident][key]=value
                self.assertEqual(judge(self.points,rows,.04)['status'],'FAIL')

    def test_corrupt_logs(self):
        for text in [self.log.replace('END;5',''),self.log.replace('P;4;','P;3;'),self.log.replace(';true;',';maybe;',1),self.log.replace('P;3;2;','P;3;nan;'),self.log+'FAIL;AFTER\n']:
            with self.subTest(text=text[-30:]):
                with self.assertRaises((AssertionError,ValueError,IndexError)):parse(text,5)

    def test_temporal_sea_uses_each_frame(self):
        rows=copy.deepcopy(self.rows)
        for i in range(3):
            level=.55+i*.2;rows[i]['surface']=level;rows[i]['sea_refs']=[level]*3
        self.assertEqual(judge(self.points,rows,.04)['status'],'SERVER_PROBE_PASS')
        rows[1]['sea_refs']=[.55]*3
        self.assertEqual(judge(self.points,rows,.04)['status'],'FAIL')

    def test_calibration_requires_vanilla_and_empty_controls(self):
        shape=r'dz\water\streambed\streambed_leaf_long_straight.p3d'
        lines=['BALTIC_COLLISION_DIAGNOSTIC_V3']
        for i in range(3):
            lines.append(f'RAY;spawn_native;{i};0;true;<{i},100,0>;{shape}|;true;<{i},100.04,0>;{shape};<0,1,0>;<0,1,0>')
            lines.append(f'RAY;empty;{i};0;false;<0,0,0>;;false;<0,0,0>;;<0,0,0>;<0,0,0>')
        text='\n'.join(lines+['END;289'])
        self.assertAlmostEqual(calibrate(text,3)['margin_m'],.04)
        for bad in (text.replace('RAY;empty;0;0;false','RAY;empty;0;0;true'),text.replace('100.04','100.2'),text.replace(shape,'baltic_stream_pilot\\fake.p3d'),text.replace('END;289','')):
            with self.assertRaises((AssertionError,ValueError,IndexError)):calibrate(bad,3)


if __name__=='__main__':unittest.main()
