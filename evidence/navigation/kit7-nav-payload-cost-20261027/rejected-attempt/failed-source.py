"""Read-only measured NM layout census; neither heap profiler nor acceptance gate."""
from pathlib import Path
from collections import Counter
import hashlib,json,mmap,struct

R=Path(__file__).parent
O=R/'kit7-nav-payload-cost-20261027'
ARTIFACTS=[
 ('kit7_8m',R/'navmesh-kit7-8m-v9-20261027/baltic_trial.nm','360a7348b86bb9560352f2aead028fb6ec801f8d3bdd30526f43e0cb7e9efb23'),
 ('kit7_12m',R/'navmesh-kit7-12m-v9-20261027/baltic_trial.nm','87988bbb007b3e1fde00836b76d436faf9c5510937494bba82bc276fb6c64690'),
 ('kit7_12p5m',R/'navmesh-kit7-v9-20261026/baltic_trial.nm','13e1ab1567740aca2ff94d6607b6f2c6423b9142674878562bf477994597f80b'),
 ('chernarus_50m',R/'chernarus-current-nav-detail-20261027/navmesh.nm','0b18d48d6c1e902e41b35b91588e84a3e3068a28df6d71cf6d74a6f80d29a163'),
]

def census(data):
 magic,version,count,nx,nz=struct.unpack_from('<5I',data)
 assert (magic,version)==(0x4d534554,9) and count==nx*nz and count>0
 assert struct.unpack_from('<I',data,40)[0]==count
 width=struct.unpack_from('<f',data,32)[0]
 base=48+4*count;offsets=struct.unpack_from(f'<{count}I',data,48)
 assert offsets[0]==0 and all(a<b for a,b in zip(offsets,offsets[1:]))
 poly_hist=Counter();sizes=Counter();empty_bytes=single_bytes=0;poly_total=vert_total=0;vertex_bytes=polygon_bytes=tail_bytes=0
 for i,offset in enumerate(offsets):
  start=base+offset;end=base+offsets[i+1] if i+1<count else len(data)
  reference,length,reserved=struct.unpack_from('<QII',data,start)
  assert reference==((1<<48)|(i<<20)) and reserved==0 and length==end-start-16
  h=start+16;ints=struct.unpack_from('<15I',data,h)
  assert ints[:2]==(0x444e4156,12) and ints[2:4]==(i%nx,i//nx)
  polygons,vertices=ints[6:8];prefix=104+vertices*12+polygons*32
  assert prefix<=length
  poly_hist[polygons]+=1;sizes[end-start]+=1;poly_total+=polygons;vert_total+=vertices
  vertex_bytes+=vertices*12;polygon_bytes+=polygons*32;tail_bytes+=length-prefix
  if polygons==0:empty_bytes+=end-start
  if polygons==1:single_bytes+=end-start
 return dict(tiles=count,grid=[nx,nz],tile_width_m=width,bytes=len(data),declared_polygons=poly_total,declared_vertices=vert_total,zero_polygon_tiles=poly_hist[0],zero_polygon_serialized_bytes=empty_bytes,one_polygon_tiles=poly_hist[1],one_polygon_serialized_bytes=single_bytes,polygon_histogram=dict(sorted(poly_hist.items())),tile_record_byte_histogram=dict(sorted(sizes.items())),accounting=dict(global_header_and_offsets=base,tile_record_prefixes=16*count,tile_headers=104*count,declared_vertex_prefixes=vertex_bytes,declared_polygon_prefixes=polygon_bytes,remaining_payload=tail_bytes))

def main():
 assert not O.exists();O.mkdir()
 rows=[]
 for label,path,expected in ARTIFACTS:
  with path.open('rb') as stream:
   with mmap.mmap(stream.fileno(),0,access=mmap.ACCESS_READ) as data:
    digest=hashlib.sha256(data).hexdigest();assert digest==expected,path
    result=census(data);assert sum(result['accounting'].values())==len(data)
  result.update(label=label,source=str(path),sha256=digest)
  rows.append(result)
  print(json.dumps({k:v for k,v in result.items() if not k.endswith('histogram')}),flush=True)
 result=dict(status='READ_ONLY_SERIALIZED_PAYLOAD_CENSUS',artifacts=rows,script_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),limits=['Serialized file accounting, NOT runtime heap allocation or a memory savings prediction.','Empirical VAND12 vertex/poly prefix sizes; remaining payload is not decoded.','Zero polygons does not authorize removing a tile; coverage/links/engine contract remain unchanged.','No generated candidate, mutation of NM, map edit, tolerance change or acceptance.'])
 (O/'result.json').write_text(json.dumps(result,indent=2)+'\n')

if __name__=='__main__':main()
