from pathlib import Path
import sys,json,csv,hashlib
import numpy as np
import shapely
from shapely.geometry import Polygon,Point,box
from shapely.affinity import translate
from scipy.spatial import cKDTree
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');E=W/'evidence/v30-global-water-risk-2026-10-09'
B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009');H=B/'halo-fix-v2'
sys.path[:0]=[str(W/'tools/terrain'),str(W/'tools/water')]
from wrp0wzd import read
from engine_water_model import ODOL
ref=json.loads((E/'halo-deploy.json').read_text())
for name,digest in ref['files'].items():assert hashlib.sha256((Path(ref['destination'])/'Addons'/name).read_bytes()).hexdigest()==digest
objects=[o for o in read(H/'world/root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp')['objects'] if o['name'].startswith('baltic_water_v30')]
tree=cKDTree(np.array([o['matrix'][9:12] for o in objects])[:,[0,2]])
cache=json.loads((B/'compiled-model-domains.json').read_text())
rows=[r for r in csv.DictReader((E/'halo-physical-anomalies.csv').open()) if r['cls']=='0'];out=[]
for r in rows:
    x,z=float(r['x']),float(r['z']);pt=Point(x,z);hits=[]
    for i in tree.query_ball_point([x,z],75):
        obj=objects[i];name=obj['name'].split('\\')[-1];mat=np.array(obj['matrix']);assert np.all(mat[:9]==np.eye(3).ravel())
        if name not in cache:
            od=ODOL.from_file(str(H/'water/temp/baltic_water_v30'/name));lod=min(od.lods,key=lambda l:abs(l.resolution-3e15));v=np.array([(q.x,q.y,q.z) for q in lod.vertices])
            g=shapely.union_all([Polygon(v[f.vertex_indices][:,[0,2]]) for f in lod.faces]);cache[name]=dict(wkb=shapely.to_wkb(g,hex=True),y=float(v[0,1]))
        c=cache[name];g=translate(shapely.from_wkb(c['wkb']),xoff=mat[9],yoff=mat[11]);distance=g.distance(pt)
        if distance>6:continue
        level=c['y']+mat[10]
        hits.append(dict(id=obj['id'],name=name,level=level,geometry_covers=g.covers(pt),geometry_distance=distance,
            bounds_cover=box(*g.bounds).covers(pt),bounds=list(g.bounds),native_level_matches=bool(abs(level-float(r['plane']))<.002)))
    out.append(dict(point=r,candidates=hits))
(E/'remaining-water-geometry.json').write_text(json.dumps(out,indent=2)+'\n')
for r in out:print(json.dumps(dict(x=r['point']['x'],z=r['point']['z'],native_plane=r['point']['plane'],matches=[q for q in r['candidates'] if q['native_level_matches']])) )
