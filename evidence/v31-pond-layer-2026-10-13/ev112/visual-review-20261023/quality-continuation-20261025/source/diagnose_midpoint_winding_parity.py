from pathlib import Path
import json,collections,io,struct,sys
import numpy as np
R=Path(__file__).parent;B=R/'river-131-midpoint-b'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path[:0]=[str(W/'tools/water'),'C:/temp/moto_lanes/review_g3/tools']
from review_compact_collision_v31 import load,vertices
from mesh_quality_v31 import closed_component
from odol_reader import ODOL
poses={x['model']:x['matrix'] for x in json.loads((B/'f-compiled-poses.json').read_text())}
def oriented(tri):
    t=tuple(map(tuple,tri));return min(t,t[1:]+t[:1],t[2:]+t[:2])
rows=[]
for i in json.loads((B/'author-report.json').read_text())['instances']:
    n=i['model'].split('\\')[-1];_,lods,_=load(B/'source'/i['model'].replace('\\','/'))
    source=(vertices(lods[1],lods[1].faces)+i['origin']).astype(np.float32).astype(float)
    od=ODOL.from_file(str(B/'temp/baltic_stream_pilot'/n),strict=True);g=min(od.lods,key=lambda l:abs(l.resolution-1e13))
    xyz=(np.array([(v.x,v.y,v.z) for v in g.vertices])+poses[i['model']][9:]).astype(np.float32).astype(float)
    tri=xyz[np.array([f.vertex_indices for f in g.faces])]
    same=collections.Counter(map(oriented,source))==collections.Counter(map(oriented,tri))
    reversed_=collections.Counter(map(oriented,source))==collections.Counter(map(oriented,tri[:,::-1]))
    volumes=[closed_component(tri[s.selected_faces])['signed_volume'] for s in g.named_selections]
    rows.append(dict(model=n,faces=len(tri),same_winding=same,reversed_winding=reversed_,components=len(volumes),positive_volumes=all(v>0 for v in volumes)))
p=B/'winding-parity-diagnostic.json';assert not p.exists();p.write_text(json.dumps(dict(rows=rows,all_reversed=all(x['reversed_winding'] and x['positive_volumes'] for x in rows)),indent=2)+'\n')
print(json.dumps(dict(models=len(rows),all_reversed=all(x['reversed_winding'] and x['positive_volumes'] for x in rows))))
