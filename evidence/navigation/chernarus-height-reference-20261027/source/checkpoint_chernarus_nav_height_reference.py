from pathlib import Path
import gzip,hashlib,json,re
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'chernarus-nav-height-reference-20261027'
E=W/'evidence/navigation/chernarus-height-reference-20261027'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def write(name,value):(E/name).write_text(json.dumps(value,indent=2)+'\n')
assert not E.exists()
result=read(D/'result.json');assert result['acceptance_eligible'] is False
identity=read(D/'identity-verification.json');assert identity['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS'
cleanup=read(D/'cleanup.json');assert cleanup['close']['run_retired'] and cleanup['self']['state']=='none' and not any(cleanup[k] for k in ('own_run_present','pending_commands','cleanup_degraded','error','cleanup_error'))
for p,h in read(D/'frozen.json')['inputs'].items():assert sha(p)==h,p
E.mkdir(parents=True)
def save(p,name):
 raw=p.read_bytes();compressed=len(raw)>250000
 dest=E/(name+'.gz' if compressed else name);dest.parent.mkdir(parents=True,exist_ok=True)
 dest.write_bytes(gzip.compress(raw,mtime=0) if compressed else raw)
for p in D.rglob('*'):
 if p.is_file() and p.suffix.lower() in ('.json','.jsonl','.log','.csv','.js'):
  save(p,p.relative_to(D).as_posix())
mission=Path(read(D/'frozen.json')['mission'])
save(mission/'init.c','mission/init.c');save(mission/'anchors.csv','mission/anchors.csv')
for prefix in ('plan','code'):
 base=R/f'chernarus-nav-height-{prefix}-review-20261027'
 for name in ('fable-review.md','adjudication.md','source-hashes.json','completion.json','adjudication.json','accepted.json'):
  if (base/name).exists():save(base/name,'reviews/'+prefix+'/'+name)
for name in ('prepare_chernarus_nav_height_runtime.py','orchestrate_chernarus_nav_height_probe.js','finish_chernarus_nav_height_probe.py','capture_chernarus_nav_height_log.ps1','test_chernarus_nav_height_probe_flow.cjs','test_chernarus_nav_height_probe_command.cjs','review_chernarus_nav_height_code.py','seal_chernarus_nav_height_probe.py','select_chernarus_nav_height_anchors.py','check_chernarus_nav_anchor_extents.py','inspect_current_chernarus_nav_detail.py','inspect_current_chernarus_world_config.py','verify_c_orderly_close.py','capture_owned_server_identity.ps1','copy_owned_server_rpt.ps1','record_nav_c_event.ps1'):
 save(R/name,'source/'+name)
save(Path(__file__),'source/'+Path(__file__).name)
for name in ('chernarus-current-nav-detail-20261027','chernarus-current-config-20261027'):
 save(R/name/'result.json','diagnostics/'+name+'.json')
rpt=D/'server.RPT';lines=rpt.read_text(encoding='utf-8',errors='replace').splitlines()
write('rpt-summary.json',dict(sha256=sha(rpt),line_count=len(lines),termination_lines=[x for x in lines if 'Termination successfully completed' in x],error_or_exception_lines=sum(any(v in x.lower() for v in ('error','exception',"can't compile")) for x in lines),full_rpt_retained_locally=True))
detail=f"{result.get('comparable_routes',0)}/48 rutas comparables; {result.get('height_exceedances',0)} puntos superan0,801 m; máximo {result.get('max_height_error_m')} m."
(E/'README.md').write_text(f'''# Referencia nativa de altura: arroyos de Chernarus

**{result['status']}**. {detail}

Un único run de servidor, 24 piezas elegidas antes de conocer resultados,
48 rutas y control NONE. Selección sin sustituciones. Capturas completas y
rutas no comparables conservadas. Tolerancias 0,801 / 0,011 / 2,1 m intactas.
Ejecutable, 118 paquetes stock, bridge, misión y anclas fijados por hash.
Cierre oficial observado y lease liberado. No cliente ni actores añadidos.

Es un diagnóstico del mismo observable, no una aceptación de Baltic. Los
extremos usan SurfaceRoadY actual+.2, distinto del max(roof,ground)+.2 offline
de Baltic. Los datos no prueban comportamiento de actores ni una causa única.
Una desviación vanilla no borra fallos de Baltic ni autoriza bajar tolerancias.

Nav8 conserva607 PASS de altura con máximo0,711963 m, pero falla RAM con ratios
1,265913/1,241333. Nav12 conserva tres alturas FAIL y no tiene medida RAM.
El original12,5 pasa RAM0,832329/0,844646 y conserva los cuatro fallos de altura.
No hay todavía una variante que reúna aceptación funcional y de memoria.

Revisión independiente Fable5.1 conciliada; 18 controles del lector,
13 escenarios de coordinación con dos mutantes y ocho de comandos pasan.
El validador estático revisó una misión sin errores ni avisos. El log nativo
y el resultado indican por separado la cobertura real de esta ejecución.
''',encoding='utf-8')
path=W/'HANDOFF.md';old=path.read_text(encoding='utf-8');new=old
updates={'updated':'2026-10-27 (Nav8 altura PASS publicado; RAM pendiente; contraste Chernarus nativo completado)', 'plan':'plans/ev112-kit7-chernarus-height-reference-20261027.md. Diagnóstico completado; no cambia aceptación Baltic ni autoriza otra generación a ciegas.', 'next':'Resolver el compromiso de memoria sin perder607PASS de Nav8. Evidencia Chernarus: '+result['status']+'. '+detail+' No rebajar0.801/0.011/2.1 ni usar el resultado vanilla como exención.', 'handoff':E.relative_to(W).as_posix()+'/README.md; Nav8 funcional, RAMFAIL y Nav12FAIL preservados.', 'cleanup':'Run propio de referencia Chernarus cerrado oficialmente, salida observada y lease liberado. Los seis RAM12,5 y Nav8/Nav12 también cerrados. Automatización anterior PAUSED.'}
for key,value in updates.items():new,count=re.subn('^'+key+':.*$',lambda _:key+': '+value,new,count=1,flags=re.M);assert count==1,key
assert path.read_text(encoding='utf-8')==old;path.write_text(new,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
write('MANIFEST.json',manifest)
print(json.dumps(dict(status='REFERENCE_CHECKPOINTED',result=result['status'],files=len(manifest))))
