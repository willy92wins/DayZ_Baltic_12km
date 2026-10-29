import copy,hashlib,json,os,struct,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest import mock
TOOLS=Path(os.environ['ROADC0_TOOL_DIR']);sys.path.insert(0,str(TOOLS))
import road_calibration_source_c0 as author
import verify_road_calibration_source_c0 as consumer
RAW=Path(os.environ['ROADC0_ORACLE']).read_bytes()
assert hashlib.sha256(RAW).hexdigest()=='c70cad59d72505d841acce60a3b34a041a2e9ac9dc3d6331f4ce896dc8bac590'
O=json.loads(RAW)
def sha(b):return hashlib.sha256(b).hexdigest()
class TestPair(unittest.TestCase):
 def setUp(self):
  base=Path(os.environ['ROADC0_TEST_ROOT']).resolve();base.mkdir(parents=True,exist_ok=True)
  self.tmp=tempfile.TemporaryDirectory(dir=base);self.root=Path(self.tmp.name).resolve();assert self.root.is_relative_to(base)
  self.addCleanup(self.tmp.cleanup);self.serial=0
 def fixture(self):
  self.serial+=1;r=self.root/str(self.serial);r.mkdir();src=r/'original.wrp';src.write_bytes(bytes.fromhex(O['source_hex']));pre=bytes.fromhex(O['prefix_hex'])
  c={'schema':'road-calibration-source-pair.v1','domain':'ISOLATED_LAB_ONLY','source':{'path':str(src),'sha256':sha(src.read_bytes()),'bytes':src.stat().st_size,'terrain_material_prefix_bytes':len(pre),'terrain_material_prefix_sha256':sha(pre),'source_pre_terminator_bytes':src.stat().st_size-56,'terminator_hex':O['terminator_hex']},'objects':[{'id':i,'raw_name_hex':n,'matrix48_hex':m,'record_bytes':len(bytes.fromhex(x))} for i,n,m,x in zip(O['record_ids'],O['record_names_hex'],O['matrix_hex'],O['record_hex'])],'output':str(r/'pair'),'consumer_result':str(r/'consumer/result.json'),'pins':{}}
  p=r/'contract.json';self.save(p,c);return p,c
 def save(self,p,c):p.write_text(json.dumps(c),encoding='utf-8');return sha(p.read_bytes())
 def create(self,p):return author.create(p,sha(p.read_bytes()))
 def verify(self,p):return consumer.verify(p,sha(p.read_bytes()))
 def fail(self,code,fn,*a):
  with self.assertRaises((author.Error,consumer.Error)) as cm:fn(*a)
  self.assertEqual(cm.exception.code,code)
 def test_literal_pair_and_separate_reader(self):
  p,c=self.fixture();src=Path(c['source']['path']).read_bytes();self.create(p);q=Path(c['output'])
  self.assertEqual((q/'control.wrp').read_bytes(),bytes.fromhex(O['expected_control_hex']))
  self.assertEqual((q/'candidate.wrp').read_bytes(),bytes.fromhex(O['expected_candidate_hex']))
  self.assertEqual(Path(c['source']['path']).read_bytes(),src);self.assertEqual(self.verify(p)['status'],'VERIFIED_ISOLATED_SOURCE_PAIR_ONLY')
  self.assertEqual(bytes.fromhex(O['matrix_hex'][0])[4:8],b'\0\0\0\x80')
 def test_cli_producer_and_consumer(self):
  p,c=self.fixture();pin=sha(p.read_bytes())
  for script in ('road_calibration_source_c0.py','verify_road_calibration_source_c0.py'):
   q=subprocess.run([sys.executable,'-I',str(TOOLS/script),'--contract',str(p),'--contract-sha256',pin],capture_output=True,timeout=15)
   self.assertEqual(q.returncode,0,q.stdout+q.stderr);self.assertIn('status',json.loads(q.stdout))
 def test_wrong_source_hash_and_external_contract_pin(self):
  p,c=self.fixture();self.fail('CONTRACT',author.create,p,'0'*64);self.fail('CONTRACT',consumer.verify,p,'0'*64)
  c['source']['sha256']='0'*64;self.save(p,c);self.fail('SOURCE_HASH',self.create,p)
  self.assertTrue((Path(c['output'])/'CONSUMED').exists());self.assertFalse((Path(c['output'])/'report.json').exists())
 def test_prefix_boundary_and_truncated_material(self):
  pre=bytes.fromhex(O['prefix_hex'])
  for b in (pre[:-1],pre[:25],pre[:-4]+b'\xff'*4,pre[:4]+b'\xff'*16+pre[20:]):
   self.fail('SOURCE_STRUCTURE',author.parse_prefix,b);self.fail('SOURCE_STRUCTURE',consumer.prefix_cursor,b)
  p,c=self.fixture();c['source']['terrain_material_prefix_bytes']-=1;c['source']['terrain_material_prefix_sha256']=sha(pre[:-1]);self.save(p,c);self.fail('SOURCE_STRUCTURE',self.create,p)
 def test_exact_output_mutations(self):
  prelen=len(bytes.fromhex(O['prefix_hex']))
  for file,offset in [('control.wrp',10),('candidate.wrp',prelen+4),('candidate.wrp',prelen+48),('candidate.wrp',prelen+56),('candidate.wrp',-12)]:
   with self.subTest(file=file,offset=offset):
    p,c=self.fixture();self.create(p);v=Path(c['output'])/file;b=bytearray(v.read_bytes());b[offset]^=1;v.write_bytes(b);self.fail('PAIR_STRUCTURE',self.verify,p)
 def test_extra_object_control_and_tail(self):
  for file,kind in [('control.wrp','object'),('candidate.wrp','tail'),('candidate.wrp','order')]:
   p,c=self.fixture();self.create(p);q=Path(c['output'])/file;b=q.read_bytes();n=len(bytes.fromhex(O['prefix_hex']))
   if kind=='object':b=b[:-56]+bytes.fromhex(O['record_hex'][0])+b[-56:]
   elif kind=='tail':b+=b'X'
   else:b=b[:n]+bytes.fromhex(O['record_hex'][1]+O['record_hex'][0]+O['record_hex'][2])+b[-56:]
   q.write_bytes(b);self.fail('PAIR_STRUCTURE',self.verify,p)
 def test_co_mutated_candidate_and_report(self):
  p,c=self.fixture();self.create(p);root=Path(c['output']);q=root/'candidate.wrp';b=bytearray(q.read_bytes());b[len(bytes.fromhex(O['prefix_hex']))+48]^=2;q.write_bytes(b)
  rp=root/'report.json';r=json.loads(rp.read_bytes());r['files']['candidate.wrp']['sha256']=sha(b);rp.write_text(json.dumps(r));self.fail('PAIR_STRUCTURE',self.verify,p)
 def test_report_type_claim_and_extra_fields(self):
  for key,value in [('control_objects',False),('build_ready',True),('bogus','value')]:
   p,c=self.fixture();self.create(p);rp=Path(c['output'])/'report.json';r=json.loads(rp.read_bytes());r[key]=value;rp.write_text(json.dumps(r));self.fail('REPORT_MISMATCH',self.verify,p)
 def test_contract_names_ids_and_matrix(self):
  for field,value in [('id',True),('id',12),('raw_name_hex',b'../a.p3d'.hex()),('raw_name_hex',b'a\xff.p3d'.hex()),('raw_name_hex',(b'a'*4097).hex()),('matrix48_hex','0000807f'+O['matrix_hex'][0][8:]),('record_bytes',True)]:
   p,c=self.fixture();c['objects'][0][field]=value;self.save(p,c)
   self.fail('CONTRACT',author.contract,p,sha(p.read_bytes()));self.fail('CONTRACT',consumer.settings,p,sha(p.read_bytes()))
 def test_caps_before_source_read(self):
  p,c=self.fixture();c['source']['bytes']=512*1024**2+1;self.save(p,c)
  self.fail('SOURCE_CAP',author.contract,p,sha(p.read_bytes()));self.fail('SOURCE_CAP',consumer.settings,p,sha(p.read_bytes()))
  p,c=self.fixture();c['source']['terrain_material_prefix_bytes']=32*1024**2;c['source']['bytes']=32*1024**2+56;c['source']['source_pre_terminator_bytes']=32*1024**2;self.save(p,c)
  self.fail('CONTRACT',author.contract,p,sha(p.read_bytes()));self.fail('CONTRACT',consumer.settings,p,sha(p.read_bytes()))
 def test_source_terminator_pin_and_reparse_simulation(self):
  p,c=self.fixture();src=Path(c['source']['path']);b=bytearray(src.read_bytes());b[-10]^=1;src.write_bytes(b);c['source']['sha256']=sha(b);self.save(p,c);self.fail('SOURCE_STRUCTURE',self.create,p)
  fake=type('Stat',(),{'st_mode':0,'st_file_attributes':1024})()
  with mock.patch.object(Path,'lstat',return_value=fake):
   self.fail('REPARSE',author.guard_path,Path(c['source']['path']));self.fail('REPARSE',consumer.no_links,Path(c['source']['path']))
 def test_changed_identity_and_exclusive_outputs(self):
  p,c=self.fixture();real=author.stamp;count=[0]
  def changing(s):
   count[0]+=1;x=real(s)
   if count[0]>1:x[-1]+=1
   return x
  with mock.patch.object(author,'stamp',side_effect=changing):self.fail('SOURCE_CHANGED',author.source,c)
  p,c=self.fixture();self.create(p);self.fail('OUTPUT_EXISTS',self.create,p);self.verify(p);self.fail('OUTPUT_EXISTS',self.verify,p)
 def test_pins_and_wrong_contract_schema(self):
  p,c=self.fixture();c['pins']={str(p.parent/'x.json'):'0'*64};(p.parent/'x.json').write_bytes(b'{}');self.save(p,c);self.fail('CONTRACT',author.contract,p,sha(p.read_bytes()));self.fail('CONTRACT',consumer.settings,p,sha(p.read_bytes()))
  p,c=self.fixture();c['source']['bytes']=True;self.save(p,c);self.fail('CONTRACT',author.contract,p,sha(p.read_bytes()));self.fail('CONTRACT',consumer.settings,p,sha(p.read_bytes()))
 def test_missing_io_and_internal_errors_stay_errors(self):
  p,c=self.fixture();Path(c['source']['path']).unlink()
  q=subprocess.run([sys.executable,'-I',str(TOOLS/'road_calibration_source_c0.py'),'--contract',str(p),'--contract-sha256',sha(p.read_bytes())],capture_output=True,timeout=15)
  self.assertEqual(q.returncode,2);self.assertEqual(json.loads(q.stdout)['code'],'IO_ERROR')
if __name__=='__main__':unittest.main()
