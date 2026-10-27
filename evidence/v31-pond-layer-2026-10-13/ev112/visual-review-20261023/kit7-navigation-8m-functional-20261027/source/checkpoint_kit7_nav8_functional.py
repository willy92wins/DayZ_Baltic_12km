"""Publishable functional proof only after full native607 PASS; RAM stays separate."""
from pathlib import Path
import gzip,hashlib,json,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav8-consumer-20261027';G=R/'nav-kit7-8m-preparation-20261027';N=R/'navmesh-kit7-8m-v9-20261027';P=R/'package-kit7-nav8-v9-20261027'
E=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-navigation-8m-functional-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not E.exists()
result=read(D/'result.json');identity=read(D/'identity-verification.json');clean=read(D/'cleanup.json')
assert result['status']=='PASS_KIT7_NATIVE_GRAPH' and len(result['cases'])==607 and not result['local_failures'] and not result['height_issues']
assert identity['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS'
assert clean['close']['run_retired'] and clean['self']['state']=='none' and not clean['own_run_present'] and not clean['cleanup_error'] and not clean['error'] and not clean['cleanup_degraded'] and clean['pending_commands']==0
assert read(G/'completion.json')['status']=='GENERATION_STAGE_COMPLETE_PENDING_VALIDATION'
inspection=read(N/'inspection.json');assert inspection['status']=='EMPIRICAL_V9_PREFIX_AND_COVERAGE_PASS'
package=read(P/'verification.json');assert package['status']=='PASS_NAVMESH_PACKED_BYTE_PARITY' and package['original_entries_unchanged']==6826
deployment=read(D/'deployment.json')
for p,h in {**deployment['inputs'],**deployment['packages']}.items():assert sha(p)==h,p
assert read(D/'contract-parity.json')['status']=='PASS_SAME607_CONTRACT_FRESH_ID'
assert (D/'queries.csv').read_bytes()==(R/'kit7-nav-consumer-20261026/queries.csv').read_bytes()
E.mkdir(parents=True,exist_ok=False)
def save(p,name):
 raw=p.read_bytes();dest=E/(name+'.gz' if len(raw)>250000 else name);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_bytes(gzip.compress(raw,mtime=0) if len(raw)>250000 else raw)
allowed={'.json','.jsonl','.log','.md','.py','.js','.cjs','.ps1','.cpp','.c','.csv','.txt'}
for label,base in [('runtime',D),('generation',G),('ram-preparation',R/'kit7-nav8-ram-ab-20261027')]:
 for p in base.rglob('*'):
  relative=p.relative_to(base)
  if label=='ram-preparation' and len(relative.parts)>1:continue
  if label=='generation' and (p.name.startswith(('launch-attempt-','handoff-before-')) or p.name=='request-preflight.json'):continue
  if p.is_file() and p.suffix.lower() in allowed and p.name not in ('server.RPT','handoff-before-functional-checkpoint.md'):
   save(p,label+'/'+p.relative_to(base).as_posix())
for name in ('generation.json','inspection.json'):save(N/name,'generation/native/'+name)
for name in ('verification.json','deployment.json'):save(P/name,'package/'+name)
for name in ('verification.json','config.cpp','roundtrip.cpp'):save(R/'package-kit7-nav8-input-20261027'/name,'config-input/'+name)
reviews=['kit7-nav8-postprocess-review-20261027','kit7-nav8-ram-review-20261027','kit7-nav8-recovery-ram-fixes-review-20261027','kit7-nav8-recovered-postprocess-review-20261027']
for folder in reviews:
 base=R/folder
 for p in base.rglob('*'):
  if p.is_file() and p.suffix.lower() in allowed and p.name!='response.json':save(p,'reviews/'+folder+'/'+p.relative_to(base).as_posix())
 response=read(base/'response.json');assert not response['is_error'] and not response['permission_denials']
 dest=E/'reviews'/folder;dest.mkdir(exist_ok=True,parents=True)
 (dest/'fable-review.md').write_text(response['result']+'\n',encoding='utf-8')
 (dest/'provenance.json').write_text(json.dumps(dict(response_sha256=sha(base/'response.json'),modelUsage=response['modelUsage'],is_error=False,permission_denials=[]),indent=2)+'\n',encoding='utf-8')
sources=['orchestrate_kit7_nav8_probe.js','finish_kit7_nav8_probe.py','prepare_kit7_nav8_runtime.py','package_and_deploy_kit7_nav8.py','package_and_deploy_kit7_nav8_recovered.py','verify_c_orderly_close.py','verify_nav8_recovered_exit.py','resume_kit7_nav8_generation.js','prepare_nav8_recovery.py','prepare_nav8_recovered_postprocess.py','test_nav8_recovered_exit.py','finish_nav8_recovery_review.py','nav8-recovery-addendum.md','prepare_nav8_ram_pass.py','orchestrate_nav8_ram.js','finish_nav8_ram_pass.py','finalize_nav8_ram_ab.py','test_nav8_ram_conditions.py','test_nav8_ram_flow.cjs','fix_nav8_ram_review.py','seal_nav8_ram_preparation.py','test_kit7_nav8_consumer.py','test_kit7_nav8_probe_flow.cjs','test_kit7_nav8_probe_command.cjs','capture_owned_server_identity.ps1','copy_owned_server_rpt.ps1','record_nav_c_event.ps1','capture_kit7_nav_log.ps1',Path(__file__).name]
for name in sources:save(R/name,'source/'+name)
save(R/'kit7-nav8-recovered-exit-controls.json','recovery-controls.json');save(R/'kit7-nav8-recovered-exit-controls-before-review.json','recovery-controls-before-review.json')
mission=Path(read(D/'frozen.json')['mission'])
for name in ('init.c','queries.csv'):save(mission/name,'mission/'+name)
for label,base in [('generation',G),('runtime',D)]:
 rpt=base/'server.RPT';count=0;warnings=0;unknown_pond=0;termination=[];errors=[]
 with rpt.open(encoding='utf-8',errors='replace') as f:
  for line in f:
   count+=1;low=line.lower();warnings+=int('(w)' in low or 'warning' in low);unknown_pond+=int("unknown object class 'pond'" in low)
   if 'termination successfully completed' in low:termination.append(line.rstrip())
   if any(x in low for x in ('error','exception',"can't compile")) and len(errors)<1000:errors.append(line.rstrip())
 (E/label/'rpt-summary.json').write_text(json.dumps(dict(sha256=sha(rpt),line_count=count,warning_lines=warnings,unknown_pond_lines=unknown_pond,termination_lines=termination,first_error_or_exception_lines=errors,selection_limit=1000,full_rpt_retained_locally=True),indent=2)+'\n',encoding='utf-8')
gen=read(N/'generation.json')
(E/'README.md').write_text(f'''# Kit7: las cuatro alturas corregidas y 607 consultas nativas verificadas

El cambio funcional reduce GenParams.tileWidth de 12.5 a 8 m. La referencia,
coordenadas, filtros y tolerancias siguen idénticos: altura 0.801 m,
terreno 0.011 m y corredor 2.1 m. El resultado nativo es PASS_KIT7_NATIVE_GRAPH:
607 consultas, cero height_issues y cero local_failures. El FAIL anterior y
sus cuatro casos se conservan en kit7-navigation-runtime-20261026.

Generación propia `{gen['run_id']}`, terminada `{gen['finished_utc']}`.
TESMv9/VAND12 inspeccionado: {inspection['tiles']} teselas y
{inspection['bytes']} bytes. La malla se empaqueta preservando6826 entradas
restantes, WRP, piloto y agua. La configuración de 8 m y su receta se archivan aquí;
los grandes binarios y los paquetes vanilla permanecen fuera de Git.

La generación recuperó un lease caducado sin reiniciar ni cancelar su proceso.
Se conservan el intento de cancelación no ejecutado, sus recibos de error y
la recaptura del mismo PID/creación/comando. El adaptador revisado clasifica
solo ese evento, conserva el registro original y exige finalización con código 0
y los controles originales de cierre, observador y RPT. Se mantuvieron el tiempo
y las tolerancias. Los registros de cola con sesiones ajenas se conservan localmente.

Esto valida el grafo y sus alturas en las 607 rutas, no locomoción de actores,
barcos, visual humana, FPS o aceptación global. La RAM de este paquete8m
todavía debe medirse frente a Chernarus con 6 pasadas nuevas ABBAAB, 30+120 s,
presupuesto 1.10 y dispersión 5 %. La preparación sellada y los controles sintéticos
incluidos no son mediciones nativas ni heredan el benchmark anterior.

Siguen pendientes los otros sectores y el censo global; el piloto híbrido de
14 vértices continúa sin integrar. Se conservan todas las protecciones aprobadas.
''',encoding='utf-8')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8');(D/'handoff-before-functional-checkpoint.md').write_text(s,encoding='utf-8')
updates={'updated':gen['finished_utc'][:10]+' (kit7: cuatro alturas nativas corregidas con8m,607PASS; RAM8m/visual/global pendientes)',
'plan':'Kit7 grafo/altura funcionalPASS conGenParams.tileWidth8m y límites intactos. Medir RAM propia8m según plans/ev112-kit7-nav-height-refinement-20261027.md antes de declarar optimización.',
'next':'Ejecutar6pasadas nuevasRAM8m vsChernarus ABBAAB,30+120s,1.10/5%; preparación sellada. Luego revisión visual/locomoción conjunta y otros sectores, sin heredarPASS global.',
'cleanup':'Generación y sonda607 propias cerradas oficialmente, sin cliente; selfnone/pending0/cleanup[]. Recuperación de lease documentada sin reinicio. Automatización anteriorPAUSED; nuevos lanzamientosporFIFO.',
'handoff':E.relative_to(W).as_posix()+'/README.md; resultado funcional real, recuperación y preparaciónRAM separados.',
'deployed':'P:/Mods/@DayZ_Baltic_EV112_Kit7Nav8: mundo'+package['pbo_sha256']+', piloto3d9550bf, agua97edcafe. Copias anteriores conservadas. Grafo607PASS; RAM8m/visual aún pendientes.'}
for k,v in updates.items():s,n=re.subn('^'+k+':.*$',lambda m:k+': '+v,s,count=1,flags=re.M);assert n==1
p.write_text(s,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(status='KIT7_NAV8_FUNCTIONAL_CHECKPOINT',files=len(manifest),bytes=sum(v['bytes'] for v in manifest.values()))))
