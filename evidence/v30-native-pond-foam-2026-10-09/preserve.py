from pathlib import Path
import hashlib,json,shutil
import numpy as np
from PIL import Image
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-native-pond-foam-2026-10-09';E.mkdir(exist_ok=True);assert not any(E.iterdir())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def cp(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b);assert sha(a)==sha(b)
for source,name in [(Path('P:/DayZ_MCP_dev/_client/profiles/baltic_pond_foam_probe_v1.log'),'native-foam.log'),(Path('P:/DayZ_MCP_dev/_server/profiles/baltic_render_layer_v1.log'),'native-sea.log')]:cp(source,B/name)
rt=json.loads((B/'runtime.json').read_text());ref=json.loads((B/'reference.json').read_text());rows=[]
for row in rt['captures']:
 a=np.array(Image.open(row['fullres_path']).convert('RGB')).astype(int);magenta=(a[:,:,0]>a[:,:,1]+65)&(a[:,:,2]>a[:,:,1]+65)&(a[:,:,0]>120)&(a[:,:,2]>120)
 rows.append(dict(phase=row['phase'],sky_magenta=int(magenta[:350].sum()),water_region_magenta=int(magenta[400:].sum())))
assert all(x['sky_magenta']>10000 for x in rows if x['phase']=='baseline')
assert next(x['sky_magenta'] for x in rows if x['phase']=='foam-zero-invalid-reference')==0
rt['status']='INCONCLUSIVE_UNSTABLE_RENDER_BASELINE';rt['correction']='Sky was magenta in every baseline frame BEFORE any material change. Attribution to FoamColor rejected by direct reference check.'
(B/'runtime.json').write_text(json.dumps(rt,indent=2)+'\n')
profile=Path('P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile');maps={p.name:sha(p) for p in Path('P:/Mods/@DayZ_Baltic_CurrentSurfaceV1/Addons').glob('*.pbo')};assert maps==ref['map_files'] and sha(profile)==ref['profile_sha256']
summary=dict(status=rt['status'],pixels=rows,run_id=rt['run_id'],profile_identical=True,map_files=maps,limits=['Sky is already magenta in untouched baseline; it is NOT attributed to FoamColor. Later sky/terrain texture appearance changes during the run.','FoamColor marks local water, but FoamPower phase lacks a stable matching reference and is not a fix test.','No engine crash: unstable graphics, then orderly client/server shutdown.','No production changes; no more parameter mutations in this block.'])
(B/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for p in B.iterdir():
 if p.is_file() and p.suffix in ('.py','.json','.md','.log','.jsonl'):cp(p,E/p.name)
for p in (B/'baltic_pond_foam_probe_v1').rglob('*'):
 if p.is_file():cp(p,E/'source'/p.relative_to(B/'baltic_pond_foam_probe_v1'))
for p in (B/'captures').rglob('*.jpg'):cp(p,E/'frames'/p.relative_to(B/'captures'))
for root in [Path('P:/DayZ_MCP_dev/_client/profiles'),Path('P:/DayZ_MCP_dev/_server/profiles')]:
 p=max(root.glob('*.RPT'),key=lambda x:x.stat().st_mtime);cp(p,E/'logs'/root.parent.name/p.name)
(E/'README.md').write_text('''# EV35 — control de espuma inconcluso

El cielo ya es magenta en las tres referencias intactas, ANTES de cambiar FoamColor. La atribucion inicial al parametro se rechaza al cotejar referencias. FoamColor marca las charcas; al restaurar, estas recuperan el color. Durante FoamPower0 cambian tambien cielo y carga de texturas: la referencia no es estable y no prueba un arreglo. Se detiene el experimento, se solicitan resets y se cierran cliente/servidor orderly. Perfil y PBO exactos, lease liberado. No modificacion de produccion ni nueva ronda de parametros.

La cuenta de pixeles documenta la referencia inestable; no identifica su causa interna ni acredita que FoamPower solucione nada. No hubo crash. Parametros aceptados/indices validos no son lectura del estado de dibujo. Continuar con geometria y consumidores; residual grafico sigue abierto.
''',encoding='utf-8')
(E/'preservation.json').write_text(json.dumps({str(p.relative_to(E)):sha(p) for p in E.rglob('*') if p.is_file()},indent=2)+'\n')
print(json.dumps(summary,indent=2))
