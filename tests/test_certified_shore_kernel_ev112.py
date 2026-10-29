import copy, hashlib, importlib.util, json, math, subprocess, sys, tempfile, unittest
from unittest.mock import patch
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROD=ROOT/'tools'/'quality'/'certified_shore_kernel_ev112.py'
CONS=ROOT/'tools'/'quality'/'verify_certified_shore_kernel_ev112.py'
def loadmod(name,path):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
prod=loadmod('prod_ev112',PROD)
FIXED_CONTRACT=json.loads((ROOT/'tests/fixtures/q02b1/contract-r1.json').read_bytes())
WINDOW=FIXED_CONTRACT['window_extras']; STATION=FIXED_CONTRACT['station_extras']; INTERVAL=FIXED_CONTRACT['interval_extras']

def fr(p): return Fraction(p[0],p[1])
def iv(p): return (fr(p[0]),fr(p[1]))
def pt(rec,st='A'): return (iv(rec['stations'][st]['point'][0]),iv(rec['stations'][st]['point'][1]))
class KernelTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory(); cls.root=Path(cls.tmp.name)
  cls.oracles_bytes=(ROOT/'tests/fixtures/q02b0/oracles.json').read_bytes()
  contract=copy.deepcopy(FIXED_CONTRACT)
  assert hashlib.sha256(cls.oracles_bytes).hexdigest()==contract['old_oracles']['sha256']
  cls.contract_bytes=(json.dumps(contract,indent=2,sort_keys=True)+'\n').encode(); cls.csha=hashlib.sha256(cls.contract_bytes).hexdigest()
  (cls.root/'tests'/'fixtures'/'q02b0').mkdir(parents=True); (cls.root/'tests'/'fixtures'/'q02b0'/'oracles.json').write_bytes(cls.oracles_bytes)
  cls.contract_path=cls.root/'contract.json'; cls.contract_path.write_bytes(cls.contract_bytes); cls.report_path=cls.root/'report.json'
  cls.prod_run=subprocess.run([sys.executable,str(PROD),'--contract',str(cls.contract_path),'--contract-sha',cls.csha,'--root',str(cls.root),'--output',str(cls.report_path)],text=True,capture_output=True,timeout=60)
  if cls.prod_run.returncode!=0: raise AssertionError(cls.prod_run.stderr)
  cls.report=json.loads(cls.report_path.read_text()); cls.by={r['id']:r for r in cls.report['records']}
  cls.ver_path=cls.root/'verification.json'; cls.cons_run=cls.run_consumer_path(cls.report_path,cls.ver_path)
  if cls.cons_run.returncode!=0: raise AssertionError(cls.cons_run.stderr+cls.ver_path.read_text())
 @classmethod
 def tearDownClass(cls): cls.tmp.cleanup()
 @classmethod
 def run_consumer_path(cls,report,out): return subprocess.run([sys.executable,str(CONS),'--contract',str(cls.contract_path),'--contract-sha',cls.csha,'--root',str(cls.root),'--report',str(report),'--output',str(out)],text=True,capture_output=True,timeout=60)
 def run_mutated(self,mut,tag):
  obj=copy.deepcopy(self.report); mut(obj); rp=self.root/f'mut_{tag}.json'; op=self.root/f'ver_{tag}.json'; rp.write_text(json.dumps(obj)); run=self.run_consumer_path(rp,op); self.assertNotEqual(run.returncode,0,tag); self.assertEqual(json.loads(op.read_text())['status'],'REJECTED')
 def test_cli_consumer_verified(self):
  self.assertEqual(self.cons_run.returncode,0); v=json.loads(self.ver_path.read_text()); self.assertEqual(v['status'],'VERIFIED_NUMERIC_KERNEL_ONLY'); self.assertFalse(v['calibration_ready']); self.assertEqual(v['natural_positive_count'],0); self.assertEqual(len(self.report['records']),30+len(WINDOW)+len(STATION)+len(INTERVAL))
  self.assertEqual(v['expected_resource_case_ids'],['wide_mixed_input']); self.assertFalse(v['all_records_numerically_defined']); self.assertEqual(v['record_count'],53)
 def test_old_exact_oracles(self):
  r=self.by['old:straight:6']; self.assertEqual(pt(r,'A'),((Fraction(-6),Fraction(-6)),(Fraction(0),Fraction(0)))); self.assertEqual(pt(r,'C'),((Fraction(6),Fraction(6)),(Fraction(0),Fraction(0))))
  self.assertEqual(self.by['old:square_seam:12']['stations']['A']['point'],[[[0,1],[0,1]],[[12,1],[12,1]]])
  spike=self.by['old:spike:6']; self.assertEqual(spike['state'],'UNDEFINED_ZERO_CHORD'); self.assertEqual(spike['features']['deficit']['interval'],[[1,1],[1,1]]); self.assertEqual(spike['features']['deviation']['state'],'UNDEFINED_ZERO_CHORD'); self.assertEqual(spike['features']['angle']['state'],'PENDING_CERTIFIED_ANGLE')
  self.assertEqual(self.by['old:rational_arc:96']['state'],'INSUFFICIENT_SUPPORT'); self.assertIsNone(self.by['old:rational_arc:96']['stations'])
  arc=self.by['old:rational_arc:6']; lo,hi=iv(arc['features']['chord_ac']['interval']); self.assertLessEqual(lo,hi)
 def test_sqrt2_witness_inequalities(self):
  rec=self.by['sqrt2_diamond']; entries=[e for e in rec['transcript'] if e['op']=='sqrt_interval' and e['input']==[[2,1],[2,1]]]; self.assertTrue(entries); e=entries[0]; wlo=e['witness_lo']; whi=e['witness_hi']; N=2*(1<<96)
  self.assertTrue(wlo*wlo<=N<(wlo+1)*(wlo+1)); self.assertTrue((whi-1)*(whi-1)<N<=whi*whi); self.assertNotEqual(wlo,whi)
  lo,hi=iv(rec['features']['chord_ac']['interval']); self.assertTrue(lo*lo<=2<=hi*hi)
 def test_window_states_threshold_and_resource(self):
  for e in WINDOW: self.assertEqual(self.by[e['id']]['state'],e['expected'],e['id'])
  self.assertEqual(self.by['threshold_equal']['state'],'SUPPORT_UNCERTAIN'); self.assertEqual(self.by['tiny_positive']['state'],'DEGENERATE')
 def test_station_states(self):
  for e in STATION: self.assertEqual(self.by[e['id']]['state'],e['expected'],e['id'])
  self.assertEqual(self.by['open_final_exact']['station']['t'],[[1,1],[1,1]]); self.assertEqual(self.by['closed_exact_end']['station']['segment'],0); self.assertEqual(self.by['zero']['station']['segment'],0)
 def test_interval_extras_and_zero_division(self):
  for e in INTERVAL: self.assertEqual(self.by[e['id']]['state'],e['expected'],e['id'])
  self.assertEqual(self.by['square_spanning_zero']['result_interval'],[[0,1],[9,1]]); self.assertEqual(self.by['near_zero_positive']['result_interval'],[[549755813888,1],[1099511627776,1]])
  b=prod.new_budget(); st,res=prod.eval_interval_op(b,None,'divide',(Fraction(1),Fraction(1)),(Fraction(0),Fraction(0))); self.assertEqual(st,'UNDEFINED_ZERO_CHORD'); self.assertIsNone(res)
  b=prod.new_budget(); st,res=prod.eval_interval_op(b,None,'sqrt',(Fraction(0),Fraction(2))); self.assertEqual(st,'DEFINED'); self.assertTrue(res[0]==0 and res[1]>Fraction(7,5))
 def test_transformations_at_anchors(self):
  base=[[-120,0],[0,0],[120,0]]
  def point_of(rec,st): return pt(rec,st)
  moved=prod.compute_window_case([[x+10,z-7] for x,z in base],False,1,6); self.assertEqual(point_of(moved,'A'),((Fraction(4),Fraction(4)),(Fraction(-7),Fraction(-7))))
  rot=prod.compute_window_case([[-z,x] for x,z in base],False,1,6); self.assertEqual(point_of(rot,'A'),((Fraction(0),Fraction(0)),(Fraction(-6),Fraction(-6)))); self.assertEqual(point_of(rot,'C'),((Fraction(0),Fraction(0)),(Fraction(6),Fraction(6))))
  rev=prod.compute_window_case(list(reversed(base)),False,1,6); self.assertEqual(point_of(rev,'A'),((Fraction(6),Fraction(6)),(Fraction(0),Fraction(0))))
  sub=prod.compute_window_case([[-120,0],[-60,0],[0,0],[60,0],[120,0]],False,2,6); self.assertEqual(point_of(sub,'A'),((Fraction(-6),Fraction(-6)),(Fraction(0),Fraction(0))))
 def test_wrong_pin_and_exclusive_output(self):
  out=self.root/'nope.json'; run=subprocess.run([sys.executable,str(PROD),'--contract',str(self.contract_path),'--contract-sha','0'*64,'--root',str(self.root),'--output',str(out)],text=True,capture_output=True); self.assertNotEqual(run.returncode,0); self.assertFalse(out.exists())
  run2=subprocess.run([sys.executable,str(PROD),'--contract',str(self.contract_path),'--contract-sha',self.csha,'--root',str(self.root),'--output',str(self.report_path)],text=True,capture_output=True); self.assertNotEqual(run2.returncode,0)
 def test_mutators(self):
  def find_sqrt(obj):
   e=[x for x in obj['records'][30]['transcript'] if x['op']=='sqrt_interval'][0]; return e
  cases={}
  cases['jplus']=lambda o: find_sqrt(o).__setitem__('witness_lo',find_sqrt(o)['witness_lo']+1)
  cases['jminus']=lambda o: find_sqrt(o).__setitem__('witness_lo',find_sqrt(o)['witness_lo']-1)
  cases['trim']=lambda o: o['records'][30]['stations']['A']['point'][0][1].__setitem__(0,o['records'][30]['stations']['A']['point'][0][1][0]-1)
  cases['dropwit']=lambda o: find_sqrt(o).pop('witness_hi')
  cases['wrongseg']=lambda o: o['records'][30]['stations']['A'].__setitem__('segment',o['records'][30]['stations']['A']['segment']+1)
  cases['wrongt']=lambda o: o['records'][30]['stations']['A']['t'][0].__setitem__(0,o['records'][30]['stations']['A']['t'][0][0]+1)
  cases['boundary']=lambda o: [r for r in o['records'] if r['id']=='irrational_boundary_lo'][0].__setitem__('state','DEFINED')
  cases['units']=lambda o: [r for r in o['records'] if r['id']=='sqrt2_diamond'][0]['features']['cross'].__setitem__('unit','m')
  cases['scale']=lambda o: [r for r in o['records'] if r['id']=='sqrt2_diamond'][0]['features']['cross']['interval'][0].__setitem__(0,[r for r in o['records'] if r['id']=='sqrt2_diamond'][0]['features']['cross']['interval'][0][0]*3)
  cases['duprec']=lambda o: o['records'].append(copy.deepcopy(o['records'][0]))
  cases['revrec']=lambda o: o['records'].reverse()
  cases['claim']=lambda o: o.__setitem__('calibration_ready',True)
  cases['pinm']=lambda o: o.__setitem__('contract_sha256','0'*64)
  cases['threshm']=lambda o: o['threshold'].__setitem__(0,o['threshold'][0]+1)
  cases['humanm']=lambda o: o['human_cases'][0].__setitem__('state','RESOLVED')
  cases['anglem']=lambda o: [r for r in o['records'] if r['id']=='sqrt2_diamond'][0]['features']['angle'].__setitem__('state','DEFINED')
  cases['resultm']=lambda o: [r for r in o['records'] if r['id']=='square_spanning_zero'][0]['result_interval'][1].__setitem__(0,10)
  cases['stationm']=lambda o: [r for r in o['records'] if r['id']=='open_final_exact'][0]['station']['t'][0].__setitem__(0,2)
  for tag,mut in cases.items(): self.run_mutated(mut,tag)
 def test_cli_roundtrip_fresh(self):
  rp=self.root/'report_rt.json'; op=self.root/'verification_rt.json'
  run=subprocess.run([sys.executable,str(PROD),'--contract',str(self.contract_path),'--contract-sha',self.csha,'--root',str(self.root),'--output',str(rp)],text=True,capture_output=True,timeout=60)
  self.assertEqual(run.returncode,0,run.stderr); self.assertTrue(rp.exists())
  run2=self.run_consumer_path(rp,op); self.assertEqual(run2.returncode,0,run2.stderr)
  self.assertEqual(json.loads(op.read_text())['status'],'VERIFIED_NUMERIC_KERNEL_ONLY')
  self.assertEqual(json.loads(rp.read_text())['contract_sha256'],self.csha)
 def test_consumer_wrong_pin_and_exclusive_output(self):
  out=self.root/'ver_wrongpin.json'
  run=subprocess.run([sys.executable,str(CONS),'--contract',str(self.contract_path),'--contract-sha','0'*64,'--root',str(self.root),'--report',str(self.report_path),'--output',str(out)],text=True,capture_output=True,timeout=60)
  self.assertNotEqual(run.returncode,0); self.assertEqual(json.loads(out.read_text())['status'],'REJECTED')
  run2=self.run_consumer_path(self.report_path,self.ver_path); self.assertNotEqual(run2.returncode,0)
  self.assertEqual(json.loads(self.ver_path.read_text())['status'],'VERIFIED_NUMERIC_KERNEL_ONLY')
 def test_duplicate_key_cli_rejections(self):
  dup=self.root/'dup_contract.json'; data=b'{"a":1,"a":2}\n'; dup.write_bytes(data); out=self.root/'dup_out.json'
  run=subprocess.run([sys.executable,str(PROD),'--contract',str(dup),'--contract-sha',hashlib.sha256(data).hexdigest(),'--root',str(self.root),'--output',str(out)],text=True,capture_output=True,timeout=60)
  self.assertNotEqual(run.returncode,0); self.assertFalse(out.exists())
  drep=self.root/'dup_report.json'; drep.write_bytes(b'{"schema":"x","schema":"y"}\n'); dout=self.root/'dup_ver.json'
  run2=self.run_consumer_path(drep,dout); self.assertNotEqual(run2.returncode,0); self.assertEqual(json.loads(dout.read_text())['status'],'REJECTED')
 def test_report_header_claims_and_order(self):
  r=self.report; self.assertEqual(r['schema'],'q02b1-report.v1'); self.assertEqual(r['contract_sha256'],self.csha)
  self.assertEqual(r['oracles_sha256'],hashlib.sha256(self.oracles_bytes).hexdigest()); self.assertEqual(r['claim_scope'],'NUMERIC_KERNEL_ONLY')
  self.assertEqual(r['producer_status'],'PRODUCED_UNVERIFIED'); self.assertFalse(r['calibration_ready']); self.assertEqual(r['natural_positive_count'],0)
  self.assertEqual(r['threshold'],[3022314549036573,302231454903657293676544])
  self.assertEqual(r['human_cases'],[{'index':i,'state':'GEOMETRY_UNBOUND'} for i in range(9)])
  self.assertEqual(r['records'][0]['id'],'old:straight:6'); self.assertEqual(r['records'][30]['id'],'sqrt2_diamond')
  self.assertEqual(r['records'][38]['id'],'zero'); self.assertEqual(r['records'][48]['id'],'sqrt_interval'); self.assertEqual(r['records'][-1]['id'],'near_zero_positive')
  self.assertEqual([x['kind'] for x in r['records']].count('old'),30)
 def test_feature_units_angle_and_straight_values(self):
  f=self.by['old:straight:6']['features']
  self.assertEqual(f['cross']['interval'],[[0,1],[0,1]]); self.assertEqual(f['dot']['interval'],[[72,1],[72,1]])
  self.assertEqual(f['chord_ac']['interval'],[[12,1],[12,1]]); self.assertEqual(f['deficit']['interval'],[[0,1],[0,1]])
  self.assertEqual(f['curvature']['interval'],[[0,1],[0,1]]); self.assertEqual(f['cross']['unit'],'m^2'); self.assertEqual(f['dot']['unit'],'m^2')
  self.assertEqual(f['chord_ac']['unit'],'m'); self.assertEqual(f['deficit']['unit'],'1'); self.assertEqual(f['deviation']['unit'],'m'); self.assertEqual(f['curvature']['unit'],'1/m')
  self.assertEqual(f['angle'],{'state':'PENDING_CERTIFIED_ANGLE','interval':None,'unit':'rad','width':None})
  for rec in self.report['records']:
   if rec.get('features'):
    for k,v in rec['features'].items():
     if v['interval'] is not None: self.assertEqual(fr(v['width']),fr(v['interval'][1])-fr(v['interval'][0]),rec['id'])
 def test_proof_completeness_caps_and_comutation(self):
  def rec(o): return [x for x in o['records'] if x['id']=='sqrt2_diamond'][0]
  self.run_mutated(lambda o: rec(o).__setitem__('transcript',[]),'emptyproof')
  self.run_mutated(lambda o: rec(o).__setitem__('transcript',[e for e in rec(o)['transcript'] if e['op']!='sqrt_interval']),'droproot')
  def fake(o): rec(o)['transcript'].append({'op':'sqrt_interval','input':[[9,1],[9,1]],'output':[[3,1],[3,1]],'witness_lo':3*(1<<48),'witness_hi':3*(1<<48)})
  self.run_mutated(fake,'fakeroot')
  def comutate(o):
   r=rec(o); e=[x for x in r['transcript'] if x['op']=='sqrt_interval'][0]; e['output'][0][0]+=1; r['stations']['A']['point'][0][0][0]+=1
  self.run_mutated(comutate,'comutate')
  cons=loadmod('cons_ev112b',CONS)
  with self.assertRaises(prod.Res): prod.eval_interval_op(prod.new_budget(),None,'sqrt',(Fraction(1<<5000),Fraction(1<<5000)))
  with self.assertRaises(cons.Cap): cons.root_interval(cons.CapB(),(Fraction(1<<5000),Fraction(1<<5000)))
  with self.assertRaises(cons.Cap): cons.mul(cons.CapB(),Fraction(1<<3000),Fraction(1<<3000))
 def test_repeated_proof_not_verified(self):
  obj=copy.deepcopy(self.report); r=[x for x in obj['records'] if x['id']=='sqrt2_diamond'][0]; r['transcript']=r['transcript']*400; rp=self.root/'mut_repeatproof.json'; op=self.root/'ver_repeatproof.json'; rp.write_text(json.dumps(obj)); run=self.run_consumer_path(rp,op); self.assertNotEqual(json.loads(op.read_text())['status'],'VERIFIED_NUMERIC_KERNEL_ONLY')
 def test_actual_query_operation_cap_before_root(self):
  cons=loadmod('cap_budget_consumer',CONS)
  b=prod.new_budget(); b.ops=prod.MAXOPS
  with patch.object(prod,'isqrt',side_effect=AssertionError('root executed after exhaustion')):
   with self.assertRaises(prod.Res): prod.sqrt_witnesses(b,Fraction(2))
  c=cons.CapB(); c.n=cons.MAXOPS
  with patch.object(cons,'isqrt',side_effect=AssertionError('root executed after exhaustion')):
   with self.assertRaises(cons.Cap): cons.root_interval(c,(Fraction(2),Fraction(2)))
  obj=copy.deepcopy(self.report); r=obj['records'][30]
  cert=next(e for e in r['transcript'] if e['op']=='sqrt_interval')
  r['transcript']=[copy.deepcopy(cert) for _ in range(4000)]
  rp=self.root/'opcap_report.json'; op=self.root/'opcap_verification.json'; rp.write_text(json.dumps(obj))
  self.assertLess(rp.stat().st_size,16*1024*1024)
  self.assertNotEqual(self.run_consumer_path(rp,op).returncode,0)
  self.assertEqual(json.loads(op.read_text())['status'],'RESOURCE_INCONCLUSIVE')
 def test_closed_duplicate_station_consumer_roundtrip(self):
  c=copy.deepcopy(FIXED_CONTRACT)
  q=next(e for e in c['station_extras'] if e['id']=='closed_exact_end'); q['points'].append([0,0])
  data=json.dumps(c).encode(); cp=self.root/'duplicate_closed_contract.json'; cp.write_bytes(data); h=hashlib.sha256(data).hexdigest()
  rp=self.root/'duplicate_closed_report.json'; op=self.root/'duplicate_closed_verified.json'
  a=['--contract',str(cp),'--contract-sha',h,'--root',str(self.root)]
  run=subprocess.run([sys.executable,str(PROD),*a,'--output',str(rp)],capture_output=True,text=True,timeout=30); self.assertEqual(run.returncode,0,run.stderr)
  run=subprocess.run([sys.executable,str(CONS),*a,'--report',str(rp),'--output',str(op)],capture_output=True,text=True,timeout=30)
  self.assertEqual(run.returncode,0,op.read_text()); self.assertEqual(json.loads(op.read_text())['status'],'VERIFIED_NUMERIC_KERNEL_ONLY')
 def test_closed_duplicate_h0_and_centers(self):
  dup=prod.compute_window_case([[0,0],[10,0],[10,10],[0,10],[0,0]],True,0,1); self.assertEqual(dup['state'],'DEFINED')
  self.assertEqual(prod.compute_window_case([[0,0],[10,0],[0,0]],False,1,1)['state'],'UNDEFINED_ZERO_CHORD')
  h0=prod.compute_window_case([[-120,0],[0,0],[120,0]],False,0,Fraction(0)); self.assertIsNone(h0['stations']['A']['segment']); self.assertEqual(h0['stations']['A']['from_point'],h0['stations']['A']['to_point'])
  self.assertEqual(prod.compute_window_case([[-120,0],[0,0],[120,0]],False,-1,1)['state'],'INVALID_QUERY')
  self.assertEqual(prod.compute_window_case([[-120,0],[0,0],[120,0]],False,99,1)['state'],'INVALID_QUERY')
  self.assertEqual(prod.compute_window_case([[0,0],[10,0],[10,10],[0,10],[0,0]],True,4,1)['state'],'INVALID_QUERY')
 def test_incorrect_window_expected_rehashed_and_threshold(self):
  thr=Fraction(*FIXED_CONTRACT['threshold_binary_ratio']); self.assertEqual(thr,Fraction(3022314549036573,302231454903657293676544)); self.assertEqual(self.by['threshold_equal']['state'],'SUPPORT_UNCERTAIN')
  contract=copy.deepcopy(FIXED_CONTRACT)
  for e in contract['window_extras']:
   if e['id']=='threshold_equal': e['expected']='DEFINED'
  data=(json.dumps(contract,indent=2,sort_keys=True)+'\n').encode(); sha=hashlib.sha256(data).hexdigest(); cpath=self.root/'contract_wrongexp.json'; cpath.write_bytes(data); rp=self.root/'report_wrongexp.json'; op=self.root/'ver_wrongexp.json'
  run=subprocess.run([sys.executable,str(PROD),'--contract',str(cpath),'--contract-sha',sha,'--root',str(self.root),'--output',str(rp)],text=True,capture_output=True,timeout=60); self.assertEqual(run.returncode,0,run.stderr)
  run2=subprocess.run([sys.executable,str(CONS),'--contract',str(cpath),'--contract-sha',sha,'--root',str(self.root),'--report',str(rp),'--output',str(op)],text=True,capture_output=True,timeout=60); self.assertNotEqual(run2.returncode,0); self.assertEqual(json.loads(op.read_text())['status'],'REJECTED')
 def test_direct_kernel_edges(self):
  cons=loadmod('cons_ev112',CONS)
  with self.assertRaises(prod.Bad): prod.parse_json(b'{"a":1,"a":2}')
  with self.assertRaises(cons.Bad): cons.parse(b'{"a":1,"a":2}')
  with self.assertRaises(prod.Bad): prod.parse_json(b'{"a":NaN}')
  b=prod.new_budget(); st,res=prod.eval_interval_op(b,None,'divide',(Fraction(1),Fraction(1)),(Fraction(0),Fraction(1))); self.assertEqual(st,'UNDEFINED_CONDITIONING'); self.assertIsNone(res)
  with self.assertRaises(prod.Bad): prod.eval_interval_op(prod.new_budget(),None,'sqrt',(Fraction(-1),Fraction(1)))
  with self.assertRaises(prod.Bad): prod.eval_interval_op(prod.new_budget(),None,'bogus',(Fraction(0),Fraction(1)))
  neg=prod.compute_window_case([[-120,0],[0,0],[120,0]],False,1,Fraction(-1,1)); self.assertEqual(neg['state'],'INVALID_QUERY')
  self.assertEqual(self.by['threshold_equal']['state'],'SUPPORT_UNCERTAIN')
if __name__=='__main__': unittest.main()
