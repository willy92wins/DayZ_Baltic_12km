import copy,hashlib,importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from types import SimpleNamespace
D=Path(__file__).parent
def module(name):
 s=importlib.util.spec_from_file_location(name,D/(name+'.py'));m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
A=module('stage_road_lab_c1b');V=module('verify_road_lab_c1b')
ORACLE=D/'oracle.json';ORACLE_SHA='677c4561ac867a0fbfc5a1edeaf1da59b6b63c03063821154cedc549b91d5429'
assert hashlib.sha256(ORACLE.read_bytes()).hexdigest()==ORACLE_SHA
L=json.loads(ORACLE.read_bytes())
def digest(b):return hashlib.sha256(b).hexdigest()
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.d=Path(self.tmp.name);self.out=self.d/'pair';files=[]
  for scope in ('common','control','candidate'):
   for name,text in L[scope].items():
    src=self.d/'source'/scope/name;src.parent.mkdir(parents=True,exist_ok=True);src.write_bytes(text.encode());s=src.stat();b=text.encode()
    files.append({'scope':scope,'dest':name,'bytes':len(b),'sha256':digest(b),'sources':[{'path':str(src),'identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns],'bytes':len(b),'sha256':digest(b),'origin':'LITERAL'}]})
  self.bind=self.d/'bindings.json';self.bind.write_text(json.dumps([{'scope':f['scope'],'dest':f['dest'],'sources':[s['path'] for s in f['sources']]} for f in files]));self.bp=digest(self.bind.read_bytes())
  self.c={'schema':'road-c1b-stage.v1','caps':{'entries':8192,'file':33554432,'common':402653184,'pair':1073741824,'json':8388608},'claims':L['claims'],'config_refs':[],'files':files,'bindings':{'path':str(self.bind),'sha256':self.bp},'output':str(self.out)};self.cp=self.d/'contract.json';self.write()
 def tearDown(self):self.tmp.cleanup()
 def write(self):self.cp.write_text(json.dumps(self.c));self.pin=digest(self.cp.read_bytes())
 def independent_stage(self):
  for arm in ('control','candidate'):
   for name,text in {**L['common'],**L[arm]}.items():
    p=self.out/arm/'root'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(text.encode())
 def check_stage(self):
  c,e,s=V.read_contract(self.cp,self.pin,self.bp);return V.verify(c,e,s,self.pin)
 def both_reject(self,code):
  self.write()
  for f,ex in [(A.contract,A.Rejected),(V.read_contract,V.Invalid)]:
   with self.subTest(reader=f.__module__),self.assertRaisesRegex(ex,'^'+code+'$'):f(self.cp,self.pin,self.bp)
 def test_independent_literal_pair(self):
  self.independent_stage();r=self.check_stage();self.assertEqual(r,{'status':'VERIFIED_LAB_STAGE_BYTES_ONLY','contract_sha256':self.pin,'STAGE_BYTES':'MATCH','SOURCE_PIN_MATCH':'MATCH','stage_errors':[],'source_errors':[],'stage_files_verified':6,'source_aliases_checked':4,'claims':L['claims'],'continuous_monitoring':False})
 def test_author_and_consumer_cli(self):
  for file,extra in [('stage_road_lab_c1b.py',[]),('verify_road_lab_c1b.py',['--report',str(self.d/'consumer.json')])]:
   r=subprocess.run([sys.executable,'-I','-X','utf8',str(D/file),'--contract',str(self.cp),'--sha',self.pin,'--bindings-sha',self.bp,*extra],capture_output=True,text=True,timeout=15);self.assertEqual(r.returncode,0,r.stdout+r.stderr)
  self.assertEqual(json.loads((self.d/'consumer.json').read_bytes())['stage_files_verified'],6)
 def test_stage_tamper(self):
  self.independent_stage();(self.out/'candidate/root/config.cpp').write_bytes(b'class Xab {};\n');r=self.check_stage();self.assertEqual((r['STAGE_BYTES'],r['SOURCE_PIN_MATCH']),('REJECTED','MATCH'));self.assertIn('STAGE_HASH',str(r['stage_errors']))
 def test_missing(self):
  self.independent_stage();(self.out/'control/root/lab.wrp').unlink();r=self.check_stage();self.assertIn('MISSING',str(r['stage_errors']))
 def test_extra_file(self):
  self.independent_stage();(self.out/'control/root/extra.txt').write_bytes(b'x');self.assertIn('EXTRA',str(self.check_stage()['stage_errors']))
 def test_extra_empty_directory(self):
  self.independent_stage();(self.out/'control/root/unlisted').mkdir();self.assertIn('EXTRA',str(self.check_stage()['stage_errors']))
 def test_source_drift_separated(self):
  self.independent_stage();Path(self.c['files'][0]['sources'][0]['path']).write_bytes(b'changed\n');r=self.check_stage();self.assertEqual((r['STAGE_BYTES'],r['SOURCE_PIN_MATCH']),('MATCH','REJECTED'))
 def test_co_mutant_png_redirect(self):
  f=self.c['files'][0];src=self.d/'unapproved.paa';src.write_bytes(b'fake PAA');s=src.stat();f['sha256']=digest(src.read_bytes());f['bytes']=s.st_size;f['sources']=[{'path':str(src),'identity':[s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns],'sha256':f['sha256'],'bytes':f['bytes'],'origin':'LITERAL'}];self.both_reject('BINDING')
 def test_closed_path_set(self):
  orig=copy.deepcopy(self.c)
  for bad in ['../outside','/outside','c:/outside','data\\a.png','nul.txt','data/end.','data/UP.png','data/a:stream','data/../x']:
   with self.subTest(bad=bad):self.c=copy.deepcopy(orig);self.c['files'][0]['dest']=bad;self.both_reject('PATH')
 def test_collision(self):
  self.c['files'].insert(1,copy.deepcopy(self.c['files'][0]));self.both_reject('COLLISION')
 def test_bool_size(self):self.c['files'][0]['bytes']=True;self.both_reject('SIZE_TYPE')
 def test_wrong_contract_pin(self):
  for f,ex in [(A.contract,A.Rejected),(V.read_contract,V.Invalid)]:
   with self.assertRaisesRegex(ex,'CONTRACT_PIN'):f(self.cp,'0'*64,self.bp)
 def test_existing_output(self):
  self.independent_stage()
  with self.assertRaisesRegex(A.Rejected,'EXISTS'):A.run(A.contract(self.cp,self.pin,self.bp),self.pin)
 def test_wrong_wrp(self):
  self.independent_stage();(self.out/'candidate/root/lab.wrp').write_bytes(L['control']['lab.wrp'].encode());self.assertEqual(self.check_stage()['STAGE_BYTES'],'REJECTED')
 def test_reparse_simulated(self):
  target=Path(self.c['files'][0]['sources'][0]['path']);original=Path.lstat
  def patched(p,*a,**kw):
   s=original(p,*a,**kw)
   return SimpleNamespace(st_mode=s.st_mode,st_file_attributes=1024) if p==target else s
  with patch.object(Path,'lstat',patched):
   with self.assertRaisesRegex(A.Rejected,'REPARSE'):A.transfer(self.c['files'][0]['sources'][0],[])
   with self.assertRaisesRegex(V.Invalid,'REPARSE'):V.hashed(target,1000)
 def test_alias_identity_and_caps(self):
  orig=copy.deepcopy(self.c);s=copy.deepcopy(self.c['files'][0]['sources'][0]);s['identity'][1]+=1;self.c['files'][0]['sources'].append(s);self.both_reject('COLLISION')
  self.c=orig;self.c['caps']['file']=33554433;self.both_reject('SCHEMA')
if __name__=='__main__':unittest.main()
