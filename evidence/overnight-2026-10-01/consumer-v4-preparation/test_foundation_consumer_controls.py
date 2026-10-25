"""Protocol controls, explicitly separate from runtime acceptance of the map."""
import copy,json,unittest
from verify_foundation_consumer import check_water,read_reference,check_nav

class ConsumerControls(unittest.TestCase):
    def setUp(self):
        self.ref=read_reference('W;0;6000 0 6000;-1;2;3;river\nW;1;6100 0 6100;-4;0.5;3;sea\nL;2;6200 0 6200;3;;0;island\n')
        self.manifest={'height_tolerance_m':.06,'pond_surface_tolerance_m':.04}
        self.lines=['BALTIC_FOUNDATION_WATER_V2','world=BalticTrial','SEA;0.5;1',
                    'S;0;<6000,2.25,6000>;-1;2;false;true;3',
                    'S;1;<6100,1.5,6100>;-4;0.7;true;false;4.7',
                    'S;2;<6200,4,6200>;3;0.7;false;false;-2.3',
                    'BALTIC_FOUNDATION_WATER_COMPLETE;3']
    def evaluate(self,lines):return check_water('\n'.join(lines),self.ref,self.manifest)
    def test_valid_contract(self):self.assertTrue(self.evaluate(self.lines)['status'].startswith('PASS'))
    def test_v3_explicit_dry_field(self):
        ref=read_reference('W;0;6000 0 6000;-1;2;3;river\nW;1;6100 0 6100;-4;0.5;3;sea\nL;2;6200 0 6200;3;0;0;island\n')
        manifest=dict(self.manifest,probe_version='v3')
        raw='\n'.join(self.lines).replace('WATER_V2','WATER_V3')
        self.assertTrue(check_water(raw,ref,manifest)['status'].startswith('PASS'))
    def test_malformed_rejected(self):
        variants={
            'incomplete':self.lines[:-1],
            'duplicate':self.lines[:-1]+[self.lines[3],self.lines[-1]],
            'missing':self.lines[:3]+self.lines[4:],
            'unknown_id':[v.replace('S;0;','S;99;') for v in self.lines],
            'wrong_world':[v.replace('world=BalticTrial','world=ChernarusPlus') for v in self.lines],
            'nan':[v.replace(';-1;2;',';nan;2;') for v in self.lines],
            'moved_query':[v.replace('<6000,2.25,6000>','<6001,2.25,6000>') for v in self.lines],
            'wrong_query_y':[v.replace('<6000,2.25,6000>','<6000,5,6000>') for v in self.lines],
            'wrong_sea':[v.replace('SEA;0.5;1','SEA;0.5;5') for v in self.lines],
            'wrong_final_count':[v.replace('COMPLETE;3','COMPLETE;2') for v in self.lines],
        }
        for name,lines in variants.items():
            with self.subTest(name=name),self.assertRaises(ValueError):self.evaluate(lines)
    def test_semantic_failures(self):
        changes={
            'stale_terrain':(3,'S;0;<6000,2.25,6000>;1;2;false;true;1'),
            'no_water':(3,'S;0;<6000,2.25,6000>;-1;2;false;false;3'),
            'wrong_pond_level':(3,'S;0;<6000,2.25,6000>;-1;2.1;false;true;3.1'),
            'dry_island_flood':(5,'S;2;<6200,4,6200>;3;4;false;true;1'),
            'invalid_depth_api':(3,'S;0;<6000,2.25,6000>;-1;2;false;true;0'),
            'shallow_fairway':(3,'S;0;<6000,2.25,6000>;-0.97;2;false;true;2.97'),
        }
        for name,(i,line) in changes.items():
            lines=self.lines.copy();lines[i]=line
            with self.subTest(name=name):self.assertEqual(self.evaluate(lines)['status'],'FAIL')
    def test_nav_header_and_height(self):
        ref=dict(header='BALTIC_FOUNDATION_NAV_V2',complete='BALTIC_FOUNDATION_NAV_COMPLETE',points=[dict(index=0,x=6000,z=6000,y=2,group='reserve')],routes=[dict(name='route',start=[6000,2,6000],end=[6010,2,6000])],height_tolerance_m=.06,sample_radius_m=2,path_max_length_factor=3)
        raw='BALTIC_FOUNDATION_NAV_V2\nworld=BalticTrial\nflags=1;50\nD;0;<6000,2,6000>;true;<6000,2,6000>\nQ;route;true;true;true;2\nP;route;0;<6000,2,6000>\nP;route;1;<6010,2,6000>\nQ;negative;false;false;false;0\nBALTIC_FOUNDATION_NAV_COMPLETE\n'
        self.assertTrue(check_nav(raw,ref)['status'].startswith('PASS'))
        stale=copy.deepcopy(ref);stale['points'][0]['y']=5
        self.assertEqual(check_nav(raw,stale)['status'],'FAIL')
        with self.assertRaises(ValueError):check_nav(raw.replace('NAV_V2','NAV_V1'),ref)
        self.assertEqual(check_nav(raw.replace('Q;negative;false;false;false;0','Q;negative;true;true;true;0'),ref)['status'],'FAIL')

if __name__=='__main__':unittest.main()
