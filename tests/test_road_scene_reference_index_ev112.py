import hashlib,importlib.util,json,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PROD=ROOT/'tools/quality/road_scene_reference_index_ev112.py'
CONS=ROOT/'tools/quality/verify_road_scene_reference_index_ev112.py'
LIT=ROOT/'tests/fixtures/road_b4b0/literal.json'
LIT_SHA='83290a3a24e7bd39b8265819f9bc1d49742d1164f395e06b59a9658118bff496'
CLAIMS={'build_ready':False,'provider_precedence_current':'NOT_EVALUATED','material_texture_closure':'NOT_EVALUATED','pivots_width_accesses':'NOT_EVALUATED','map_repaired':False,'consumer_id_uniqueness':'INHERITED_SEALED_B3_PRODUCER_RECHECKED'}
LIMITS={'wrp_bytes':536870912,'name_bytes':4096,'references':10000,'objects':3000000,'json_total_bytes':16777216,'report_bytes':16777216,'buffer_bytes':1048576}
def _sha(b): return hashlib.sha256(b).hexdigest()
def _lit():
 data=LIT.read_bytes()
 if _sha(data)!=LIT_SHA: raise AssertionError('literal hash mismatch')
 return json.loads(data)
def _load_mod(path,name):
 spec=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
class RoadB4B0Tests(unittest.TestCase):
 def _fixture(self,variant=None):
  lit=_lit(); td=tempfile.TemporaryDirectory(); self.addCleanup(td.cleanup); d=Path(td.name)
  header=bytes.fromhex(lit['header_hex']); term=bytes.fromhex(lit['terminator_hex']); matb=bytes.fromhex(lit['matrix_hex'])
  recs=[(int.from_bytes(bytes.fromhex(r['id_hex']),'little'),bytes.fromhex(r['name_hex'])) for r in lit['source_records']]
  if variant=='dup_id': recs[1]=(recs[0][0],recs[1][1])
  if variant=='traversal': recs[0]=(recs[0][0],b'../a.p3d')
  if variant=='nonascii': recs[0]=(recs[0][0],b'dz/'+bytes([255])+b'.p3d')
  if variant=='alias_exterior': recs[0]=(recs[0][0],b'/dz/a.p3d/')
  if variant=='name_comutant': recs[2]=(recs[2][0],b'dz/x.p3d')
  if variant=='name4097': recs=[(1,b'a'*4093+b'.p3d')]
  if variant=='refs10001': recs=[(i+1,(str(i)+'.p3d').encode()) for i in range(10001)]
  def rec_bytes(i,n): return matb+struct.pack('<II',i,len(n))+n
  added=[(4+i,n.encode()) for i,n in enumerate(lit['added_names'])]
  source=header+b''.join(rec_bytes(i,n) for i,n in recs)+term
  prefix_bytes=len(header)+sum(len(rec_bytes(i,n)) for i,n in recs); prefix_sha=_sha(source[:prefix_bytes])
  candidate=source[:prefix_bytes]+b''.join(rec_bytes(i,n) for i,n in added)+term
  if variant=='candidate_omitted': candidate=source
  if variant=='truncated_header': source=source[:10]
  if variant=='truncated_material':
   hb=bytearray(header); hb[42:46]=struct.pack('<I',1); source=bytes(hb)+struct.pack('<I',100)+b'ab'
  if variant=='truncated_name': source=header+matb+struct.pack('<II',1,8)+b'dz'
  if variant in ('truncated','truncated_terminator'): source=source[:-10]
  if variant=='candidate_truncated_name': candidate=candidate[:prefix_bytes+56+2]
  if variant in ('truncated_header','truncated_material','truncated_name'):
   prefix_bytes=0; prefix_sha=_sha(b'')  # Bind truncation fixture to reach parser, not prior prefix-length guard.
  sp=d/'source.wrp'; cp=d/'candidate.wrp'; sp.write_bytes(source); cp.write_bytes(candidate)
  objs=[{'name':n.decode(),'raw_name_hex':n.hex(),'id':i,'matrix12':[1,0,0,0,1,0,0,0,1,0,0,0]} for i,n in added]
  road_rows=[{'name':'a.p3d','sha256':'a'*64,'status':'READ_STRICT','measurement':{}},{'name':'c.p3d','sha256':'e'*64,'status':'READ_STRICT','measurement':{}},{'name':'d.p3d','sha256':'f'*64,'status':'READ_STRICT','measurement':{}}]
  entries=[{'name':'a.p3d','normalized_name':'a.p3d','category':'x','size':1,'mime':0,'sha256':'a'*64},{'name':'c.p3d','normalized_name':'c.p3d','category':'x','size':1,'mime':0,'sha256':'e'*64},{'name':'d.p3d','normalized_name':'d.p3d','category':'x','size':1,'mime':0,'sha256':'f'*64}]
  models=[{'name':'dz/a.p3d','sha256':'a'*64,'package':'pkg.pbo','entry':'a.p3d'},{'name':'dz/b.p3d','sha256':'b'*64,'package':'pkg.pbo','entry':'b.p3d'}]
  catalog=[{'index':i,'name':k,'instances':v,'group':'x'} for i,(k,v) in enumerate(lit['counts'].items())]
  if variant=='counts_permuted':
   vals=list(lit['counts'].values())[::-1]; catalog=[{'index':i,'name':k,'instances':vals[i],'group':'x'} for i,k in enumerate(lit['counts'].keys())]
  if variant=='name_comutant':
   catalog=[{'index':0,'name':'dz/a.p3d','instances':2,'group':'x'},{'index':1,'name':'dz/x.p3d','instances':1,'group':'x'}]; models=[{'name':'dz/a.p3d','sha256':'a'*64,'package':'pkg.pbo','entry':'a.p3d'},{'name':'dz/x.p3d','sha256':'b'*64,'package':'pkg.pbo','entry':'b.p3d'}]
  if variant=='provider_conflict': models.append({'name':'dz/c.p3d','sha256':'9'*64,'package':'pkg.pbo','entry':'c.p3d'})
  b2a_report={'status':'x','scene_instances':len(recs),'scene_models':len(catalog),'packages':[{'path':'pkg.pbo','sha256':'c'*64,'prefix':'dz'}]}
  b2a_config={'packages':[],'package_pins':{'pkg.pbo':'c'*64}}
  if variant=='provider_prefix_entry_comutant':
   b2a_report['packages']=[{'path':'pkg.pbo','sha256':'c'*64,'prefix':'dz/sub'}]; models=[dict(m,entry='../'+m['entry']) for m in models]
  if variant=='bool_report': b2a_report['scene_instances']=True
  if variant=='missing_b2a_pin': b2a_config['package_pins']={}
  if variant=='missing_scene_models': b2a_report.pop('scene_models',None)
  b3_report={'added_count':3,'added_ids':[4,5,6],'candidate_bytes':len(candidate),'candidate_max_id':6,'candidate_object_count':len(recs)+3,'candidate_path':'x','candidate_sha256':_sha(candidate),'max_id':max(i for i,n in recs),'object_count':len(recs),'ok':True,'prefix_sha256':prefix_sha,'source_bytes':len(source),'source_sha256':_sha(source),'status':'x'}
  if variant=='missing_b3': b3_report.pop('candidate_sha256',None)
  files={}
  def wj(name,obj):
   p=d/name; data=(json.dumps(obj,sort_keys=True)+'\n').encode(); p.write_bytes(data); return p,data
  def wjl(name,rows):
   p=d/name; data=b''.join((json.dumps(r,sort_keys=True)+'\n').encode() for r in rows); p.write_bytes(data); return p,data
  def pin(key,p,data): files[key]={'path':str(p),'sha256':_sha(data),'bytes':len(data)}
  p,data=wj('b3_contract.json',{'schema':'x','status':'x','source_path':'x','source_sha256':_sha(source),'source_bytes':len(source),'object_count':len(recs),'max_id':max(i for i,n in recs),'prefix_bytes':prefix_bytes,'prefix_sha256':prefix_sha,'terminator_hex':term.hex(),'objects':objs,'pins':{}}); pin('b3_contract',p,data)
  p,data=wj('b3_report.json',b3_report); pin('b3_report',p,data)
  p,data=wj('b2a_models.json',models); pin('b2a_models',p,data)
  p,data=wj('b2a_report.json',b2a_report); pin('b2a_report',p,data)
  p,data=wj('b2a_config.json',b2a_config); pin('b2a_config',p,data)
  p,data=wj('catalog.json',catalog); pin('catalog',p,data)
  p,rm_data=wjl('road_models.jsonl',road_rows); pin('road_models',p,rm_data)
  p,re_data=wj('road_entries.json',entries); pin('road_entries',p,re_data)
  p,data=wj('b4a3_contract.json',{'schema':'x','sources':{'previous:report.json':{'path':'x','sha256':'7'*64,'size':1},'helper':{'path':'x','sha256':'8'*64,'size':1},'models':{'path':'x','sha256':_sha(rm_data),'size':len(rm_data)},'catalog':{'path':'x','sha256':_sha(re_data),'size':len(re_data)},'previous:assets/dz/a.p3d':{'path':'x','sha256':'a'*64,'size':1},'previous:assets/dz/c.p3d':{'path':'x','sha256':'e'*64,'size':1},'previous:assets/dz/d.p3d':{'path':'x','sha256':'f'*64,'size':1}}}); pin('b4a3_contract',p,data)
  p,data=wj('b4a3_summary.json',{'status':'x','pbo':{'path':'pkg.pbo','prefix':'dz','sha256':'c'*64}}); pin('b4a3_summary',p,data)
  expected={'object_count':len(recs),'max_id':max(i for i,n in recs),'prefix_bytes':prefix_bytes,'prefix_sha256':prefix_sha,'terminator_hex':term.hex(),'objects':objs,'candidate_count':lit['expected_candidate_count'] if len(recs)==lit['source_count'] else len(recs)+3,'catalog_model_count':len(catalog)}
  if variant=='bool': expected['object_count']=True
  contract={'schema':'road-b4b0.v1','scope':'SAVED_SCENE_REFERENCE_INDEX_ONLY','plan_sha256':'78a043c49bca893899583d023bae53083f13a7a818578f8607f46f41e23792ea','source':{'path':str(sp),'sha256':_sha(source),'bytes':len(source)},'candidate':{'path':str(cp),'sha256':_sha(candidate),'bytes':len(candidate)},'files':files,'expected':expected,'limits':dict(LIMITS),'budgets':{'author_s':240,'review_s':180,'suite_s':120,'producer_s':120,'producer_rss':1073741824,'consumer_s':60,'consumer_rss':268435456},'claims':dict(CLAIMS)}
  if variant=='unknown_claim': contract['claims']=dict(CLAIMS,build_ready='UNKNOWN_CLAIM')
  if variant=='missing_b4a3_pin':
   p2=d/'b4a3_contract.json'; obj=json.loads(p2.read_text()); obj['sources'].pop('previous:assets/dz/c.p3d',None); data2=(json.dumps(obj,sort_keys=True)+'\n').encode(); p2.write_bytes(data2); files['b4a3_contract']={'path':str(p2),'sha256':_sha(data2),'bytes':len(data2)}
  cpath=d/'contract.json'; cpath.write_bytes((json.dumps(contract,sort_keys=True)+'\n').encode()); return d,cpath,lit
 def _run(self,script,contract,out,report=None):
  sha=_sha(Path(contract).read_bytes()); cmd=[sys.executable,str(script),'--contract',str(contract),'--contract-sha',sha,'--output',str(out)]
  if report is not None: cmd+=['--report',str(report)]
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=120); data=None
  if Path(out).exists(): data=json.loads(Path(out).read_text())
  return r,data
 def _codes(self,data): return [x['code'] for x in data['issues']]
 def _details(self,data): return ' | '.join(x['detail'] for x in data['issues'])
 def test_positive_producer_then_consumer(self):
  d,c,lit=self._fixture(); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,0,r.stderr); self.assertEqual(data['status'],'SAVED_SCENE_REFERENCE_INDEX_ONLY'); self.assertEqual(data['source']['bytes'],lit['source_bytes']); self.assertEqual(data['candidate']['bytes'],lit['expected_candidate_bytes']); self.assertEqual(data['counts'],{'distinct_references':4,'source_total':lit['source_count'],'candidate_total':lit['expected_candidate_count']}); rows={x['name']:x for x in data['table']}
  for name,want in lit['expected_candidate_counts'].items(): self.assertEqual(rows[name]['candidate_instances'],want)
  for name,want in lit['counts'].items(): self.assertEqual(rows[name]['source_instances'],want)
  self.assertEqual(rows['dz/a.p3d']['state'],'PROVIDER_RESOLVED'); self.assertEqual(rows['dz/a.p3d']['candidate_instances'],3); self.assertIn('DZ'+chr(92)+'A.p3d',rows['dz/a.p3d']['aliases']); self.assertIn('dz/a.p3d',rows['dz/a.p3d']['aliases']); self.assertEqual(rows['dz/c.p3d']['state'],'NEW_REFERENCE_WITH_B4A3_PIN'); self.assertEqual(rows['dz/d.p3d']['state'],'NEW_REFERENCE_WITH_B4A3_PIN')
  cout=d/'consumer.json'; r2,cdata=self._run(CONS,c,cout,report=out); self.assertEqual(r2.returncode,0,r2.stderr); self.assertEqual(cdata['status'],'SAVED_SCENE_REFERENCE_INDEX_ONLY')
 def test_positive_exterior_slash_alias(self):
  d,c,lit=self._fixture('alias_exterior'); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,0,r.stderr); rows={x['name']:x for x in data['table']}; self.assertIn('/dz/a.p3d/',rows['dz/a.p3d']['aliases']); self.assertEqual(rows['dz/a.p3d']['source_instances'],2)
 def test_negative_variants_producer_precise(self):
  cases=[('dup_id','FATAL','duplicate object id'),('truncated_header','FATAL','truncated WRP header'),('truncated_material','FATAL','truncated material string bytes'),('truncated_name','FATAL','truncated object name bytes'),('truncated_terminator','FATAL','truncated object record or terminator'),('candidate_truncated_name','FATAL','truncated candidate name bytes'),('name4097','FATAL','object name exceeds cap before read'),('refs10001','FATAL','references cap exceeded'),('nonascii','FATAL','printable ASCII'),('traversal','FATAL','traversal'),('candidate_omitted','FATAL','candidate object omitted'),('provider_conflict','PROVIDER_CONFLICT',None),('counts_permuted','CATALOG_COUNTS',None),('name_comutant','B2A_PROVIDER_ENTRY',None),('provider_prefix_entry_comutant','B2A_PROVIDER_ENTRY',None),('missing_b3','B3_REPORT_CANDIDATE_SHA256',None),('missing_b4a3_pin','NEW_REFERENCE_WITH_B4A3_PIN',None),('missing_b2a_pin','B2A_PACKAGE_PIN_MISSING',None),('missing_scene_models','B2A_SCENE_MODELS',None),('bool_report','B2A_SCENE_INSTANCES',None),('bool','FATAL','bad expected object_count'),('unknown_claim','FATAL','claims mismatch')]
  for variant,code,detail in cases:
   with self.subTest(variant=variant):
    d,c,lit=self._fixture(variant); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,2); self.assertIsNotNone(data); self.assertNotEqual(data['status'],'SAVED_SCENE_REFERENCE_INDEX_ONLY'); self.assertIn(code,self._codes(data))
    if detail is not None: self.assertIn(detail,self._details(data))
 def test_consumer_rejects_mutated_report(self):
  d,c,lit=self._fixture(); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,0)
  data['table'][0]['candidate_instances']=999; out.write_text(json.dumps(data)); cout=d/'consumer.json'; r2,cdata=self._run(CONS,c,cout,report=out); self.assertEqual(r2.returncode,2); self.assertEqual(cdata['status'],'INCONCLUSIVE_REFERENCE_MISMATCH'); self.assertIn('FATAL',self._codes(cdata)); self.assertIn('producer report differs',self._details(cdata))
 def test_consumer_rejects_bool_equal_one_mutation(self):
  d,c,lit=self._fixture(); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,0)
  for row in data['table']:
   if row['name']=='dz/b.p3d': row['source_instances']=True
  out.write_text(json.dumps(data)); cout=d/'consumer.json'; r2,cdata=self._run(CONS,c,cout,report=out); self.assertEqual(r2.returncode,2); self.assertNotEqual(cdata['status'],'SAVED_SCENE_REFERENCE_INDEX_ONLY'); self.assertIn('FATAL',self._codes(cdata))
 def test_consumer_rejects_substituted_producer_path(self):
  d,c,lit=self._fixture(); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,0)
  data['tool']['path']=str(CONS); data['tool']['sha256']=_sha(CONS.read_bytes()); out.write_text(json.dumps(data)); cout=d/'consumer.json'; r2,cdata=self._run(CONS,c,cout,report=out); self.assertEqual(r2.returncode,2); self.assertIn('producer tool path mismatch',self._details(cdata))
 def test_consumer_verified_mismatch_diagnostic(self):
  d,c,lit=self._fixture('counts_permuted'); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,2); self.assertEqual(data['status'],'INCONCLUSIVE_REFERENCE_MISMATCH'); self.assertIn('CATALOG_COUNTS',self._codes(data))
  cout=d/'consumer.json'; r2,cdata=self._run(CONS,c,cout,report=out); self.assertEqual(r2.returncode,2); self.assertEqual(cdata['status'],'VERIFIED_MISMATCH_DIAGNOSTIC'); self.assertIn('CATALOG_COUNTS',self._codes(cdata))
 def test_consumer_detects_independent_source_change(self):
  d,c,lit=self._fixture(); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,0)
  sp=Path(data['source']['path']); sp.write_bytes(sp.read_bytes()+b'x'); cout=d/'consumer.json'; r2,cdata=self._run(CONS,c,cout,report=out); self.assertEqual(r2.returncode,2); self.assertNotEqual(cdata['status'],'SAVED_SCENE_REFERENCE_INDEX_ONLY')
 def test_stat_identity_units(self):
  prod=_load_mod(PROD,'prod_mod_for_test')
  class S:
   def __init__(self,ctime,mtime): self.st_dev=1; self.st_ino=2; self.st_size=3; self.st_mtime_ns=mtime; self.st_ctime_ns=ctime
  a=prod._statd(S(10,20)); b=prod._statd(S(99,20)); self.assertFalse(prod._same_handle_identity(a,b)); self.assertFalse(prod._same_path_identity(a,b)); b2=prod._statd(S(99,21)); self.assertFalse(prod._same_path_identity(a,b2))
 def test_literal_original_bytes_exact(self):
  d,c,lit=self._fixture(); x=json.loads(c.read_bytes())
  expected=bytes.fromhex(lit['header_hex'])+b''.join(bytes.fromhex(lit['matrix_hex']+r['id_hex']+r['size_hex']+r['name_hex']) for r in lit['source_records'])+bytes.fromhex(lit['terminator_hex'])
  self.assertEqual(Path(x['source']['path']).read_bytes(),expected)
 def test_saved_asset_siblings_do_not_make_assets(self):
  d,c,lit=self._fixture(); out=d/'report.json'; r,data=self._run(PROD,c,out); self.assertEqual(r.returncode,0)
  self.assertEqual({x['name'] for x in data['table']},set(lit['expected_candidate_counts']))
 def test_road_entry_name_normalization_comutant(self):
  d,c,lit=self._fixture(); x=json.loads(c.read_bytes()); ep=Path(x['files']['road_entries']['path']); entries=json.loads(ep.read_bytes()); entries[1]['name']='different.p3d'; b=(json.dumps(entries)+'\n').encode();ep.write_bytes(b);x['files']['road_entries'].update(sha256=_sha(b),bytes=len(b))
  bp=Path(x['files']['b4a3_contract']['path']);bc=json.loads(bp.read_bytes());bc['sources']['catalog'].update(sha256=_sha(b),size=len(b));b=(json.dumps(bc)+'\n').encode();bp.write_bytes(b);x['files']['b4a3_contract'].update(sha256=_sha(b),bytes=len(b));c.write_text(json.dumps(x))
  r,data=self._run(PROD,c,d/'out.json');self.assertEqual(r.returncode,2);self.assertIn('road entry normalized name mismatch',self._details(data))
  r2,checked=self._run(CONS,c,d/'consumer-out.json',report=d/'nonexistent.json');self.assertEqual(r2.returncode,2);self.assertIn('road entry normalized name mismatch',self._details(checked))
 def test_consumer_rescans_against_full_comutant_counts(self):
  d,c,lit=self._fixture(); out=d/'report.json';r,data=self._run(PROD,c,out);self.assertEqual(r.returncode,0)
  rows={x['name']:x for x in data['table']};rows['dz/a.p3d']['source_instances']=1;rows['dz/a.p3d']['candidate_instances']=2;rows['dz/b.p3d']['source_instances']=2;rows['dz/b.p3d']['candidate_instances']=2
  self.assertEqual(sum(x['source_instances'] for x in data['table']),3);out.write_text(json.dumps(data));r2,checked=self._run(CONS,c,d/'checked.json',report=out);self.assertEqual(r2.returncode,2);self.assertIn('producer report differs',self._details(checked))
 def test_consumer_independent_truncation_guards(self):
  for variant,detail in [('truncated_header','truncated WRP header'),('truncated_material','truncated material string bytes'),('truncated_name','truncated object name bytes'),('truncated_terminator','truncated object record or terminator')]:
   with self.subTest(variant=variant):
    d,c,lit=self._fixture(variant);r,checked=self._run(CONS,c,d/'checked.json',report=d/'nonexistent.json');self.assertEqual(r.returncode,2);self.assertIn(detail,self._details(checked))
if __name__=='__main__': unittest.main()
