"""Classify native diagnostics using frozen fields and actual bridge roadways."""
from pathlib import Path
import csv,json,sys,hashlib
import numpy as np
import shapely
from shapely.geometry import Polygon,Point
B=Path(__file__).parent;R=B.parent;E=R/'v30-isolated-basin-repair-20261009'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from wrp0wzd import read
from engine_water_model import ODOL
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
t=np.load(E/'candidate/terrain.npz');h=t['heights'];p=np.load(E/'candidate/plane.npy');f=np.load(E/'candidate/visible-field.npy')
wrp=E/'package/world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp';assert sha(wrp)=='6c056a61402356aa0f48b04c528e5c696ef17ba6b7eeb42308a62f9942d52f91'
world=read(wrp);objects=[o for o in world['objects'] if not o['name'].startswith('baltic_water_v30')];bridges=[]
for o in objects:
    path=Path('P:/')/o['name'].replace('\\','/')
    if not path.exists():raise FileNotFoundError(path)
    od=ODOL.from_file(str(path));roads=[lod for lod in od.lods if abs(lod.resolution-3e15)/3e15<1e-5]
    m=np.array(o['matrix']);parts=[];elev=[]
    for lod in roads:
        verts=np.array([(a.x,a.y,a.z) for a in lod.vertices])@m[:9].reshape(3,3)+m[9:]
        for face in lod.faces:
            v=verts[face.vertex_indices];poly=Polygon(v[:,[0,2]])
            if poly.area>1e-8:parts.append(poly);elev.extend(v[:,1])
    geom=shapely.union_all(parts)
    bridges.append(dict(id=o['id'],name=o['name'],sha256=sha(path),geometry=geom,roadway_y_min=min(elev) if elev else None,roadway_y_max=max(elev) if elev else None))
def incident(r,c):
    vals=[];visible=[]
    for dr,dc,j in [(0,0,0),(0,-1,1),(-1,0,2),(-1,-1,3)]:
        a,b=r+dr,c+dc
        if 0<=a<2047 and 0<=b<2047 and np.isfinite(p[a,b]):vals.append(float(p[a,b]));visible.append(float(f[a,b,j]))
    return vals,visible
points=[]
for row in csv.DictReader((E/'basins-physical-anomalies.csv').open()):
    r,c=int(row['row']),int(row['col']);x,z=c*6,12282-r*6;ground=float(h[r,c]);kind=int(row['cls']);levels,vis=incident(r,c);plane=float(row['plane']);dep=float(row['depth'])
    hit=[{k:v for k,v in b.items() if k!='geometry'} for b in bridges if b['geometry'].buffer(1e-5).covers(Point(x,z))]
    if kind==1:reason='ocean_intertidal_or_wave_phase'
    elif not levels:reason='no_frozen_pond_at_vertex'
    elif ground>=max(levels)-1e-4:reason='design_water_class_on_dry_bank'
    elif hit:reason='wet_point_beneath_bridge_roadway_flag_unproven'
    else:reason='wet_point_without_flag_not_under_bridge'
    points.append(dict(row=r,col=c,x=x,z=z,ground_m=ground,cls=kind,reason=reason,nominal_levels=levels,visible_levels=vis,native_plane=plane,native_depth=dep,bridge_hits=hit))
qs=[]
for row in csv.DictReader((E/'basins-unflagged-scalar-queries.csv').open(),delimiter=';'):
    r,c=int(row['row']),int(row['col']);levels,vis=incident(r,c);hit=[b['id'] for b in bridges if b['geometry'].buffer(1e-5).covers(Point(c*6,12282-r*6))]
    qs.append(dict(row=r,col=c,ground=float(row['ground']),plane=float(row['plane']),depth=float(row['depth']),frozen_levels=levels,under_bridge=hit))
counts={reason:sum(p['reason']==reason for p in points) for reason in sorted({p['reason'] for p in points})}
report=dict(status='CLASSIFIED_NOT_CLOSED',terrain_sha256=sha(E/'candidate/terrain.npz'),world_source_sha256=sha(wrp),counts=counts,points=points,unflagged_scalar_count=len(qs),scalar_under_bridge=sum(bool(q['under_bridge']) for q in qs),scalar_with_frozen_pond=sum(bool(q['frozen_levels']) for q in qs),scalar_queries=qs,limits=['Roadway overlap is a hypothesis for SurfaceIsPond suppression, not proof of the opaque native mechanism.','Class mismatch is not a geometric gap. Retain all observations.'])
(B/'classification.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['points','scalar_queries']},indent=2))
