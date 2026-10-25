from pathlib import Path
import hashlib,json,shutil,sys
import numpy as np
if not __debug__:raise RuntimeError('Assertions required')
R=Path(__file__).parent;O=R/'runtime-road-f';B=Path('E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/water'));from streambed_kit_v31 import tri_h
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=B/'personal-view-visual-20261024-r/points.json';old=json.loads(source.read_text());assert len(old['road_sections'])==11
terrain=R/'rectangle-pilot-f-merged/terrain-buried.npz';assert sha(terrain)=='caa5398021399b6e435faf407005f053d58758091371b5b8fbd2e60e53f69cfc'
H=np.load(terrain)['heights'];prior={p['id']:p for p in old['points']};points=[];sections=[]
for section in old['road_sections']:
    ids=[]
    for i in section['ids']:
        p=prior[i];h=float(tri_h(H,np.array([p['x']]),np.array([p['z']]))[0]);assert p['expect']=='dry'
        q={**p,'id':len(points),'ground':h,'bed':h};ids.append(q['id']);points.append(q)
    assert len(ids)==17 and max(points[i]['ground'] for i in ids)-min(points[i]['ground'] for i in ids)<=.03
    sections.append(dict(station_m=section['station_m'],ids=ids))
assert len(points)==187 and len({(p['x'],p['z']) for p in points})==187
mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticRoadF.BalticTrial');assert not O.exists() and not mission.exists();O.mkdir();mission.mkdir()
shutil.copyfile(Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticRectangleF.BalticTrial/init.c'),mission/'init.c')
(mission/'points.csv').write_text(''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in points),encoding='ascii',newline='\n')
base=json.loads((R/'runtime-midpoint-b/full/deployment.json').read_text());inputs={str(p):sha(p) for p in [source,terrain,mission/'init.c',mission/'points.csv',W/'tools/water/eval_visual_road_probe_ev112.py',W/'tools/water/eval_visual_probe_v31.py']};inputs.update(base['deployed'])
for path,h in inputs.items():assert sha(path)==h,path
doc=dict(schema='ev112-visual-probe-v1',points=points,road_sections=sections,inputs=inputs,inherited_inputs={str(source):sha(source)},scope='All17 original XZ samples in each of11 former road49 cross-slope failures. Expected terrain Y recalculated on frozen F; previous R retained separately. No driving acceptance.')
(O/'points.json').write_text(json.dumps(doc,indent=2)+'\n');inputs[str(O/'points.json')]=sha(O/'points.json')
deployment=dict(base,kind='roads',points=187,mission=str(mission),inputs=inputs);(O/'deployment.json').write_text(json.dumps(deployment,indent=2)+'\n')
s=(R/'capture_midpoint_log.ps1').read_text().replace('@(4749,300)','@(187)');(R/'capture_road_f_log.ps1').write_text(s)
s=(R/'finish_midpoint_probe.py').read_text().replace("kind=sys.argv[1];assert kind in ('full','grid');O=R/'runtime-midpoint-b'/kind", "kind='full';O=R/'runtime-road-f'")
s=s.replace("W/'tools/water/eval_visual_probe_v31.py'","W/'tools/water/eval_visual_road_probe_ev112.py'")
(R/'finish_road_f_probe.py').write_text(s)
print(json.dumps(dict(status='PREPARED_NOT_RUN',points=187,sections=11,unchanged_XZ=True,expected_ground='frozen F terrain')))
