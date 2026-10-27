"""Offline LOD and empirical polygon heights at five fixed diagnostic points."""
from pathlib import Path
import hashlib,json,mmap,struct,sys
import numpy as np
from shapely.geometry import shape
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),str(W/'tools/playtest'),'C:/temp/moto_lanes/review_g3/tools']
from prepare_visual_probe_v31 import height
from streambed_kit_v31 import tri_h
from attach_navmesh import read_pbo
from odol_reader import ODOL
import odol_reader
O=R/'kit7-grid-vertex-diagnostic-20261027';O.mkdir(exist_ok=False)
G=R/'kit7-packed-nav-discovery-20261026';geo=json.loads((G/'geometry.json').read_text())
pilot=Path('P:/Mods/@DayZ_Baltic_EV112_Kit7Nav12/Addons/baltic_stream_pilot.pbo')
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert sha(pilot)=='3d9550bfb3f27e3916b14579990c240c4aaf4d779e628658ec572cb2c806a2b6'
assert sha(Path(odol_reader.__file__))=='fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57'
points=[(9132.,11280.),(9132.,11268.),(9132.,11292.),(9120.,11280.),(9144.,11280.)]
rows=[dict(x=x,z=z,model_lods=[]) for x,z in points]
terrain=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz';H=np.load(terrain)['heights']
for row in rows:row['terrain_y']=float(tri_h(H,row['x'],row['z']))
_,_,entries=read_pbo(pilot)
selected=[]
for model,meta in geo['models'].items():
    a=shape(meta['dry']);b=shape(meta['water']);bounds=a.union(b).bounds
    ids=[i for i,(x,z) in enumerate(points) if bounds[0]-1e-6<=x<=bounds[2]+1e-6 and bounds[1]-1e-6<=z<=bounds[3]+1e-6]
    if not ids:continue
    path=G/model.split('\\')[-1];blob=entries[path.name]
    assert hashlib.sha256(blob).hexdigest()==meta['odol_sha256'] and path.read_bytes()==blob
    od=ODOL.from_file(str(path),strict=True);assert not getattr(od,'lod_errors',{}) and all(l.lod_end_ok for l in od.lods)
    matrix=np.array(meta['pose']['matrix']);assert matrix[:9].tolist()==[1,0,0,0,1,0,0,0,1]
    selected.append(dict(model=model,sha256=meta['odol_sha256']))
    for lod in od.lods:
        if not lod.faces:continue
        xyz=(np.array([(v.x,v.y,v.z) for v in lod.vertices])+matrix[9:]).astype(np.float32).astype(float)
        faces=np.array([f.vertex_indices for f in lod.faces]);assert faces.shape[1]==3
        triangles=xyz[faces]
        ab=triangles[:,1,:][:,[0,2]]-triangles[:,0,:][:,[0,2]]
        ac=triangles[:,2,:][:,[0,2]]-triangles[:,0,:][:,[0,2]]
        valid=ab[:,0]*ac[:,1]-ab[:,1]*ac[:,0]!=0
        triangles=triangles[valid] # vertical faces have no defined downward-ray height
        if not len(triangles):continue
        for i in ids:
            y=height(triangles,np.array(points[i]))
            if y is not None:
                assert np.isfinite(y)
                rows[i]['model_lods'].append(dict(model=model,resolution=lod.resolution,y=y))
navs=[]
# Explicit artifact identities, no mixed-grid rewriting.
for label,width,grid,digest in [('8m',8.,1536,'360a7348b86bb9560352f2aead028fb6ec801f8d3bdd30526f43e0cb7e9efb23'),('12m',12.,1024,'87988bbb007b3e1fde00836b76d436faf9c5510937494bba82bc276fb6c64690')]:
    path=R/f'navmesh-kit7-{label}-v9-20261027/baltic_trial.nm';assert sha(path)==digest
    targets=set()
    for x,z in points:
        xs={int(x//width)};zs={int(z//width)}
        if x%width==0:xs.add(int(x//width)-1)
        if z%width==0:zs.add(int(z//width)-1)
        targets.update((a,b) for a in xs for b in zs)
    decoded=[];all_triangles=[]
    with path.open('rb') as f,mmap.mmap(f.fileno(),0,access=mmap.ACCESS_READ) as data:
        _,version,count,nx,nz=struct.unpack_from('<5I',data);assert (version,nx,nz)==(9,grid,grid)
        base=48+4*count
        for index in range(count):
            off=struct.unpack_from('<I',data,48+4*index)[0];h=base+off+16
            ints=struct.unpack_from('<15I',data,h)
            if tuple(ints[2:4]) not in targets:continue
            assert ints[0]==1145979222 and ints[1]==12 and ints[9:12]==(0,0,0) and ints[13]==0
            verts=np.frombuffer(data,dtype='<f4',count=ints[7]*3,offset=h+104).reshape(-1,3).astype(float)
            polys=[]
            for k in range(ints[6]):
                raw=struct.unpack_from('<I6H6HHBB',data,h+104+len(verts)*12+32*k);n=raw[-2];ids=raw[1:1+n]
                assert 3<=n<=6 and len(set(ids))==n and max(ids)<len(verts) and raw[-1]>>6==0
                poly=verts[list(ids)];polys.append(poly.tolist())
                all_triangles.extend([[poly[0],poly[t],poly[t+1]] for t in range(1,n-1)])
            decoded.append(dict(tile=list(ints[2:4]),vertices=verts.tolist(),polygons=polys))
    assert len(decoded)==len(targets)
    for row,(x,z) in zip(rows,points):
        y=height(np.array(all_triangles),np.array([x,z]));assert y is not None and np.isfinite(y)
        row['nav_'+label+'_y']=float(y)
    navs.append(dict(label=label,sha256=digest,source=str(path),tiles=decoded))
report=dict(status='READ_ONLY_DIAGNOSTIC_POINTS',points=rows,models=selected,navmeshes=navs,inputs={str(p):sha(p) for p in [Path(__file__),pilot,terrain,G/'geometry.json',Path(odol_reader.__file__),W/'tools/water/prepare_visual_probe_v31.py']},limits=['Five additional offline diagnostic points, not changes to the 607 acceptance queries.','Pointwise packed model/terrain sampling; no native corner query or actor proof.','Empirical local polygon fan decoding only; no artifact changes or acceptance.'])
(O/'result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({'status':report['status'],'points':rows},indent=2))
