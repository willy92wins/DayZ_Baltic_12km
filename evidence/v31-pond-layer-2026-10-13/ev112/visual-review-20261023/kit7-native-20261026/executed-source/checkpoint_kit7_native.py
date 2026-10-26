from pathlib import Path
import gzip,hashlib,json,re
from datetime import datetime
R=Path(__file__).parent;O=R/'kit7-native-20261026';V=R/'kit7-native-data-review-20261026'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
rel='evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-native-20261026';E=W/rel
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
dep=read(O/'deployment.json');pre=read(O/'prelaunch.json');final=read(O/'final-session-status.json')
assert final['self']['state']=='none' and not final['own_run_present'] and not final['cleanup_degraded'] and final['pending_commands']==0
assert all(sha(Path(p))==h for p,h in dep['inputs'].items())
packages={str(Path(p)):h for p,h in dep['deployed'].items()};packages[str(Path(pre['bridge_pbo']))]=pre['bridge_sha256']
results={};diagnostics={}
for kind,status in [('heights','NATIVE_HEIGHT_SAMPLE_PASS'),('forest','SAMPLED_BOUNDARY_CLEAR')]:
 d=O/kind;result=read(d/'result.json');host=read(d/'host-identity.json');mcp=read(d/'mcp-identity.json');capture=read(d/'log-capture.json');cleanup=read(d/'cleanup.json');launch=read(d/'launch.json')
 assert result['status']==status and result['manifest_sha256']==sha(d/'points.json') and result['log_sha256']==sha(d/'native.log')==capture['sha256']
 assert capture['survey_id']==dep['surveys'][kind] and capture['count']==result['points']
 assert host['run_id']==mcp['run_id']==launch['run_id']==cleanup['close']['run_id']
 assert host['pid']==mcp['processes'][0]['pid']==capture['pid'] and len(mcp['processes'])==1
 # Host emits 100ns digits, MCP timestamp is truncated to microseconds.
 assert datetime.fromisoformat(host['created_utc'])==datetime.fromisoformat(capture['created_utc'])==datetime.fromisoformat(mcp['processes'][0]['creation_time_utc'])
 assert host['navmesh_data_server'] and host['executable_file_sha256']==pre['executable_sha256']
 assert {str(Path(p)):h for p,h in host['package_hashes'].items()}==packages
 assert mcp['server_binding']=='BOUND' and mcp['version_state']=='ok' and mcp['server_run_id']==host['run_id'] and mcp['poll_age_s']<10
 assert all(c['state']=='not_started' for c in mcp['client_diagnostics'])
 assert cleanup['close']['run_retired'] and cleanup['self']['state']=='none' and not cleanup['error'] and not cleanup['cleanup_error'] and not cleanup['own_run_present']
 assert not cleanup['cleanup_degraded'] and cleanup['pending_commands']==0
 assert read(d/'preflight.json')['status']=='succeeded'
 results[kind]=dict(result,run_id=host['run_id'])
 # Publish diagnostics only, never the raw RPT command line. Keep original hash.
 lines=(d/'server.RPT').read_text(encoding='utf-8-sig',errors='replace').splitlines()
 selected=[re.sub(r'^\d\d:\d\d:\d\d\.\d+\s*','',line) for line in lines if '(E):' in line or '(W):' in line]
 diagnostics[kind]=dict(rpt_sha256=sha(d/'server.RPT'),rpt_binding=read(d/'rpt-binding.json'),diagnostics=selected,termination_marker=any('Termination successfully completed' in s for s in lines),note='Diagnostics are recorded, not claimed absent; GetPlugin stack and cleanup leaks also occur in F boundary reference.')
 assert diagnostics[kind]['termination_marker']
assert results['heights']['points']==11052 and results['heights']['failure_count']==0
assert results['forest']['objects']==3727 and results['forest']['points']==269968 and not any(results['forest']['counts'].values())
summary=dict(status='NATIVE_HEIGHT_AND_BOUNDARY_SAMPLES_PASS',heights=results['heights'],forest=results['forest'],counts=dep['counts'],packages=dep['deployed'],tests=19,client_started=False,navigation_accepted=False,limits=['Finite native SurfaceY and boundary samples only.','Water/collision kit7, navigation, client visual acceptance and performance remain pending.'],final_session=final)
(O/'result.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
E.mkdir(parents=True,exist_ok=False)
def save(p,name):
 raw=p.read_bytes();out=E/(name+'.gz' if len(raw)>250000 else name);out.parent.mkdir(parents=True,exist_ok=True);assert not out.exists();out.write_bytes(gzip.compress(raw,mtime=0) if len(raw)>250000 else raw)
for name in ('deployment.json','prelaunch.json','result.json','final-session-status.json'):save(O/name,name)
for kind in ('heights','forest'):
 for p in sorted((O/kind).iterdir()):
  if p.suffix in ('.json','.log'):save(p,kind+'/'+p.name)
 (E/kind/'rpt-diagnostics.json').write_text(json.dumps(diagnostics[kind],indent=2)+'\n',encoding='utf-8')
for p in sorted(V.iterdir()):
 if p.name in ('accepted.json','source-hashes.json','completion.json','review-brief.md') or p.name.endswith('.py.log') or p.name=='optimized-python-negative.log':save(p,'review/'+p.name)
review=read(V/'review-response.json');(E/'review/fable-review.md').write_text(review['result']+'\n',encoding='utf-8')
(E/'review/provenance.json').write_text(json.dumps(dict(response_sha256=sha(V/'review-response.json'),modelUsage=review['modelUsage'],is_error=review['is_error'],permission_denials=review.get('permission_denials')),indent=2)+'\n')
for name in ('prepare_kit7_native_data.py','accept_kit7_native_preparation.py','capture_kit7_native_log.ps1','capture_owned_server_identity.ps1','copy_owned_server_rpt.ps1','finish_kit7_native_survey.js','checkpoint_kit7_native.py'):save(R/name,'executed-source/'+name)
save(W/'missions/BalticForestBoundaryV1.BalticTrial/init.c','producer/init.c')
save(R/'kit7-regression-discovery-20261026.json','next-water-regression-discovery.json')
body='''# Kit7 — alturas y apoyos nativos verificados

El paquete mundo `10e09e3f…` con piloto `46244e7f…` pasa dos sondas nuevas en DayZ 1.30, sin cliente. No se heredan resultados de F.

- Alturas: **11.052/11.052**, todos los **3.430 vértices modificados** y **7.622 centroides de triángulos incidentes**. Cero fallos; diferencia máxima **0,0001861622 m** (0,19 mm), umbral 0,01 m.
- Bosque de frontera: **3.727 objetos / 269.968 muestras**, cero fallos de raíz, apoyo o margen con agua. `SAMPLED_BOUNDARY_CLEAR` describe muestreo finito; no acepta el disco continuo ni todo el bosque.
- UUID, CSV, fuentes, paquetes, run, PID/creación y puente ligados a cada log. Las dos sesiones cerradas por MCP; lease liberado, sin comandos pendientes ni cleanup degradado.
- **19 tests** pasan. Fable 5.1 por CLI emitió SOUND-with-fixes; corregidos sus hallazgos, con negativo real de Python optimizado y del productor cambiado incluso actualizando su hash.

El preflight rechazó primero la ruta con separadores `/`; el contrato exige la forma Windows normalizada. Con esa forma, ambos preflights y lanzamientos pasan. No se modificó la política del launcher. Las sondas usaron DataServer como la referencia F, porque este paquete conserva NM6; **navegación sigue pendiente**.

Los RPT tienen avisos de recursos sin render, stack GetPlugin de diagnóstico y avisos de limpieza también observados en F. Se publican los diagnósticos y hashes; no se afirma log limpio. La misión completó todos los puntos y ambos cierres terminaron correctamente.

Siguiente: ligar los 2.050 puntos de agua/colisión nuevos al paquete combinado, verificar cobertura de las 139 piezas/138 juntas y todos los controles laterales frente al agua completa, añadir regresión de los 4.749 puntos F y calibración física nueva. El descubrimiento conserva las expectativas F (ninguno cae sobre geometría nueva), pero aún no autoriza el lanzamiento combinado.

La navegación propia, vista conjunta, conducción, FPS y comparación de rendimiento del candidato siguen pendientes. Los defectos visuales globales de ríos y terreno no se declaran cerrados.
'''
(E/'README.md').write_text(body,encoding='utf-8')
# Keep full historical handoff; update only named live-state lines with backups.
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8');(O/'handoff-before.md').write_text(s,encoding='utf-8')
updates={
'updated':'2026-10-26 (kit7 alturas y bosque de frontera medidos y aprobados por muestreo en motor; agua/física pendiente)',
'plan':'Unidad kit7-native-20261026 completada según plans/ev112-kit7-native-data-unit-20261026.md; continuar punto1 agua/colisión y punto4 navegación del plan ev112-kit7-native-verification-20261026.md.',
'blocker':'Kit7 agua/física/regresión y navegación pendientes; alturas y3727apoyos de frontera ya medidos sobre su paquete.38/48/71/79 con conflictos de soporte;98/67 protegidos;01545/60m pendiente. No heredar CNav9 ni rendimientoE.',
'validation':'Kit7 fuente2578398objetos y201modelos; G2/G3/G7/G8 y carreteras offlinePASS. Motor propio11052alturas/0fallos (3430vértices+7622centroides, máximo0.0001861622m); frontera3727/269968 SAMPLED_BOUNDARY_CLEAR,3categorías0.19tests; Fable5.1 revisado y corregido. No aceptación visual/global.',
'cleanup':'Dos runs propios cerrados oficialmente y retirados; selfnone,pending0,cleanup[],sincliente. Banco libre en recibo final; consultar de nuevo antes de lanzar.',
'next':'Agua/colisión kit7: cobertura139piezas/138juntas y controles laterales contra agua global; unir2050puntos a4749F con calibración nueva. Después navegación propia, rendimiento y vista conjunta.',
'handoff':rel+'/README.md; sesión C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-26-dayz-baltic-kit7-native.md.',
'deployed':'Kit7 aislado P:/Mods/@DayZ_Baltic_EV112_Kit7Native: mundo10e09e3f…,piloto46244e7f…,agua97edcafe…; hashes completos en evidencia. Alturas/frontera medidos en DataServer; agua/física y NM propia pendientes. CNav9 conservado.'}
for key,value in updates.items():s,n=re.subn('^'+re.escape(key)+':.*$',lambda m:key+': '+value,s,count=1,flags=re.M);assert n==1,key
assert len(s)>=.9*len(p.read_text(encoding='utf-8'));p.write_text(s,encoding='utf-8')
p=W/'README.md';s=p.read_text(encoding='utf-8');old='El paquete combinado declara sus **201 piezas**; faltan las pruebas propias en el motor.';assert old in s
s=s.replace(old,'El paquete combinado declara sus **201 piezas** y ya pasa **11.052 mediciones de altura**\ny **269.968 muestras de apoyo en la frontera** en el motor. Agua/colisión propia y navegación\nsiguen pendientes. [Pruebas nativas y límites]('+rel+'/README.md).');p.write_text(s,encoding='utf-8')
p=W/'bugs.md';s=p.read_text(encoding='utf-8');old='35clases ausentes reparadas,3727frontera y motor propios pendientes.';assert old in s
s=s.replace(old,'35clases ausentes reparadas; alturas11052/0fallos y frontera3727/269968 medidas sin fallos; agua/física, navegación y vista propias pendientes. [Sondas nativas]('+rel+'/README.md).',1);p.write_text(s,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
note=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-26-dayz-baltic-kit7-native.md');assert not note.exists()
note.write_text(body+'\nEvidencia: '+str(E)+'\nRecibo de publicación: '+str(R/'publication-kit7-native-receipt.json')+'\n',encoding='utf-8')
print(json.dumps(dict(status=summary['status'],files=len(manifest),bytes=sum(x['bytes'] for x in manifest.values()))))
