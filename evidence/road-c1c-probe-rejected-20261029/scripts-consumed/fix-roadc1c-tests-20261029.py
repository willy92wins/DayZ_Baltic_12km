from pathlib import Path
import json,time,hashlib
D=Path('E:/DayZ-Baltic-Build/shape-repair-20261025/road-c1c-local-author-20261029');p=D/'test_probe_road_compile_c1c.py';s=p.read_text();s=s.replace('import hashlib,importlib.util,json,os,sys,tempfile,time,unittest,copy','import hashlib,importlib.util,json,os,sys,tempfile,time,unittest,copy\nfrom unittest.mock import patch')
s=s.replace("self.phase={'receipt':self.receipt,'logs':self.logs,'artifacts':[self.art]};self.c={'root':str(self.r),'tools':{'binarize':{'sha256':self.ih}},'tool_files':[{'dest':'AddonBuilder.exe','sha256':self.ih}]}",'''self.rootimage=self.r/'tools/AddonBuilder/AddonBuilder.exe';self.rootimage.parent.mkdir(parents=True);self.rootimage.write_bytes(b'ROOT SYNTHETIC');self.rh=rec(self.rootimage)['sha256']
  self.c={'root':str(self.r),'tool_root':'SYNTHETIC_TOOLS','prefix':'literal/addon','tools':{k:{'path':str(self.image),'sha256':self.ih} for k in ['binarize','cfgConvert','fileBank','dsSignFile']},'tool_files':[{'dest':'AddonBuilder.exe','sha256':self.rh}]}
  project=self.r/'work/control/root';out=self.r/'output/control';args=[str(project/'literal/addon'),str(out/'out'),'-prefix=literal\\\\addon','-project='+str(project),'-temp='+str(out/'temp'),'-include='+str(self.r/'fixed/include.lst'),'-exclude='+str(self.r/'fixed/exclude.lst'),'-binarizeFullLogs','-toolsDirectory=SYNTHETIC_TOOLS']+['-'+k+'='+str(self.image) for k in ['binarize','cfgConvert','fileBank','dsSignFile']]
  self.receipt.update(command=[str(self.rootimage),*args],cwd=str(self.rootimage.parent));self.receipt['identities']['122']=now-1;self.receipt['observed_processes'].append({'pid':122,'birth':now-1,'observed_at':now,'exe':str(self.rootimage),'argv':self.receipt['command'],'image_path_sha256':self.rh})
  self.phase={'receipt':self.receipt,'logs':self.logs,'artifacts':[self.art]}''')
s=s.replace("self.ih,{self.ih})","self.ih,{self.ih,self.rh})")
s=s.replace("self.receipt['observed_processes']=[];", "self.receipt['observed_processes']=self.receipt['observed_processes'][1:];self.receipt['identities'].pop('123');")
start=s.index(' def test_candidate_requires_control(self):');end=s.index(' def test_real_child_receipt',start)
s=s[:start]+''' def test_candidate_requires_control(self):
  for status,mutate in [('PROCESS_REJECTED',False),('ARTIFACT_OBSERVED_ONLY',True)]:
   with self.subTest(status=status):
    base=self.r/str(mutate);base.mkdir();root=base/'probe';source=base/'source';h=hashlib.sha256(b'x').hexdigest()
    for arm in ['control','candidate']:q=source/arm/'root/x';q.parent.mkdir(parents=True);q.write_bytes(b'x')
    def row(p):return {k:v for k,v in rec(p).items() if k in ['path','bytes','sha256']}
    logger=D/'logger-fixture.xml';inc=base/'include';inc.write_bytes(b'x');exc=base/'exclude';exc.write_bytes(b'');pre=base/'pre';pre.write_bytes(b'pass')
    c={'root':str(root),'source_stage':str(source),'c1b_consumer':row(pre),'profile_roots':[],'prefix':'literal','tool_root':'SYNTHETIC','claims':{},'caps':{'total_seconds':1050,'observe_seconds':120},'tool_files':[{**row(self.rootimage),'dest':'AddonBuilder.exe'},{**row(logger),'dest':'logger.xml'}],'tools':{k:row(self.image) for k in ['binarize','cfgConvert','fileBank','dsSignFile']},'include':row(inc),'exclude':row(exc),'preflight':row(pre),'preflight_original':row(pre)}
    calls=[];checks=[]
    def proc(cmd,cwd,out,*args):
     phase='preflight' if cmd[0]==sys.executable else ('help' if '-help' in cmd else 'control' if 'control' in str(cmd) else 'candidate');calls.append(phase);return {'rc':0,'reason':None}
    def trees(c,targets,deadline):
     checks.append(str(targets));
     if mutate and len(checks)==4:raise A.Stop('SOURCE_CHANGED')
     return []
    with patch.object(A,'expected',return_value={a:{'x':(1,h)} for a in ['control','candidate']}),patch.object(A,'trees',side_effect=trees),patch.object(A,'proc_run',side_effect=proc),patch.object(A,'snapshot_logs',return_value=[]),patch.object(A,'command_check'),patch.object(A,'gate',side_effect=['HELP_OBSERVED',status]):
     result=A.mainrun(c,'literal')
    self.assertEqual(calls,['preflight','help','control']);self.assertEqual(result['status'],'PROBE_STOPPED');self.assertIn('WORK_INPUT_MUTATED' if mutate else status,result['reason'])
 def test_unmapped_identity(self):
  self.receipt['identities']['999']=time.time()-1;self.assertEqual(self.gate(),'PROBE_INCONCLUSIVE_NOT_OBSERVED')
  with self.assertRaisesRegex(V.Reject,'PROBE_INCONCLUSIVE_NOT_OBSERVED'):V.arm_check(self.c,self.phase)
 def test_command_binding(self):
  self.receipt['command']=['WRONG INPUT']
  with self.assertRaisesRegex(A.Stop,'ARG_BINDING'):A.command_check(self.c,self.receipt,'control')
  with self.assertRaisesRegex(V.Reject,'ARG_BINDING'):V.arm_check(self.c,self.phase)
 def test_help_unexpected_child(self):
  self.receipt['observed_processes'][0]['image_path_sha256']='0'*64
  self.assertEqual(A.gate(self.receipt,self.logs,[],self.ih,{self.rh},True),'UNEXPECTED_CHILD')
 def test_private_marker_required(self):
  p=Path(self.logs[2]['path']);p.write_text('diagnostic');self.logs[2]=rec(p);self.assertEqual(self.gate(),'NO_MARKER')
 def test_profile_and_portable_pins(self):
  row=rec(self.rootimage);row['dest']='AddonBuilder.exe';c={**self.c,'tool_files':[row]};A.portable_check(c,self.rootimage.parent,b'','control');self.rootimage.write_bytes(b'CHANGED')
  with self.assertRaises(A.Stop):A.portable_check(c,self.rootimage.parent,b'','control')
  with self.assertRaises(V.Reject):V.portable(c,'control')
 def test_preflight_unique_delta(self):
  raw=(D/'preflight-original.py').read_bytes();fixed=(D/'preflight-local.py').read_bytes()
  with self.assertRaises(SyntaxError) as got:compile(raw,'original','exec')
  self.assertEqual(got.exception.lineno,213);compile(fixed,'local','exec');a=raw.splitlines(keepends=True);b=fixed.splitlines(keepends=True);self.assertEqual(len(a),len(b));diff=[i for i in range(len(a)) if a[i]!=b[i]];self.assertEqual(diff,[212]);self.assertEqual(b[212],a[212].replace(b"'subst",b"r'subst",1))
 def test_report_pin_comutation(self):
  p=self.r/'report.json';raw=b'{"status":"PROBE_STOPPED"}';p.write_bytes(raw);pin=hashlib.sha256(raw).hexdigest();p.write_bytes(b'{"status":"COMPILE_PROBE_OBSERVED_ONLY"}');os.utime(p,(self.receipt['started']+1,)*2)
  with self.assertRaisesRegex(V.Reject,'PIN'):V.readjson(p,pin)
 def test_observed_grandchild(self):
  child="import subprocess,sys,time;subprocess.Popen([sys.executable,'-I','-c','import time;time.sleep(4)']);time.sleep(4)"
  r=A.proc_run([sys.executable,'-I','-c',child],self.r,self.r/'grandchild',.6,268435456);self.assertEqual(r['reason'],'TIMEOUT');self.assertGreaterEqual(len(r['identities']),2)
  for pid,birth in r['identities'].items():
   try:self.assertNotEqual(A.psutil.Process(int(pid)).create_time(),birth)
   except A.psutil.NoSuchProcess:pass
''' +s[end:]
p.write_text(s,encoding='utf-8');started=json.loads((D/'correction-start.json').read_bytes())['started'];dump={'seconds':time.time()-started,'budget':180,'within_budget':time.time()-started<=180,'files':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in D.glob('*.py')}};(D/'correction-completion.json').write_text(json.dumps(dump,indent=2),encoding='utf-8');print(json.dumps(dump))
