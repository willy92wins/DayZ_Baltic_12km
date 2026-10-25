"""Archive the completed reviewed build without inventing a runtime attempt."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,shutil
O=Path(__file__).parent;P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=P/'evidence/v31-pond-layer-2026-10-13/ev112/integration/reviewed-ae-awaiting-runtime';assert not D.exists()
read=lambda name:json.loads((O/name).read_text(encoding='utf-8'))
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
deploy=read('deploy.json');build=read('build-review-closure-ae.json');closure=read('forest-review-closure-ae.json')
assert deploy['offline_status']=='PASS' and build['critical_major_open']==0 and build['ready_for_server_probe']
assert build['world_sha256']==deploy['world_sha256'] and build['water_sha256']==deploy['water_sha256']
assert not (O/'missions-installed-ae.json').exists()
bound={};selected=set()
for table in (closure['evidence'],deploy['evidence'],build['evidence'],read('forest-ae-frozen.json')['files'],read('forest-validation-inputs.json')['files']):
 for name,h in table.items():
  path=Path(name).resolve();assert path.is_file() and sha(path)==h,(name,'changed')
  selected.add(path);bound[str(path)]=h
for name in ('deploy.json','forest-review-closure-ae.json','build-review-closure-ae.json','runtime-blocker-ae.json','runtime-preflight-ae.json','record-build-review-ae-provenance.py','close-build-review-ae.py','record-ae-offline-complete.py','archive-reviewed-build-ae.py','archive-final-ev112.py','install-ev112-missions.py','capture-runtime-probe-ae.py','evaluate-runtime-probe-c.py','eval_bridge_regression_ev112.py','bind-personal-view-final.py','prepare-final-build-review.py','forest-ae-control-domain-boundary.json','audit-ae-control-domain-boundary.py','forest-ae-negative-domains.log','forest-ae-negative-domains-execution.json','forest-ae-resume-after-domains.log','forest-ae-resume-after-domains.json','forest-ae-validated-chain.json','forest-ae-validated-chain.log','forest-ae-resume-after-import.json','forest-ae-resume-after-import.log','forest-ae-resume-negatives.log','pipeline-ae-package.attempt1-import-failure.json','pipeline-ae-package.attempt2-regional-failure.json','forest-source-s-to-ae.diff','forest-clearings-s-to-ae.diff','forest-ae-runner-bindings.json','forest-ae-runners.json'):
  path=(O/name).resolve();assert path.is_file(),name;selected.add(path)
for name in ('build-review-ae-provenance','personal-view-ae','probe-c','forest-final-renders-ae','forest-r2-diagnostics-ae-painted','forest-map-51ae','forest-final-negatives-ae','forest-final-negatives-ae/domain-positive','forest-final-negatives-ae/mutations/physical','forest-final-negatives-ae/mutations/distribution','surface-gates-ae-results','surface-gates-b','wrp-readback-ae'):
 root=O/name;assert root.is_dir()
 selected.update(x.resolve() for x in root.iterdir() if x.is_file() and x.suffix.lower() in ('.json','.log','.md','.png','.txt','.csv','.py','.lst'))
route=read('personal-view-ae/route.json')
for rel,h in route['mission_files'].items():
 source=Path(route['prepared_mission'])/rel;assert sha(source)==h;selected.add(source.resolve())
for seed in range(181,191):
 for name in ('report.json','g2r2.json','g3r2.json','g7r2.json'):
  path=O/f'forest-holdout-ae-seed{seed}'/name;assert path.is_file();selected.add(path.resolve())
for pattern in ('review-build-ae-r1*','run-review-build-ae-r1.py','forest-holdout-ae*.log','forest-ae-*-regression-steps.json','run-*ae*.py'):
 selected.update(x.resolve() for x in O.glob(pattern) if x.is_file())
for name,h in closure['conditions']['promoted'].items():
 path=Path(name).resolve();assert sha(path)==h;selected.add(path);bound[str(path)]=h
for name in ('package-final-ae/packed/narva_trial.pbo','water-prepared-fp49ee/baltic_water_v30.pbo'):
 selected.add((O/name).resolve())
D.mkdir(parents=True);rows=[]
for source in sorted(selected):
 h=sha(source);assert str(source) not in bound or bound[str(source)]==h
 size=source.stat().st_size;rel=None
 if size<=20*1024*1024:
  if source.is_relative_to(O):rel=source.relative_to(O)
  elif source.is_relative_to(P):rel=Path('promoted-sources')/source.relative_to(P)
  if rel is not None:
   target=D/rel;target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
   shutil.copyfile(source,target);assert sha(target)==h
 rows.append(dict(source=str(source),sha256=h,bytes=size,archived_relative=rel.as_posix() if rel else None))
manifest=dict(schema='ev112-reviewed-build-before-runtime.v1',recorded_at_utc=datetime.now(timezone.utc).isoformat(),
 status='OFFLINE_AND_OT7_COMPLETE_RUNTIME_BLOCKED',world_sha256=deploy['world_sha256'],water_sha256=deploy['water_sha256'],
 source_commit=build['source_commit'],offline='PASS',review=build['verdict'],critical_major_open=0,server_probe='NOT_RUN_EXTERNAL_BOX_OCCUPIED',
 personal_view='PREPARED_NOT_INSTALLED_NOT_ACCEPTED',protected_01545='PENDING60m;never PASS',files=rows)
(D/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(D/'README.md').write_text(f'''# EV112 AE: build revisado, sonda pendiente\n\nOffline PASS y OT7 **SOUND-with-fixes**, sin criticos ni mayores. Fuentes en commit `{build['source_commit']}`. La sonda no se ha ejecutado: el banco DayZ esta ocupado por otra sesion protegida por actividad humana. No se ha adquirido lease, cerrado/adoptado el run ni cambiado misiones vivas.\n\n- [Revision independiente real](review-build-ae-r1.json) y [cierre de sus hallazgos](build-review-closure-ae.json).\n- [Despliegue](deploy.json): `{deploy['mod']}`. Mundo `{deploy['world_sha256']}`, agua `{deploy['water_sha256']}`.\n- Bosque:45etapas conocidas y50/50 nuevas(181–190),6positivos/25mutaciones;2.561.015 registros. Los fallos historicos del arnes permanecen archivados.\n- [Vista personal preparada](personal-view-ae/README.md),16archivos vinculados al paquete; sin instalar ni lanzarcliente.\n- [Bloqueo externo observado](runtime-blocker-ae.json); [preflight](runtime-preflight-ae.json) valido, sin lanzar procesos. No fue necesario renovar el lanzador.\n\n## Limites\n\n015-45 conserva su disco60m pendiente. OT4≤0,03m solo en el dominio central aprobado. G8 pasa sin exenciones por ventana y conserva exclusiones estructurales de Narva/kit/puentes. G2/G3 global no significa todaslasventanasPASS. G9 mantiene3filas diagnosticasFAIL de juncos.124traslacionesWRP no entran en lasmutaciones; cada gate conserva sus filtros. El inventario de dependencias de compilacion es posterior, no una atestacion retroactiva. Vista personal, FPS, alturas compiladas decodificadas y resultado motor no acreditados.\n\n## Continuacion exacta\n\nCuando el banco este libre: session_status, session_acquire_wait, instalar con `install-ev112-missions.py ae`, liberar; dayz_test_run solo servidor con rutas Windows normalizadas, sinfilepatching/base-mods, moduloEV112; adquirir para adoptar runpropio; esperarEND4114; `capture-runtime-probe-ae.py` sobre el perfil devuelto realmente; cerrar runpropio/liberar/status; `evaluate-runtime-probe-c.py`; investigar todoFAIL y conservar losveredictoscrudos; `archive-final-ev112.py ae <intento>`. Sin cliente automatico.\n\nEl manifiesto conserva hashes de todoslosarchivos seleccionados. Ficheros mayoresde20MiB y entradas externas permanecen en sus rutas originales, fijados por SHA256. Este archivo no sustituye una sonda ni declara EV112 aceptado en juego.\n''',encoding='utf-8')
print('ARCHIVED_REVIEWED_BUILD_RUNTIME_NOT_RUN',D,'files',len(rows))
