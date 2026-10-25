"""Archive the actual final evidence byte-for-byte; large GIS/PBO inputs stay hash-bound on E:.

Run only after the offline chain, independent build review and server attempt exist.
A runtime FAIL remains FAIL in the archive; this command cannot grant acceptance.
"""
from pathlib import Path
import datetime, hashlib, json, re, shutil, sys
O=Path(__file__).resolve().parent
P=Path('P:/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
tag=sys.argv[1];assert re.fullmatch('[a-z][a-z0-9]*',tag)
attempt=Path(sys.argv[2]).resolve();assert attempt.is_relative_to(O) and attempt.is_dir()
dest=P/'evidence/v31-pond-layer-2026-10-13/ev112/integration'/f'final-{tag}'
assert not dest.exists()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<22),b''):h.update(b)
 return h.hexdigest()
def read(name):return json.loads((O/name).read_text(encoding='utf-8-sig'))
deploy=read('deploy.json');assert deploy['forest_tag']==tag and deploy['offline_status']=='PASS'
closure=read(f'forest-review-closure-{tag}.json')
build=read(f'build-review-closure-{tag}.json')
assert closure['critical_major_open']==build['critical_major_open']==0
assert build['world_sha256']==deploy['world_sha256'] and build['water_sha256']==deploy['water_sha256']
assert sha(build['raw_review'])==build['raw_review_sha256']
runtime=json.loads((attempt/'acceptance.json').read_text())
assert runtime['status'] in ('PASS','FAIL')
assert runtime['terrain_sha256']==deploy['terrain_sha256']
assert sha(attempt/'baltic_bridge_probe_v2.log')==runtime['raw_log_sha256']
selected=set()
bound={}
for table in (closure['evidence'],deploy['evidence'],build.get('evidence',{}),read(f'forest-{tag}-frozen.json')['files']):
 for name,h in table.items():
  p=Path(name).resolve();assert p.is_file() and sha(p)==h,(name,'changed evidence')
  selected.add(p);bound[str(p)]=h
for name in (
 'deploy.json',f'forest-review-closure-{tag}.json',f'build-review-closure-{tag}.json',
 f'forest-{tag}-change.json',f'forest-{tag}-runner-bindings.json',f'forest-{tag}-runners.json',
 f'forest-candidate-{tag}/forest_v31.py','forest-final-tools-s/forest_v31.py',
 f'prepare-forest-{tag}-validation.py',f'forest-{tag}-validation-prepared.json',
 'run-forest-known-cache-v5.py',f'forest-{tag}-known-driver.json',
 f'forest-final-negatives-{tag}/steps.json',f'forest-final-negatives-{tag}/mutations/negatives.json',
 f'forest-source-s-to-{tag}.diff',f'forest-clearings-s-to-{tag}.diff',
 f'forest-{tag}-map-canopy-binding.json',f'forest-{tag}-all-known-steps.json',f'forest-{tag}-calibration-controls.json',f'forest-{tag}-mass-controls.json',f'forest-{tag}-halo-cli-control.json',f'forest-{tag}-canopy-boundary-controls-v2/report.json', 'audit-accepted-canopy-records.py', 'check-accepted-canopy-calibration.py', 'check-ad-conservative-mass.py', 'check-ad-halo-cli.py', 'check-accepted-canopy-boundaries.py',f'forest-map-51{tag}/counts.json',
 'terrain-c-review-closure.json','water-final-binding-c.json',
 'review-terrain-r1.json','review-terrain-r2.json','review-terrain-r2-run.json',
 'review-s-r2.json','review-s-r2-run.json',
 f'forest-r2-diagnostics-{tag}-painted/diagnostics.json',
 f'forest-r2-diagnostics-{tag}-painted/visual-inspection.md',
 f'personal-view-{tag}/route.json',f'personal-view-{tag}/README.md',f'missions-installed-{tag}.json',
 'probe-c/manifest.json','probe-c/points.csv','probe-c/points.json','probe-c/families.json',
 'eval_bridge_regression_ev112.py','evaluate-runtime-probe-c.py',
 f'close-forest-offline-{tag}.py','deploy-verified-ev112.py','prepare-final-build-review.py',
 'install-ev112-missions.py','bind-personal-view-final.py','archive-final-ev112.py',
 'audit-wrp-readback-v2.py','forest-validation-inputs.json','refresh-build-tools-preflight.py',
 'clearings400-moss-controls/controls.json','surface-trial-clearings400/budget.json',
 'surface-trial-clearings400/make_forest_clearings_v31.py',
 ):
  p=(O/name).resolve();assert p.is_file(),name;selected.add(p)
if tag=='ae':
 for name in ('forest-ae-map-nonbush-identity.json','forest-painted-development-ae/binding.json','forest-painted-development-ae/steps.json','forest-ae-planned-clearings-controls/controls.json','forest-ae-extra-control-sources.json','forest-ae-preparer-lint.json','forest-ae-chain-source-binding.json','ae-chain-prerequisite-controls-v2.json','check-ae-calibration.py','check-ae-conservative-mass.py','check-ae-canopy-boundaries.py','check-ae-halo-cli.py','check-ae-chain-prerequisites.py','prepare-forest-ae-surface-floor.py','prepare-ae-validation-chain.py','prepare-ae-closure.py'):
  p=(O/name).resolve();assert p.is_file(),name;selected.add(p)
 for name in ('forest-map-51ad/g2g3-painted.json','forest-final-tools-ad/forest_v31.py'):
  p=(O/name).resolve();assert p.is_file(),name;selected.add(p)
 for name in ('forest-ae-import-repair.json','forest-ae-resume-after-import.json','forest-ae-resume-after-import.log','forest-ae-resume-negatives.log','forest-ae-validated-chain.json','forest-ae-validated-chain.log','pipeline-ae-package-negatives.log','pipeline-ae-package.attempt1-import-failure.json','forest-ae-closure-preparation.json'):
  p=(O/name).resolve();assert p.is_file(),name;selected.add(p)
 diagnostic=O/'forest-painted-development-ae';assert diagnostic.is_dir()
 selected.update(p.resolve() for p in diagnostic.iterdir() if p.is_file() and p.suffix.lower() in ('.json','.log'))
 for name in ('forest-ae-negative-domains.log','forest-ae-negative-domains-execution.json','forest-ae-resume-after-domains.json','forest-ae-resume-after-domains.log','record-ae-domains-execution.py','record-ae-visual-inspection.py','capture-runtime-probe-ae.py'):
  p=(O/name).resolve();assert p.is_file(),name;selected.add(p)
 for name in ('domain-positive','mutations/physical','mutations/distribution'):
  root=O/'forest-final-negatives-ae'/name;assert root.is_dir()
  selected.update(p.resolve() for p in root.iterdir() if p.is_file() and p.suffix.lower() in ('.json','.log'))
 for name in ('forest-ae-control-domain-boundary.json','audit-ae-control-domain-boundary.py'):
  p=(O/name).resolve();assert p.is_file(),name;selected.add(p)
selected.add(Path(build['raw_review']).resolve())
if tag=='ae':
 for name in ('close-build-review-ae.py','record-build-review-ae-provenance.py','record-ae-offline-complete.py','runtime-preflight-ae.json'):
  p=(O/name).resolve();assert p.is_file();selected.add(p)
 provenance=O/'build-review-ae-provenance';assert provenance.is_dir()
 selected.update(p.resolve() for p in provenance.iterdir() if p.is_file())
reservation=read(f'forest-holdout-{tag}-reservation.json')
assert len(reservation['seeds'])==10 and len(set(reservation['seeds']))==10
for seed in reservation['seeds']:
 root=O/f'forest-holdout-{tag}-seed{seed}'
 for name in ('report.json','g2r2.json','g3r2.json','g7r2.json'):
  p=(root/name).resolve();assert p.is_file(),p;selected.add(p)
for pattern in (f'review-build-{tag}-r*.*',f'run-review-build-{tag}-r*.py',f'run-*{tag}*.py',f'compile_world_ev112_{tag}.ps1','build-tools-preflight-*.json',f'forest-{tag}-*-regression-steps.json',f'pipeline-{tag}-package*.json',f'forest-holdout-{tag}*.log'):
 selected.update(p.resolve() for p in O.glob(pattern) if p.is_file())
for root in (attempt,O/f'forest-final-renders-{tag}',O/f'forest-r2-diagnostics-{tag}-painted',O/f'forest-final-negatives-{tag}',O/f'forest-map-51{tag}',O/f'surface-gates-{tag}-results',O/f'wrp-readback-{tag}'):
 assert root.is_dir(),root
 selected.update(p.resolve() for p in root.iterdir() if p.is_file() and p.suffix.lower() in ('.json','.log','.md','.png','.txt'))
surface_gates=O/'surface-gates-b';assert surface_gates.is_dir()
selected.update(p.resolve() for p in surface_gates.iterdir() if p.is_file() and p.suffix.lower()=='.py')
dest.mkdir(parents=True,exist_ok=False);rows=[]
for p in sorted(selected):
 assert p.is_file()
 h=sha(p);assert str(p) not in bound or bound[str(p)]==h
 size=p.stat().st_size;rel=None
 if p.is_relative_to(O) and size<=20*1024*1024:
  rel=p.relative_to(O);target=dest/rel;target.parent.mkdir(parents=True,exist_ok=True)
  assert not target.exists();shutil.copyfile(p,target);assert sha(target)==h
 rows.append(dict(source=str(p),sha256=h,bytes=size,archived_relative=str(rel) if rel else None))
manifest=dict(schema='ev112-final-evidence.v1',scope=__doc__,time=datetime.datetime.now().astimezone().isoformat(),forest_tag=tag,
 world_sha256=deploy['world_sha256'],water_sha256=deploy['water_sha256'],offline_status=deploy['offline_status'],
 independent_build_review=build['verdict'],server_probe=runtime['status'],personal_visual_acceptance='PENDING',
 protected_01545='60m disk PENDING, never PASS',files=rows)
(dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
runtime_relative=attempt.relative_to(O).as_posix()
runtime_rows='\n'.join(f"| {name} | {'PASS' if value else 'FAIL'} |" for name,value in runtime['checks'].items())
(dest/'README.md').write_text(f'''# EV112: evidencia final {tag.upper()}

Instantanea de los archivos reales; no modifica ni sustituye sus veredictos.
Offline: {deploy['offline_status']}. Revision independiente del build: {build['verdict']}.
Sonda del servidor: {runtime['status']}. Vista personal: preparada, pendiente de Guillermo.
015-45: disco protegido de60m pendiente, nunca PASS.

## Identidad de la entrega

| Artefacto | SHA256 |
|---|---|
| Mundo desplegado | `{deploy['world_sha256']}` |
| Agua desplegada | `{deploy['water_sha256']}` |
| Terreno | `{deploy['terrain_sha256']}` |
| Generador de bosque | `{closure['source_sha256']}` |
| Registros del bosque | `{deploy['forest_records_sha256']}` |

Paquete local: `{deploy['mod']}`. Los hashes se comprobaron sobre las copias desplegadas.
La cadena incluye kit, puentes, presa, orillas, calzadas, despike, bosque y superficie final.

## Pruebas

La evidencia offline está vinculada en [deploy.json](deploy.json) y en
[el cierre mecánico](forest-review-closure-{tag}.json). La revisión independiente del paquete
está en [build-review-closure-{tag}.json](build-review-closure-{tag}.json).
El bosque pasa 45 etapas conocidas, 50 etapas de semillas nuevas, partición de 250/500 m,
consumidores de superficie final y 6 positivos/25 negativos. Estos resultados no son una medición de FPS.

La [sonda estricta del servidor]({runtime_relative}/acceptance.json) conserva cada resultado:

| Comprobación | Resultado |
|---|---|
{runtime_rows}

La [ruta personal](personal-view-{tag}/README.md) queda preparada y vinculada al paquete.
La aceptación visual de Guillermo y los FPS siguen pendientes.

`manifest.json` registra SHA256, tamano y ruta original de cada fuente.
Las copias conservan bytes; los datos GIS/PBO grandes permanecen en E: y quedan fijados por hash.
Los paths absolutos dentro de recibos son los usados realmente; no se reescriben como si se hubieran ejecutado desde este archivo.
El cierre mecanico declara el delta desde S; la revision OT7 del build evalua el candidato final y su evidencia.
No interpretar densidades, renders offline o sonda como aceptacion visual ni medicion de FPS.
''',encoding='utf-8')
print(json.dumps(dict(archived=str(dest),files=len(rows),copied=sum(r['archived_relative'] is not None for r in rows),server_probe=runtime['status'])))
