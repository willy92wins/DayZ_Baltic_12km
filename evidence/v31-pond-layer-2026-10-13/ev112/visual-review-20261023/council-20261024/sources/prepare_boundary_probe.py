from pathlib import Path
import json,hashlib,shutil,numpy as np,sys
ROOT=Path(__file__).parent;WT=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
sys.path.insert(0,str(WT/'tools/water'));from streambed_kit_v31 import tri_h
out=ROOT/'boundary-probe-r';out.mkdir(exist_ok=False)
mission=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticQCBoundaryR.BalticTrial');mission.mkdir(exist_ok=False)
src=WT/'missions/BalticVisualProbeV1.BalticTrial/init.c';shutil.copy2(src,mission/'init.c')
H=np.load(B/'road-merged-20261024-h/terrain-buried.npz')['heights'];rows=[]
def add(x,z,kind):
    rows.append(dict(id=len(rows),x=float(x),z=float(z),kind=kind,clamped_hypothesis=float(tri_h(H,x,z))))
# Fixed transects sample boundary vertex, half-cell, final world edge and beyond.
for u in (600,1800,3400,5400,7200,9000,10800,12000):
    for d in (-6,0,3,6,9,12):
        add(u,12276+d,'north_strip');add(12276+d,u,'east_strip')
        add(u,6-d,'south_control');add(6-d,u,'west_control')
# Actual failing support roots selected deterministically on both outer edges.
diagnosis=json.loads((ROOT/'support-boundary-diagnosis.json').read_text())
for side in ('north','east'):
    selected=[r for r in diagnosis['rows'] if r['minimum'] is None and r['origin'][2 if side=='north' else 0]>12282]
    for i in np.linspace(0,len(selected)-1,12).astype(int):
        r=selected[i];add(r['origin'][0],r['origin'][2],'actual_'+side+'_root');rows[-1]['object_id']=r['id']
text=''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in rows);(mission/'points.csv').write_text(text,encoding='ascii')
mods=Path('P:/Mods/@DayZ_Baltic_EV112_VisualReviewR/Addons');expected={'narva_trial.pbo':'234881855edd0529c4c899ed5e68c3517379588e857652132fbb6f3708a343c8','baltic_stream_pilot.pbo':'742fcc8d076df39a8c54cb99f86c3099976219afe00bc62561794f7cc701bec7','baltic_water_v30.pbo':'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}
for f,h in expected.items():assert hashlib.sha256((mods/f).read_bytes()).hexdigest()==h
launch=json.loads((B/'personal-view-visual-20261024-r/launch-server.json').read_text());launch.update(mission=str(mission),on_busy='queue',server_wait_s=60)
(out/'launch.json').write_text(json.dumps(launch,indent=2));(out/'points.json').write_text(json.dumps(dict(schema='boundary-hypothesis-probe-v1',points=rows,mod_sha256=expected,mission=str(mission),init_sha256=hashlib.sha256(src.read_bytes()).hexdigest(),csv_sha256=hashlib.sha256((mission/'points.csv').read_bytes()).hexdigest(),scope='Diagnostic only: clamped_hypothesis is not expected truth or an acceptance criterion.'),indent=2))
print(json.dumps(dict(points=len(rows),mission=str(mission),launch=launch)))
