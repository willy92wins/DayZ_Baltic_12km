"""Save the reviewed/tested607 consumer while its separate NM generation runs."""
from pathlib import Path
import gzip,hashlib,json,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav-consumer-20261026';O=R/'kit7-nav-postprocess-review-20261026'
E=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-navigation-consumer-preparation-20261026'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
accepted=read(O/'accepted.json');assert accepted['status']=='ACCEPTED_AFTER_REVIEW'
for p,h in accepted['inputs'].items():assert sha(Path(p))==h,p
assert not (D/'result.json').exists()
assert read(D/'synthetic-controls-v2/result.json')['native_acceptance'] is False
E.mkdir(parents=True,exist_ok=False)
def save(p,name):
    raw=p.read_bytes();target=E/(name+'.gz' if len(raw)>250000 else name);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(gzip.compress(raw,mtime=0) if len(raw)>250000 else raw)
for p in D.glob('*.json'):save(p,'preparation/'+p.name)
save(D/'queries.csv','mission/queries.csv')
save(Path(read(D/'frozen.json')['mission'])/'init.c','mission/init.c')
for folder in ['synthetic-controls','synthetic-controls-v2']:
    for p in (D/folder).glob('*.json'):save(p,folder+'/'+p.name)
for label,folder in [('plan-review','kit7-nav-consumer-plan-review-20261026'),('code-review','kit7-nav-postprocess-review-20261026'),('fix-review','kit7-nav-postprocess-fix-review-20261026')]:
    base=R/folder
    for p in base.glob('*.json'):
        if p.name!='review-response.json':save(p,label+'/'+p.name)
    for p in base.glob('*.md'):save(p,label+'/'+p.name)
    for p in (base/'reviewed-source').glob('*'):
        if p.is_file():save(p,label+'/reviewed-source/'+p.name)
    response=read(base/'review-response.json');assert not response['is_error'] and not response['permission_denials']
    (E/label/'fable-review.md').write_text(response['result']+'\n',encoding='utf-8')
    (E/label/'provenance.json').write_text(json.dumps(dict(response_sha256=sha(base/'review-response.json'),modelUsage=response['modelUsage'],is_error=False,permission_denials=[]),indent=2)+'\n')
for folder in ['kit7-nav-route-discovery-20261026','kit7-packed-nav-discovery-20261026']:
    for p in (R/folder).glob('*'):
        if p.suffix in ('.json','.npz'):save(p,'discovery/'+folder+'/'+p.name)
names=['discover_kit7_nav_routes.py','discover_kit7_packed_nav.py','screen_kit7_nav_corridors.py','screen_kit7_full_nav_corridors.py','freeze_kit7_nav_routes.py','prepare_kit7_nav_runtime.py','orchestrate_kit7_nav_probe.js','capture_kit7_nav_log.ps1','finish_kit7_nav_probe.py','prepare_kit7_nav_package.py','package_and_deploy_kit7_nav9.py','verify_c_orderly_close.py','test_kit7_nav_consumer.py','test_kit7_nav_consumer_v2.py','test_kit7_nav_probe_flow.cjs','test_kit7_nav_probe_flow_v2.cjs','test_kit7_nav_probe_command.cjs','test_kit7_nav_probe_command_v2.cjs','repair_kit7_nav_review.py','prepare_kit7_nav_consumer_plan_review.py','run_kit7_nav_consumer_plan_review.py','prepare_kit7_nav_code_review.py','run_kit7_nav_code_review.py','prepare_kit7_nav_fix_review.py','run_kit7_nav_postprocess_fix_review.py','orchestrate_nav_kit7_fifo_v4.js','test_nav_kit7_fifo_v4.cjs','prepare_nav_kit7_fifo.py','seal_nav_kit7_fifo.py','checkpoint_kit7_nav_consumer_preparation.py']
names.append('seal_kit7_nav_consumer.py')
for name in names:save(R/name,'source/'+name)
for name in ['fifo-user-request.json','coordinator-control-flow-fifo-v4.json']:save(R/'nav-kit7-preparation-20261026'/name,'fifo/'+name)
(E/'README.md').write_text('''# Kit7:607 consultas preparadas y revisadas

Este checkpoint guarda el nuevo consumidor, su misión y el contrato geométrico.
No contiene un PASS de navegación nativa: la NM propia está en generación.

45regresiones conservadas (solo dos Y actualizadas al cauce actual) y562rutas
locales fijadas antes de consultar el motor. Cubren139piezas,138juntas, extremos
naturales y transiciones al terreno por ambas orillas. Los corredores se han
contrastado con Roadway extraído del PBO y poses leídas del WRP compilado.
No invaden agua; las piezas contiguas permitidas se distinguen de las piezas
obligatorias. El consumidor comprueba la polilínea completa y recalcula el
corredor, su zona exterior y su cobertura con los binarios congelados.

11fixtures geométricos y19controles sintéticos del consumidor;11escenarios del
lifecycle y8del wrapper. ValidadorEnforce:1archivo,0errores,0avisos.
Plan y código revisados por Fable5.1 y correcciones verificadas. Los resultados
sintéticos solo prueban el verificador; nunca se usan como evidencia del juego.

El MCP concede el turno mediante FIFO nativo de dayz_test_run, sin sondeo previo
del banco ni takeover. La automatización periódica anterior quedó pausada.
Tras terminar generación, inspección y empaquetado exclusivo deNM, se ejecutará
la sonda en un servidor normal propio y se registrará su cierre oficial.

Quedan pendientes el grafo nativo607, locomoción, revisión visual, rendimiento
del paquete actual y los defectos globales del mapa. Los binarios grandes no se
publican en este repositorio; se conservan identidades y evidencia reproducible.
''',encoding='utf-8')
p=W/'HANDOFF.md';text=p.read_text(encoding='utf-8')
for key,value in {
'updated':'2026-10-26 (consumidor607 revisado SOUND y preparado; generación kit7 activa por FIFO nativo)',
'plan':'Física kit7PASS6801/6801. Consumidor607 preparado con11fixtures,19controles sintéticos,11flujos y8controles de comando; FableSOUND. Ver plans/ev112-kit7-navigation-consumer-20261026.md. Sin aceptación nativa del grafo todavía.',
'handoff':E.relative_to(W).as_posix()+'/README.md; estado activo en E:/DayZ-Baltic-Build/shape-repair-20261025/ACTIVE-WORK.md. Esperarcell229 antes de empaquetar y lanzar la sonda607.'
}.items():text,n=re.subn('^'+key+':.*$',lambda m:key+': '+value,text,count=1,flags=re.M);assert n==1
p.write_text(text,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='PREPARED_CONSUMER_NOT_NATIVE_CHECKPOINT',files=len(manifest),bytes=sum(v['bytes'] for v in manifest.values()))))
