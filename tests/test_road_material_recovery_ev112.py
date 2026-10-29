import copy,hashlib,json,os,sys,tempfile,time,unittest
from pathlib import Path
from unittest import mock
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'/'quality'))
import verify_road_material_snapshot_ev112 as V
import recover_road_material_samples_ev112 as R
def sha(b): return hashlib.sha256(b).hexdigest()
def js(o): return (json.dumps(o,ensure_ascii=False,indent=2,sort_keys=True)+chr(10)).encode()
BS=chr(92)
VPS=['dz/structures/roads/parts/asf1_25.p3d','dz/structures/roads/parts/asf2_25.p3d','dz/structures/roads/parts/asf1_10 100.p3d','dz/structures/roads/parts/data/asf1_dashedline.rvmat','dz/structures/roads/parts/data/asf1_dashedline_ca.paa','dz/structures/roads/parts/data/asf2_dashedline.rvmat','dz/structures/roads/parts/data/asf2_dashedline_ca.paa','dz/surfaces/data/roadway/asphalt_ext.paa']
FIXTURE=ROOT/'tests'/'fixtures'/'road_b4a2_runner_receipt.json'
def receipt(pid,exe,inp,rc,outb=b'',errb=b'',run_seconds=30):
 started=time.time(); birth=started+0.0005; finished=started+0.002
 run={'pid':pid,'birth':birth,'started':started,'seconds':float(run_seconds),'executable':exe,'input_sha':inp}
 done={'rc':rc,'reason':None,'seconds':0.001,'peak_rss':1000,'started':started,'finished':finished,'identities':{str(pid):birth},'stdout_sha':sha(outb),'stderr_sha':sha(errb)}
 return run,done,outb,errb
class Builder:
 def __init__(self,tmp):
  self.tmp=Path(tmp); self.tmp.mkdir(parents=True,exist_ok=True); self.snap=self.tmp/'snapshot'; self.snap.mkdir(parents=True)
  self.tools=self.tmp/'tools'; self.tools.mkdir(); self.runner=self.tools/'runner.py'; self.runner.write_bytes(b'runner-owned-synthetic'); self.cfg=self.tools/'CfgConvert.exe'; self.cfg.write_bytes(b'cfg-owned-synthetic'); self.dep=self.tools/'dep.py'; self.dep.write_bytes(b'dep-owned-synthetic')
  assets=[]; blobs={}
  for i,vp in enumerate(VPS):
   lp='assets/'+vp; pref=bytes([0])+b'raP' if vp.endswith('.rvmat') else b'ODOL'; b=pref+bytes([65+i])*32; blobs[lp]=b; assets.append({'kind':'material' if vp.endswith('.rvmat') else 'synthetic','local_path':lp,'prefix16':b[:16].hex(),'provider':'surfaces' if i==7 else 'roads','sha256':sha(b),'size':len(b),'virtual_path':vp,'status':'EXTRACTED'})
  old={'schema':'OLD_SYNTHETIC','cfgconvert':str(self.cfg),'runner':str(self.runner),'pins':{str(self.runner):sha(b'runner-owned-synthetic'),str(self.cfg):sha(b'cfg-owned-synthetic'),str(self.dep):sha(b'dep-owned-synthetic')},'pbos':{'roads':{'bytes':1000,'sha256':'a'*64},'surfaces':{'bytes':2000},'surfaces_bliss':{'bytes':3000}},'selected':[{'virtual_path':v,'sha256':assets[i]['sha256']} for i,v in enumerate(VPS[:7])],'external':[VPS[7]]}; oldb=js(old)
  tables={}
  for n,s,z,cnt in [('roads','a'*64,1000,501),('surfaces','b'*64,2000,109),('surfaces_bliss','c'*64,3000,34)]:
   tables[n]={'entry_count':cnt,'path':'E:'+BS+'Synthetic'+BS+n+'.pbo','prefix':V.PREFIXES[n],'sha256_after':s,'sha256_observed':s,'sha256_observed_now':s,'size':z,'stat_before':[11,22,z,33],'stat_after':[11,22,z,33]}
  report={'assets':assets,'external':[{'provider':'surfaces','providers':['surfaces'],'sha256':assets[7]['sha256'],'virtual_path':VPS[7]}],'contract_sha256':sha(oldb),'tables':tables,'status':'INCONCLUSIVE_INITIAL_DISCOVERY','error':'DiscoveryError:conversion_stream_missing','build_ready':False,'dependency_closure':'NOT_EVALUATED'}; repb=js(report)
  manifest={'assets':assets,'artifacts':[{'local_path':a['local_path'],'sha256':a['sha256'],'size':a['size']} for a in assets],'report_sha256':sha(repb),'contract_sha256':sha(oldb),'status':report['status'],'error':report['error'],'build_ready':False,'dependency_closure':'NOT_EVALUATED'}
  failed=b'failed-code-synthetic'; appr={'contract_sha256':sha(oldb),'tool_sha256':sha(failed)}
  blobs.update({'report.json':repb,'manifest.json':js(manifest),'original-contract.json':oldb,'original-approval.json':js(appr),'code-failed.py':failed,'code-corrected.py':b'corrected-code-synthetic'})
  pr=receipt(111,str(self.tmp/'python.exe'),sha(js(appr)),1,b'',b'pe',120); cr=receipt(222,str(self.cfg),assets[3]['sha256'],0)
  blobs['parent/running.json']=js(pr[0]); blobs['parent/completion.json']=js(pr[1]); blobs['parent/stdout']=pr[2]; blobs['parent/stderr']=pr[3]; blobs['receipts/conversion_1/running.json']=js(cr[0]); blobs['receipts/conversion_1/completion.json']=js(cr[1]); blobs['receipts/conversion_1/stdout']=cr[2]; blobs['receipts/conversion_1/stderr']=cr[3]; blobs['decoded/dz/structures/roads/parts/data/asf1_dashedline.rvmat.txt']=b'text-one-synthetic'
  for rel,b in blobs.items():
   p=self.snap/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
  self.assets=assets; self.output=self.tmp/'recovery'; self.marker=self.tmp/'marker.json'
  contract={'schema':'ROAD_SAVED_MATERIAL_RECOVERY_V1','snapshot_root':str(self.snap),'pins':{k:sha(v) for k,v in blobs.items()},'roles':V.ROLES,'tools':{'runner':{'path':str(self.runner),'sha256':sha(b'runner-owned-synthetic')},'cfgconvert':{'path':str(self.cfg),'sha256':sha(b'cfg-owned-synthetic')},'dependencies':{str(self.dep):sha(b'dep-owned-synthetic')}},'output':str(self.output),'attempt_marker':str(self.marker),'conversion2_receipt':str(self.output/'receipts'/'conversion_2'),'conversion2_text':str(self.output/'decoded'/'asf2_dashedline.rvmat.txt'),'limits':V.LIMITS,'build_ready':False,'dependency_closure':'NOT_EVALUATED'}
  self.contract=self.tmp/'contract.json'; self.cb=js(contract); self.contract.write_bytes(self.cb); self.hash=sha(self.cb)
 def save_contract(self,obj):
  self.cb=js(obj); self.contract.write_bytes(self.cb); self.hash=sha(self.cb); return obj
 def load_contract_obj(self): return json.loads(self.contract.read_text(encoding='utf-8'))
 def repin_blob(self,rel,data):
  p=self.snap/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(data); obj=self.load_contract_obj(); obj['pins'][rel]=sha(data); self.save_contract(obj)
 def mutate_report(self,fn):
  report=json.loads((self.snap/'report.json').read_text(encoding='utf-8')); fn(report); report['contract_sha256']=sha((self.snap/'original-contract.json').read_bytes()); repb=js(report); self.repin_blob('report.json',repb); manifest=json.loads((self.snap/'manifest.json').read_text(encoding='utf-8')); manifest['report_sha256']=sha(repb); manifest['contract_sha256']=report['contract_sha256']; self.repin_blob('manifest.json',js(manifest))
 def mutate_old(self,fn):
  old=json.loads((self.snap/'original-contract.json').read_text(encoding='utf-8')); fn(old); self.repin_blob('original-contract.json',js(old)); self.mutate_report(lambda r: None)
 def fake(self,calls,fail=False,tamper_return=False):
  def run(job):
   calls.append(copy.deepcopy(job))
   if fail: raise RuntimeError('boom-synthetic')
   out=Path(job['out']); out.mkdir(parents=True); inp=Path(job['input_file']).read_bytes(); started=1700000000.0; birth=1700000000.25
   Path(job['command'][3]).write_bytes(b'text-two-synthetic'); finished=1700000001.0
   os.utime(job['command'][3],(1700000000.5,1700000000.5))  # Synthetic fixture clock only.
   running={'pid':333,'birth':birth,'started':started,'seconds':float(job['seconds']),'executable':job['command'][0],'input_sha':sha(inp)}
   done={'rc':0,'reason':None,'seconds':max(0.0,finished-started),'peak_rss':1000,'started':started,'finished':finished,'identities':{333:birth},'stdout_sha':sha(b''),'stderr_sha':sha(b'')}
   (out/'running.json').write_bytes(js(running)); (out/'completion.json').write_bytes(js({**done,'identities':{str(333):birth}})); (out/'stdout').write_bytes(b''); (out/'stderr').write_bytes(b'')
   if tamper_return: return {'id':job['id'],'rc':999}
   return {'id':job['id'],**done}
  return run
class T(unittest.TestCase):
 def setUp(self):
  self.td=tempfile.TemporaryDirectory(); self.b=Builder(self.td.name)
 def tearDown(self): self.td.cleanup()
 def test_golden_real_receipt_mandatory(self):
  self.assertTrue(FIXTURE.is_file(), 'golden fixture REAL obligatorio ausente')
  g=json.loads(FIXTURE.read_text(encoding='utf-8')); self.assertEqual(g['running']['pid'],72168); self.assertEqual(g['completion']['rc'],0); self.assertEqual(g['running']['input_sha'],'656944f65b11750c76999be6eb6f07f002b5d3be690d7a0effeffda7159421c9')
  m=V.verify_receipt(g['running'],g['completion'],b'',b'','656944f65b11750c76999be6eb6f07f002b5d3be690d7a0effeffda7159421c9',r'C:\Program Files (x86)\Steam\steamapps\common\DayZ Tools\Bin\CfgConvert\CfgConvert.exe'); self.assertEqual(m['stdout_sha'],'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855')
 def test_verify_snapshot_no_runner(self):
  with mock.patch.object(R,'_load_runner',side_effect=AssertionError('runner loaded')) as loaded:
   s=V.verify_snapshot(str(self.b.contract),self.b.hash)
  self.assertEqual(loaded.call_count,0); self.assertEqual(s['result']['status'],'SAVED_SNAPSHOT_VERIFIED_ONLY'); self.assertEqual(s['result']['assets'],8); self.assertEqual(s['result']['conversions'],1)
 def test_recover_success_one_call_and_final_consumer(self):
  calls=[]; rep=R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls))
  self.assertEqual(len(calls),1); self.assertEqual([j['id'] for j in calls],['conversion_2']); self.assertEqual(calls[0]['command'][1:3],['-txt','-dst']); self.assertEqual(calls[0]['seconds'],30); self.assertEqual(calls[0]['max_bytes'],268435456); self.assertEqual(rep['status'],'MATERIAL_SAMPLES_RECOVERED_ONLY'); self.assertEqual(rep['contract_sha256'],self.b.hash); self.assertEqual(rep['conversions'],2)
  again=V.verify_recovery(str(self.b.contract),self.b.hash); self.assertEqual(again,rep)
  with self.assertRaises(Exception):
   R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls))
  self.assertEqual(len(calls),1)
 def test_failure_marker_consumed(self):
  calls=[]
  with self.assertRaises(Exception):
   R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls,True))
  self.assertTrue(self.b.marker.exists()); self.assertEqual(json.loads((self.b.output/'report.json').read_text())['status'],'INCONCLUSIVE_RECOVERY'); self.assertEqual(len(calls),1)
 def test_rejected_final_report_preserved(self):
  calls=[]
  with mock.patch.object(V,'verify_recovery',side_effect=V.SnapshotError('independent-rejection')):
   with self.assertRaisesRegex(V.SnapshotError,'independent-rejection'):
    R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls))
  raw=(self.b.output/'report.json').read_bytes()
  self.assertEqual(json.loads(raw)['status'],'MATERIAL_SAMPLES_RECOVERED_ONLY')
  self.assertEqual(json.loads((self.b.output/'failure.json').read_bytes())['status'],'INCONCLUSIVE_RECOVERY')
  with self.assertRaisesRegex(V.SnapshotError,'recovery_failure_recorded'):
   V.verify_recovery(str(self.b.contract),self.b.hash)
  self.assertEqual((self.b.output/'report.json').read_bytes(),raw)
  self.assertEqual(len(calls),1)
 def test_output_sentinel_byteidentical_zero_calls_marker_consumed(self):
  self.b.output.mkdir(); sentinel=b'SENTINEL-REPORT-DO-NOT-TOUCH'; (self.b.output/'report.json').write_bytes(sentinel); calls=[]
  with self.assertRaises(Exception):
   R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls))
  self.assertEqual((self.b.output/'report.json').read_bytes(),sentinel); self.assertEqual(calls,[]); self.assertTrue(self.b.marker.exists())
  with self.assertRaises(Exception):
   R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls))
  self.assertEqual((self.b.output/'report.json').read_bytes(),sentinel); self.assertEqual(calls,[])
 def test_marker_inside_output_rejected(self):
  obj=self.b.load_contract_obj(); obj['attempt_marker']=str(self.b.output/'marker.json'); self.b.save_contract(obj)
  with self.assertRaisesRegex(V.SnapshotError,'marker_inside_output'):
   V.load_contract(str(self.b.contract),self.b.hash)
 def test_receipt_negatives_literal(self):
  self.assertTrue(FIXTURE.is_file()); g=json.loads(FIXTURE.read_text(encoding='utf-8'))
  muts=[('birth_none',lambda r,d: r.update(birth=None)),('input_zero',lambda r,d: r.update(input_sha='0'*64)),('exe_other',lambda r,d: r.update(executable='other.exe')),('rc_one',lambda r,d: d.update(rc=1)),('rc_bool',lambda r,d: d.update(rc=True)),('reason_text',lambda r,d: d.update(reason='TIMEOUT')),('started_shift',lambda r,d: d.update(started=d['started']+1.0)),('identity_birth',lambda r,d: d['identities'].update({'72168':1.0})),('extra_key',lambda r,d: d.update(extra=1))]
  for name,mut in muts:
   with self.subTest(name=name):
    r=copy.deepcopy(g['running']); d=copy.deepcopy(g['completion']); mut(r,d)
    with self.assertRaises(V.SnapshotError):
     V.verify_receipt(r,d,b'',b'',g['running']['input_sha'],g['running']['executable'])
    self.assertEqual(g['completion']['rc'],0)
  with self.assertRaises(V.SnapshotError):
   V.verify_receipt(copy.deepcopy(g['running']),copy.deepcopy(g['completion']),b'x',b'',g['running']['input_sha'],g['running']['executable'])
  self.assertEqual(g['running']['pid'],72168)
 def test_hash_before_parse_duplicate_and_wrong_pin(self):
  bad=self.b.tmp/'bad.json'; bad.write_bytes(b'{"a":1,"a":2}')
  with self.assertRaises(V.SnapshotError):
   V.load_contract(str(bad),'0'*64)
  self.assertEqual(bad.read_bytes(),b'{"a":1,"a":2}')
  with self.assertRaises(V.SnapshotError):
   V.load_contract(str(bad),sha(bad.read_bytes()))
  self.assertTrue(str(self.b.contract))
 def test_snapshot_byte_change_tool_change_missing_text(self):
  p=self.b.snap/self.b.assets[0]['local_path']; p.write_bytes(p.read_bytes()+b'x')
  with self.assertRaises(V.SnapshotError):
   V.verify_snapshot(str(self.b.contract),self.b.hash)
  self.assertTrue(p.read_bytes().endswith(b'x'))
  b2=Builder(self.b.tmp/'x2'); Path(b2.runner).write_bytes(b'changed')
  with self.assertRaises(V.SnapshotError):
   V.verify_snapshot(str(b2.contract),b2.hash)
  self.assertEqual(Path(b2.runner).read_bytes(),b'changed')
  b3=Builder(self.b.tmp/'x3'); (b3.snap/'decoded/dz/structures/roads/parts/data/asf1_dashedline.rvmat.txt').unlink()
  with self.assertRaises(V.SnapshotError):
   V.verify_snapshot(str(b3.contract),b3.hash)
  self.assertFalse((b3.snap/'decoded/dz/structures/roads/parts/data/asf1_dashedline.rvmat.txt').exists())
 def test_tables_malformed_repinned(self):
  cases=[('all_none',lambda t: [t[n].update(sha256_after=None,sha256_observed=None,sha256_observed_now=None) for n in t]),('bool_stat',lambda t: t['roads']['stat_after'].__setitem__(0,True)),('short_stat',lambda t: t['roads'].update(stat_after=[1,2,3],stat_before=[1,2,3])),('bad_prefix',lambda t: t['surfaces'].update(prefix='DZ/wrong')),('size_mismatch',lambda t: t['roads'].update(size=999))]
  for i,(name,fn) in enumerate(cases):
   with self.subTest(name=name):
    b=Builder(self.b.tmp/f't{i}'); b.mutate_report(lambda r,fn=fn: fn(r['tables']))
    with self.assertRaises(V.SnapshotError):
     V.verify_snapshot(str(b.contract),b.hash)
    self.assertEqual(b.assets[0]['provider'],'roads')
 def test_selected_duplicate_and_asset_duplicate_repinned(self):
  b=Builder(self.b.tmp/'dupsel'); b.mutate_old(lambda o: o['selected'].append(dict(o['selected'][0])))
  with self.assertRaises(V.SnapshotError):
   V.verify_snapshot(str(b.contract),b.hash)
  self.assertEqual(len(b.assets),8)
  b2=Builder(self.b.tmp/'dupasset'); b2.mutate_report(lambda r: r['assets'].append(dict(r['assets'][0])))
  with self.assertRaises(V.SnapshotError):
   V.verify_snapshot(str(b2.contract),b2.hash)
  self.assertEqual(len(b2.assets),8)
 def test_runner_return_mismatch(self):
  calls=[]
  with self.assertRaises(V.SnapshotError):
   R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls,tamper_return=True))
  self.assertEqual(json.loads((self.b.output/'report.json').read_text())['status'],'INCONCLUSIVE_RECOVERY'); self.assertTrue(self.b.marker.exists())
 def test_verify_recovery_corruptions(self):
  def fresh(name):
   b=Builder(self.b.tmp/name); calls=[]; R.recover(str(b.contract),b.hash,runner_call=b.fake(calls)); return b
  b=fresh('c1'); p=b.output/'snapshot'/b.assets[0]['local_path']; p.write_bytes(b'corrupt-copy')
  with self.assertRaises(V.SnapshotError):
   V.verify_recovery(str(b.contract),b.hash)
  self.assertEqual(p.read_bytes(),b'corrupt-copy')
  b=fresh('c2'); rep=json.loads((b.output/'report.json').read_text()); rep['texts'][1]['path']=rep['texts'][0]['path']; (b.output/'report.json').write_bytes(js(rep))
  with self.assertRaises(V.SnapshotError):
   V.verify_recovery(str(b.contract),b.hash)
  self.assertEqual(rep['texts'][1]['path'],rep['texts'][0]['path'])
  b=fresh('c3'); rep=json.loads((b.output/'report.json').read_text()); rep['receipt_2']['rc']=7; (b.output/'report.json').write_bytes(js(rep))
  with self.assertRaises(V.SnapshotError):
   V.verify_recovery(str(b.contract),b.hash)
  self.assertEqual(rep['receipt_2']['rc'],7)
  b=fresh('c4'); job=json.loads((b.output/'job.json').read_text()); job['seconds']=31; (b.output/'job.json').write_bytes(js(job))
  with self.assertRaises(V.SnapshotError):
   V.verify_recovery(str(b.contract),b.hash)
  self.assertEqual(job['seconds'],31)
  b=fresh('c5'); job=json.loads((b.output/'job.json').read_text()); job['command'][3]='elsewhere.txt'; (b.output/'job.json').write_bytes(js(job))
  with self.assertRaises(V.SnapshotError):
   V.verify_recovery(str(b.contract),b.hash)
  self.assertEqual(job['command'][3],'elsewhere.txt')
 def test_verify_recovery_stale_text2_mocked_mtime(self):
  calls=[]; R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls))
  with mock.patch.object(V,'_mtime',return_value=1000.0):
   with self.assertRaises(V.SnapshotError):
    V.verify_recovery(str(self.b.contract),self.b.hash)
   self.assertEqual(len(calls),1)
  self.assertEqual(V.verify_recovery(str(self.b.contract),self.b.hash)['status'],'MATERIAL_SAMPLES_RECOVERED_ONLY')
 def test_no_rss_self_check_api(self):
  self.assertFalse(hasattr(R,'_rss')); self.assertTrue(hasattr(V,'verify_recovery')); self.assertFalse(hasattr(R,'verify_recovery'))
if __name__=='__main__': unittest.main()
