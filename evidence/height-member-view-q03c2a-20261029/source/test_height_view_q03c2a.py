"""Literal NPY oracles, independent ZIP fixture assembly and CLI/co-mutants."""
from pathlib import Path
import sys,os,json,hashlib,struct,zlib,tempfile,unittest,subprocess,io,zipfile,copy
sys.path.insert(0,str(Path(__file__).parent))
import height_view_producer_q03c2a as P
import height_view_consumer_q03c2a as C
D=Path(__file__).parent;CONTRACT=D/'contract.json';SHA='33de008a5f62c60e86bc28ae90be5b35033fd899b0042bb7e15077ce461924ea';assert P.sha(CONTRACT.read_bytes())==SHA;c=json.loads(CONTRACT.read_bytes());oracle=json.loads((D/'oracle.json').read_bytes());assert P.sha((D/'oracle.json').read_bytes())==c['oracle']['sha256']
def archive(npy,method=8,level=6,zip64=False,aux_declared=134217729,names=('aux.npy','heights.npy')):
 local=[];central=[];offset=0
 for name in names:
  data=npy if name=='heights.npy' else b'auxiliary intentionally not decoded';rawname=name.encode();declared=len(data) if name=='heights.npy' else aux_declared
  if method==8:
   obj=zlib.compressobj(level,zlib.DEFLATED,-15);packed=obj.compress(data)+obj.flush()
  else:packed=data
  crc=zlib.crc32(data);extra=struct.pack('<HHQQ',1,16,declared,len(packed)) if zip64 else b''
  chunk=struct.pack('<4s5H3I2H',b'PK\x03\x04',45 if zip64 else 20,0,method,0,0,crc,0xffffffff if zip64 else len(packed),0xffffffff if zip64 else declared,len(rawname),len(extra))+rawname+extra+packed
  entry=struct.pack('<4s6H3I5H2I',b'PK\x01\x02',20,45 if zip64 else 20,0,method,0,0,crc,len(packed),declared,len(rawname),0,0,0,0,0,offset)+rawname
  local.append(chunk);central.append(entry);offset+=len(chunk)
 body=b''.join(local);directory=b''.join(central);return body+directory+struct.pack('<4s4H2IH',b'PK\x05\x06',0,0,len(names),len(names),len(directory),len(body),0)
class Tests(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory(dir=os.environ.get('Q03C2A_TEST_ROOT'));self.root=Path(self.tmp.name);self.c,self.I,self.rd=P.bootstrap(CONTRACT,SHA)
 def tearDown(self):self.tmp.cleanup()
 def raw(self,id=0,**kw):return archive(bytes.fromhex(oracle['fixtures'][id]['npy_hex']),**kw)
 def file(self,data,name='source.npz'):p=self.root/name;p.write_bytes(data);return p
 def reject(self,fn,code=None):
  with self.assertRaises(Exception) as e:fn()
  self.assertTrue(hasattr(e.exception,'code'),repr(e.exception))
  if code:self.assertEqual(e.exception.code,code)
 def checks(self,data,code=oracle['negative_codes']['directory']):
  for fn in (P.metadata,C.directory):self.reject(lambda:fn(data,['aux.npy','heights.npy'],self.rd.archive),code)
 def pair(self,data,id=0):
  p=self.file(data);out=self.root/'capture';proof=self.root/'consumer';shape=oracle['fixtures'][id]['shape'];digest=P.sha(data)
  r=P.run(CONTRACT,SHA,out,str(p),digest,shape);v=C.run(CONTRACT,SHA,out,proof,str(p),digest,shape);return r,v,out
 def test_literal_versions_stored_deflated_zip64(self):
  for id,method,z64 in ((0,0,False),(0,8,True),(1,8,False)):
   with self.subTest(id=id,method=method,zip64=z64):
    data=self.raw(id,method=method,zip64=z64);names=['aux.npy','heights.npy'];a=P.metadata(data,names,self.rd.archive);b=C.directory(data,names,self.rd.archive);self.assertEqual(a,b)
    view,row=P.project(data,a);desc,header,h=P.inspect_view(view,self.I,self.rd,{'dtypes':['<f8'],'shape':oracle['fixtures'][id]['shape'],'fortran_order':False})
    self.assertEqual(h,P.sha(bytes.fromhex(oracle['fixtures'][id]['npy_hex'])))
    self.assertEqual(struct.unpack_from('<H',view,len(view)-14)[0],oracle['eocd_count']);self.assertEqual(self.rd.archive._central(view,{'heights.npy':None},self.rd.session.limits)[0][0]['offset'],oracle['view_central_local_offset'])
    with zipfile.ZipFile(io.BytesIO(view)) as z:self.assertEqual(z.namelist(),oracle['output_member_names']);self.assertEqual(z.read('heights.npy'),bytes.fromhex(oracle['fixtures'][id]['npy_hex']))
 def test_real_cli_pair_and_no_aux_decoding(self):
  data=self.raw(1,zip64=True);src=self.file(data);out=self.root/'cap';proof=self.root/'proof'
  for mod,extra in (('height_view_producer_q03c2a.py',[]),('height_view_consumer_q03c2a.py',['--capture',str(out)])):
   cmd=[sys.executable,'-I','-X','utf8',str(D/mod),'--contract',str(CONTRACT),'--sha',SHA,'--fixture',str(src),'--fixture-sha',P.sha(data),'--fixture-shape','matrix','--out',str(out if not extra else proof),*extra]
   r=subprocess.run(cmd,capture_output=True,timeout=20);self.assertEqual(r.returncode,0,r.stderr.decode())
  result=json.loads((proof/'consumer.json').read_bytes());self.assertEqual(result['status'],'VERIFIED_SINGLE_HEIGHT_MEMBER_VIEW_ONLY');self.assertFalse(result['claims']['other_payloads_decoded']);self.assertIs(result['fixture'],True)
  report=json.loads((out/'report.json').read_bytes());self.assertGreater(report['declared_expanded_sum_observed'],134217728)
  # Deliberately short auxiliary stream cannot satisfy its declared size; pair succeeds only without reading it.
  self.assertEqual(report['metadata_rows'][0]['expanded'],oracle['aux_declared_expanded'])
 def test_recompressed_same_npy_fails_provenance(self):
  data=self.raw();r,v,out=self.pair(data);alternate=self.raw(level=0);view,_=P.project(alternate,P.metadata(alternate,['aux.npy','heights.npy'],self.rd.archive));(out/'heights-view.npz').write_bytes(view)
  with zipfile.ZipFile(io.BytesIO(view)) as z:self.assertEqual(z.read('heights.npy'),bytes.fromhex(oracle['fixtures'][0]['npy_hex']))
  self.reject(lambda:C.run(CONTRACT,SHA,out,self.root/'bad',str(self.root/'source.npz'),P.sha(data),[2]),oracle['negative_codes']['recompressed'])
 def test_equal_payload_wrong_source_and_report_mutant(self):
  data=self.raw();r,v,out=self.pair(data);r['declared_expanded_sum_observed']-=1;(out/'report.json').write_text(json.dumps(r));self.reject(lambda:C.run(CONTRACT,SHA,out,self.root/'bad',str(self.root/'source.npz'),P.sha(data),[2]),'REPORT')
  self.reject(lambda:P.run(CONTRACT,SHA,self.root/'fail',str(self.root/'source.npz'),'0'*64,[2]),oracle['negative_codes']['source_pin'])
 def test_central_negative_layouts(self):
  raw=self.raw();rows=P.metadata(raw,['aux.npy','heights.npy'],self.rd.archive);c0=rows[0]['central_offset'];c1=rows[1]['central_offset']
  variants=[]
  for off,width,val in [(c0+24,4,0xffffffff),(c0+20,4,0xffffffff),(c0+42,4,0xffffffff),(c0+30,2,1),(c0+32,2,1),(c0+34,2,1),(c1+42,4,0)]:
   b=bytearray(raw);b[off:off+width]=val.to_bytes(width,'little');variants.append(bytes(b))
  variants += [raw[:-1],raw+b'x',b'x'+raw]
  for b in variants:self.checks(b)
 def test_names_flags_methods_and_local_mismatch(self):
  raw=self.raw();rows=P.metadata(raw,['aux.npy','heights.npy'],self.rd.archive);off=rows[1]['offset'];cent=rows[1]['central_offset']
  for pos,width,val,code in [(off+6,2,8,'ZIP_LAYOUT_UNSUPPORTED'),(cent+8,2,8,'ZIP_LAYOUT_UNSUPPORTED'),(cent+8,2,1,'ZIP_ENCRYPTED'),(cent+10,2,99,'ZIP_COMPRESSION'),(off+14,4,123,'ZIP_LAYOUT_UNSUPPORTED'),(off+18,4,0,'ZIP_LAYOUT_UNSUPPORTED')]:
   b=bytearray(raw);b[pos:pos+width]=val.to_bytes(width,'little');self.checks(bytes(b),code)
  for names,code in [(('heights.npy','heights.npy'),'ZIP_LAYOUT_UNSUPPORTED'),(('aux.npy','../height.npy'),'ZIP_PATH'),(('heights.npy','aux.npy'),'ZIP_LAYOUT_UNSUPPORTED')]:self.checks(self.raw(names=names),code)
 def test_zip64_local_fields(self):
  raw=self.raw(zip64=True);rows=P.metadata(raw,['aux.npy','heights.npy'],self.rd.archive);off=rows[1]['offset'];extra=off+30+len('heights.npy')
  for pos in (extra,extra+4,extra+12):
   b=bytearray(raw);b[pos]^=1;self.checks(bytes(b))
 def test_selected_cap_before_decode(self):
  raw=self.raw();rows=P.metadata(raw,['aux.npy','heights.npy'],self.rd.archive);rows[1]['expanded']=33570829
  self.reject(lambda:P.project(raw,rows),oracle['negative_codes']['selected_cap'])
 def test_physical_crc_truncation_and_hidden_tail(self):
  npy=bytes.fromhex(oracle['fixtures'][0]['npy_hex'])
  for contents in (npy+b'EXTRA',npy[:-1]):
   raw=archive(contents);rows=P.metadata(raw,['aux.npy','heights.npy'],self.rd.archive);view,_=P.project(raw,rows)
   self.reject(lambda:P.inspect_view(view,self.I,self.rd,{'dtypes':['<f8'],'shape':[2],'fortran_order':False}),oracle['negative_codes']['schema'])
  raw=self.raw();rows=P.metadata(raw,['aux.npy','heights.npy'],self.rd.archive);b=bytearray(raw);b[rows[1]['data_stop']-1]^=255
  view,_=P.project(bytes(b),rows);self.reject(lambda:P.inspect_view(view,self.I,self.rd,{'dtypes':['<f8'],'shape':[2],'fortran_order':False}),oracle['negative_codes']['stream'])
 def test_unknown_dtype_shape_order_header(self):
  npy=bytes.fromhex(oracle['fixtures'][0]['npy_hex'])
  for payload in (npy.replace(b'<f8',b'<i8'),npy.replace(b'False',b'True '),npy.replace(b'(2,)',b'(3,)')):
   raw=archive(payload);view,_=P.project(raw,P.metadata(raw,['aux.npy','heights.npy'],self.rd.archive));self.reject(lambda:P.inspect_view(view,self.I,self.rd,{'dtypes':['<f8'],'shape':[2],'fortran_order':False}),oracle['negative_codes']['schema'])
 def test_co_mutated_claim_still_rejected(self):
  data=self.raw();r,v,out=self.pair(data);r['claims']['whole_source_archive_validated']=True;self.assertFalse(P.CLAIMS['whole_source_archive_validated']);(out/'report.json').write_text(json.dumps(r));self.reject(lambda:C.run(CONTRACT,SHA,out,self.root/'bad',str(self.root/'source.npz'),P.sha(data),[2]),'REPORT')
 def test_header_cap_before_header_decode(self):
  npy=bytearray(bytes.fromhex(oracle['fixtures'][0]['npy_hex']));npy[8:10]=(16385).to_bytes(2,'little');raw=archive(bytes(npy));view,_=P.project(raw,P.metadata(raw,['aux.npy','heights.npy'],self.rd.archive))
  self.reject(lambda:P.inspect_view(view,self.I,self.rd,{'dtypes':['<f8'],'shape':[2],'fortran_order':False}),'HEADER_LIMIT')
 def test_second_output_not_overwritten(self):
  data=self.raw();src=self.file(data);out=self.root/'out';P.run(CONTRACT,SHA,out,str(src),P.sha(data),[2])
  with self.assertRaises(FileExistsError):P.run(CONTRACT,SHA,out,str(src),P.sha(data),[2])
if __name__=='__main__':unittest.main(verbosity=2)
