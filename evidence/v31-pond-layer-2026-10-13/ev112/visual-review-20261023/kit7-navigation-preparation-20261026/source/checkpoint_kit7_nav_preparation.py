from pathlib import Path
import gzip,hashlib,json,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'nav-kit7-preparation-20261026';E=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-navigation-preparation-20261026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
q=read(D/'ready-summary.json');assert q['physical_failures']==0 and q['generation_attempts']==0
assert q['launch_inputs_sha256']==sha(D/'launch-inputs.json')
assert all(sha(Path(p))==h for p,h in read(D/'launch-inputs.json')['inputs'].items())
assert not (R/'navmesh-kit7-v9-20261026').exists()
E.mkdir(parents=True,exist_ok=False)
def save(p,n):
 raw=p.read_bytes();out=E/(n+'.gz' if len(raw)>250000 else n);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(gzip.compress(raw,mtime=0) if len(raw)>250000 else raw)
for p in D.glob('*.json'):save(p,p.name)
for folder,label in [('kit7-nav-coordinator-review-20261026','initial-review'),('kit7-nav-coordinator-fix-review-20261026','fix-review')]:
 v=R/folder
 for n in ['completion.json','source-hashes.json','review-brief.md']:save(v/n,label+'/'+n)
 rv=read(v/'review-response.json');assert not rv['is_error'] and not rv['permission_denials']
 (E/label/'fable-review.md').write_text(rv['result']+'\n',encoding='utf-8')
 (E/label/'provenance.json').write_text(json.dumps(dict(response_sha256=sha(v/'review-response.json'),modelUsage=rv['modelUsage'],is_error=False,permission_denials=[]),indent=2)+'\n')
names=['orchestrate_nav_kit7.js','orchestrate_nav_kit7_v2.js','orchestrate_nav_kit7_v3.js','prepare_kit7_nav_draft.py','adapt_nav_kit7_contact_only.py','repair_nav_kit7_review.py','repair_nav_kit7_manifest_read.py','seal_nav_kit7_ready.py','accept_nav_kit7_bounded_read.py','checkpoint_kit7_nav_preparation.py','capture_nav_c_generator.ps1','cancel_owned_nav_c_generator.ps1','bind_nav_c_rpt_clock.ps1','record_nav_c_event.ps1']
names+=['test_nav_kit7_'+kind+suffix+'.cjs' for kind,suffix in [('coordinator',''),('command',''),('coordinator','_v2'),('command','_v2'),('lease','_v2'),('host_binding','_v2'),('coordinator','_v3'),('command','_v3'),('lease','_v3')]]
for n in names:save(R/n,'source/'+n)
for p in (D/'host-check-tests').glob('*/check.ps1'):save(p,'host-checks/'+p.parent.name+'/'+p.name)
for p in (D/'host-check-tests').glob('*/output.log'):save(p,'host-checks/'+p.parent.name+'/'+p.name)
save(Path('C:/temp/DayZ_MCP_130_dev/mpmissions/BalticKit7NavData.BalticTrial/init.c'),'mission/init.c')
(E/'README.md').write_text("""# Kit7 — navegación preparada, sin generación

La puerta física ya pasa6801puntos con cero fallos. Este checkpoint prepara
la generación propia del kit7; **no contiene una navmesh nueva ni un PASS de IA**.
El banco compartido mantenía la reserva de otra prueba H2R al guardar el estado.

El coordinador conserva la generación observada de C y fija exactamente el
nuevo mundo,piloto,agua,bridge y motor. Fable5.1 encontró cinco defectos; todos
se corrigieron y la segunda revisión dioSOUND. El cambio posteriorv3 proyecta
solo tres campos del manifiesto al runtime JS para evitar truncar la salida;
la verificación completa de hashes sigue ejecutándose sobre el archivo.
El único fallo de preparación ocurrió antes de cualquier llamada de lanzamiento.
Cero intentos de generación consumidos.

Pruebas:17escenarios de flujo y3mutaciones,2casos de lease,8casos del wrapper,
7ejecuciones reales del PowerShell de identidad(incluidos6rechazos), métodos
JS comprobados en Functions y lectura real del manifiesto de714caracteres.
Los controles simulados no sustituyen un servidor ni una generación nativa.

Siguiente: consultar session_status y solo con banco libre ejecutar
orchestrate_nav_kit7_v3.js mediante Functions; mantiene heartbeat,captura del
generador y cierre oficial propio. Presupuesto7200s,observador7500s,un intento.
Después inspeccionar TESMv9, empaquetar exclusivamenteNM y probar45regresiones
más rutas específicas del kit7 que demuestren atravesar la superficie nueva.
La vista humana y locomoción real siguen separadas.
""",encoding='utf-8')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8');(D/'handoff-before-preparation-checkpoint.md').write_text(s,encoding='utf-8')
updates={'updated':'2026-10-26 (kit7 física6801/0fallos publicada; navegación preparada y revisada, sin generación)','plan':'Física kit7PASS6801. Coordinador navv3 listo, FableSOUND en lógica v2, lectura acotadav3 probada. Ver plans/ev112-kit7-navmesh-generation-20261026.md.','next':'Cuando banco y lease ajenos queden libres: ejecutar R/orchestrate_nav_kit7_v3.js, inputs en nav-kit7-preparation-20261026/launch-inputs.json;1intento7200s. Después estructura/NM/sonda propia.','cleanup':'Calibración3eedb524 y físicaa91c4a81 cerradas oficialmente; selfnone,pending0,cleanup[]. Sincliente. ReservaH2R ajena al preparar nav; no cerrar ni adoptar.','handoff':E.relative_to(W).as_posix()+'/README.md; resultado físico en kit7-contact-repair-20261026; públicoe9f213a verificado.'}
for k,v in updates.items():s,n=re.subn('^'+k+':.*$',lambda m:k+': '+v,s,count=1,flags=re.M);assert n==1
p.write_text(s,encoding='utf-8')
m={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()};(E/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps(dict(status='READY_NOT_GENERATED_CHECKPOINT',files=len(m),bytes=sum(v['bytes'] for v in m.values()))))

