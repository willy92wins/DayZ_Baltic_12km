"""Saved view verification: field-offset traversal and independent source bytes."""
from pathlib import Path
import sys,types,json,hashlib,io,zipfile,argparse,os,zlib
class Reject(Exception):
 def __init__(self,code):self.code=code;super().__init__(code)
def need(ok,code='ZIP_LAYOUT_UNSUPPORTED'):
 if not ok:raise Reject(code)
def sha(b):return hashlib.sha256(b).hexdigest()
def read_header(I,member,expanded):
 try:return I.header_candidate(member,expanded)
 except I.Rejected as e:
  if e.code=='SCHEMA':raise Reject('MEMBER_SCHEMA') from e
  raise

def bootstrap(path,digest):
 b=Path(path).read_bytes();need(sha(b)==digest,'IDENTITY');c=json.loads(b)
 need(c['schema']=='q03c2a-single-height-view-v1' and c['limits']=={'source_stored':16777216,'view_stored':16777216,'selected_expanded':33570828,'members':35,'report':1048576,'chunk':65536,'rss':268435456},'MEMBER_SCHEMA')
 p=c['reader'];b=Path(p['path']).read_bytes();need(sha(b)==p['sha256']=='d0734c068d59c87a9d35e31e431a0eb864d4e5ce22d29b2ab9c597c62bd15a44','IDENTITY')
 I=types.ModuleType('_q03c2a_consumer_io');I.__file__=p['path'];exec(compile(b,p['path'],'exec'),I.__dict__)
 cc=I.parse(I.read_small(c['index_contract']['path'],c['index_contract']));rd=I.Reader(cc);need(rd.session.limits==c['archive_limits'],'IDENTITY')
 hist=I.parse(I.read_small(c['historical_directory']['path'],c['historical_directory']));need(c['expected_names']==[r['name'] for r in hist['zip_entries']],'IDENTITY');return c,I,rd
def directory(data,names,A):
 need(22<=len(data)<=16777216 and 1<=len(names)<=35)
 def u(pos,n):need(0<=pos and pos+n<=len(data));return int.from_bytes(data[pos:pos+n],'little')
 tail=len(data)-22;need(data[tail:tail+4]==b'PK\x05\x06' and u(tail+4,2)==u(tail+6,2)==u(tail+20,2)==0)
 need(u(tail+8,2)==u(tail+10,2)==len(names));start=u(tail+16,4);need(start+u(tail+12,4)==tail)
 cursor=start;rows=[]
 for name in names:
  need(cursor+46<=tail and data[cursor:cursor+4]==b'PK\x01\x02');n=u(cursor+28,2)
  need(u(cursor+30,2)==u(cursor+32,2)==u(cursor+34,2)==0 and cursor+46+n<=tail)
  need(A._name(data[cursor+46:cursor+46+n])==name and name not in [r['name'] for r in rows]);flags=u(cursor+8,2);method=u(cursor+10,2);A._flags(flags,method)
  off,compressed,expanded=u(cursor+42,4),u(cursor+20,4),u(cursor+24,4);need(all(x!=0xffffffff for x in (off,compressed,expanded)) and expanded>0)
  rows.append({'name':name,'central_offset':cursor,'central_stop':cursor+46+n,'offset':off,'flags':flags,'method':method,'crc':u(cursor+16,4),'compressed':compressed,'expanded':expanded});cursor+=46+n
 need(cursor==tail);cursor=0
 for row in sorted(rows,key=lambda r:r['offset']):
  off=row['offset'];need(off==cursor and off+30<=start and data[off:off+4]==b'PK\x03\x04');n=u(off+26,2);extra=u(off+28,2);begin=off+30+n+extra;end=begin+row['compressed'];need(begin<=end<=start)
  need(data[off+30:off+30+n]==row['name'].encode() and (u(off+6,2),u(off+8,2),u(off+14,4))==(row['flags'],row['method'],row['crc']))
  x,y=u(off+18,4),u(off+22,4)
  if x==0xffffffff or y==0xffffffff:
   a=off+30+n;need(x==y==0xffffffff and extra==20 and data[a:a+4]==b'\x01\x00\x10\x00' and u(a+4,8)==row['expanded'] and u(a+12,8)==row['compressed'])
  else:need(extra==0 and (x,y)==(row['compressed'],row['expanded']))
  row['data_start']=begin;row['data_stop']=end;cursor=end
 need(cursor==start and sum(r['name']=='heights.npy' for r in rows)==1);return rows
def run(contract,contract_sha,capture,out,fixture=None,fixture_sha=None,fixture_shape=None):
 c,I,rd=bootstrap(contract,contract_sha);claims={'whole_source_archive_validated':False,'other_payloads_decoded':False,'terrain_geometry_evaluated':False,'map_repaired':False};need(c['claims']==claims,'MEMBER_SCHEMA')
 if fixture:
  need(fixture_shape in ([2],[2,2]),'MEMBER_SCHEMA');pin={'path':fixture,'sha256':fixture_sha};names=['aux.npy','heights.npy'];expected={'dtypes':['<f8'],'shape':fixture_shape,'fortran_order':False}
 else:pin=c['source'];names=c['expected_names'];expected=c['expected_heights']
 source,digest=rd.archive._snapshot(Path(pin['path']),rd.session);need(digest==pin['sha256'] and ('bytes' not in pin or len(source)==pin['bytes']),'IDENTITY')
 rows=directory(source,names,rd.archive);row=next(r for r in rows if r['name']=='heights.npy');need(row['expanded']<=33570828 and row['compressed']<=16777216,'SELECTED_CAP')
 root=Path(capture);report_raw=I.read_small(root/'report.json',limit=1048576);report=I.parse(report_raw);vp=root/'heights-view.npz';view,view_sha=rd.archive._snapshot(vp,rd.session)
 vr,total=rd.archive._central(view,{'heights.npy':None},rd.session.limits);need(total<=33570828,'SELECTED_CAP');vrow=vr[0]
 # Byte provenance, not merely equal inflated data. Central bytes may change only offset.
 n=row['data_stop']-row['offset'];central=source[row['central_offset']:row['central_stop']];expected_central=central[:42]+b'\x00'*4+central[46:]
 need(view[:n]==source[row['offset']:row['data_stop']] and view[n:n+len(central)]==expected_central,'PROVENANCE')
 need(vrow['offset']==0 and len(view)==n+len(central)+22 and view[-2:]==b'\x00\x00','PROVENANCE')
 need(view[vrow['data_start']:vrow['data_stop']]==source[row['data_start']:row['data_stop']],'PROVENANCE')
 raw_hash=hashlib.sha256();count=0
 with zipfile.ZipFile(io.BytesIO(source)) as old,zipfile.ZipFile(io.BytesIO(view)) as new:
  need(old.namelist()==names and new.namelist()==['heights.npy'],'IDENTITY')
  with old.open('heights.npy') as a,new.open('heights.npy') as b:
   while True:
    x=a.read(min(65536,row['expanded']+1-count));y=b.read(len(x));need(x==y,'PROVENANCE');count+=len(x);need(count<=row['expanded'],'ZIP_TRUNCATED');raw_hash.update(x)
    if not x:need(not b.read(1),'ZIP_TRUNCATED');break
  with new.open('heights.npy') as f:desc,header=read_header(I,f,total)
 need(count==row['expanded'],'ZIP_TRUNCATED');need(desc['dtype'] in expected['dtypes'] and desc['shape']==expected['shape'] and expected['fortran_order'] is False,'MEMBER_SCHEMA')
 rd.archive.header.inspect_header(io.BytesIO(header),total,desc);need(rd.archive._decoded_extent(view,vrow)==raw_hash.hexdigest(),'ZIP_TRUNCATED')
 with rd.session.open(vp,{'heights.npy':desc}) as got:
  need(got['source_sha256']==view_sha,'SOURCE_CHANGED');payload=got['payloads']['heights.npy']
 I.read_small(vp,{'sha256':view_sha},16777216)
 want={'status':'SINGLE_HEIGHT_MEMBER_VIEW_UNVERIFIED','contract_sha256':contract_sha,'source_sha256':digest,'source_bytes':len(source),'view_sha256':view_sha,'view_bytes':len(view),'declared_expanded_sum_observed':sum(r['expanded'] for r in rows),'metadata_rows':rows,'selected':row,'compressed_sha256':sha(source[row['data_start']:row['data_stop']]),'local_record_sha256':sha(source[row['offset']:row['data_stop']]),'npy_sha256':raw_hash.hexdigest(),'header_sha256':sha(header),'header_observed':desc,'payload':payload,'claims':claims,'fixture':bool(fixture)}
 need(I.exact(report,want),'REPORT');result={'status':'VERIFIED_SINGLE_HEIGHT_MEMBER_VIEW_ONLY','contract_sha256':contract_sha,'report_sha256':sha(report_raw),'view_sha256':view_sha,'npy_sha256':raw_hash.hexdigest(),'source_sha256':digest,'claims':claims,'fixture':bool(fixture)}
 p=Path(out);p.mkdir(exist_ok=False);b=(json.dumps(result,sort_keys=True,separators=(',',':'))+'\n').encode()
 with (p/'consumer.json').open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
 return result
def main():
 p=argparse.ArgumentParser();p.add_argument('--contract',required=True);p.add_argument('--sha',required=True);p.add_argument('--capture',required=True);p.add_argument('--out',required=True);p.add_argument('--fixture');p.add_argument('--fixture-sha');p.add_argument('--fixture-shape',choices=['signed','matrix']);a=p.parse_args();run(a.contract,a.sha,a.capture,a.out,a.fixture,a.fixture_sha,{'signed':[2],'matrix':[2,2]}.get(a.fixture_shape))
if __name__=='__main__':
 try:main()
 except (zipfile.BadZipFile,EOFError,zlib.error) as e:print(json.dumps({'status':'REJECTED','code':'ZIP_TRUNCATED','detail':str(e)}),file=sys.stderr);sys.exit(1)
 except OSError as e:print(json.dumps({'status':'REJECTED','code':'IO_ERROR','detail':str(e)}),file=sys.stderr);sys.exit(1)
 except Exception as e:print(json.dumps({'status':'REJECTED','code':getattr(e,'code','INTERNAL_ERROR'),'detail':str(e)}),file=sys.stderr);sys.exit(1)
