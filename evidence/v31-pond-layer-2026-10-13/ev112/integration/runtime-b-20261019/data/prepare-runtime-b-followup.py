"""Prepare documentation/diagnostic bindings; never launches or edits live missions."""
from pathlib import Path
import hashlib,json,shutil,sys
import numpy as np
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(P/'tools/terrain'));from v30_common import tri_sample
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
dep=json.loads((O/'deploy-runtime-b.json').read_text(encoding='utf-8'));installed=json.loads((O/'missions-installed-ae.json').read_text(encoding='utf-8'))
assert all(sha(Path(installed['personal_mission'])/p)==h for p,h in installed['personal_files'].items())
h=np.load(O/'water-fix-b/terrain.npz')['heights']
V=O/'personal-view-runtime-b';V.mkdir(exist_ok=False)
route=json.loads((O/'personal-view-ae/route.json').read_text(encoding='utf-8'));route['terrain_sha256']=dep['terrain_sha256']
for r in route['route']:r['offline_ground_y']=float(tri_sample(h,[r['x']],[r['z']])[0])
route.update(world_sha256=dep['world_sha256'],water_sha256=dep['water_sha256'],mod=dep['mod'],mission=installed['personal_mission'],live_files=installed['personal_files'],status='INSTALLED_AND_PREPARED_NOT_LAUNCHED_NOT_VISUALLY_ACCEPTED')
(V/'route.json').write_text(json.dumps(route,indent=2)+'\n')
request=dict(project='DayZ_MCP',mode='all',mission=installed['personal_mission'],extra_mods=[dep['mod']],no_base_mods=True,no_file_patching=True,build=False,takeover=False,on_busy='queue',wait_for_box_s=600)
(V/'launch-request.json').write_text(json.dumps(request,indent=2)+'\n')
s=(O/'personal-view-ae/README.md').read_text(encoding='utf-8');s=s.replace('preparada y vinculada al paquete; no lanzada ni aceptada visualmente.','instalada, preparada y vinculada al paquete corregido; no lanzada ni aceptada visualmente.')
s=s.replace('Para instalar la copia en mpmissions y lanzar:','Para lanzar la copia ya instalada en mpmissions:').replace('@DayZ_Baltic_EV112_LatticeForestV1','@DayZ_Baltic_EV112_RuntimeMarginsV2').replace('bf2627eb7abe95652eb215b27694983252c11d019e147635795b8d4cf114246e',dep['world_sha256'])
s+='\nMisión: '+installed['personal_mission']+'\n\nLos 16 archivos se verificaron por hash contra la instalación. Ruta en `route.json`; solicitud pública preparada en `launch-request.json`, para ejecutar cuando Guillermo esté delante. Comprobar session_status, lanzar dayz_test_run sin lease previo y después adoptar con session_acquire_wait. Mantener heartbeat durante la visita y cierre ordenado al terminar. No se ha lanzado ningún cliente.\n'
(V/'README.md').write_text(s,encoding='utf-8')
D=O/'water-temporal-runtime-b';D.mkdir(exist_ok=False)
live=Path('C:/Program Files (x86)/Steam/steamapps/common/DayZServer/mpmissions/BalticWaterTemporalEV112.BalticTrial')
for name in ('init.c','points.csv'):
 assert sha(live/name)==sha(O/'water-temporal-ae'/name);shutil.copyfile(live/name,D/name)
ps=json.loads((O/'water-temporal-ae/points.json').read_text(encoding='utf-8'))
for p in ps:p['ground']=float(tri_sample(h,[p['x']],[p['z']])[0])
(D/'points.json').write_text(json.dumps(ps,indent=2)+'\n')
(D/'binding.json').write_text(json.dumps(dict(status='PREPARED_NOT_RUN',deploy_sha256=sha(O/'deploy-runtime-b.json'),world_sha256=dep['world_sha256'],water_sha256=dep['water_sha256'],terrain_sha256=dep['terrain_sha256'],mission=str(live),files={n:sha(D/n) for n in ('init.c','points.csv','points.json')},samples=30,scope='Same eight temporal points and fixed weather. Require corrected wet controls positive on all30 samples and dry controls nonpositive on all30. Concrete test retained separately. No all-weather/player/FPS claim.'),indent=2)+'\n')
s=(O/'evaluate-water-temporal-ae.py').read_text(encoding='utf-8');assert "D=O/'water-temporal-ae'" in s;s=s.replace("D=O/'water-temporal-ae'","D=O/'water-temporal-runtime-b'")
old="required_points_cross_zero=all(result[str(i)]['crosses_zero'] for i in (2733,3807,3808,3836))"
new="required_points_match_all_samples=all(result[str(i)]['positive_depths']==(30 if ps[i]['expect']=='wet' else 0) for i in (2733,3807,3808,3836)), controls_match_all_samples=all(result[str(i)]['positive_depths']==(30 if ps[i]['expect']=='wet' else 0) for i in (1136,1116,3837))"
assert old in s;s=s.replace(old,new).replace('One minute, fixed weather, eight points. No bound for all weather; original strict FAIL unchanged.','One minute, fixed weather, eight identical coordinates. No all-weather bound or visual/player acceptance. Historical strict FAIL preserved; concrete-joint test remains pending.')
s=s.replace("print(json.dumps(out,indent=2))","print(json.dumps({k:v for k,v in out.items() if k!='points'},indent=2))")
(O/'evaluate-water-temporal-runtime-b.py').write_text(s,encoding='utf-8')
print('Personal view and temporal verification prepared; no launch.')
