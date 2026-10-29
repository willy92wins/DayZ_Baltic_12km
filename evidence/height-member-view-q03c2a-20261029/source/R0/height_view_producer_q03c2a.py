"""Single-member provenance projection. Other member payloads are not read."""
from pathlib import Path
import sys,types,json,hashlib,struct,io,zipfile,argparse,os,zlib
LIMITS={'source_stored':16777216,'view_stored':16777216,'selected_expanded':33570828,'members':35,'report':1048576,'chunk':65536,'rss':268435456}
CLAIMS={'whole_source_archive_validated':False,'other_payloads_decoded':False,'terrain_geometry_evaluated':False,'map_repaired':False}
class Reject(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(ok,code='ZIP_LAYOUT_UNSUPPORTED'):
 if not ok:raise Reject(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def bootstrap(path,digest):
 b=Path(path).read_bytes();need(sha(b)==digest,'IDENTITY');c=json.loads(b)
 need(c['schema']=='q03c2a-single-height-view-v1' and c['limits']==LIMITS and c['claims']==CLAIMS,'MEMBER_SCHEMA')
 p=c['reader'];b=Path(p['path']).read_bytes();need(sha(b)==p['sha256']=='d0734c068d59c87a9d35e31e431a0eb864d4e5ce22d29b2ab9c597c62bd15a44','IDENTITY')
 I=types.ModuleType('_q03c2a_io');I.__file__=p['path'];exec(compile(b,p['path'],'exec'),I.__dict__)
 cc=I.parse(I.read_small(c['index_contract']['path'],c['index_contract']));rd=I.Reader(cc);need(rd.session.limits==c['archive_limits'],'IDENTITY')
 hist=I.parse(I.read_small(c['historical_directory']['path'],c['historical_directory']));need(c['expected_names']==[r['name'] for r in hist['zip_entries']],'IDENTITY')
 return c,I,rd
def metadata(data,names,A):
 need(0<len(data)<=LIMITS['source_stored'] and 1<=len(names)<=35)
 need(len(data)>=22);end=len(data)-22;e=struct.unpack_from('<4s4H2IH',data,end)
 need(e[0]==b'PK\x05\x06' and e[1]==e[2]==e[7]==0 and e[3]==e[4]==len(names) and e[6]+e[5]==end)
 cursor=e[6];rows=[];seen=set()
 for name in names:
  need(cursor+46<=end);t=struct.unpack_from('<4s6H3I5H2I',data,cursor)
  need(t[0]==b'PK\x01\x02' and t[11]==t[12]==t[13]==0 and all(t[k]!=0xffffffff for k in (8,9,16)))
  stop=cursor+46+t[10];need(stop<=end);raw=data[cursor+46:stop];decoded=A._name(raw)
  need(decoded==name and decoded not in seen);seen.add(decoded);A._flags(t[3],t[4]);need(t[9]>0)
  rows.append({'name':decoded,'central_offset':cursor,'central_stop':stop,'offset':t[16],'flags':t[3],'method':t[4],'crc':t[7],'compressed':t[8],'expanded':t[9]});cursor=stop
 need(cursor==end);cursor=0
 for row in sorted(rows,key=lambda r:r['offset']):
  off=row['offset'];need(off==cursor and off+30<=e[6]);h=struct.unpack_from('<4s5H3I2H',data,off)
  start=off+30+h[9]+h[10];stop=start+row['compressed'];need(start<=stop<=e[6] and h[0]==b'PK\x03\x04')
  need(data[off+30:off+30+h[9]]==row['name'].encode() and (h[2],h[3],h[6])==(row['flags'],row['method'],row['crc']))
  extra=data[off+30+h[9]:start]
  if h[7]==0xffffffff or h[8]==0xffffffff:
   need(h[7]==h[8]==0xffffffff and len(extra)==20 and extra[:4]==b'\x01\x00\x10\x00');need(struct.unpack_from('<QQ',extra,4)==(row['expanded'],row['compressed']))
  else:need(not extra and (h[8],h[7])==(row['expanded'],row['compressed']))
  row.update(data_start=start,data_stop=stop);cursor=stop
 need(cursor==e[6]);need(sum(r['name']=='heights.npy' for r in rows)==1)
 return rows
def project(data,rows):
 row=next(r for r in rows if r['name']=='heights.npy');need(row['expanded']<=LIMITS['selected_expanded'] and row['compressed']<=16777216,'SELECTED_CAP')
 n=row['data_stop']-row['offset'];central_len=row['central_stop']-row['central_offset'];need(n+central_len+22<=16777216,'SELECTED_CAP')
 local=data[row['offset']:row['data_stop']];central=bytearray(data[row['central_offset']:row['central_stop']]);struct.pack_into('<I',central,42,0)
 return local+central+struct.pack('<4s4H2IH',b'PK\x05\x06',0,0,1,1,len(central),len(local),0),row
def _inspect_view(view,I,rd,expected):
 rows,expanded=rd.archive._central(view,{'heights.npy':None},rd.session.limits);need(expanded<=LIMITS['selected_expanded'],'SELECTED_CAP')
 with zipfile.ZipFile(io.BytesIO(view)) as z:
  with z.open('heights.npy') as f:desc,header=I.header_candidate(f,expanded)
 need(desc['dtype'] in expected['dtypes'] and desc['shape']==expected['shape'] and expected['fortran_order'] is False,'MEMBER_SCHEMA')
 rd.archive.header.inspect_header(io.BytesIO(header),expanded,desc)
 return desc,header,rd.archive._decoded_extent(view,rows[0])
def inspect_view(view,I,rd,expected):
 try:return _inspect_view(view,I,rd,expected)
 except (zipfile.BadZipFile,EOFError,zlib.error) as e:raise Reject('ZIP_TRUNCATED') from e

def emit(path,value,cap=1048576):
 b=(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();need(len(b)<=cap,'OUTPUT_CAP')
 with Path(path).open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
def run(contract,contract_sha,out,fixture=None,fixture_sha=None,fixture_shape=None):
 c,I,rd=bootstrap(contract,contract_sha)
 if fixture:
  need(fixture_shape in ([2],[2,2]),'MEMBER_SCHEMA');pin={'path':fixture,'sha256':fixture_sha};names=['aux.npy','heights.npy'];expected={'dtypes':['<f8'],'shape':fixture_shape,'fortran_order':False}
 else:pin=c['source'];names=c['expected_names'];expected=c['expected_heights']
 data,digest=rd.archive._snapshot(Path(pin['path']),rd.session);need(digest==pin['sha256'] and ('bytes' not in pin or len(data)==pin['bytes']),'IDENTITY')
 rows=metadata(data,names,rd.archive);view,row=project(data,rows);desc,header,npy_sha=inspect_view(view,I,rd,expected)
 output=Path(out);output.mkdir(exist_ok=False);vp=output/'heights-view.npz'
 with vp.open('xb') as f:f.write(view);f.flush();os.fsync(f.fileno())
 with rd.session.open(vp,{'heights.npy':desc}) as got:
  need(got['source_sha256']==sha(view),'SOURCE_CHANGED');payload=got['payloads']['heights.npy']
 need(sha(I.read_small(vp,{'sha256':sha(view)},16777216))==sha(view),'SOURCE_CHANGED')
 report={'status':'SINGLE_HEIGHT_MEMBER_VIEW_UNVERIFIED','contract_sha256':contract_sha,'source_sha256':digest,'source_bytes':len(data),'view_sha256':sha(view),'view_bytes':len(view),'declared_expanded_sum_observed':sum(r['expanded'] for r in rows),'metadata_rows':rows,'selected':row,'compressed_sha256':sha(data[row['data_start']:row['data_stop']]),'local_record_sha256':sha(data[row['offset']:row['data_stop']]),'npy_sha256':npy_sha,'header_sha256':sha(header),'header_observed':desc,'payload':payload,'claims':CLAIMS,'fixture':bool(fixture)}
 emit(output/'report.json',report);return report
def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--out',required=True);p.add_argument('--fixture');p.add_argument('--fixture-sha');p.add_argument('--fixture-shape',choices=['signed','matrix']);a=p.parse_args()
 run(a.contract,a.sha,a.out,a.fixture,a.fixture_sha,{'signed':[2],'matrix':[2,2]}.get(a.fixture_shape))
if __name__=='__main__':
 try:main()
 except (zipfile.BadZipFile,EOFError,zlib.error) as e:print(json.dumps({'status':'REJECTED','code':'ZIP_TRUNCATED','detail':str(e)}),file=sys.stderr);sys.exit(1)
 except OSError as e:print(json.dumps({'status':'REJECTED','code':'IO_ERROR','detail':str(e)}),file=sys.stderr);sys.exit(1)
 except Exception as e:print(json.dumps({'status':'REJECTED','code':getattr(e,'code','INTERNAL_ERROR'),'detail':str(e)}),file=sys.stderr);sys.exit(1)
