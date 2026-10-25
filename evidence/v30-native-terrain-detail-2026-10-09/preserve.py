from pathlib import Path
import hashlib,json,shutil,re
import numpy as np
from PIL import Image
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-native-terrain-detail-2026-10-09'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def cp(a,b):
 b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b);assert sha(a)==sha(b)
ref=json.loads((B/'reference.json').read_text());runtime=json.loads((B/'runtime.json').read_text())
profile=Path('P:/DayZ_MCP_dev/_client/profiles/Users/Dev/guill_settings.DayZProfile')
assert sha(profile)==ref['profile_sha256']
maps={p.name:sha(p) for p in Path('P:/Mods/@DayZ_Baltic_CurrentSurfaceV1/Addons').glob('*.pbo')};assert maps==ref['map_files']
cp(Path('P:/DayZ_MCP_dev/_client/profiles/baltic_detail_probe_v1.log'),B/'native-detail.log')
cp(Path('P:/DayZ_MCP_dev/_server/profiles/baltic_render_layer_v1.log'),B/'native-sea.log')
lines=(B/'native-detail.log').read_text().splitlines();phases=[s for s in lines if s.startswith('PHASE;')]
assert len(phases)==3 and ';index=4;changed=1;restart=0' in phases[1] and ';requested;index=2;changed=0' in phases[2]
groups={};image_stats={};rois={'pond_group':(650,475,1510,680),'dry_control':(300,850,600,1030)}
for label in ['baseline','extreme','restored']:
 frames=[r for r in runtime['captures'] if r['phase']==label];assert len(frames)==6
 assert all(r['frame_stale'] is False for r in frames)
 arrays=np.stack([np.asarray(Image.open(r['fullres_path']).convert('RGB'),dtype=np.float32) for r in frames])
 groups[label]=arrays
 image_stats[label]={}
 for name,(x0,y0,x1,y1) in rois.items():
  region=arrays[:,y0:y1,x0:x1];means=region.mean(axis=(1,2,3))
  image_stats[label][name]=dict(frame_mean_rgb_min=float(means.min()),frame_mean_rgb_max=float(means.max()),mean_rgb=float(region.mean()),temporal_abs_rgb=float(np.mean(np.ptp(region,axis=0))))
pairs={}
for a,b in [('baseline','extreme'),('baseline','restored')]:
 pairs[a+'_vs_'+b]={}
 for name,(x0,y0,x1,y1) in rois.items():
  x=groups[a][:,y0:y1,x0:x1];y=groups[b][:,y0:y1,x0:x1]
  gap=np.maximum(np.maximum(x.min(0)-y.max(0),y.min(0)-x.max(0)),0)
  pairs[a+'_vs_'+b][name]=dict(temporal_envelopes_disjoint_over10_share=float((gap.max(-1)>10).mean()),median_abs_rgb=float(np.abs(np.median(x,axis=0)-np.median(y,axis=0)).mean()))
report=dict(status='DETAIL_OPTION_CONSUMED_RESIDUAL_REMAINS',phases=phases,profile_identical=True,profile_sha256=sha(profile),map_hashes=maps,rois=rois,images=image_stats,pairs=pairs,run_id=runtime['run_id'],restored_index=2,original_index=2,changed_index=4,limits=['Six distinct frames spanning multiple waves per phase; not synchronized exact wave phases.','Texture and water appearance change, but dark halos remain. No map fix promoted.','Index readback verifies option consumption; it does not expose exact native triangles/LOD.','Do not infer a whole-map visual PASS or production FPS.'],close=runtime['close'],final_state=runtime['final'])
(B/'summary.json').write_text(json.dumps(report,indent=2)+'\n')
E.mkdir(exist_ok=False)
for name in ['plan.md','build_probe.py','set_phase.py','preserve.py','reference.json','runtime.json','summary.json','phase-writes.jsonl','native-detail.log','native-sea.log','lint.json','cfgconvert.log','filebank.log']:cp(B/name,E/name)
for p in (B/'baltic_detail_probe_v1').rglob('*'):
 if p.is_file():cp(p,E/'source'/p.relative_to(B/'baltic_detail_probe_v1'))
for p in (B/'captures').rglob('*.jpg'):cp(p,E/'frames'/p.relative_to(B/'captures'))
for src in [Path('P:/DayZ_MCP_dev/_client/profiles'),Path('P:/DayZ_MCP_dev/_server/profiles')]:
 rp=sorted(src.glob('*.RPT'),key=lambda p:p.stat().st_mtime)
 if rp:cp(rp[-1],E/'logs'/src.parent.name/rp[-1].name)
(E/'README.md').write_text('''# EV32 — detalle nativo, sin arreglo promovido

En EV28 exacto, una secuencia original medio(indice2) -> extremo(4) -> Revert(2) conserva la camara cerca de las charcas residuales. El acceso nativo confirma cambio aplicado, sin reinicio, y restauracion sin estado pendiente. Seis capturas distintas por fase abarcan varios ciclos de ola. El aspecto cambia, pero persisten halos; no se propone subir el detalle del usuario como arreglo del mapa. Las olas no se sincronizan exactamente; summary.json conserva la comparacion de envolventes y un control seco, sin convertir una diferencia de fase en causa aislada.

Perfil completo exacto por SHA, mapa/agua exactos. Cierre orderly y banco libre. No se modifican preferencias persistentes, vanilla, terreno ni materiales. Dos solicitudes iniciales de arranque fueron rechazadas por mission_not_allowed (ruta no normalizada/nombre no alias); se corrigen leyendo dayz_test_request.py y pasando la ruta absoluta Windows canonica. Ninguna de esas solicitudes inicio procesos.
''',encoding='utf-8')
(E/'preservation.json').write_text(json.dumps({str(p.relative_to(E)):sha(p) for p in E.rglob('*') if p.is_file()},indent=2)+'\n')
print(json.dumps(dict(status=report['status'],profile_identical=True,pairs=pairs,evidence=str(E)),indent=2))
