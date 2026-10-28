"""Analytic planes, unchanged historical flags, and adversarial wire mutations."""
import copy,unittest
import contact_pair_b3g_ev112 as c
from test_collision_native_b2_ev112 import fixture as ray_fixture

def fixture():
    pts,orig,hits,lookup,old=ray_fixture()
    for o in orig['rows']:
        o['expected'].update(roadway=8.125,water_ext=9.,bed_shapes=['bed.p3d'],uncertain=[])
    lines=old.splitlines();lines[0]=c.HEADER;out=[]
    for line in lines:
        out.append(line)
        if line.startswith('Q;'):
            q=line.split(';');out.append(';'.join(['W',*q[1:4],q[5],q[5],'false','false','0','0','8.125','true','false','0.75','true','false','0.75','true','false','0.75']))
    return pts,orig,c.wire.csv_for(pts),'\n'.join(out)+'\n'

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.fixture=fixture()
    def consume(self,text=None,original=None,csv=None,points=None):
        p,o,cs,t=self.fixture
        return c.consume(t if text is None else text,cs if csv is None else csv,p if points is None else points,o if original is None else original)
    def mutate(self,tag,field,value):
        lines=self.fixture[3].splitlines();i=next(i for i,s in enumerate(lines) if s.startswith(tag+';'));a=lines[i].split(';');a[field]=value;lines[i]=';'.join(a);return '\n'.join(lines)+'\n'
    def test_complete_is_not_acceptance(self):
        r=self.consume();self.assertEqual(r['status'],'INCONCLUSIVE_DIAGNOSTIC');self.assertFalse(r['identity_bound']);self.assertEqual((r['rows'],r['rays'],r['water_groups']),(270,1080,270))
        self.assertEqual(r['coverage']['rv_high'],{'FAIL':30});self.assertEqual(r['coverage']['rv_low'],{'PASS':30});self.assertEqual(r['coverage']['bullet_low'],{'INCONCLUSIVE':30})
        self.assertEqual(r['coverage']['water'],{'PASS':30})
    def test_old_header_rejected(self):
        with self.assertRaises(ValueError):self.consume(self.fixture[3].replace(c.HEADER,c.wire.HEADER))
    def test_water_fields_reject(self):
        for i,v in ((1,'1'),(2,'99'),(3,'8'),(4,'-1'),(5,'NaN'),(6,'maybe'),(8,'nan'),(9,'inf'),(10,'-inf'),(12,'yes'),(19,'NaN')):
            with self.subTest(i=i),self.assertRaises(ValueError):self.consume(self.mutate('W',i,v))
    def test_missing_duplicate_and_misplaced_water(self):
        lines=self.fixture[3].splitlines();i=next(i for i,s in enumerate(lines) if s.startswith('W;'))
        for a in (lines[:i]+lines[i+1:],lines[:i]+[lines[i]]+lines[i:],lines[:i-1]+[lines[i]]+[lines[i-1]]+lines[i+1:]):
            with self.assertRaises(ValueError):self.consume('\n'.join(a)+'\n')
    def test_clock_order(self):
        for field,v in ((4,'999'),(5,'1011')):
            with self.assertRaises(ValueError):self.consume(self.mutate('W',field,v))
    def test_water_clock_does_not_change_ray_clock(self):
        r=self.consume(self.mutate('W',5,'1001'));conf=r['details'][0]['confounders']
        self.assertIn('water_clock_changed_not_motion_proof',conf);self.assertNotIn('ray_clock_changed_not_motion_proof',conf)
    def test_water_reference_flags_and_spread_preserved(self):
        self.assertIn('sea_reference_flags_invalid',self.consume(self.mutate('W',11,'false'))['details'][0]['confounders'])
        self.assertIn('sea_reference_spread',self.consume(self.mutate('W',13,'1.0'))['details'][0]['confounders'])
    def test_water_on_dry_is_fail(self):self.assertEqual(self.consume(self.mutate('W',7,'true'))['details'][0]['channels']['states']['water'],'FAIL')
    def test_wet_surface_tolerance_unchanged(self):
        o=copy.deepcopy(self.fixture[1]);o['rows'][349]['expected']['expect']='wet'
        t=self.fixture[3];t=t.replace(';false;false;0;0;8.125;', ';false;true;9.051;1;8.125;')
        self.assertEqual(self.consume(t,original=o)['details'][0]['channels']['states']['water'],'FAIL')
    def test_road_tolerance(self):self.assertEqual(self.consume(self.mutate('W',10,'8.156'))['details'][0]['channels']['states']['roadway'],'FAIL')
    def test_incomplete_contract_rejected(self):
        for key in c.REQUIRED:
            o=copy.deepcopy(self.fixture[1]);del o['rows'][349]['expected'][key]
            with self.subTest(key=key),self.assertRaises((ValueError,KeyError)):self.consume(original=o)
    def test_original_uncertainty_retained(self):
        o=copy.deepcopy(self.fixture[1]);o['rows'][349]['expected']['uncertain']=['flagged_surface']
        states=self.consume(original=o)['details'][0]['channels']['states']
        self.assertEqual(states['water'],'INCONCLUSIVE');self.assertEqual(states['rv_low'],'INCONCLUSIVE')
    def test_unknown_uncertainty_rejected(self):
        o=copy.deepcopy(self.fixture[1]);o['rows'][349]['expected']['uncertain']=['hide_fail']
        with self.assertRaises(ValueError):self.consume(original=o)
    def test_offsets_have_no_inherited_oracle(self):
        r=self.consume();self.assertIsNone(r['details'][1]['channels']);self.assertIsNone(r['details'][1]['original_expected'])
    def test_miss_payload_not_contact(self):
        lines=self.fixture[3].splitlines();i=next(i for i,s in enumerate(lines) if s.startswith('R;') and s.split(';')[4]=='RL')
        a=lines[i].split(';');a[5]='false';lines[i]=';'.join(a)
        self.assertEqual(self.consume()['details'][0]['channels']['states']['rv_low'],'PASS')
        d=self.consume('\n'.join(lines)+'\n')['details'][0];self.assertIsNone(d['rays']['RL']['contact_height']);self.assertEqual(d['channels']['states']['rv_low'],'FAIL');self.assertEqual(d['measured']['rays']['RL']['pos'][1],8.125)
    def test_low_origin_unchanged(self):
        with self.assertRaises(ValueError):self.consume(self.mutate('Q',10,'<8243.490234, 12, 8940>'))
    def test_xz_unchanged(self):
        with self.assertRaises(ValueError):self.consume(self.mutate('Q',7,'<8240, 8, 8940>'))
    def test_csv_change_rejected(self):
        with self.assertRaises(ValueError):self.consume(csv=self.fixture[2]+'\n')
    def test_point_label_change_rejected(self):
        p=copy.deepcopy(self.fixture[0]);p[0]['original_states']['rv']='PASS'
        with self.assertRaises(ValueError):self.consume(points=p)
    def test_duplicate_and_extra_rejected(self):
        with self.assertRaises(ValueError):self.consume(self.fixture[3]+'END;270\n')
    def test_pair_miss_does_not_make_delta(self):
        a=self.consume();b=self.consume(self.mutate('R',5,'false'));r=c.compare(a,b)
        self.assertIsNone(r['details'][0]['rays']['RH']['candidate_minus_control_y']);self.assertEqual(r['causality'],'UNPROVEN');self.assertFalse(r['identity_bound'])
    def test_pair_cannot_drop_point_or_reorder(self):
        a=self.consume();b=copy.deepcopy(a);b['details'].reverse()
        with self.assertRaises(ValueError):c.compare(a,b)
        b['details'].pop()
        with self.assertRaises(ValueError):c.compare(a,b)
    def test_pair_contract_change_rejected(self):
        a=self.consume();b=copy.deepcopy(a);b['details'][0]['original_expected']['expect']='wet'
        with self.assertRaises(ValueError):c.compare(a,b)
    def test_pair_snapshot_change_is_confounder(self):
        a=self.consume();b=copy.deepcopy(a);b['details'][0]['measured']['objects'][0]['matrix'][10]+=1
        self.assertIn('pair_snapshot_drift',c.compare(a,b)['details'][0]['confounders'])
    def test_adapter_receipts(self):
        a=self.consume()['adapter'];self.assertNotEqual(a['normalized_text_sha256'],a['adapted_sha256']);self.assertIn('exactly one W',a['transformation'])
    def test_review_original_xz_repro_already_rejected(self):
        for k in ('x','z'):
            o=copy.deepcopy(self.fixture[1]);o['rows'][349]['expected'][k]+=5
            with self.assertRaisesRegex(ValueError,'central_or_offset_changed'):self.consume(original=o)
    def test_crlf_hash_is_explicitly_normalized_text(self):
        import hashlib
        raw=self.fixture[3].replace('\n','\r\n').encode();text=raw.decode().replace('\r\n','\n');r=self.consume(text)
        self.assertNotEqual(hashlib.sha256(raw).hexdigest(),r['adapter']['normalized_text_sha256'])

if __name__=='__main__':unittest.main()
