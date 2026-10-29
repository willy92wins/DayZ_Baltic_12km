from pathlib import Path
import json,hashlib,sys,io,struct,zipfile,time
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'q03c2-terrain-headers-20261029';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
plan=W/'plans/quality-council-q03c2-source-terrain-water-partition-20261029.md';assert sha(plan)=='79160993e66653336c0eee77ef6cce27498ace51056c1414873f7f5ff543ee30'
code=R/'q03b6-local-author-20261029/saved_scene_io_q03b6.py';assert sha(code)=='d0734c068d59c87a9d35e31e431a0eb864d4e5ce22d29b2ab9c597c62bd15a44'
import types
I=types.ModuleType('_header_q03c2');I.__file__=str(code);exec(compile(code.read_bytes(),str(code),'exec'),I.__dict__)
c=I.parse(I.read_small(R/'q03b6-local-author-20261029/contract.json',{'sha256':'f8f8f6dcd1e3e74029875e5f40e7a2bb6dbfdaab84e892bd5c7457487ad87c9b'}));rd=I.Reader(c);A=rd.archive
p=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz';data,digest=A._snapshot(p,rd.session)
assert digest=='815ef8b772bfa10e9d6886d953878c24ef6819c5667ce4700c91faab992aec40' and len(data)==12875883
# Bounded inventory of raw central names; sealed _central revalidates all fields
# before ZipFile is allowed to instantiate any members.
end=None
for pos in range(len(data)-22,max(-1,len(data)-65558),-1):
 if data[pos:pos+4]==b'PK\x05\x06':
  e=struct.unpack_from('<4s4H2IH',data,pos)
  if pos+22+e[7]==len(data):end=pos;break
assert end is not None and 1<=e[4]<=35 and e[6]+e[5]==end
cursor=e[6];names=[]
for _ in range(e[4]):
 assert cursor+46<=end
 v=struct.unpack_from('<4s6H3I5H2I',data,cursor);assert v[0]==b'PK\x01\x02'
 stop=cursor+46+v[10]+v[11]+v[12];assert stop<=end
 names.append(A._name(data[cursor+46:cursor+46+v[10]]));cursor=stop
assert cursor==end and len(set(names))==len(names)
rows,expanded=A._central(data,{n:None for n in names},rd.session.limits);assert expanded<=262434599
schemas={};details=[]
with zipfile.ZipFile(io.BytesIO(data)) as z:
 for row in rows:
  with z.open(row['name']) as f:desc,head=I.header_candidate(f,row['expanded'])
  A.header.inspect_header(io.BytesIO(head),row['expanded'],desc)
  schemas[row['name']]=desc;details.append({'name':row['name'],'expanded':row['expanded'],'compressed':row['compressed'],'header_bytes':len(head),'header_sha256':hashlib.sha256(head).hexdigest(),'fortran_order':False,'method':row['method']})
assert schemas['heights.npy']['shape']==[2048,2048] and schemas['heights.npy']['dtype'] in ('<f4','<f8')
report={'status':'TERRAIN_HEADER_SCHEMAS_ONLY','plan_sha256':sha(plan),'source':str(p),'sha256':digest,'bytes':len(data),'expanded_bound':expanded,'schemas':schemas,'members':details,'array_payload_interpreted':False,'finite_heights_verified':False,'limits':rd.session.limits,'helpers':c['helpers'],'reader_sha256':sha(code),'time':time.time()}
(D/'report.json').write_bytes((json.dumps(report,indent=2)+'\n').encode());print(json.dumps(report))
