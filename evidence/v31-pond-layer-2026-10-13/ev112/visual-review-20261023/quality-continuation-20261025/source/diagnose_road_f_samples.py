from pathlib import Path
import json,sys,hashlib
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');sys.path.insert(0,str(W/'tools/water'));from streambed_kit_v31 import tri_h
source=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/personal-view-visual-20261024-r/points.json');terrain=R/'rectangle-pilot-f-merged/terrain-buried.npz'
a=json.loads(source.read_text());H=np.load(terrain)['heights'];pts={x['id']:x for x in a['points']};rows=[];sections=[]
for s in a['road_sections']:
    heights=[]
    for i in s['ids']:
        p=pts[i];h=float(tri_h(H,np.array([p['x']]),np.array([p['z']]))[0]);heights.append(h);rows.append(dict(id=i,expect=p['expect'],old=p['ground'],F=h,delta=h-p['ground'],x=p['x'],z=p['z']))
    sections.append(dict(station_m=s['station_m'],cross=max(heights)-min(heights)))
out=dict(points=rows,sections=sections,max_ground_difference=max(abs(x['delta']) for x in rows),expectations=sorted({x['expect'] for x in rows}),max_cross=max(s['cross'] for s in sections),sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (source,terrain)})
(R/'road-sections-f/samples-diagnostic.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ('points','sections','sources')}))
