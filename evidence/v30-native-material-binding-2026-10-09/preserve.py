from pathlib import Path
import hashlib,json,shutil,re
import numpy as np
from PIL import Image
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-native-material-binding-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def cp(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b);assert sha(a)==sha(b)
rt=json.loads((B/'runtime.json').read_text());ref=json.loads((B/'reference.json').read_text())
cp(Path('P:/DayZ_MCP_dev/_client/profiles/baltic_material_binding_probe_v1.log'),B/'native-binding.log')
cp(Path('P:/DayZ_MCP_dev/_server/profiles/baltic_render_layer_v1.log'),B/'native-sea.log')
phases=[s for s in (B/'native-binding.log').read_text().splitlines() if s.startswith('PHASE;')]
assert [int(s.split(';')[1]) for s in phases]==[0,1,2,3,4]
assert all('true;true;true;true' in phases[i] for i in (1,3))
pixels=[]
for row in rt['captures']:
 a=np.array(Image.open(row['fullres_path']).convert('RGB')).astype(int)
 # Native fullres_file is the effective client surface, not the surrounding HWND.
 assert a.shape[:2]==(1080,1920)
 magenta=(a[:,:,0]>a[:,:,1]+65)&(a[:,:,2]>a[:,:,1]+65)&(a[:,:,0]>120)&(a[:,:,2]>120)
 cyan=(a[:,:,1]>a[:,:,0]+65)&(a[:,:,2]>a[:,:,0]+65)&(a[:,:,1]>120)&(a[:,:,2]>120)
 pixels.append(dict(phase=row['phase'],magenta=int(magenta.sum()),cyan=int(cyan.sum()),shape=list(a.shape),file_sha256=sha(Path(row['fullres_path']))))
assert next(x['magenta'] for x in pixels if x['phase']=='moss-marker')>1000
assert all(x['magenta']==0 for x in pixels if x['phase']!='moss-marker')
profile=Path('P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile')
assert sha(profile)==ref['profile_sha256']
maps={p.name:sha(p) for p in Path('P:/Mods/@DayZ_Baltic_CurrentSurfaceV1/Addons').glob('*.pbo')};assert maps==ref['map_files']
report=dict(status='PASS_POND_MOSS_BINDING_CONTROL_NO_FIX',phases=phases,pixel_marker_counts=pixels,profile_byte_identical=True,map_files=maps,run_id=rt['run_id'],limits=['Moss controls actual rendered ponds, but dry halos are not shown eliminated.','Clear receives valid indices/returns but no cyan marker in this view: no proof of visible fallback use.','Initial baseline had some textures still streaming; chromatic positive control is distinct from texture changes.','All marker parameters reset; no production modification.','EV33 WetFloor remains no stable suppression; this run confirms consumer binding but is not a synchronized repeat of EV33.'])
(B/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
E.mkdir(exist_ok=False)
for p in B.iterdir():
 if p.is_file() and p.suffix in ('.py','.json','.md','.log','.c','.jsonl'):cp(p,E/p.name)
for p in (B/'baltic_material_binding_probe_v1').rglob('*'):
 if p.is_file():cp(p,E/'source'/p.relative_to(B/'baltic_material_binding_probe_v1'))
for p in (B/'captures').rglob('*.jpg'):cp(p,E/'frames'/p.relative_to(B/'captures'))
for root in [Path('P:/DayZ_MCP_dev/_client/profiles'),Path('P:/DayZ_MCP_dev/_server/profiles')]:
 p=max(root.glob('*.RPT'),key=lambda x:x.stat().st_mtime);cp(p,E/'logs'/root.parent.name/p.name)
(E/'README.md').write_text('''# EV34 — consumidor del material confirmado

La lectura estatica del ejecutable identifica el enlace CalmWater: busca EMAT con el basename del RVMAT, despues junto a la ruta original y por ultimo la reserva pond_clear. El control nativo confirma pond_moss_1: Color/ReflectionColor magenta con extinction100 y normal0 dibuja las charcas magenta, y reset elimina la marca. Cuenta cromatica independiente en summary.json. Cambiar pond_clear a cyan no marca esta vista pese a handle/indices/retornos validos; no equivale a un consumidor de pixeles.

El halo exterior sigue presente. Se confirma el recurso de EV33, no una cura del residual. La referencia temprana tenia teselas en carga; no se usa una diferencia RGB global como prueba del marcador. El color magenta intenso no existe en referencias ni en la restauracion. Parametros restaurados, perfil completo y mapa exactos, cierre orderly y banco libre.

Se conserva un fallo de arranque con presupuesto10s insuficiente y un primer run que se nego por handle aun nulo. Sonda corregida para resolver cada material al solicitar la fase, con la escena ya establecida. No hubo modificacion del mapa. Base1.0 y 016/018 siguen abiertos.
''',encoding='utf-8')
(E/'preservation.json').write_text(json.dumps({str(p.relative_to(E)):sha(p) for p in E.rglob('*') if p.is_file()},indent=2)+'\n')
p=W/'HANDOFF.md';t=p.read_text(encoding='utf-8');lines=t.splitlines()
updates={'runtime_lock:':'runtime_lock: EV34 eecb3880 cerrado orderly, parametros restaurados; perfil exacto, lease liberado y banco libre. EV33 cambio solo limites horizontales de UI al ampliar ventana antes de medir.','next:':'next: EV34 confirma consumidor pond_moss_1 con marcador magenta y reset; reserva clear no marca la vista. Halo exterior persiste. EV33 WetFloor no resuelve. Examinar espuma del material confirmado; cambiar estrategia de remates: solver previo mantiene signos por vertice y solo mueve cruces existentes. Lagos reservados/TB pendientes.','handoff:':'handoff: EV31 bruma por distancia; EV32 detalle no resuelve; EV33 WetFloor sin supresion; EV34 enlace de material demostrado en runtime. No arreglo grafico promovido; continuar toda la superficie.','git:':'git: Rama claude/codex-handoff-review-74f290; checkpoint EV33/34 propio tras3d8bca9, sin push ni subagentes.'}
for i,line in enumerate(lines):
 for prefix,value in updates.items():
  if line.startswith(prefix):lines[i]=value
p.write_text('\n'.join(lines)+'\n',encoding='utf-8')
p=W/'evidence/v30-global-water-risk-2026-10-09/bug-status-current.md';t=p.read_text(encoding='utf-8').replace('vigente hasta EV32','vigente hasta EV34').replace('MatWaterPool de charcas no habia recibido el cambioWetFloor; EV33 en curso, sin fix promovido.','EV33 WetFloor sin supresion estable; EV34 confirma consumidor pond_moss_1 por marcador/reset. Halo exterior pendiente; sin fix promovido.');p.write_text(t,encoding='utf-8')
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md')
with session.open('a',encoding='utf-8') as f:f.write('\n## EV33/34 — material real, sin cierre del residual\n\nEV33 WetFloor de charca no supera variacion natural; perfil cambia solo limites UI tras redimensionar. EV34 lectura estatica de enlace RVMAT/EMAT y control magenta/reset confirman pond_moss_1. Clear sin marca visible. No arreglo grafico; parametros restaurados, mapa exacto, EV34 perfil exacto, runs cerrados orderly y banco libre. Evidencia W/evidence/v30-native-pond-material-2026-10-09 y v30-native-material-binding-2026-10-09. Smoothing restante, lagos reservados, TB/navmesh/IA abiertos.\n')
print(json.dumps(report,indent=2))
