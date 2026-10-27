"""Read-only empirical header sample; comparisons are NOT a VAND12 specification."""
from pathlib import Path
from collections import Counter
import hashlib,json,mmap,struct,time

R=Path(__file__).parent
O=R/'nav8-storage-sample-20261027'
ARTIFACTS=[
('nav8','navmesh-kit7-8m-v9-20261027/baltic_trial.nm','360a7348b86bb9560352f2aead028fb6ec801f8d3bdd30526f43e0cb7e9efb23'),
('nav12','navmesh-kit7-12m-v9-20261027/baltic_trial.nm','87988bbb007b3e1fde00836b76d436faf9c5510937494bba82bc276fb6c64690'),
('nav12p5','navmesh-kit7-v9-20261026/baltic_trial.nm','13e1ab1567740aca2ff94d6607b6f2c6423b9142674878562bf477994597f80b'),
('chernarus','chernarus-current-nav-detail-20261027/navmesh.nm','0b18d48d6c1e902e41b35b91588e84a3e3068a28df6d71cf6d74a6f80d29a163')]

def tile_header(data,index):
 if len(data)<48:raise ValueError('short header')
 magic,version,count,nx,nz=struct.unpack_from('<5I',data)
 if (magic,version)!=(0x4d534554,9) or count!=nx*nz or not 0<=index<count:raise ValueError('outer header')
 base=48+count*4
 if base>=len(data):raise ValueError('offset table')
 a=base+struct.unpack_from('<I',data,48+4*index)[0]
 b=base+struct.unpack_from('<I',data,48+4*(index+1))[0] if index+1<count else len(data)
 if not base<=a<b<=len(data) or b-a<120:raise ValueError('tile bounds')
 ref,length,reserved=struct.unpack_from('<QII',data,a)
 if reserved or length!=b-a-16 or ref!=((1<<48)|(index<<20)):raise ValueError('record')
 ints=struct.unpack_from('<15I',data,a+16)
 if ints[:2]!=(0x444e4156,12) or not (ints[2]<nx and ints[3]<nz):raise ValueError('tile header')
 prefix=104+12*ints[7]+32*ints[6]
 if prefix>length:raise ValueError('prefix beyond tile')
 # Numerical comparisons only. i8..i14 remain empirical field indices.
 detail=12*ints[9]+12*ints[10]+4*ints[11]
 residuals={str(link_size):length-prefix-(link_size*ints[8]+detail+16*ints[12]+36*ints[13]) for link_size in (12,16,24)}
 return dict(index=index,xz=list(ints[2:4]),length=length,polygons=ints[6],vertices=ints[7],fields8_14=list(ints[8:15]),u32_at100=struct.unpack_from('<I',data,a+116)[0],tail_bytes=length-prefix,residuals=residuals)

def main():
 O.mkdir(exist_ok=False);start=time.monotonic();results=[]
 for label,rel,expected in ARTIFACTS:
  path=R/rel
  with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
   before=hashlib.sha256(data).hexdigest()
   if before!=expected:raise ValueError('input identity')
   count,nx,nz=struct.unpack_from('<3I',data,8)
   # Uniform fixed grid, not cherry-picked by value; add original local witness vicinity.
   indices=set(round(k*(count-1)/255) for k in range(256))
   width=struct.unpack_from('<f',data,32)[0]
   # Existing format traversal shows physical order can differ from coordinate order.
   # These extra indices are grid-derived sampling positions, NOT claimed witness tiles.
   for x,z in [(9132,11280),(9137.9,11268),(8253,9038)]:
    ix,iz=int(x/width),int(z/width)
    if ix<nx and iz<nz:indices.add(iz*nx+ix)
   rows=[tile_header(data,i) for i in sorted(indices)]
   after=hashlib.sha256(data).hexdigest()
   if after!=before:raise ValueError('input changed')
  results.append(dict(label=label,source=str(path),sha256=before,hash_after=after,sample_count=len(rows),total_tiles=count,field_histograms={str(k):dict(Counter(r['fields8_14'][k-8] for r in rows)) for k in range(8,15)},unknown100_histogram=dict(Counter(r['u32_at100'] for r in rows)),residual_histograms={str(s):dict(Counter(r['residuals'][str(s)] for r in rows)) for s in (12,16,24)},rows=rows))
  print(label,len(rows),results[-1]['residual_histograms'],flush=True)
 out=dict(status='OBSERVATION_ONLY_NOT_FORMAT_SUPPORT',seconds=time.monotonic()-start,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),artifacts=results,limits=['Deterministic sample, not whole-map census.','Header field names/section lengths from Detour are hypotheses for VAND12.','Serialized tail equations do not prove internal semantics, heap allocation, safe shrinking or retiling.','No NM mutations, candidate, engine run, generation, or new acceptance.'])
 (O/'result.json').write_text(json.dumps(out,indent=2)+'\n')

if __name__=='__main__':main()
