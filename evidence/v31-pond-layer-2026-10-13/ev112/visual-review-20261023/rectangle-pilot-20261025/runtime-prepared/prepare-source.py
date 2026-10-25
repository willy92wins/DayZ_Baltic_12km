from pathlib import Path
from collections import Counter
import hashlib,json,shutil,sys
import numpy as np
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(W/'tools/navigation'));from waterway_common import sample
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
out=R/'runtime-rectangle-f';assert not out.exists()
source=R/'runtime-guarded-e/points.json';doc=json.loads(source.read_text());assert len(doc['points'])==4401
for p,h in doc['inputs'].items():assert sha(Path(p))==h
doc['inherited_inputs']=doc['inputs'];doc['inputs']={str(source):sha(source)}
terrain=R/'rectangle-pilot-f-merged/terrain-buried.npz';H=np.load(terrain)['heights'].astype(float)
oldH=np.load(R/'guarded-relief-batch-e-merged/terrain-buried.npz')['heights'];changed=H!=oldH
assert int(changed.sum())==94
for p in doc['points']:p['ground']=float(sample(H,np.array([p['x']+200000]),np.array([p['z']]))[0])
existing={(p['x'],p['z']) for p in doc['points']}
def add(x,z,kind):
    if (x,z) in existing:return
    doc['points'].append(dict(id=len(doc['points']),x=float(x),z=float(z),ground=float(sample(H,np.array([x+200000]),np.array([z]))[0]),expect='ground',kind=kind));existing.add((x,z))
for r,c in np.argwhere(changed):add(c*6,12282-r*6,'rectangle_changed_native_vertex')
cells=changed[:-1,:-1]|changed[:-1,1:]|changed[1:,:-1]|changed[1:,1:]
for r,c in np.argwhere(cells):
    for dx,dz in ((4,-2),(2,-4)):add(c*6+dx,12282-r*6+dz,'rectangle_incident_cell_triangle_centroid')
mission=Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticRectangleF.BalticTrial');assert not mission.exists()
mod=Path('P:/Mods/@DayZ_Baltic_EV112_RectangleF');assert not mod.exists()
package=R/'package-rectangle-f/verification.json';report=json.loads(package.read_text());assert report['status']=='OBJECTS_AND_PAYLOAD_VERIFIED_BOUNDARY_PENDING'
sources={R/'package-rectangle-f/Addons/narva_trial.pbo':report['pbo_sha256'],Path('P:/Mods/@DayZ_Baltic_EV112_RVOverlapU2/Addons/baltic_stream_pilot.pbo'):'c0be9abc9d36ee19c636325b825dbf09880a9dc31b5dfb8432e0f91d0e1cfa87',Path('P:/Mods/@DayZ_Baltic_EV112_RVOverlapU2/Addons/baltic_water_v30.pbo'):'97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43'}
for p,h in sources.items():assert sha(p)==h
out.mkdir();mission.mkdir();(mod/'Addons').mkdir(parents=True)
shutil.copyfile(R/'probe-combined/BalticVisualProbeV1.BalticTrial/init.c',mission/'init.c')
(mission/'points.csv').write_text(''.join(f"{p['id']};{p['x']:.6f} 0 {p['z']:.6f}\n" for p in doc['points']),encoding='ascii',newline='\n')
deployed={}
for p,h in sources.items():
    dst=mod/'Addons'/p.name;shutil.copy2(p,dst);assert sha(dst)==h;deployed[str(dst)]=h
for p in (terrain,package,mission/'init.c',mission/'points.csv',Path(__file__)):doc['inputs'][str(p)]=sha(p)
doc['inputs'].update(deployed);doc['counts']=dict(Counter(p['kind'] for p in doc['points']))
doc['scope']='All 4401 inherited E controls plus all 94 changed F vertices and both native triangle centroids in every cell incident to a changed vertex. Expectations bind to F. No client, navigation or visual acceptance.'
(out/'points.json').write_text(json.dumps(doc,indent=2),encoding='utf-8')
launch=dict(project='DayZ_MCP',mode='server',mission=str(mission),extra_mods=[mod.name],base_mods=[],no_base_mods=True,no_file_patching=True,build=False,takeover=False,wait_for_box_s=0,navmesh_data_server=True)
(out/'launch-server.json').write_text(json.dumps(launch,indent=2))
receipt=dict(status='DEPLOYED_ISOLATED_PENDING_RUNTIME',deployed=deployed,points=len(doc['points']),changed_vertices=94,incident_native_cells=int(cells.sum()),mission=str(mission),terrain_sha256=sha(terrain),points_sha256=sha(out/'points.json'),package_sha256=sha(package),previous_mods_preserved=True,global_acceptance=False)
(out/'receipt.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt,indent=2))
