"""Read current packed vanilla Roadway to check frozen nominal route extent."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from shapely.geometry import Polygon,Point
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/playtest'),'C:/temp/moto_lanes/review_g3/tools']
from attach_navmesh import read_pbo
from odol_reader import ODOL
import odol_reader
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(odol_reader.__file__)=='fa0d74b6fa8e9000041a2e0f2799b0b6971da8967ac5ae68b7776cde25a78f57'
ref=json.loads((R/'kit7-navv9diag-ram-ab-20261027/pass-06/reference.json').read_text())
p,digest=next((Path(p),h) for p,h in ref['packages'].items() if Path(p).name=='water.pbo')
raw,props,entries=read_pbo(p);assert hashlib.sha256(raw).hexdigest()==digest
D=R/'chernarus-nav-height-reference-20261027';O=D/'packed-extents';O.mkdir(exist_ok=False)
rows=[]
for fam in ('leaf','sand','moss'):
    filename='streambed_'+fam+'_long_straight.p3d';matches=[k for k in entries if k.split('/')[-1]==filename];assert len(matches)==1
    path=O/filename;path.write_bytes(entries[matches[0]])
    od=ODOL.from_file(str(path),strict=True);assert not getattr(od,'lod_errors',{}) and all(l.lod_end_ok for l in od.lods)
    lods=[l for l in od.lods if abs(l.resolution-3e15)/3e15<1e-4];assert len(lods)==1;lod=lods[0]
    vertices=np.array([(v.x,v.y,v.z) for v in lod.vertices]);polys=[Polygon(vertices[f.vertex_indices][:,[0,2]]) for f in lod.faces]
    coverage=[]
    for x in (-6.,6.):
        for z in (-6.,6.):
            covered=any(p.covers(Point(x,z)) for p in polys);assert covered,(fam,x,z)
            coverage.append(dict(x=x,z=z,inside_roadway_footprint=covered))
    bc=od.model_info.bounding_center;assert abs(bc.x)<.001 and abs(bc.z)<.001
    rows.append(dict(family=fam,entry=matches[0],model_sha256=sha(path),bounding_center=[bc.x,bc.y,bc.z],roadway_resolution=lod.resolution,roadway_x_bounds=[float(vertices[:,0].min()),float(vertices[:,0].max())],roadway_z_bounds=[float(vertices[:,2].min()),float(vertices[:,2].max())],roadway_y_bounds=[float(vertices[:,1].min()),float(vertices[:,1].max())],nominal_endpoint_coverage=coverage))
result=dict(status='PASS_CURRENT_PACKED_NOMINAL_ROUTE_EXTENTS',package=str(p),package_sha256=digest,models=rows,inputs={str(Path(__file__)):sha(__file__),str(Path(odol_reader.__file__)):sha(odol_reader.__file__),str(D/'anchors.json'):sha(D/'anchors.json')},limits=['Local model footprint only; current placement/scale and actual ground/road heights remain native checks.','Coverage does not prove dry bank, route success or actor behavior.'])
(D/'extent-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(status=result['status'],models=[{k:r[k] for k in ('family','roadway_x_bounds','roadway_z_bounds','roadway_y_bounds')} for r in rows]),indent=2))
