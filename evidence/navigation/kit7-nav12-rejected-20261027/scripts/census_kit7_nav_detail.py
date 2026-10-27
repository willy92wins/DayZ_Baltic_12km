"""Read-only census of empirical detail-counter fields, not a topology decoder."""
from pathlib import Path
from collections import Counter
import hashlib,json,mmap,struct
R=Path(__file__).parent;O=R/'kit7-nav-detail-census-20261027';O.mkdir(exist_ok=False)
rows=[]
for name,grid,digest in [('navmesh-kit7-8m-v9-20261027',1536,'360a7348b86bb9560352f2aead028fb6ec801f8d3bdd30526f43e0cb7e9efb23'),('navmesh-kit7-12m-v9-20261027',1024,'87988bbb007b3e1fde00836b76d436faf9c5510937494bba82bc276fb6c64690')]:
    path=R/name/'baltic_trial.nm'
    with path.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
    counts=Counter();examples=[]
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
        magic,version,count,nx,nz=struct.unpack_from('<5I',data)
        assert (version,nx,nz)==(9,grid,grid) and count==grid*grid
        base=48+count*4
        for index in range(count):
            offset=struct.unpack_from('<I',data,48+index*4)[0]
            h=base+offset+16;ints=struct.unpack_from('<15I',data,h)
            assert ints[0]==1145979222 and ints[1]==12
            detail=tuple(ints[9:12]);counts[detail]+=1
            if any(detail) and len(examples)<10:examples.append(dict(tile=list(ints[2:4]),detail_fields=list(detail)))
    rows.append(dict(source=str(path),sha256=digest,tiles=count,counts=[dict(fields=list(k),tiles=v) for k,v in sorted(counts.items())],nonzero_tiles=sum(v for k,v in counts.items() if any(k)),examples=examples))
report=dict(status='READ_ONLY_DETAIL_FIELD_CENSUS',artifacts=rows,limits=['Counters at empirical VAND12 header integer indices9:12; not a general format proof.','Zero counters do not prove every polygon has bad height or isolate the generator simplification algorithm.','No mutation, generated candidate or acceptance.'])
(O/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
