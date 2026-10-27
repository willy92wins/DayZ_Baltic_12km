from pathlib import Path
import hashlib,json,re
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-native-config-types-20261027';V=R/'kit7-config-types-code-review-20261027';P=R/'kit7-onload-numeric-plan-review-20261027-v2'
E=W/'evidence/navigation/kit7-native-config-types-20261027'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,name):
 dest=E/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
assert not E.exists()
result=read(D/'result.json');identity=read(D/'identity-verification.json');cleanup=read(D/'cleanup.json')
assert result['status']=='OBSERVED_SCRIPT_NUMERIC_CONVERSION_DIFFERENCE' and result['controls']=='PASS' and not result['acceptance_eligible']
assert identity['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS' and identity['inputs_unchanged']
assert cleanup['close']['run_retired'] and cleanup['close']['graceful'] and cleanup['self']['state']=='none' and not cleanup['own_run_present'] and not cleanup['error'] and not cleanup['cleanup_error']
assert read(P/'adjudication.json')['status']=='ACCEPTED_AFTER_REVIEW'
for path,digest in read(D/'frozen.json')['inputs'].items():assert sha(path)==digest,path
E.mkdir(parents=True)
for name in ('result.json','runtime.log','identity-verification.json','cleanup.json','timeline.jsonl','log-binding.json','rpt-binding.json','rpt-config-observations.json','script-config-observations.json','script-validator.json','coordinator-controls.json','command-flow-controls.json','consumer-controls.stderr.log','runtime-preparation.json','frozen.json','deployment.json','vanilla-packages.json'):
 save(D/name,name)
for name in ('attached.json','terminal.json'):save(D/'observer'/name,'observer/'+name)
host=read(D/'host-identity.json');summary={k:host[k] for k in ('run_id','pid','created_utc','executable_file_sha256','mission_path','mission_sha256','navmesh_data_server','package_hashes')}
(E/'host-identity-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
for name in ('prepare_kit7_config_types_runtime.py','seal_kit7_config_types_probe.py','orchestrate_kit7_config_types_probe.js','capture_kit7_config_types_log.ps1','finish_kit7_config_types_probe.py','test_kit7_config_types_probe_flow.cjs','test_kit7_config_types_probe_command.cjs','review_kit7_config_types_code.py','review_kit7_onload_numeric_plan_v2.py'):
 save(R/name,'source/'+name)
for name in ('plans/ev112-kit7-native-config-types-20261027.md','missions/BalticNavConfigTypes.BalticTrial/init.c','tools/navigation/verify_nav_config_types_ev112.py','tools/navigation/test_nav_config_types_ev112.py'):
 save(W/name,'source/'+name)
for folder,prefix in ((V,'operation'),(P,'next-pilot')):
 for name in ('fable-review.md','adjudication.md','adjudication.json','source-hashes.json','completion.json'):save(folder/name,'reviews/'+prefix+'/'+name)
save(R/'kit7-onload-numeric-plan-review-20261027/preparation-failure.json','reviews/next-pilot-preparation-failure.json')
save(Path(__file__),'source/'+Path(__file__).name)
(E/'README.md').write_text('''# Lectura nativa de los flags de navegación

**Diferencia confirmada en getters script; causa del consumo RAM todavía sin
probar.** Run2e1e9c77-222e-438c-955e-55b2f0ec0371, Nav8 intacto, nueve campos
capturados con identidad/UUID y controles válidos. Sin cambio de PBO, NM,
terreno, geometría ni tolerancias. No es un benchmark ni una repetición607.

|Campo|Baltic|Chernarus|
|---|---|---|
|filterIsolatedIslandsOnLoad|texto"true", int/float0|número1, int/float1|
|GenParams.filterIsolatedIslands|texto"true", int/float0|número1, int/float1|
|tileWidth|8|50|

Los textos"12:00" y"Chernarus" se recuperan correctamente y ambos dan0 por
getters numéricos; el campo inventado no existe. No se supone la semántica
nativa del cargador ni conversión por prefijo. El lector pasa15controles
positivos/negativos; misión1archivoPASS; lifecycle13casos+2mutantes y8controles
de finalización de comandoPASS. Revisión independiente Fable5.1 integrada.

RPT completo184líneas conservado en el build privado: cero coincidencias del
patrón de conversión/Navmesh. Script log44líneas vinculado por UUID: cuatro
avisos de zonas ausentes antes de los marcadores, ninguno entreBEGIN/END.
Se publican resúmenes con hashes/índices, sin los logs completos. Ausencia de
coincidencias no demuestra ausencia universal de avisos ni filtrado correcto.

El único run se cerró oficialmente, observador registró salida-1 después de
CLOSE_INTENT, válida bajo el contrato revisado; lease liberado, sin run propio
ni comandos pendientes.118paquetesvanilla y4PBOde mods ligados antes/después.

Siguiente plan revisado: variante experimental que cambia únicamente OnLoad
a número1 sobre el mismo NM. Exige otra prueba607 y RAMNUEVAcontraChernarus;
no cambia GenParams ni regenera. Su cobertura seguirá siendo local hasta
ampliar testigos. El plan y la revisión explican esa limitación.

Nav8 mantiene607PASS y RAMFAIL1,265913/1,241333. No se ha obtenido aún una
variante que cierre ambos gates. Council ampliado sigue en cola detrás del
trabajo vigente. Esta evidencia se publica sin declarar cierre de EV112.
''',encoding='utf-8')
p=W/'plans/ev112-kit7-native-config-types-20261027.md';old=p.read_text(encoding='utf-8')
old=old.replace('Estado: PLAN_REVISADO_SOUND_WITH_FIXES; ajustes conciliados por Codex tras\nrevisión independiente Fable5.1. Implementación y prueba nativa pendientes.','Estado: EJECUTADO_DIAGNOSTICO_VALIDO. Implementación revisada Fable5.1 y\nprueba nativa completa; ambos flags Baltic dan int/float0, controlesPASS.\nVer evidence/navigation/kit7-native-config-types-20261027. No cierre de RAM.')
p.write_text(old,encoding='utf-8')
p=W/'HANDOFF.md';old=p.read_text(encoding='utf-8');new=old
updates={'updated':'2026-10-27 (Nav8 funcional/RAM abierto; conversión nativa de flags observada; siguiente piloto revisado)','plan':'plans/ev112-kit7-onload-numeric-pilot-20261027.md. Cambio experimental únicamente OnLoad texto true -> número1, mismo NM. Plan revisado; implementación y nueva aceptación pendientes.','next':'Implementar y revisar piloto Nav8Load1; preservar bytes NM/WRP/auxiliares. Confirmar flag en motor y607; solo entonces bloque RAM nuevo contra Chernarus. Sin causalidad ni aceptación global anticipada.','cleanup':'Run2e1e9c77-222e-438c-955e-55b2f0ec0371 cerrado oficialmente, observador y lease liberado, selfnone,0pending. No relanzar sonda config consumida.','handoff':E.relative_to(W).as_posix()+'/README.md; Nav8/Nav12/original12,5 y diagnóstico Chernarus preservados.'}
for key,value in updates.items():new,count=re.subn('^'+key+':.*$',lambda _:key+': '+value,new,count=1,flags=re.M);assert count==1,key
assert p.read_text(encoding='utf-8')==old;p.write_text(new,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='NATIVE_CONFIG_DIAGNOSTIC_CHECKPOINTED',files=len(manifest),run_id=identity['run_id'])))
