from pathlib import Path
import hashlib,json,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');D=R/'kit7-nav8load1-consumer-20261027';V=R/'kit7-nav8load1-code-review-20261027';F=R/'kit7-nav8load1-recovery-review-20261027';E=W/'evidence/navigation/kit7-nav8load1-native-20261027'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,name):
 target=E/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
assert not E.exists()
joint=read(D/'joint-result.json');assert joint['status']=='PASS_LOAD1_CONFIG_AND_NATIVE607'
assert read(D/'config-recovery.json')['native_runs_added']==0
clean=read(D/'cleanup.json');assert clean['close']['run_retired'] and clean['self']['state']=='none' and not clean['own_run_present'] and not clean['pending_commands'] and not clean['cleanup_error']
E.mkdir(parents=True)
for name in ['config-result.json','joint-result.json','config-recovery.json','result.json','identity-verification.json','host-identity.json','mcp-identity.json','cleanup.json','timeline.jsonl','log-binding.json','rpt-binding.json','rpt-config-observations.json','script-config-observations.json','runtime.log','config-runtime.log','queries.csv','reference.json','frozen.json','deployment.json','deployment-parity.json','contract-parity.json','runtime-preparation.json','vanilla-packages.json','script-validator.json','capture-controls.json','capture-parse.log','coordinator-controls.json','command-flow-controls.json','isolated-wrapper-controls.json','consumer-controls.stderr.log','config-consumer.stderr.log','config-consumer-recovery.stderr.log']:
 save(D/name,name)
for name in ['attached.json','terminal.json']:save(D/'observer'/name,'observer/'+name)
for name in ['fable-review.md','adjudication.md','adjudication.json','completion.json','source-hashes.json','rejected-capture.ps1','rejected-capture-test.ps1','reviewed-seal.py']:save(V/name,'review/'+name)
for name in ['adjudication.json','completion.json','source-hashes.json']:save(F/name,'recovery-review/'+name)
for p in F.glob('*.diff'):save(p,'recovery-review/'+p.name)
(E/'recovery-review/fable-review.md').write_text(read(F/'response.json')['result'],encoding='utf-8')
for name in ['prepare_kit7_nav8load1_runtime.py','orchestrate_kit7_nav8load1_probe.js','capture_kit7_nav8load1_logs.ps1','finish_kit7_nav8load1_probe.py','seal_kit7_nav8load1_probe.py','test_kit7_nav8load1_probe_flow.cjs','test_kit7_nav8load1_probe_command.cjs','test_capture_nav8load1_logs_v2.ps1','recover_kit7_nav8load1_config_consumer.py','test_nav8load1_isolated_wrapper.py','adjudicate_nav8load1_recovery_and_ram.py']:
 save(R/name,'source/'+name)
for name in ['verify_nav8_load1_config_ev112.py','test_nav8_load1_config_ev112.py']:save(W/'tools/navigation'/name,'source/'+name)
save(W/'missions/BalticKit7Nav8Load1.BalticTrial/init.c','source/mission-init.c')
save(W/'plans/ev112-kit7-onload-numeric-pilot-20261027.md','source/reviewed-plan.md')
save(Path(__file__),'source/'+Path(__file__).name)
(E/'README.md').write_text('''# Nav8Load1: configuración nativa y navegación verificadas

**PASS local: configuración esperada y las 607 consultas de navegación. RAM pendiente.**
El servidor cargó el paquete f0e0e6b9… en una única ejecución
f6f09de4-8fe7-4947-a695-c284dc042919. El flag OnLoad presenta tipo entero0,
texto1 e int/float1; GenParams permanece texto true con conversión0.
El resto de los nueve controles pasa. No se conoce la implementación interna
del cargador y estos getters no demuestran por sí solos el efecto en memoria.

607 consultas PASS, sin fallos de altura ni continuidad. Se mantienen 0,801m,
0,011m y 2,1m. El despliegue conserva las 6826 entradas distintas de config.bin,
el NM y el WRP. No se regenera navegación. Identidad de proceso, cuatro paquetes,
118 paquetes vanilla, observador de salida, cierre oficial y liberación verificados.

La revisión detectó un capturador PowerShell inválido antes de lanzar; quedó
corregido y probado con siete controles reales. Se conservan el rechazo y la
corrección. Tras capturar, la invocación aislada de Python no encontró un módulo
hermano del lector de configuración. La recuperación revisada añadió la ruta de
importación explícita, ejecutó el mismo lector sin modificarlo y reprocesó el mismo
registro. Tres controles de CLI aislada validan positivo, flag antiguo y UUID
incorrecto. El error original permanece; no hubo otra partida ni otro muestreo.
El lector publicado debe invocarse con el bootstrap documentado en el script de
recuperación mientras se conserva esta cadena congelada.

Esto permite preparar un único bloque nuevo ABBAAB frente a Chernarus, con seis
mediciones y los límites originales. No hay todavía resultado RAM del candidato,
ni aceptación global, cliente/FPS, actores, barcos o revisión visual. Nav8 original
conserva su FAIL RAM. La ampliación del council sigue detrás del trabajo vigente.
''',encoding='utf-8')
p=W/'HANDOFF.md';old=p.read_text(encoding='utf-8');new=old
updates={'updated':'2026-10-27 (Nav8Load1: config nativa y607PASS; RAM pendiente)','plan':'plans/ev112-kit7-onload-numeric-pilot-20261027.md. Paquete aislado f0e0e6b9…, OnLoad entero1, NM idéntico. Config+607PASS en run único; falta bloque RAM nuevo.','next':'Seguir ACTIVE-WORK.md externo. Preparar o seguir únicamente el bloque RAM Nav8Load1 ABBAAB revisado; no duplicar ejecuciones. RAM1.10 y dispersión5% intactos. Council aún en cola.','cleanup':'Runf6f09de4-8fe7-4947-a695-c284dc042919 cerrado oficialmente, observador válido, lease liberado, selfnone,0pending. Captura consumida; no relanzar sonda.','handoff':E.relative_to(W).as_posix()+'/README.md. Recuperación offline del lector conservando registros y fuentes originales; ninguna nueva partida.'}
for key,value in updates.items():new,count=re.subn('^'+key+':.*$',lambda _:key+': '+value,new,count=1,flags=re.M);assert count==1,key
assert p.read_text(encoding='utf-8')==old;p.write_text(new,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(dict(status='LOAD1_NATIVE_CHECKPOINTED',files=len(manifest))))
