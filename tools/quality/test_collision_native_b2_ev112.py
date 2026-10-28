"""Independent analytic planes plus corruptions of the native B2 wire contract."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
import collision_native_b2_ev112 as b


def fixture():
    states = dict(ground='PASS',roadway='PASS',water='PASS',rv='PASS',bullet='PASS')
    original = dict(status='FAIL',points=2658,rows=[],failures=[dict(id=i) for i in range(46)]+[dict(id=349)],inconclusive=[dict(id=i) for i in range(47,68)])
    for i in range(2658):
        e = dict(id=i,x=b.f32(8240+i*.01),z=8940.,ground=8.,effective_bed=8.125,expect='dry')
        s = dict(states)
        if i == 349: s['rv'] = 'FAIL'
        original['rows'].append(dict(id=i,expected=e,states=s,measured=dict(ground=8.,rv=25.)))
    points = []
    for i in b.IDS:
        o = original['rows'][i];e=o['expected']
        for slot,(dx,dz) in enumerate(b.OFFSETS):
            x,z=b.f32(e['x']+dx),b.f32(e['z']+dz)
            points.append(dict(id=i,slot=slot,x=x,z=z,H=8.,B=8.125,low_y=10.125,
                terrain_at_offset=8.,nominal_offset=[dx,dz],effective_offset=[x-e['x'],z-e['z']],
                original_states=dict(o['states']),state='CLEAR_UNDER_FRAME_HYPOTHESES'))
    poses = [dict(id=1,model='tree.p3d',matrix=[1.,0.,0.,0.,1.,0.,0.,0.,1.,8250.,20.,8940.]),
             dict(id=2,model='bed.p3d',matrix=[1.,0.,0.,0.,1.,0.,0.,0.,1.,8250.,8.,8940.])]
    def lookup(o): return b.match_pose(o,[p for p in poses if p['model']==b.norm(o['shape'])])
    def v(seq): return '<'+', '.join(f'{x:.6f}' for x in seq)+'>'
    lines = [b.HEADER,'BEGIN;90;3','LINK;GetTransform;BEGIN','LINK;GetTransform;OK']
    hits = []
    for p in points:
        for h,inst in ((25.,1),(8.125,2)):
            hits.append(dict(id=p['id'],slot=p['slot'],height=h,instance=inst,frame='raw',face=inst,state='FACE_INTERIOR'))
    for rnd in range(3):
        for pi,p in enumerate(points):
            key = f"{rnd};{p['id']};{p['slot']}";t=1000+(rnd*90+pi)*200
            x,z=p['x'],p['z']
            lines.append(f'Q;{key};{t};{t};{t+10};{v([x,8,z])};8;{v([x,108,z])};{v([x,10.125,z])};{v([x,-2,z])};2;0;2')
            for code in b.CODES:
                high=code=='RH';height=25. if high else 8.125;obj=poses[0 if high else 1]
                component='0' if code.startswith('R') else '-1';fraction='0' if code.startswith('R') else '.5'
                lines.append(f'R;{key};{code};true;{v([x,height,z])};<0, 1, 0>;{component};{fraction};1')
                lines.append(f"H;{key};{code};0;true;{obj['model']};{v(obj['matrix'][9:])}")
            for oi,obj in enumerate(poses):
                mat=obj['matrix']
                lines.append(f"O;{key};{oi};true;{obj['model']};{v(mat[9:])};"+';'.join(v(mat[k:k+3]) for k in (0,3,6,9)))
    lines.append('END;270')
    return points,original,hits,lookup,'\n'.join(lines)+'\n'


class ContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.data=fixture()

    def consume(self,text=None,points=None,original=None,csv=None,lookup=None):
        p,o,h,l,t=self.data
        return b.consume(t if text is None else text,b.csv_for(p) if csv is None else csv,
                         p if points is None else points,o if original is None else original,h,[1,2],l if lookup is None else lookup)

    def alter(self,tag,field,value):
        lines=self.data[-1].splitlines();i=next(i for i,s in enumerate(lines) if s.startswith(tag+';'))
        a=lines[i].split(';');a[field]=value;lines[i]=';'.join(a)
        return '\n'.join(lines)+'\n'

    def test_complete_is_only_diagnostic(self):
        r=self.consume();self.assertTrue(r['contract_complete']);self.assertFalse(r['identity_bound'])
        self.assertEqual((r['rows'],r['rays']),(270,1080));self.assertEqual(r['status'],'INCONCLUSIVE_DIAGNOSTIC')
        self.assertEqual(r['original_fail_points'],47);self.assertEqual(r['details'][0]['original_states']['rv'],'FAIL')
        self.assertEqual(len(r['confounders']),270)
        self.assertEqual({v['reason'] for v in r['confounders']},{'native_bullet_layer_ordinal_unverified'})
        self.assertEqual(r['details'][0]['high_low']['RV_high_minus_low'],16.875)
        self.assertEqual(len(r['details'][0]['rays']['RH']['geometry_at_nominal_xz']),2)

    def test_wire_corruptions_fail_closed(self):
        for tag,field,value in [('Q',1,'1'),('Q',2,'9999'),('Q',3,'1'),('Q',4,'-1'),
            ('Q',5,'999'),('Q',6,'999'),('Q',7,'<8250, 8, 8940>'),('Q',8,'nan'),
            ('Q',9,'<8243.490234, 109, 8940>'),('Q',10,'<8243.490234, 11, 8940>'),
            ('Q',11,'<8243.490234, -3, 8940>'),('Q',12,'1'),('Q',13,'10001'),('Q',14,'3'),
            ('R',4,'BL'),('R',5,'1'),('R',6,'<0, Inf, 0>'),('R',8,'-2'),('R',9,'.4'),('R',10,'0'),
            ('H',4,'RL'),('H',5,'1'),('H',6,'false'),('O',4,'1'),('O',5,'false'),('O',8,'<0, nan, 0>')]:
            with self.subTest(tag=tag,field=field,value=value),self.assertRaises(ValueError): self.consume(self.alter(tag,field,value))

    def test_missing_duplicate_extra(self):
        lines=self.data[-1].splitlines()
        for tag in ('Q','R','H','O'):
            index=next(i for i,s in enumerate(lines) if s.startswith(tag+';'))
            for changed in (lines[:index]+lines[index+1:],lines[:index]+[lines[index]]+lines[index:]):
                with self.subTest(tag=tag),self.assertRaises(ValueError): self.consume('\n'.join(changed))
        for text in ('',self.data[-1].replace('LINK;GetTransform;OK\n',''),self.data[-1]+'extra\n'):
            with self.assertRaises(ValueError):self.consume(text)

    def test_reference_mutations(self):
        for key,value in [('x',1.),('slot',1),('low_y',11.),('H',9.),('B',8.5),('state','PASS'),('nominal_offset',[1.,0.])]:
            points=copy.deepcopy(self.data[0]);points[0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError): self.consume(points=points)
        points=copy.deepcopy(self.data[0]);points[0]['original_states']['rv']='PASS'
        with self.assertRaises(ValueError): self.consume(points=points)
        for key,value in [('status','PASS'),('rows',self.data[1]['rows'][:-1]),('failures',[]),('inconclusive',[])]:
            orig=copy.deepcopy(self.data[1]);orig[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):self.consume(original=orig)
        with self.assertRaises(ValueError):self.consume(csv=b.csv_for(self.data[0]).replace('10.125','11',1))

    def test_miss_keeps_raw_but_never_height(self):
        r=self.consume(self.alter('R',5,'false'))['details'][0]
        self.assertEqual(r['measured']['rays']['RH']['pos'][1],25.)
        self.assertIsNone(r['rays']['RH']['contact_height']);self.assertIsNone(r['high_low']['RV_high_minus_low'])
        self.assertEqual(r['rays']['RH']['geometry_at_nominal_xz'],[])

    def test_empty_objects_never_identifies_terrain(self):
        for y,label in ((8.,'NO_OBJECT_NEAR_SURFACE'),(8.001,'NO_OBJECT_OFF_SURFACE')):
            result=b.classify(dict(hit=True,pos=[0,y,0],objects=[]),8.)
            self.assertEqual(result['label'],label);self.assertNotIn('terrain',str(result).lower())

    def test_rv_component_minus_one_valid(self): self.assertTrue(self.consume(self.alter('R',8,'-1'))['contract_complete'])

    def test_all_hit_objects_survive(self):
        lines=self.data[-1].splitlines();index=next(i for i,s in enumerate(lines) if s.startswith('R;'))
        lines[index]=lines[index][:-1]+'2';extra=lines[index+1].replace(';RH;0;',';RH;1;')
        lines.insert(index+2,extra)
        r=self.consume('\n'.join(lines))['details'][0]['measured']['rays']
        self.assertEqual(len(r['RH']['objects']),2);self.assertEqual(len(r['RL']['objects']),1)

    def test_pose_format_drift_and_ambiguity(self):
        p=dict(id=1,matrix=[1.,0,0,0,1.,0,0,0,1.,8246.21484375,18.88936996459961,8940.923828125])
        obj=dict(valid=True,shape='tree',pos=[round(v,6) for v in p['matrix'][9:]],matrix=[round(v,6) for v in p['matrix']])
        self.assertTrue(b.match_pose(obj,[p])['matches'][0]['matrix_matches_format'])
        obj['matrix'][0]+=.001
        self.assertFalse(b.match_pose(obj,[p])['matches'][0]['matrix_matches_format'])
        self.assertEqual(b.match_pose(obj,[p,p])['state'],'AMBIGUOUS')
        self.assertEqual(b.match_pose(obj,[])['state'],'UNMATCHED')

    def test_clock_unknown_and_matrix_are_confounders(self):
        r=self.consume(self.alter('Q',5,'1001'));self.assertIn('ray_interval_clock_changed_not_motion_proof',r['details'][0]['confounders'])
        r=self.consume(self.alter('O',8,'<1.001, 0, 0>'));self.assertIn('matrix_differs_from_WRP',r['details'][0]['confounders'])
        r=self.consume(lookup=lambda o:dict(state='UNMATCHED',matches=[]));self.assertEqual(r['details'][0]['missing_candidates'],[1,2])
        self.assertEqual(r['status'],'INCONCLUSIVE_DIAGNOSTIC')

    def test_layer_representation_never_certifies_mapping(self):
        for value in (2,8,16):
            lines=self.data[-1].splitlines()
            for i,line in enumerate(lines):
                if line.startswith('Q;'):lines[i]=line.rsplit(';',1)[0]+';'+str(value)
            r=self.consume('\n'.join(lines))
            self.assertEqual(r['layer_observation']['script_representation'],value)
            self.assertEqual(len(r['confounders']),270)
            self.assertEqual({v['reason'] for v in r['confounders']},{'native_bullet_layer_ordinal_unverified'})
            self.assertEqual(r['status'],'INCONCLUSIVE_DIAGNOSTIC')
        for value in ('0','-1','16'):
            with self.subTest(value=value),self.assertRaises(ValueError):self.consume(self.alter('Q',14,value))

    def test_real_b2a_schema_keeps_all_inconclusive_records(self):
        path=Path(__file__).resolve().parents[2]/'evidence/collision-scene-b2a-20261028/hits.json'
        raw=path.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),'3a375ddd92cb08126b120455f2c9fdaae05c154f5817240973c5018f33e67146')
        hits=json.loads(raw);p,o,unused,lookup,text=self.data
        result=b.consume(text,b.csv_for(p),p,o,hits,[1,2],lookup)
        contacts=[h for r in result['details'] for h in r['rays']['RH']['geometry_at_nominal_xz']]
        self.assertEqual(len(contacts),1106*3)
        inc=[h for h in contacts if h['state']=='INCONCLUSIVE_VERTICAL_OR_DEGENERATE']
        self.assertEqual(len(inc),834*3);self.assertTrue(all(h['native_minus_geometry'] is None and 'height' not in h for h in inc))
        self.assertEqual(sum(h['native_minus_geometry'] is not None for h in contacts),272*3)
        affected={(h['id'],h['slot']) for h in hits if h['state']!='FACE_INTERIOR'}
        for row in result['details']:
            self.assertEqual('offline_geometry_ambiguous_or_degenerate' in row['confounders'],(row['id'],row['slot']) in affected)
        self.assertEqual(result['status'],'INCONCLUSIVE_DIAGNOSTIC')

    def test_invalid_geometry_records_reject(self):
        p,o,h,lookup,text=self.data
        for mutation in ('missing','nan','unknown','invented'):
            hits=copy.deepcopy(h)
            if mutation=='missing':hits[0].pop('height')
            elif mutation=='nan':hits[0]['height']=float('nan')
            elif mutation=='unknown':hits[0]['state']='UNKNOWN'
            else:hits[0]['state']='INCONCLUSIVE_VERTICAL_OR_DEGENERATE'
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):b.consume(text,b.csv_for(p),p,o,hits,[1,2],lookup)


if __name__ == '__main__': unittest.main()
