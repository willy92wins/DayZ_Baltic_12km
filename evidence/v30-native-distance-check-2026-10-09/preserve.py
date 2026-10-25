from pathlib import Path
import hashlib,json,shutil,re
import numpy as np
from PIL import Image
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-native-distance-check-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b);assert sha(a)==sha(b)
profile=Path('P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile')
ref=json.loads((B/'reference.json').read_text())
settings={k:float(re.search(r'^'+k+r'=([^;]+);',profile.read_text(),re.M).group(1)) for k in ref['settings']}
assert settings==ref['settings']
assert sha(profile)==ref['profile_sha256']
maps={p.name:sha(p) for p in Path('P:/Mods/@DayZ_Baltic_CurrentSurfaceV1/Addons').glob('*.pbo')}
assert maps==ref['map_files']
copy(Path('P:/DayZ_MCP_dev/_client/profiles/baltic_distance_probe_v1.log'),B/'native-distance.log')
blocks=[]
for line in (B/'native-distance.log').read_text().splitlines():
 v=line.split(';')
 if v[0]=='PHASE':blocks.append(dict(phase=int(v[1]),start=int(v[2]),samples=[]))
 if v[0]=='FPS':blocks[-1]['samples'].append(dict(ms=int(v[2]),last=float(v[3]),avg64=float(v[4]),camera=v[7],direction=v[8]))
assert [b['phase'] for b in blocks]==[0,1,3,1,2,3]
stats=[]
for i,b in enumerate(blocks):
 rows=[r for r in b['samples'] if r['ms']-b['start']>=5000]
 valid=i>=2
 if valid:
  assert len(rows)>=15
  assert len({(r['camera'],r['direction']) for r in rows})==1
  assert rows[0]['camera']=='<6640.000000, 440.000000, 6340.000000>'
 stats.append(dict(block=i,phase=b['phase'],valid=valid,reason='corrected active scene' if valid else 'pause menu observed; excluded',settled_samples=len(rows),settle_ms=5000,last_fps_median=float(np.median([r['last'] for r in rows])) if rows else None,avg64_fps_median=float(np.median([r['avg64'] for r in rows])) if rows else None))
runtime=json.loads((B/'runtime.json').read_text())
images={k:np.asarray(Image.open(runtime[k]['fullres_path']).convert('RGB'),dtype=np.float32) for k in ['baseline','view5000','objects5000','restored']}
# Central scene only. Full source frames are preserved; no edited evidence images.
region=(slice(300,1000),slice(60,1860))
metrics={}
for name,a,b in [('base_vs_restored','baseline','restored'),('base_vs_view','baseline','view5000'),('view_vs_objects','view5000','objects5000')]:
 d=np.abs(images[a][region]-images[b][region]);metrics[name]=dict(mean_abs_rgb=float(d.mean()),share_pixels_over10=float((d.max(axis=2)>10).mean()))
report=dict(status='DISTANCE_FOG_DISCRIMINATED_NOT_STREAMING_FIXED',run_id=runtime['run_id'],blocks=stats,image_metrics=metrics,settings_after=settings,profile_hash_after=sha(profile),profile_byte_identical=True,map_files_after=maps,world_time=runtime['time']['world_time'],camera=runtime['camera']['camera'],close=runtime['close'],final_state=runtime['final'],limitations=['Reference is explicitly restored1600, not untouched initial state.','No native view-distance getter; setter execution and reversible image change are evidence.','Native19FPS in test client is descriptive, not a production benchmark.','All captures have distinct frames but tiny adjacent deltas trigger render_frozen_signal.','Object-distance addition changes some distant water pixels; no all-map streaming or water-gap closure.'])
(B/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
E.mkdir(exist_ok=False)
for name in ['plan.md','build_probe.py','set_phase.py','preserve.py','reference.json','runtime.json','summary.json','phase-writes.jsonl','native-distance.log','lint.json','cfgconvert.log','filebank.log']:copy(B/name,E/name)
for p in (B/'baltic_distance_probe_v1').rglob('*'):
 if p.is_file():copy(p,E/'source'/p.relative_to(B/'baltic_distance_probe_v1'))
for p in (B/'captures').rglob('*.jpg'):copy(p,E/'frames'/p.relative_to(B/'captures'))
for source in [Path('P:/DayZ_MCP_dev/_client/profiles'),Path('P:/DayZ_MCP_dev/_server/profiles')]:
 files=sorted(source.glob('*.RPT'),key=lambda p:p.stat().st_mtime)
 if files:copy(files[-1],E/'logs'/source.parent.name/files[-1].name)
(E/'README.md').write_text('''# EV31 — distancia de dibujo y bruma

En EV28 byte-identico se ejecuta una secuencia cliente1600 -> vista5000 -> vista/objetos5000 ->1600, con camara y hora fijas. La bruma cercana se retira al ampliar la vista y vuelve al restaurarla. La fuente opaca queda aislada por reversibilidad del ajuste, sin cambiar geometria/materiales. El añadido de distancia de objetos tiene cambios menores en agua lejana; no prueba cobertura global ni arregla el streaming intermitente019.

La fase0 inicial y primera fase1 tenian menu de pausa: se conservan pero quedan excluidas. La secuencia valida comienza tras ui_click continuebtn, restaurando explicitamente1600; no se presenta como referencia inicial intacta. Cada bloque valido conserva >=15 muestras tras5s de asentamiento. El cliente registra ~19FPS durante la escena; no es benchmark, no se midio foco del SO. Distintas imagenes con diferencias pequeñas activan la advertencia heuristica render_frozen_signal; no ocultada.

Perfil de usuario exacto por SHA despues del cierre. Mapa y agua exactos. Run cerrado orderly cliente/servidor, lease liberado y banco libre. Este diagnostico no se incorpora al mapa. La vista lejana de EV28 deja de ser una prueba util de textura mas alla de la distancia configurada; 019 y los halos siguen abiertos.
''',encoding='utf-8')
(E/'preservation.json').write_text(json.dumps({str(p.relative_to(E)):sha(p) for p in E.rglob('*') if p.is_file()},indent=2)+'\n')
print(json.dumps(dict(status=report['status'],blocks=stats,metrics=metrics,evidence=str(E)),indent=2))
