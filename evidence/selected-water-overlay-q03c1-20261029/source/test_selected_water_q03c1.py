"""Frozen literal geometry; independent expectations, CLI and co-mutant negatives."""
from pathlib import Path
import sys,json,hashlib,unittest,tempfile,os,copy,subprocess,types
sys.path.insert(0,str(Path(__file__).parent))
import selected_water_io_q03c1 as I
import selected_water_producer_q03c1 as P
import selected_water_consumer_q03c1 as C
from fractions import Fraction as F
D=Path(__file__).parent;ORACLE=I.parse((D/'oracle.json').read_bytes());CONTRACT=I.parse((D/'contract.json').read_bytes());SHA=I.digest((D/'contract.json').read_bytes())
assert I.digest((D/'oracle.json').read_bytes())==CONTRACT['oracle']['sha256']
def bed(case):return {'key':[10,0,[0,7]],'triangle':copy.deepcopy(case['bed'])}
def target(name):return next(copy.deepcopy(c) for c in ORACLE['cases'] if c['id']==name)
def projection(r):return {'status':r['status'],'areas':r['areas'],'contact_pairs':len(r['contacts'])}
class Tests(unittest.TestCase):
 def setUp(self):self.temp=tempfile.TemporaryDirectory(dir=os.environ.get('Q03C1_TEST_ROOT'));self.root=Path(self.temp.name)
 def tearDown(self):self.temp.cleanup()
 def checkreject(self,fn,code):
  with self.assertRaises(I.Rejected) as e:fn()
  self.assertEqual(e.exception.code,code)
 def fixture(self,name='upper'):
  c=target(name);x={'bed':[bed(c)],'water':c['water']};p=self.root/'fixture.json';p.write_bytes(I.canonical(x));return p,I.digest(p.read_bytes()),x
 def command(self,script,out,fixture,sha,capture=None):
  args=[sys.executable,'-I','-X','utf8',str(D/script),'--contract',str(D/'contract.json'),'--sha',SHA,'--out',str(out),'--fixture',str(fixture),'--fixture-sha',sha]
  if capture:args+=['--capture',str(capture)]
  return subprocess.run(args,capture_output=True,timeout=20)
 def test_all_literals(self):
  for c in ORACLE['cases']:
   for fn in (P.measure,C.measure):
    with self.subTest(case=c['id'],walker=fn.__module__):self.assertEqual(projection(fn(bed(c),c['water'])),c['expected'])
 def test_areas_states_metamorphic(self):
  for name in ('interior_hole','cross','nonconvex_remainder','multilayer','seam'):
   c=target(name)
   for version in range(3):
    x=copy.deepcopy(c)
    if version==0:x['water'].reverse()
    if version==1:
     x['bed'].reverse()
     for w in x['water']:w['triangle'].reverse()
    if version==2:
     for tri in [x['bed']]+[w['triangle'] for w in x['water']]:
      for p in tri:p[0]+=64;p[1]-=8;p[2]-=32
    for fn in (P.measure,C.measure):self.assertEqual(projection(fn(bed(x),x['water'])),c['expected'])
 def test_subdivision_different_pairs_same_areas(self):
  whole=target('upper');split=target('seam')
  for fn in (P.measure,C.measure):
   a=fn(bed(whole),whole['water']);b=fn(bed(split),split['water']);self.assertEqual(a['areas'],b['areas']);self.assertNotEqual(a['pairs'],b['pairs'])
 def test_no_aabb_or_false_height_acceptance(self):
  case=target('cross');rows=[P.measure(bed(case),case['water'])]
  for variant in ('area','omit','below','duplicate','contact','key'):
   r=copy.deepcopy(rows)
   if variant=='area':r[0]['areas']=[[72,1],[0,1],[0,1]]
   if variant=='omit':r[0]['pairs']=[]
   if variant=='below':r[0]['pairs'][0]['min_W_B']=[0,1]
   if variant=='duplicate':r[0]['pairs']*=2
   if variant=='contact':r[0]['contacts']=[[55,0,[1,1]]]
   if variant=='key':r[0]['key'][1]=1
   self.checkreject(lambda:C.verify_rows(r,[bed(case)],case['water']),'REPORT')
 def test_duplicate_bed_preserves_multiplicity(self):
  c=target('upper');a=bed(c);b=bed(c);b['key'][1]=1
  rows=[P.measure(v,c['water']) for v in [a,b]];self.assertEqual(C.verify_rows(rows,[a,b],c['water'])[0],2)
  self.assertEqual(sum(I.unpack(v['areas'][0]) for v in rows),F(144))
 def test_resource_guards_before_operations(self):
  q=I.Budget({'ops':1});q.add(F(1),F(1));self.checkreject(lambda:q.mul(F(1),F(1)),'RESOURCE_INCONCLUSIVE');self.assertEqual(q.ops,1)
  q=I.Budget({'bits':8});self.checkreject(lambda:q.mul(F(255),F(255)),'RESOURCE_INCONCLUSIVE')
  q=I.Budget({'pieces':1});self.checkreject(lambda:q.reserve(2,6),'RESOURCE_INCONCLUSIVE');self.assertEqual(q.peak_pieces,0)
  q=I.Budget({'vertices':5});self.checkreject(lambda:q.reserve(1,6),'RESOURCE_INCONCLUSIVE')
  c=target('multilayer')
  for fn in (P.measure,C.measure):
   for limits in ({'ops':4},{'pieces':1},{'bits':3}):self.assertEqual(fn(bed(c),c['water'],limits)['status'],'RESOURCE_INCONCLUSIVE')
 def test_geometry_and_identity_guards(self):
  c=target('upper')
  for value in (float('nan'),float('inf'),True):
   a=copy.deepcopy(c['bed']);a[0][0]=value;self.checkreject(lambda:I.validate_face(a),'GEOMETRY')
  for opts in ({'n':4},{'flag':1},{'padding':[-0.,0.,0.]},{'padding':[1.,0.,0.]}):self.checkreject(lambda:I.validate_face(c['bed'],**opts),'GEOMETRY')
  I.validate_face(c['bed'],padding=[0.,0.,0.])
  p,sha,x=self.fixture();x['water']*=2;p.write_bytes(I.canonical(x));self.checkreject(lambda:I.fixture_data(p,I.digest(p.read_bytes())),'IDENTITY')
  self.checkreject(lambda:I.fixture_data(p,sha),'IDENTITY')
 def test_rational_schema(self):
  for r in ([True,1],[1,False],[1,0],[2,2],[0,2],[1.,1],[1,-1],[1,1,1]):self.checkreject(lambda:I.unpack(r),'REPORT')
  self.assertEqual(I.unpack([0,1]),0);self.assertEqual(I.unpack([-1,2]),F(-1,2))
 def test_prefix_truncation_gap_and_orphan(self):
  o=I.Output(self.root/'capture',33554432);o.write('header.json',{});c=target('upper');r=P.measure(bed(c),c['water']);o.terminal(0,r)
  self.assertEqual(len(I.prefix(o.path,33554432)),1)
  (o.path/'0001.json').write_bytes(b'partial');self.assertEqual(len(I.prefix(o.path,33554432)),1)
  (o.path/'0001.json').unlink();(o.path/'0002.receipt.json').write_bytes(I.canonical({'seq':2,'bytes':1,'sha256':'a'*64}));self.checkreject(lambda:I.prefix(o.path,33554432),'TERMINAL');(o.path/'0002.receipt.json').unlink()
  (o.path/'0000.json').write_bytes(b'{}');self.checkreject(lambda:I.prefix(o.path,33554432),'IDENTITY')
 def test_output_budget_and_co_mutant(self):
  o=I.Output(self.root/'cap',32);self.checkreject(lambda:o.write('x.json',{'a':'z'*100}),'OUTPUT_CAP');self.assertEqual(list(o.path.iterdir()),[])
  c=target('upper');r=P.measure(bed(c),c['water']);r['areas']=[[0,1],[0,1],[72,1]];out=I.Output(self.root/'mutated',33554432);out.write('header.json',{});out.terminal(0,r)
  rows=I.prefix(out.path,33554432);self.checkreject(lambda:C.verify_rows(rows,[bed(c)],c['water']),'REPORT')
 def test_cli_full_and_co_mutated_claim(self):
  p,sha,x=self.fixture('cross');capture=self.root/'production';out=self.root/'consumer'
  run=self.command('selected_water_producer_q03c1.py',capture,p,sha);self.assertEqual(run.returncode,0,run.stderr)
  run=self.command('selected_water_consumer_q03c1.py',out,p,sha,capture);self.assertEqual(run.returncode,0,run.stderr)
  report=I.parse((out/'consumer.json').read_bytes());self.assertEqual(report['status'],'MEASURED_SELECTED_WATER_OVERLAY_ONLY');self.assertEqual(report['verified_numeric'],1)
  h=I.parse((capture/'header.json').read_bytes());h['claims']['exposure_evaluated']=True;(capture/'header.json').write_bytes(I.canonical(h))
  run=self.command('selected_water_consumer_q03c1.py',self.root/'bad',p,sha,capture);self.assertNotEqual(run.returncode,0);self.assertIn(b'REPORT',run.stderr)
 def test_cli_partial_not_full(self):
  p,sha,x=self.fixture('water_point');capture=self.root/'production'
  run=self.command('selected_water_producer_q03c1.py',capture,p,sha);self.assertEqual(run.returncode,0,run.stderr)
  run=self.command('selected_water_consumer_q03c1.py',self.root/'consumer',p,sha,capture);self.assertEqual(run.returncode,0,run.stderr)
  report=I.parse((self.root/'consumer/consumer.json').read_bytes());self.assertEqual(report['status'],'VERIFIED_PARTIAL_OVERLAY');self.assertEqual(report['verified_numeric'],0)
  m=I.parse((capture/'manifest.json').read_bytes());m['status']='MEASURED_SELECTED_WATER_OVERLAY_ONLY';(capture/'manifest.json').write_bytes(I.canonical(m))
  run=self.command('selected_water_consumer_q03c1.py',self.root/'bad',p,sha,capture);self.assertNotEqual(run.returncode,0)
 def test_cli_source_double_transform_and_changed_epoch(self):
  p,sha,x=self.fixture();capture=self.root/'production';run=self.command('selected_water_producer_q03c1.py',capture,p,sha);self.assertEqual(run.returncode,0,run.stderr)
  x['bed'][0]['triangle'][0][1]+=1;p.write_bytes(I.canonical(x));run=self.command('selected_water_consumer_q03c1.py',self.root/'bad',p,sha,capture);self.assertNotEqual(run.returncode,0);self.assertIn(b'IDENTITY',run.stderr)
 def test_resource_record_never_accepts_full(self):
  c=target('upper');r=P.measure(bed(c),c['water'],{'ops':1});v,u,_=C.verify_rows([r],[bed(c)],c['water']);self.assertEqual((v,u),(0,1))
 def test_missing_spec_is_identity_before_archive(self):
  c={'scene':{'path':'scene','sha256':'scenehash'},'index_contract':{'path':'cc','sha256':'contract'},'index':{'path':'idx'},'index_consumer':{'path':'proof'},'epoch':{},'receipts':[],'archive_limits':{'stored':1},'pilot_count':1}
  s={'epoch':{},'pins':{},'arrays':[{'kind':'pilot','relative':'other'}]};cc={'scene':{'sha256':'scenehash'},'limits':{'stored':1}};idx={'status':'VERIFIED_SAVED_SELECTED_SURFACE_INDEX_ONLY','contract_sha256':'contract','pilots':[{'model_index':1,'archive':'missing','arraydigestmap':{}}]};proof={'status':idx['status'],'files_read':204,'contract_sha256':'contract'}
  values={'scene':s,'cc':cc,'idx':idx,'proof':proof};fake=types.SimpleNamespace(parse=I.parse,read_small=lambda path,pin:I.canonical(values[path]),Reader=lambda c:object())
  self.checkreject(lambda:I.historical(c,fake),'IDENTITY')
 def test_large_terminal_within_contract_cap(self):
  p=self.root/'large';p.mkdir();(p/'header.json').write_bytes(b'{}');v={'diagnostic':'x'*16777216};b=I.canonical(v);(p/'0000.json').write_bytes(b);(p/'0000.receipt.json').write_bytes(I.canonical({'seq':0,'bytes':len(b),'sha256':I.digest(b)}))
  # Framing must accept its declared <=32MiB budget; semantic validation remains separate.
  self.assertEqual(I.prefix(p,33554432),[v])
 def test_outer_live_polygons_reserved_before_subtraction(self):
  q=I.Budget({'pieces':8});base=[(F(0),F(0)),(F(12),F(0)),(F(0),F(12))];cut=[(F(1),F(1)),(F(3),F(1)),(F(1),F(3))]
  self.checkreject(lambda:P.subtract([base],cut,q,outer=(8,24)),'RESOURCE_INCONCLUSIVE')
if __name__=='__main__':unittest.main(verbosity=2)
