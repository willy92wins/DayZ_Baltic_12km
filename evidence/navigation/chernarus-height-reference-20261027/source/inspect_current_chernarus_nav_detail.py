"""Compare empirical detail fields in the actually measured Chernarus package."""
from pathlib import Path
from collections import Counter
import hashlib,json,struct,sys
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/playtest'))
from attach_navmesh import read_pbo
O=R/'chernarus-current-nav-detail-20261027';assert not O.exists()
reference=R/'kit7-navv9diag-ram-ab-20261027/pass-06/reference.json'
ref=json.loads(reference.read_text());matches=[(Path(p),h) for p,h in ref['packages'].items() if Path(p).name=='worlds_chernarusplus_nav.pbo'];assert len(matches)==1
p,digest=matches[0];raw,props,entries=read_pbo(p);assert hashlib.sha256(raw).hexdigest()==digest
names=[n for n in entries if n.lower().endswith('.nm')];assert len(names)==1
data=entries[names[0]];sha=hashlib.sha256(data).hexdigest()
assert sha=='0b18d48d6c1e902e41b35b91588e84a3e3068a28df6d71cf6d74a6f80d29a163'
magic,version,count,nx,nz=struct.unpack_from('<5I',data);assert magic==0x4d534554 and version==9 and count==nx*nz
origin=struct.unpack_from('<5f',data,20);assert origin==(0.,0.,0.,50.,50.)
base=48+count*4;counts=Counter();examples=[];poly=verts=0
for index in range(count):
    offset=struct.unpack_from('<I',data,48+index*4)[0];h=base+offset+16;ints=struct.unpack_from('<15I',data,h)
    assert ints[0]==1145979222 and ints[1]==12
    detail=tuple(ints[9:12]);counts[detail]+=1;poly+=ints[6];verts+=ints[7]
    if any(detail) and len(examples)<10:examples.append(dict(tile=list(ints[2:4]),detail_fields=list(detail)))
O.mkdir();(O/'navmesh.nm').write_bytes(data)
result=dict(status='READ_ONLY_CURRENT_VANILLA_DETAIL_FIELD_CENSUS',package=str(p),package_sha256=digest,reference_sha256=hashlib.sha256(reference.read_bytes()).hexdigest(),entry=names[0],navmesh_sha256=sha,version=version,grid=[nx,nz],tile_width=50.,tiles=count,declared_polygons=poly,declared_vertices=verts,counts=[dict(fields=list(k),tiles=v) for k,v in sorted(counts.items())],nonzero_tiles=sum(v for k,v in counts.items() if any(k)),examples=examples,limits=['Same empirical integer fields9:12 as Baltic; no general format or generator-algorithm proof.','Bound to the actual Chernarus package measured in the last RAM pass.','The unpacked P:/ copy is TESM6 and is not this deployed TESM9 reference.','No runtime height query, actor proof, tolerance change or Baltic acceptance.'])
(O/'result.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
