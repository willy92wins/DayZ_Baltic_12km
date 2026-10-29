import hashlib,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'/'quality'))
import verify_road_material_snapshot_ev112 as V
import recover_road_material_samples_ev112 as R
def sha(b): return hashlib.sha256(b).hexdigest()
def js(o): return (json.dumps(o,ensure_ascii=False,indent=2,sort_keys=True)+'\n').encode()
VPS=['dz/structures/roads/parts/asf1_25.p3d','dz/structures/roads/parts/asf2_25.p3d','dz/structures/roads/parts/asf1_10 100.p3d','dz/structures/roads/parts/data/asf1_dashedline.rvmat','dz/structures/roads/parts/data/asf1_dashedline_ca.paa','dz/structures/roads/parts/data/asf2_dashedline.rvmat','dz/structures/roads/parts/data/asf2_dashedline_ca.paa','dz/surfaces/data/roadway/asphalt_ext.paa']
GOLDEN={"running":{"pid":72168,"birth":1793249173.9533355,"started":1793249173.7858894,"seconds":30.0,"executable":"C:\\Program Files (x86)\\Steam\\steamapps\\common\\DayZ Tools\\Bin\\CfgConvert\\CfgConvert.exe","input_sha":"656944f65b11750c76999be6eb6f07f002b5d3be690d7a0effeffda7159421c9"},"completion":{"rc":0,"reason":None,"seconds":0.34399999999732245,"peak_rss":17416192,"started":1793249173.7858894,"finished":1793249174.134283,"identities":{"72168":1793249173.9533355,"82756":1793249173.959208},"stdout_sha":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855","stderr_sha":"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"}}
def receipt(pid,exe,inp,rc,outb=b'',errb=b'',seconds=30):
 run={'pid':pid,'birth':1000.5,'started':1000.0,'seconds':seconds,'executable':exe,'input_sha':inp}; done={'rc':rc,'reason':None,'seconds':1.0,'peak_rss':1000,'started':1000.0,'finished':1001.0,'identities':{str(pid):1000.5},'stdout_sha':sha(outb),'stderr_sha':sha(errb)}; return run,done,outb,errb
class Builder:
 def __init__(self,tmp):
  self.tmp=Path(tmp); self.snap=self.tmp/'snapshot'; self.snap.mkdir(parents=True)
  self.tools=self.tmp/'tools'; self.tools.mkdir(); self.runner=self.tools/'runner.py'; self.runner.write_bytes(b'runner-owned'); self.cfg=self.tools/'CfgConvert.exe'; self.cfg.write_bytes(b'cfg-owned'); self.dep=self.tools/'dep.py'; self.dep.write_bytes(b'dep-owned')
  assets=[]; blobs={}
  for i,vp in enumerate(VPS):
   lp='assets/'+vp; pref=b'\x00raP' if vp.endswith('.rvmat') else b'ODOL'; b=pref+bytes([65+i])*32; blobs[lp]=b; assets.append({'kind':'material' if vp.endswith('.rvmat') else 'x','local_path':lp,'prefix16':b[:16].hex(),'provider':'surfaces' if i==7 else 'roads','sha256':sha(b),'size':len(b),'virtual_path':vp,'status':'EXTRACTED'})
  old={'schema':'OLD','cfgconvert':str(self.cfg),'runner':str(self.runner),'pins':{str(self.runner):sha(b'runner-owned'),str(self.cfg):sha(b'cfg-owned'),str(self.dep):sha(b'dep-owned')},'pbos':{'roads':{'bytes':1000,'sha256':'a'*64},'surfaces':{'bytes':2000},'surfaces_bliss':{'bytes':3000}},'selected':[{'virtual_path':v,'sha256':assets[i]['sha256']} for i,v in enumerate(VPS[:7])],'external':[VPS[7]]}; oldb=js(old)
  tables={n:{'sha256_after':s,'sha256_observed':s,'sha256_observed_now':s,'size':z,'stat_before':[1,2,z,3],'stat_after':[1,2,z,3]} for n,s,z in [('roads','a'*64,1000),('surfaces','b'*64,2000),('surfaces_bliss','c'*64,3000)]}
  report={'assets':assets,'external':[{'provider':'surfaces','providers':['surfaces'],'sha256':assets[7]['sha256'],'virtual_path':VPS[7]}],'contract_sha256':sha(oldb),'tables':tables,'status':'INCONCLUSIVE_INITIAL_DISCOVERY','error':'DiscoveryError:conversion_stream_missing','build_ready':False,'dependency_closure':'NOT_EVALUATED'}; repb=js(report)
  manifest={'assets':assets,'artifacts':[{'local_path':a['local_path'],'sha256':a['sha256'],'size':a['size']} for a in assets],'report_sha256':sha(repb),'contract_sha256':sha(oldb),'status':report['status'],'error':report['error'],'build_ready':False,'dependency_closure':'NOT_EVALUATED'}
  failed=b'failed-code'; appr={'contract_sha256':sha(oldb),'tool_sha256':sha(failed)}
  blobs.update({'report.json':repb,'manifest.json':js(manifest),'original-contract.json':oldb,'original-approval.json':js(appr),'code-failed.py':failed,'code-corrected.py':b'corrected-code'})
  pr=receipt(111,str(self.tmp/'python.exe'),sha(js(appr)),1,b'',b'pe',120); cr=receipt(222,str(self.cfg),assets[3]['sha256'],0)
  blobs['parent/running.json']=js(pr[0]); blobs['parent/completion.json']=js(pr[1]); blobs['parent/stdout']=pr[2]; blobs['parent/stderr']=pr[3]; blobs['receipts/conversion_1/running.json']=js(cr[0]); blobs['receipts/conversion_1/completion.json']=js(cr[1]); blobs['receipts/conversion_1/stdout']=cr[2]; blobs['receipts/conversion_1/stderr']=cr[3]; blobs['decoded/dz/structures/roads/parts/data/asf1_dashedline.rvmat.txt']=b'text-one'
  for rel,b in blobs.items(): p=self.snap/rel; p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(b)
  self.assets=assets; self.output=self.tmp/'recovery'; self.marker=self.tmp/'marker.json'
  contract={'schema':'ROAD_SAVED_MATERIAL_RECOVERY_V1','snapshot_root':str(self.snap),'pins':{k:sha(v) for k,v in blobs.items()},'roles':V.ROLES,'tools':{'runner':{'path':str(self.runner),'sha256':sha(b'runner-owned')},'cfgconvert':{'path':str(self.cfg),'sha256':sha(b'cfg-owned')},'dependencies':{str(self.dep):sha(b'dep-owned')}},'output':str(self.output),'attempt_marker':str(self.marker),'conversion2_receipt':str(self.output/'receipts'/'conversion_2'),'conversion2_text':str(self.output/'decoded'/'asf2_dashedline.rvmat.txt'),'limits':V.LIMITS,'build_ready':False,'dependency_closure':'NOT_EVALUATED'}
  self.contract=self.tmp/'contract.json'; self.cb=js(contract); self.contract.write_bytes(self.cb); self.hash=sha(self.cb)
 def fake(self,calls,fail=False):
  def run(job):
   calls.append(job)
   if fail: raise RuntimeError('boom')
   out=Path(job['out']); out.mkdir(parents=True); inp=Path(job['input_file']).read_bytes(); exe=job['command'][0]; r=receipt(333,exe,sha(inp),0); (out/'running.json').write_bytes(js(r[0])); (out/'completion.json').write_bytes(js(r[1])); (out/'stdout').write_bytes(b''); (out/'stderr').write_bytes(b''); Path(job['command'][3]).write_bytes(b'text-two'); return {'id':job['id'],'rc':0}
  return run
class T(unittest.TestCase):
 def setUp(self):
  import tempfile; self.td=tempfile.TemporaryDirectory(); self.b=Builder(self.td.name)
 def tearDown(self): self.td.cleanup()
 def test_golden_real_receipt(self):
  p=ROOT/'tests'/'fixtures'/'road_b4a2_runner_receipt.json'; g=json.loads(p.read_text(encoding='utf-8')) if p.exists() else GOLDEN; m=V.verify_receipt(g['running'],g['completion'],b'',b'',g['running']['input_sha'],g['running']['executable']); self.assertEqual(m['rc'],0)
 def test_verify_snapshot_no_runner(self):
  calls=[]; self.b.fake(calls); s=V.verify_snapshot(str(self.b.contract),self.b.hash); self.assertEqual(s['result']['status'],'SAVED_SNAPSHOT_VERIFIED_ONLY'); self.assertEqual(calls,[])
 def test_recover_success_one_call(self):
  calls=[]; rep=R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls)); self.assertEqual(len(calls),1); self.assertEqual(rep['status'],'MATERIAL_SAMPLES_RECOVERED_ONLY'); self.assertEqual(len(rep['texts']),2); self.assertEqual(R.verify_recovery(str(self.b.contract),self.b.hash)['status'],rep['status'])
  with self.assertRaises(Exception): R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls))
  self.assertEqual(len(calls),1)
 def test_failure_marker_consumed(self):
  calls=[]
  with self.assertRaises(Exception): R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls,True))
  self.assertTrue(self.b.marker.exists()); self.assertEqual(json.loads((self.b.output/'report.json').read_text())['status'],'INCONCLUSIVE_RECOVERY')
  with self.assertRaises(Exception): R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls))
 def test_output_exists_marker_consumed(self):
  self.b.output.mkdir(); calls=[]
  with self.assertRaises(Exception): R.recover(str(self.b.contract),self.b.hash,runner_call=self.b.fake(calls)); self.assertTrue(self.b.marker.exists()); self.assertEqual(calls,[])
 def test_receipt_negatives(self):
  g=GOLDEN
  for mut in [lambda r,d:(r.update(input_sha='0'*64)),lambda r,d:(r.update(executable='x')),lambda r,d:(d['identities'].update({'72168':1.0})),lambda r,d:(d.update(rc=True)),lambda r,d:(d.update(reason='x')),lambda r,d:(r.update(birth=None)),lambda r,d:(d.update(stdout_sha256='x')),lambda r,d:(r.pop('pid'))]:
   import copy; r=copy.deepcopy(g['running']); d=copy.deepcopy(g['completion']); mut(r,d)
   with self.assertRaises(Exception): V.verify_receipt(r,d,b'',b'',g['running']['input_sha'],g['running']['executable'])
 def test_hash_before_parse_and_duplicate(self):
  bad=self.b.tmp/'bad.json'; bad.write_bytes(b'{"a":1,"a":2}')
  with self.assertRaises(Exception): V.load_contract(str(bad),'0'*64)
  with self.assertRaises(Exception): V.load_contract(str(bad),sha(bad.read_bytes()))
 def test_byte_change_tools_missing_text(self):
  p=self.b.snap/self.b.assets[0]['local_path']; p.write_bytes(p.read_bytes()+b'x')
  with self.assertRaises(Exception): V.verify_snapshot(str(self.b.contract),self.b.hash)
  b2=Builder(self.b.tmp/'x2'); Path(b2.runner).write_bytes(b'changed')
  with self.assertRaises(Exception): V.verify_snapshot(str(b2.contract),b2.hash)
  b3=Builder(self.b.tmp/'x3'); (b3.snap/'decoded/dz/structures/roads/parts/data/asf1_dashedline.rvmat.txt').unlink()
  with self.assertRaises(Exception): V.verify_snapshot(str(b3.contract),b3.hash)
if __name__=='__main__': unittest.main()
