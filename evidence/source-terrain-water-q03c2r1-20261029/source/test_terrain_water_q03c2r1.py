"""Closed external literals; two walkers, source-binding negatives and CLI co-mutants."""
from pathlib import Path
import sys,json,copy,tempfile,os,subprocess,hashlib,types
import unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).parent))
import terrain_water_io_q03c2r1 as S
import terrain_water_producer_q03c2r1 as A
import terrain_water_consumer_q03c2r1 as B
I=S.I;D=Path(__file__).parent;CONTRACT=D/'contract.json';SHA='6d449d112f975c492355b937b5fb1d80ceadf282eb595a34eb71a3f16ca7c1bf'
assert I.digest(CONTRACT.read_bytes())==SHA
contract=I.parse(CONTRACT.read_bytes());oracle=I.parse((D/'oracle.json').read_bytes());assert I.digest((D/'oracle.json').read_bytes())==contract['oracle']['sha256']=='df950382bd73af517e85a70faa1cfe499d1b5a5daccab31f09e5b38f9c02b3d5'
CASES={x['id']:x for x in oracle['cases']}
def grid(data):return S.Grid(S.np.asarray(data['heights'],dtype='<f4'),data['step'])
def both(data,limits=None):
 g=grid(data);bed=data['bed'][0];return A.measure(bed,A.P.Prepared(data['water']),g,limits),B.measure(bed,B.C.Prepared(data['water']),g,limits)
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(dir=os.environ.get('Q03C2R1_TEST_ROOT'));self.root=Path(self.tmp.name)
 def tearDown(self):self.tmp.cleanup()
 def reject(self,fn,code):
  with self.assertRaises(Exception) as e:fn()
  self.assertEqual(getattr(e.exception,'code',None),code,str(e.exception))
 def test_seventeen_external_joint_oracles(self):
  self.assertEqual(len(CASES),17)
  for case in oracle['cases']:
   with self.subTest(case=case['id']):
    a,b=both(case['data']);self.assertEqual(a['status'],'DEFINED');self.assertEqual(b['status'],'DEFINED');self.assertEqual(a['areas'],case['areas']);self.assertEqual(b['areas'],case['areas']);self.assertTrue(I.exact(S.semantic(a),S.semantic(b)))
 def test_constant_height_witnesses(self):
  for tag,delta in [('flat_0_2',1),('flat_1_2',0),('flat_2_2',-1)]:
   for out in both(CASES[tag]['data']):
    self.assertEqual(sum((I.unpack(p['area']) for p in out['parts']),S.F(0)),S.F(72))
    self.assertTrue(all(p['min_B_H']==p['max_B_H']==[delta,1] for p in out['parts']))
 def test_winding_and_water_order(self):
  data=copy.deepcopy(CASES['opposed_overlapping_waters']['data']);ref=both(data)[0];data['bed'][0]['triangle'].reverse();data['water'].reverse()
  for w in data['water']:w['triangle'].reverse()
  for out in both(data):self.assertTrue(I.exact(S.semantic(out),S.semantic(ref)))
 def test_duplicate_water_is_union(self):
  data=copy.deepcopy(CASES['opposed_overlapping_waters']['data']);dup=copy.deepcopy(data['water'][1]);dup['key']=[100,2,[0,2]];data['water'].append(dup)
  for out in both(data):self.assertEqual(out['areas'],CASES['opposed_overlapping_waters']['areas'])
 def test_subdivision_preserves_area(self):
  data=copy.deepcopy(CASES['flat_0_2']['data']);sums=[[S.F(0)]*9,[S.F(0)]*9]
  for tri in ([[0,1,0],[6,1,0],[0,1,12]],[[6,1,0],[12,1,0],[0,1,12]]):
   data['bed'][0]['triangle']=tri
   for k,out in enumerate(both(data)):
    self.assertEqual(out['status'],'DEFINED');sums[k]=[a+I.unpack(b) for a,b in zip(sums[k],out['areas'])]
  self.assertEqual(sums[0],[S.F(*x) for x in CASES['flat_0_2']['areas']]);self.assertEqual(sums[0],sums[1])
 def test_boundary_contacts_are_not_area(self):
  data=copy.deepcopy(CASES['final_corner']['data']);data['water']=[{'key':[100,0,[0,0]],'triangle':[[0,2,12],[6,2,12],[0,2,6]]}]
  for out in both(data):
   self.assertEqual(out['areas'],CASES['final_corner']['areas']);self.assertEqual(out['water_contacts'],[[100,0,[0,0]]]);self.assertTrue(out['terrain_contacts']);self.assertTrue(all(I.unpack(p['area'])>0 for p in out['parts']))
 def test_degenerate_bed_and_water(self):
  data=copy.deepcopy(CASES['flat_0_2']['data']);data['bed'][0]['triangle']=[[0,1,0],[6,1,0],[12,1,0]]
  for out in both(data):self.assertEqual(out['status'],'DEGENERATE_PROJECTION');self.assertIsNone(out['areas'])
  data=copy.deepcopy(CASES['flat_0_2']['data']);data['water']=[{'key':[100,0,[0,0]],'triangle':[[0,1,0],[6,1,0],[12,1,0]]}]
  for out in both(data):self.assertEqual(out['status'],'INCONCLUSIVE_GEOMETRY')
 def test_outside_grid_not_clamped(self):
  data=copy.deepcopy(CASES['flat_0_2']['data']);data['bed'][0]['triangle'][0][0]=-1
  for fn,prep in ((A.measure,A.P.Prepared),(B.measure,B.C.Prepared)):self.reject(lambda:fn(data['bed'][0],prep([]),grid(data)),'GEOMETRY')
 def test_nonfinite_dtype_and_step(self):
  for h,step in ((S.np.zeros((3,3),dtype='<f8'),6),(S.np.full((3,3),S.np.nan,dtype='<f4'),6),(S.np.zeros((3,3),dtype='<f4'),True)):
   self.reject(lambda:S.Grid(h,step),'GEOMETRY')
 def test_remainder_comparison_preguard(self):
  raw=(D/'correction-oracle.json').read_bytes();self.assertEqual(I.digest(raw),'185b8798c97d22df51b80153528af540378436893b87f0a2a527a7a4a814ab49');v=I.parse(raw)
  a,b=S.F(*v['a']),S.F(*v['b']);self.assertEqual(a>b,v['raw_a_gt_b']);self.assertTrue(0<=b<=a)
  self.reject(lambda:A.remainder_bounds(S.Budget({'bits':v['bits']}),S.F(0),b,a),v['expected'])
  A.remainder_bounds(S.Budget(),S.F(0),S.F(1),S.F(1))
  self.reject(lambda:A.remainder_bounds(S.Budget(),S.F(0),S.F(2),S.F(1)),'INTERNAL_ERROR')
 def test_resource_caps_no_full(self):
  for limits in ({'ops':10},{'bits':8},{'pieces':2}):
   for out in both(CASES['interior_peak']['data'],limits):self.assertEqual(out['status'],'RESOURCE_INCONCLUSIVE');self.assertIsNone(out['areas']);self.assertLessEqual(out['stats']['ops'],limits.get('ops',100000))
  data=copy.deepcopy(CASES['flat_0_2']['data']);data['heights']=[[0]*40 for _ in range(40)];data['bed'][0]['triangle']=[[0,1,0],[234,1,0],[0,1,234]]
  for out in both(data):self.assertEqual(out['status'],'RESOURCE_INCONCLUSIVE')
 def test_axis_row_and_diagonal_mutants(self):
  data=copy.deepcopy(CASES['asymmetric_z_rows']['data']);data['heights'].reverse()
  for out in both(data):self.assertNotEqual(out['areas'],CASES['asymmetric_z_rows']['areas'])
  code=(D/'terrain_water_producer_q03c2r1.py').read_text();self.assertIn('((0,1,3),(0,2,3))',code);code=code.replace('((0,1,3),(0,2,3))','((0,1,2),(1,2,3))');mut=types.ModuleType('wrong_diagonal');mut.__file__=str(D/'terrain_water_producer_q03c2r1.py');exec(compile(code,mut.__file__,'exec'),mut.__dict__)
  data=CASES['noncoplanar_diagonal']['data'];out=mut.measure(data['bed'][0],A.P.Prepared([]),grid(data));self.assertNotEqual(out['areas'],CASES['noncoplanar_diagonal']['areas']);self.reject(lambda:B.verify([out],data['bed'],[],grid(data),None),'REPORT')
 def test_semantic_mutants_and_marginal(self):
  data=CASES['opposed_slope']['data'];r=both(data)[0]
  for mutation in ('area','part','contact','bool','marginal'):
   v=copy.deepcopy(r)
   if mutation=='area':v['areas'][1]=[53,1]
   elif mutation=='part':v['parts'].pop()
   elif mutation=='contact':v['terrain_contacts'].append([99,99,0])
   elif mutation=='bool':v['key'][1]=False
   else:v['water_marginal'][0]=[0,1]
   self.reject(lambda:B.verify([v],data['bed'],data['water'],grid(data),None),'REPORT' if mutation!='bool' else 'SCHEMA')
  self.reject(lambda:S.check_marginal(r,[[0,1],[0,1],[72,1]]),'REPORT')
 def test_view_binding_and_guard_before_zip(self):
  c=copy.deepcopy(contract);proof=I.parse(I.read(c['view_consumer']['path'],c['view_consumer']));report=I.parse(I.read(c['view_report']['path'],c['view_report']));S.validate_view_binding(c,proof,report)
  for key in ('fixture','view_sha256','npy_sha256'):
   bad=copy.deepcopy(proof);bad[key]=True if key=='fixture' else '0'*64;self.reject(lambda:S.validate_view_binding(c,bad,report),'IDENTITY')
  with patch('zipfile.ZipFile',side_effect=AssertionError('ZIP must not open')) as opened:
   self.reject(lambda:S.view_input(c,str(self.root/'not-the-view.npz')),'IDENTITY');opened.assert_not_called()
 def test_real_cli_fixture_and_rehashed_wrong_report(self):
  case=CASES['opposed_overlapping_waters'];data=case['data'];fixture=self.root/'fixture.json';fixture.write_bytes(I.canonical(data));capture=self.root/'capture';proof=self.root/'proof'
  common=['--contract',str(CONTRACT),'--sha',SHA,'--fixture',str(fixture),'--fixture-sha',I.digest(fixture.read_bytes())]
  for script,extra,out in [('terrain_water_producer_q03c2r1.py',[],capture),('terrain_water_consumer_q03c2r1.py',['--capture',str(capture)],proof)]:
   p=subprocess.run([sys.executable,'-I','-X','utf8',str(D/script),*common,*extra,'--out',str(out)],capture_output=True,timeout=30);self.assertEqual(p.returncode,0,p.stderr.decode())
  result=I.parse((proof/'consumer.json').read_bytes());self.assertTrue(result['fixture']);self.assertEqual(result['verified_numeric'],1)
  payload=capture/'0000.json';v=I.parse(payload.read_bytes());v['areas'][0]=[35,1];payload.write_bytes(I.canonical(v));receipt={'seq':0,'bytes':len(payload.read_bytes()),'sha256':I.digest(payload.read_bytes())};(capture/'0000.receipt.json').write_bytes(I.canonical(receipt))
  p=subprocess.run([sys.executable,'-I','-X','utf8',str(D/'terrain_water_consumer_q03c2r1.py'),*common,'--capture',str(capture),'--out',str(self.root/'bad')],capture_output=True,timeout=30);self.assertNotEqual(p.returncode,0);self.assertEqual(json.loads(p.stderr)['code'],'REPORT')
 def test_prefix_gap_and_noncanonical_rational(self):
  cap=self.root/'gap';cap.mkdir();(cap/'0001.receipt.json').write_bytes(I.canonical({'seq':1,'bytes':1,'sha256':'0'*64}));self.reject(lambda:I.prefix(cap,33554432),'TERMINAL')
  r=both(CASES['flat_0_2']['data'])[0];r['areas'][2]=[144,2];self.reject(lambda:S.semantic(r),'REPORT')
if __name__=='__main__':unittest.main(verbosity=2)
