import hashlib,importlib.util,json,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROD=ROOT/'tools/quality/road_scene_reference_index_ev112.py'
CONS=ROOT/'tools/quality/verify_road_scene_reference_index_ev112.py'
CLAIMS={'build_ready':False,'provider_precedence_current':'NOT_EVALUATED','material_texture_closure':'NOT_EVALUATED','pivots_width_accesses':'NOT_EVALUATED','map_repaired':False,'consumer_id_uniqueness':'INHERITED_SEALED_B3_PRODUCER_RECHECKED'}
LIMITS={'wrp_bytes':536870912,'name_bytes':4096,'references':10000,'objects':3000000,'json_total_bytes':16777216,'report_bytes':16777216,'buffer_bytes':1048576}
MAT=struct.pack('<12f',1,0,0,0,1,0,0,0,1,0,0,0)
TERM=bytes(48)+struct.pack('<II',999,0)
def _sha(b): return hashlib.sha256(b).hexdigest()
def _rec(i,name,matrix=MAT): return matrix+struct.pack('<II',i,len(name))+name
def _prefix(): return struct.pack('<4s4If',b'0WZD',1,1,2,2,6.0)+bytes(16)+bytes(2)+struct.pack('<I',0)
def _load_mod(path,name):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
class RoadB4B0Tests(unittest.TestCase):
 def _fixture(self,variant=None):
  td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); d=Path(td.name)
  recs=[(1,b'dz/a.p3d'),(2,b'DZ\\A.p3d'),(3,b'dz/b.p3d')]
  if variant=='dup_id': recs[1]=(1,recs[1][1])
  if variant=='traversal': recs[0]=(1,b'../a.p3d')
  if variant=='nonascii': recs[0]=(1,b'dz/\xff.p3d')
  if variant=='name4097': recs=[(1,b'a'*4093+b'.p3d')]
  if variant=='refs10001': recs=[(i+1,(str(i)+'.p3d').encode()) for i in range(10001)]
  source=_prefix()+b''.join(_rec(i,n) for i,n in recs)+TERM
  if variant=='truncated': source=source[:-10]
  added=[(4,b'dz/a.p3d'),(5,b'dz/c.p3d'),(6,b'dz/d.p3d')]
  cand_recs=added
  candidate=_prefix()+b''.join(_rec(i,n) for i,n in recs)+b''.join(_rec(i,n) for i,n in cand_recs)+TERM
  if variant=='candidate_omitted': candidate=source
  sp=d/'source.wrp'; cp=d/'candidate.wrp'; sp.write_bytes(source); cp.write_bytes(candidate)
  prefix_bytes=len(_prefix())+sum(len(_rec(i,n)) for i,n in recs); prefix_sha=_sha(source[:prefix_bytes])
  def wj(name,obj):
   p=d/name; data=(json.dumps(obj,sort_keys=True)+'\n').encode(); p.write_bytes(data); return p,data
  def wjl(name,rows):
   p=d/name; data=b''.join((json.dumps(r,sort_keys=True)+'\n').encode() for r in rows); p.write_bytes(data); return p,data
  objs=[{'name':n.decode(),'raw_name_hex':n.hex(),'id':i,'matrix12':[1,0,0,0,1,0,0,0,1,0,0,0]} for i,n in added]
  road_rows=[{'name':'a.p3d','sha256':'a'*64,'status':'READ_STRICT','measurement':{}},{'name':'c.p3d','sha256':'0'*64 if variant=='provider_conflict' else 'e'*64,'status':'READ_STRICT','measurement':{}},{'name':'d.p3d','sha256':'f'*64,'status':'READ_STRICT','measurement':{}}]
  entries=[{'name':'a.p3d','normalized_name':'a.p3d','category':'x','size':1,'mime':0,'sha256':'a'*64},{'name':'c.p3d','normalized_name':'c.p3d','category':'x','size':1,'mime':0,'sha256':'e'*64},{'name':'d.p3d','normalized_name':'d.p3d','category':'x','size':1,'mime':0,'sha256':'f'*64}]
  files={}
  def pin(key,p,data): files[key]={'path':str(p),'sha256':_sha(data),'bytes':len(data)}
  p,data=wj('b3_contract.json',{'schema':'x','status':'x','source_path':'x','source_sha256':_sha(source),'source_bytes':len(source),'object_count':len(recs),'max_id':max(i for i,n in recs),'prefix_bytes':prefix_bytes,'prefix_sha256':prefix_sha,'terminator_hex':TERM.hex(),'objects':objs,'pins':{}}); pin('b3_contract',p,data)
  p,data=wj('b3_report.json',{'added_count':3,'added_ids':[4,5,6],'candidate_bytes':len(candidate),'candidate_max_id':6,'candidate_object_count':len(recs)+3,'candidate_path':'x','candidate_sha256':_sha(candidate),'max_id':max(i for i,n in recs),'object_count':len(recs),'ok':True,'prefix_sha256':prefix_sha,'source_bytes':len(source),'source_sha256':_sha(source),'status':'x'}); pin('b3_report',p,data)
  models=[{'name':'dz/a.p3d','sha256':'a'*64,'package':'pkg.pbo','entry':'a.p3d'},{'name':'dz/b.p3d','sha256':'b'*64,'package':'pkg.pbo','entry':'b.p3d'}]
  p,data=wj('b2a_models.json',models); pin('b2a_models',p,data)
  p,data=wj('b2a_report.json',{'status':'x','scene_instances':len(recs),'scene_models':2,'packages':[{'path':'pkg.pbo','sha256':'c'*64,'prefix':'dz'}]}); pin('b2a_report',p,data)
  p,data=wj('b2a_config.json',{'packages':[],'package_pins':{'pkg.pbo':'c'*64}}); pin('b2a_config',p,data)
  instances={'dz/a.p3d':2,'dz/b.p3d':1}
  if variant=='counts_permuted': instances={'dz/a.p3d':1,'dz/b.p3d':2}
  if variant in ('name4097','refs10001','traversal','nonascii'): instances={}
  catalog=[{'index':0,'name':'dz/a.p3d','instances':instances.get('dz/a.p3d',0),'group':'x'},{'index':1,'name':'dz/b.p3d','instances':instances.get('dz/b.p3d',0),'group':'x'}]
  p,data=wj('catalog.json',catalog); pin('catalog',p,data)
  p,rm_data=wjl('road_models.jsonl',road_rows); pin('road_models',p,rm_data)
  p,re_data=wj('road_entries.json',entries); pin('road_entries',p,re_data)
  p,data=wj('b4a3_contract.json',{'schema':'x','sources':{'models':{'path':'x','sha256':_sha(rm_data),'size':len(rm_data)},'catalog':{'path':'x','sha256':_sha(re_data),'size':len(re_data)},'previous:assets/dz/a.p3d':{'path':'x','sha256':'a'*64,'size':1},'previous:assets/dz/c.p3d':{'path':'x','sha256':'e'*64,'size':1},'previous:assets/dz/d.p3d':{'path':'x','sha256':'f'*64,'size':1}}}); pin('b4a3_contract',p,data)
  p,data=wj('b4a3_summary.json',{'status':'x','pbo':{'path':'pkg.pbo','prefix':'dz','sha256':'c'*64}}); pin('b4a3_summary',p,data)
  expected={'object_count':len(recs),'max_id':max(i for i,n in recs),'prefix_bytes':prefix_bytes,'prefix_sha256':prefix_sha,'terminator_hex':TERM.hex(),'objects':objs,'candidate_count':len(recs)+3,'catalog_model_count':2}
  if variant=='bool': expected['object_count']=True
  contract={'schema':'road-b4b0.v1','scope':'SAVED_SCENE_REFERENCE_INDEX_ONLY','plan_sha256':'78a043c49bca893899583d023bae53083f13a7a818578f8607f46f41e23792ea','source':{'path':str(sp),'sha256':_sha(source),'bytes':len(source)},'candidate':{'path':str(cp),'sha256':_sha(candidate),'bytes':len(candidate)},'files':files,'expected':expected,'limits':dict(LIMITS),'budgets':{'author_s':240,'review_s':180,'suite_s':120,'producer_s':120,'producer_rss':1073741824,'consumer_s':60,'consumer_rss':268435456},'claims':dict(CLAIMS)}
  cpath=d/'contract.json'; cpath.write_bytes((json.dumps(contract,sort_keys=True)+'\n').encode()); return d,cpath
 def _run(self,script,contract,out,report=None):
  sha=_sha(Path(contract).read_bytes()); cmd=[sys.executable,str(script),'--contract',str(contract),'--contract-sha',sha,'--output',str(out)]
  if report is not None: cmd+=['--report',str(report)]
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=120); data=None
  if Path(out).exists(): data=json.loads(Path(out).read_text())
  return r,data
 def test_positive_producer_then_consumer(self):
  d,c=self._fixture(); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,0,r.stderr); self.assertEqual(data['status'],'SAVED_SCENE_REFERENCE_INDEX_ONLY'); rows={x['name']:x for x in data['table']}; self.assertEqual(rows['dz/a.p3d']['candidate_instances'],3); self.assertEqual(rows['dz/c.p3d']['state'],'NEW_REFERENCE_WITH_B4A3_PIN'); self.assertEqual(rows['dz/b.p3d']['source_instances'],1)
  cout=d/'consumer.json'; r2,cdata=self._run(CONS,c,cout,report=out); self.assertEqual(r2.returncode,0,r2.stderr); self.assertEqual(cdata['status'],'SAVED_SCENE_REFERENCE_INDEX_ONLY')
 def test_negative_variants_producer(self):
  for variant in ('dup_id','truncated','name4097','nonascii','traversal','refs10001','provider_conflict','counts_permuted','candidate_omitted','bool'):
   with self.subTest(variant=variant):
    d,c=self._fixture(variant); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,2); self.assertIsNotNone(data); self.assertNotEqual(data['status'],'SAVED_SCENE_REFERENCE_INDEX_ONLY')
 def test_consumer_rejects_mutated_report(self):
  d,c=self._fixture(); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,0)
  data['table'][0]['candidate_instances']=999; out.write_text(json.dumps(data))
  cout=d/'consumer.json'; r2,cdata=self._run(CONS,c,cout,report=out); self.assertEqual(r2.returncode,2); self.assertNotEqual(cdata['status'],'SAVED_SCENE_REFERENCE_INDEX_ONLY')
 def test_consumer_verified_mismatch_diagnostic(self):
  d,c=self._fixture('counts_permuted'); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,2); self.assertEqual(data['status'],'INCONCLUSIVE_REFERENCE_MISMATCH')
  cout=d/'consumer.json'; r2,cdata=self._run(CONS,c,cout,report=out); self.assertEqual(r2.returncode,2); self.assertEqual(cdata['status'],'VERIFIED_MISMATCH_DIAGNOSTIC')
 def test_stat_identity_units(self):
  prod=_load_mod(PROD,'prod_mod_for_test')
  class S:
   def __init__(self,ctime,mtime): self.st_dev=1; self.st_ino=2; self.st_size=3; self.st_mtime_ns=mtime; self.st_ctime_ns=ctime
  a=prod._statd(S(10,20)); b=prod._statd(S(99,20)); self.assertFalse(prod._same_handle_identity(a,b)); self.assertTrue(prod._same_path_identity(a,b)); b2=prod._statd(S(99,21)); self.assertFalse(prod._same_path_identity(a,b2))
if __name__=='__main__': unittest.main()
