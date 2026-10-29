from pathlib import Path
import hashlib,importlib.util,json,os,sys,tempfile,time,unittest,copy
D=Path(__file__).parent
def mod(name):
 s=importlib.util.spec_from_file_location(name,D/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=mod('probe_road_compile_c1c');V=mod('observe_road_compile_c1c')
ob=(D/'oracle.json').read_bytes();assert hashlib.sha256(ob).hexdigest()=='0a809df80c7766f114a5c330418145fa9a831dab80ccd593486a9e5a84de236b';O=json.loads(ob)
def rec(p):
 b=p.read_bytes();s=p.stat();return {'path':str(p),'sha256':hashlib.sha256(b).hexdigest(),'bytes':len(b),'identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns]}
class Tests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.r=Path(self.t.name);self.image=self.r/'image.exe';self.image.write_bytes(b'SYNTHETIC IMAGE ONLY');self.ih=rec(self.image)['sha256'];self.logs=[]
  for rel,text in [('process/control/stdout',O['positive_log']),('process/control/stderr',''),('logs/control/AddonBuilder.rpt',O['positive_log'])]:
   p=self.r/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode());self.logs.append(rec(p))
  self.w=self.r/'output/control/temp/probe.wrp';self.w.parent.mkdir(parents=True);self.w.write_bytes(bytes.fromhex(O['valid_header_hex']));self.art=rec(self.w);self.art['header_hex']=self.w.read_bytes()[:8].hex();now=time.time()
  self.receipt={'started':now-2,'finished':now+2,'rc':0,'reason':None,'identities':{'123':now-1},'observed_processes':[{'pid':123,'birth':now-1,'observed_at':now,'exe':str(self.image),'image_path_sha256':self.ih,'argv':['literal synthetic']}]}
  self.phase={'receipt':self.receipt,'logs':self.logs,'artifacts':[self.art]};self.c={'root':str(self.r),'tools':{'binarize':{'sha256':self.ih}},'tool_files':[{'dest':'AddonBuilder.exe','sha256':self.ih}]}
 def tearDown(self):self.t.cleanup()
 def gate(self,wrps=None):return A.gate(self.receipt,self.logs,[self.w] if wrps is None else wrps,self.ih,{self.ih})
 def test_literal_positive(self):self.assertEqual(self.gate(),O['expected_positive']);self.assertEqual(V.arm_check(self.c,self.phase)['raw_header_hex'],O['valid_header_hex'][:16])
 def test_nonzero_and_timeout(self):
  self.receipt['rc']=1;self.assertEqual(self.gate(),O['expected_nonzero']);self.receipt['reason']='TIMEOUT';self.assertEqual(self.gate(),O['expected_timeout'])
 def test_logs_fail_closed(self):
  for text in O['negative_logs']:
   p=Path(self.logs[0]['path']);p.write_text(text);self.logs[0]=rec(p)
   q=Path(self.logs[2]['path']);q.write_text('');self.logs[2]=rec(q)
   self.assertNotEqual(self.gate(),O['expected_positive'])
 def test_no_marker(self):
  for i in [0,2]:p=Path(self.logs[i]['path']);p.write_text('diagnostic');self.logs[i]=rec(p)
  self.assertEqual(self.gate(),O['expected_missing_marker'])
 def test_no_child(self):
  self.receipt['observed_processes']=[];self.assertEqual(self.gate(),O['expected_no_child'])
  with self.assertRaisesRegex(V.Reject,O['expected_no_child']):V.arm_check(self.c,self.phase)
 def test_bad_child(self):self.receipt['observed_processes'][0]['image_path_sha256']='0'*64;self.assertEqual(self.gate(),O['expected_bad_image'])
 def test_old_log(self):
  p=Path(self.logs[2]['path']);os.utime(p,(1,1));self.logs[2]=rec(p);self.assertEqual(self.gate(),O['expected_old_log'])
 def test_source_magic_and_comutation(self):
  self.w.write_bytes(bytes.fromhex(O['source_header_hex']));self.phase['artifacts'][0]=rec(self.w);self.phase['artifacts'][0]['header_hex']=self.w.read_bytes()[:8].hex();self.assertEqual(self.gate(),O['expected_source_header'])
  with self.assertRaisesRegex(V.Reject,'WRP_MAGIC'):V.arm_check(self.c,self.phase)
 def test_multiple_unreported_wrps(self):
  other=self.w.parent/'extra.wrp';other.write_bytes(self.w.read_bytes());self.assertEqual(self.gate([self.w,other]),O['expected_multiple'])
  with self.assertRaisesRegex(V.Reject,'WRP_COUNT'):V.arm_check(self.c,self.phase)
 def test_artifact_pin(self):
  self.phase['artifacts'][0]['sha256']='0'*64
  with self.assertRaisesRegex(V.Reject,O['expected_co_mutant']):V.arm_check(self.c,self.phase)
 def test_foreign_log(self):
  p=self.r/'unrelated.rpt';p.write_text(O['positive_log']);self.phase['logs'][2]=rec(p)
  with self.assertRaisesRegex(V.Reject,'LOG_BINDING'):V.arm_check(self.c,self.phase)
 def test_changed_and_extra_tree(self):
  p=self.r/'tree/data';p.mkdir(parents=True);q=p/'x';q.write_bytes(b'literal');expected={'data/x':(7,hashlib.sha256(b'literal').hexdigest())};self.assertEqual(V.stage_check(p.parent,expected,float('inf')),1)
  q.write_bytes(b'changed')
  with self.assertRaisesRegex(V.Reject,'ARTIFACT_PIN'):V.stage_check(p.parent,expected,float('inf'))
  q.write_bytes(b'literal');(p/'extra').write_bytes(b'x')
  with self.assertRaisesRegex(V.Reject,'EXTRA'):V.stage_check(p.parent,expected,float('inf'))
 def test_logger_delta(self):
  raw=(D/'logger-fixture.xml').read_bytes();dest=[self.r/n for n in ['a.rpt','b.rpt','c.rpt']];out=A.logger_bytes(raw,dest);A.verify_logger(raw,out,dest)
  with self.assertRaisesRegex(A.Stop,O['expected_extra_logger_change']):A.verify_logger(raw,out.replace(b'DEBUG',b'ERROR'),dest)
 def test_candidate_requires_control(self):
  for status in ['WRP_COUNT','PROCESS_REJECTED','TIMEOUT','PROBE_INCONCLUSIVE_NOT_OBSERVED']:
   self.assertFalse(status==O['expected_positive'])
  self.assertEqual(O['candidate_requires'],'control.status == ARTIFACT_OBSERVED_ONLY')
 def test_real_child_receipt_and_timeout(self):
  ok=A.proc_run([sys.executable,'-I','-c','print("literal child")'],self.r,self.r/'child',5,268435456);self.assertEqual((ok['rc'],ok['reason']),(0,None));self.assertTrue(ok['identities']);self.assertEqual(Path(ok['stdout']['path']).read_text().strip(),'literal child')
  bad=A.proc_run([sys.executable,'-I','-c','import time;time.sleep(4)'],self.r,self.r/'timeout',.25,268435456);self.assertEqual(bad['reason'],'TIMEOUT')
  for pid,birth in bad['identities'].items():
   try:p=A.psutil.Process(int(pid));self.assertNotEqual(p.create_time(),birth)
   except A.psutil.NoSuchProcess:pass
if __name__=='__main__':unittest.main()
