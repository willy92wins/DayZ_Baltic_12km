"""Prepare a fresh, package-bound preview folder; no live mission or DayZ mutations."""
from pathlib import Path
import json,sys,hashlib,shutil,re
import numpy as np
O=Path(__file__).parent;tag=sys.argv[1];assert re.fullmatch('[a-z][a-z0-9]*',tag)
P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
sys.path.insert(0,str(P/'tools/terrain'));from v30_common import tri_sample
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
base=O/'personal-view-c';assert sha(base/'route.json')=='d577ac1746b303b89868ed86ad88e4ebe078cf988f245b2b37d610a32201e8a8'
deploy=O/'deploy.json';d=json.loads(deploy.read_text());assert d['forest_tag']==tag and d['offline_status']=='PASS'
mod=Path(d['mod']);assert sha(mod/'Addons/narva_trial.pbo')==d['world_sha256'] and sha(mod/'Addons/baltic_water_v30.pbo')==d['water_sha256']
terrain=O/'terrain-ev112-c.npz';assert sha(terrain)==d['terrain_sha256'];H=np.load(terrain)['heights']
counts_path=O/f'forest-map-51{tag}/counts.json';counts=json.loads(counts_path.read_text());dense=counts['baltic']['densest_km2_all']
route=json.loads((base/'route.json').read_text());assert route['terrain_sha256']==d['terrain_sha256']
x,z=[v+500 for v in dense['x0_z0']]
row=next(v for v in route['route'] if v['id']=='densest-vegetation-km2');row.update(x=float(x),z=float(z),offline_ground_y=float(tri_sample(H,[x],[z])[0]),purpose=f"Km2 X{x-500}..{x+500}/Z{z-500}..{z+500}; {dense['all']} instancias. Medir FPS, sin inferirlos del recuento.")
route['package_binding']={k:d[k] for k in ('mod','world_sha256','water_sha256','terrain_sha256','footprint_sha256','forest_records_sha256','compiled_wrp_sha256')}
route['package_binding'].update(deploy_sha256=sha(deploy),counts_sha256=sha(counts_path))
route['densest_trees_diagnostic']=counts['baltic']['densest_km2_trees']
D=O/f'personal-view-{tag}';D.mkdir(exist_ok=False);mission=D/'BalticBasicEV112.BalticTrial';mission.mkdir();(mission/'db').mkdir()
static=json.loads((base/'mission-static-files.json').read_text());files={v['relative']:v['prepared_sha256'] for v in static['files']};files['init.c']=route['prepared_init_sha256'];assert len(files)==16
for rel,h in files.items():
 src=base/'BalticBasicEV112.BalticTrial'/rel;assert sha(src)==h
 dst=mission/rel;shutil.copyfile(src,dst);assert sha(dst)==h
route['prepared_mission']=str(mission);route['mission_files']=files
route['live_installation']='PENDING_UNDER_LEASE; fresh BalticBasicEV112.BalticTrial in approved DayZServer mpmissions root'
(D/'route.json').write_bytes((json.dumps(route,indent=2)+'\n').encode())
lines=['# Vista personal EV112 preparada','',
 'Estado: preparada y vinculada al paquete; no lanzada ni aceptada visualmente.',
 'Para instalar la copia en mpmissions y lanzar: comprobar hashes y lease disponible. No cerrar ni adoptar procesos ajenos.',
 'El cliente requiere foco de Guillermo y Continuar si aparece pausa. La aparicion preparada es Narva (2392,6948).','',
 '| Punto | X | Z | Revisar |','|---|---:|---:|---|']
lines += [f"| {v['id']} | {v['x']} | {v['z']} | {v['purpose']} |" for v in route['route']]
lines += ['',f"Paquete: {mod}",f"Mundo SHA256: {d['world_sha256']}",f"Agua SHA256: {d['water_sha256']}",
 '','Traslado: lease, bridge_status listo, place_safely y altura consultada en el motor; nunca usar la altura offline como prueba de colision.',
 'FPS: registrar equipo, opciones, resolucion, posicion, direccion, duracion y minimo/mediana. No deducir rendimiento del recuento.',
 '015-45 conserva su disco protegido de60m PENDIENTE. El cambio de caracter de turbera frenteEV111 requiere vista personal.']
(D/'README.md').write_bytes(('\n'.join(lines)+'\n').encode())
print('PREPARED_NOT_RUN_NOT_VISUALLY_ACCEPTED',D,len(files),'mission files')
