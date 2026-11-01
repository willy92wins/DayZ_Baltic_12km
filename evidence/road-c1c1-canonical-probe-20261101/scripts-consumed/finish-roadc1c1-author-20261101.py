from pathlib import Path
import time,json,hashlib
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c1-local-author-20261101'
start=json.loads((D/'author-start.json').read_bytes())['started'];assert time.time()-start<600
p=D/'probe_road_compile_c1c1.py';s=p.read_text()
s=s.replace("canonical_check(c);pincheck(c['os_helper'])","canonical_check(c);need(pincheck(c['os_helper'])['identity']==c['os_helper']['identity'],'OS_HELPER_IDENTITY')")
s=s.replace("args=p['argv'];need(key!=root", "need(p.get('image_identity')==helper['identity'],'OS_HELPER_IDENTITY');args=p['argv'];need(key!=root")
p.write_text(s,encoding='utf-8')
p=D/'observe_road_compile_c1c1.py';s=p.read_text().replace("args=p['argv'];require(p['pid']!=root", "require(p.get('image_identity')==h['identity'] and list(fileid(Path(h['path']).stat()))==h['identity'],'OS_HELPER_IDENTITY');args=p['argv'];require(p['pid']!=root")
p.write_text(s,encoding='utf-8')
p=D/'test_probe_road_compile_c1c1.py';s=p.read_text();a=s.index(' def test_preflight_unique_delta');b=s.index(' def test_report_pin_comutation',a)
s=s[:a]+''' def test_preflight_saved_pins(self):
  for name,digest in [('preflight-original.py','9f8786a5f37b6b2abbd206bce51d4cad44d58536e766b97fd93bae692804c9a7'),('preflight-local.py','812e68aa2744428b3fce1b8016b552252e13244fa37eec7084e42763ab446646')]:self.assertEqual(hashlib.sha256((D/name).read_bytes()).hexdigest(),digest)
'''+s[b:]
s=s.replace("'os_helper':row(self.image)","'os_helper':rec(self.image)")
s=s.replace("if __name__=='__main__':unittest.main()",''' def helper(self):
  hp=self.r/'conhost.exe';hp.write_bytes(b'HELPER ONLY');self.c['os_helper']=rec(hp);p=copy.deepcopy(self.receipt['observed_processes'][0]);p.update(exe=str(hp),argv=[str(hp),'0xffffffff'],image_path_sha256=self.c['os_helper']['sha256'],image_identity=self.c['os_helper']['identity']);self.receipt['observed_processes'][0]=p;return p
 def test_parent_and_optional_helper(self):
  A.native_graph(self.c,self.receipt);V.process_tree(self.c,self.receipt);p=self.helper();A.native_graph(self.c,self.receipt);V.process_tree(self.c,self.receipt)
  self.assertEqual(A.gate(self.receipt,self.logs,[self.w],self.ih,{self.rh,p['image_path_sha256']}),N['helper_is_not_binarize'])
  p['parent_birth']-=1
  for fn,exc in [(A.native_graph,A.Stop),(V.process_tree,V.Reject)]:
   with self.assertRaisesRegex(exc,N['wrong_helper_parent']):fn(self.c,self.receipt)
 def test_helper_argv_identity_and_cycle(self):
  p=self.helper();p['argv'][1]='OTHER ARGUMENT'
  for fn,exc in [(A.native_graph,A.Stop),(V.process_tree,V.Reject)]:
   with self.assertRaisesRegex(exc,N['wrong_helper_argv']):fn(self.c,self.receipt)
  p['argv'][1]='0x123';p['image_identity'][1]+=1
  for fn,exc in [(A.native_graph,A.Stop),(V.process_tree,V.Reject)]:
   with self.assertRaisesRegex(exc,'OS_HELPER_IDENTITY'):fn(self.c,self.receipt)
  p['image_identity']=list(rec(Path(p['exe']))['identity']);p['parent_pid']=p['pid'];p['parent_birth']=p['birth']
  for fn,exc in [(A.native_graph,A.Stop),(V.process_tree,V.Reject)]:
   with self.assertRaisesRegex(exc,'PROCESS_PARENT'):fn(self.c,self.receipt)
 def test_phase_missing_started_and_closed(self):
  r={'phases':{}};self.assertEqual(V.phase_state(self.c,r,'help'),N['before_help']);folder=self.r/'phases';folder.mkdir();mark={'phase':'help','state':'STARTED','time':1};A.dump(folder/'help.started.json',mark)
  with self.assertRaisesRegex(V.Reject,N['started_without_close']):V.phase_state(self.c,r,'help')
  entry={'state':'CLOSED','start':mark};r['phases']['help']=entry;A.dump(folder/'help.closed.json',entry);self.assertEqual(V.phase_state(self.c,r,'help'),'CLOSED')
  mark['phase']='candidate';A.dump(folder/'help.started.json',mark)
  with self.assertRaisesRegex(V.Reject,'PHASE_BINDING'):V.phase_state(self.c,r,'help')
 def test_original_logger_before_launch(self):
  raw=(D/'logger-fixture.xml').read_bytes();folder=self.r/'tools/AddonBuilder';(folder/'logger.xml').write_bytes(raw);self.c['tool_files'].append({**rec(D/'logger-fixture.xml'),'dest':'logger.xml'});fixed=self.r/'fixed';fixed.mkdir()
  for n in ['include','exclude']:(fixed/(n+'.lst')).write_bytes(b'');self.c[n]=rec(fixed/(n+'.lst'))
  V.portable(self.c,None);(folder/'logger.xml').write_bytes(raw+b' ')
  with self.assertRaisesRegex(V.Reject,'LOGGER_DELTA'):V.portable(self.c,None)
 def canonical_fixture(self):
  p=self.r/'canonical/preflight.py';p.parent.mkdir();p.write_bytes(b'ORIGINAL');a=p.parent.lstat();rows=[]
  for q in [p,*p.parents]:
   z=q.lstat();rows.append({'path':str(q),'dev':z.st_dev,'ino':z.st_ino,'is_dir':q.is_dir()})
  return {'canonical_preflight':{'file':rec(p),'ancestors':rows,'alias':{'path':str(p.parent),'dev':a.st_dev,'ino':a.st_ino,'tag':getattr(a,'st_reparse_tag',0),'target':'SYNTHETIC_TARGET'}}}
 def test_canonical_identity_and_changed_alias(self):
  c=self.canonical_fixture()
  with patch.object(os,'readlink',return_value='SYNTHETIC_TARGET'):
   self.assertEqual(A.canonical_check(c)['sha256'],c['canonical_preflight']['file']['sha256']);V.canonical(c)
  with patch.object(os,'readlink',return_value='OTHER_TARGET'):
   for fn,exc in [(A.canonical_check,A.Stop),(V.canonical,V.Reject)]:
    with self.assertRaisesRegex(exc,N['changed_alias']):fn(c)
 def test_canonical_changed_source_and_reparse(self):
  from types import SimpleNamespace
  c=self.canonical_fixture();p=Path(c['canonical_preflight']['file']['path']);p.write_bytes(b'CHANGED!')
  with patch.object(os,'readlink',return_value='SYNTHETIC_TARGET'):
   with self.assertRaisesRegex(A.Stop,N['changed_source']):A.canonical_check(c)
   with self.assertRaisesRegex(V.Reject,'ARTIFACT_PIN'):V.canonical(c)
  old=Path.lstat
  def fake(q,*a,**k):
   z=old(q,*a,**k)
   return SimpleNamespace(st_dev=z.st_dev,st_ino=z.st_ino,st_mode=z.st_mode,st_file_attributes=1024) if q==p else z
  with patch.object(os,'readlink',return_value='SYNTHETIC_TARGET'),patch.object(Path,'lstat',fake):
   for fn,exc in [(A.canonical_check,A.Stop),(V.canonical,V.Reject)]:
    with self.assertRaisesRegex(exc,N['new_reparse']):fn(c)
if __name__=='__main__':unittest.main()''')
s=s.replace("O=json.loads(ob)","O=json.loads(ob)\nnb=(D/'oracle-c1c1.json').read_bytes();assert hashlib.sha256(nb).hexdigest()=='2f215d50773e5b84458ffe97e80b69f326b989c825dc216f779a566fb6af42f0';N=json.loads(nb)")
s=s.replace("image_identity=self.c['os_helper']['identity']","image_identity=list(self.c['os_helper']['identity'])")
p.write_text(s,encoding='utf-8')
files={}
for p in D.glob('*.py'):
 if p.name.startswith(('probe_','observe_','test_')):compile(p.read_bytes(),str(p),'exec');files[p.name]={'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
elapsed=time.time()-start;assert elapsed<=600
(D/'author-completion.json').write_text(json.dumps({'seconds':elapsed,'within_budget':True,'files':files,'role':'Codex local executor/integrator shared context','new_native_operations':0},indent=2))
print(json.dumps({'seconds':elapsed,'files':files}))
