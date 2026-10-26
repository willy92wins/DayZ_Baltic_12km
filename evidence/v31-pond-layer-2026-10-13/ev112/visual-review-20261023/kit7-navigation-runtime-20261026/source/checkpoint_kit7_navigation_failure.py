"""Retain completed native navigation evidence without converting a height FAIL into PASS."""
from pathlib import Path
import gzip,hashlib,json,re,subprocess
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav-consumer-20261026';G=R/'nav-kit7-preparation-20261026';N=R/'navmesh-kit7-v9-20261026';P=R/'package-kit7-nav-v9-20261026'
E=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-navigation-runtime-20261026'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not subprocess.check_output(['git','status','--porcelain'],cwd=W).strip(),'Preserve unrelated changes'
result=read(D/'result.json');identity=read(D/'identity-verification.json');clean=read(D/'cleanup.json')
expected=['kit7_piece_124_right/1','kit7_piece_133_right/1','kit7_seam_124_right/0','kit7_seam_133_right/0']
assert result['status']=='FAIL_KIT7_NATIVE_GRAPH' and sorted(result['height_issues'])==[v+': nav waypoint too far from physical surface' for v in expected]
assert len(result['cases'])==607 and all(c['status']=='PASS' for c in result['cases'])
assert len(result['local_coverage'])==562 and all(c['status']=='PASS' for c in result['local_coverage'].values()) and not result['local_failures']
assert identity['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS'
for cleanup in [clean,read(G/'cleanup.json')]:
    assert cleanup['close']['run_retired'] and cleanup['close']['graceful'] and cleanup['self']['state']=='none'
    assert not cleanup['own_run_present'] and not cleanup['cleanup_error'] and cleanup['pending_commands']==0 and not cleanup['cleanup_degraded']
assert read(G/'completion.json')['status']=='GENERATION_STAGE_COMPLETE_PENDING_VALIDATION'
assert read(N/'inspection.json')['status']=='EMPIRICAL_V9_PREFIX_AND_COVERAGE_PASS'
assert read(P/'verification.json')['status']=='PASS_NAVMESH_PACKED_BYTE_PARITY'
accepted=read(R/'kit7-nav-postprocess-review-20261026/accepted.json');assert accepted['status']=='ACCEPTED_AFTER_REVIEW'
for p,h in {**accepted['inputs'],**read(D/'frozen.json')['inputs'],**read(D/'deployment.json')['packages']}.items():assert sha(Path(p))==h,p
assert read(R/'kit7-nav-height-reconstruction-20261026/result.json')['max_native_residual_m']<1e-6
E.mkdir(parents=True,exist_ok=False)
def save(p,name):
    raw=p.read_bytes();compress=len(raw)>250000 and p.suffix not in ('.png','.jpg')
    target=E/(name+'.gz' if compress else name);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(gzip.compress(raw,mtime=0) if compress else raw)
for p in D.glob('*'):
    if p.suffix in ('.json','.jsonl','.log') and p.is_file():save(p,'runtime/'+p.name)
for p in (D/'observer').glob('*'):
    if p.is_file():save(p,'runtime/observer/'+p.name)
for name in ['launch-inputs.json','fifo-user-request.json','coordinator-control-flow-fifo-v4.json','host-identity.json','mcp-before.json','mcp-after.json','generator-identity.json','rpt-binding.json','cleanup.json','completion.json','timeline.jsonl']:
    save(G/name,'generation/'+name)
for p in (G/'observer').glob('*'):
    if p.is_file():save(p,'generation/observer/'+p.name)
for name in ['generation.json','inspection.json']:save(N/name,'generation/'+name)
for name in ['verification.json','deployment.json']:save(P/name,'package/'+name)
for folder in ['kit7-nav-height-diagnostic-20261026','kit7-nav-layer-diagnostic-20261026-v2','kit7-nav-tile-diagnostic-20261026','kit7-nav-height-reconstruction-20261026']:
    save(R/folder/'result.json','diagnosis/'+folder+'/result.json')
save(R/'kit7-nav-layer-diagnostic-20261026-v2/config.cpp','diagnosis/deployed-config.cpp')
review=R/'kit7-nav-height-review-20261026';response=read(review/'response.json')
assert read(review/'completion.json')['inputs_unchanged'] and not response['is_error'] and not response['permission_denials'] and 'claude-fable-5-1' in response['modelUsage']
for name in ['brief.md','source-hashes.json','completion.json']:save(review/name,'diagnosis/fable/'+name)
(E/'diagnosis/fable/review.md').write_text(response['result']+'\n',encoding='utf-8')
(E/'diagnosis/fable/provenance.json').write_text(json.dumps(dict(response_sha256=sha(review/'response.json'),modelUsage=response['modelUsage'],is_error=False,permission_denials=[]),indent=2)+'\n')
(E/'diagnosis/fable/adjudication.md').write_text('''# Adjudicación del diagnóstico

Se conserva el informe tal como lo emitió Fable. Corrección factual: las ocho
muestras del diagnóstico inicial pertenecen a la orilla derecha; cuatro pasan
el umbral y cuatro fallan. La mención a «cuatro de orilla izquierda» es errónea.
La existencia de una sola capa no queda demostrada solo por la consulta nearest.
No se promueven esas inferencias a hechos ni se atribuye locomoción a6801raycasts.

Después de esa revisión se reconstruyó el plano de los polígonos de tres teselas
del propio archivo NM. Reproduce las ocho Y nativas con error máximo4.82e-7m.
Eso localiza la discrepancia en la aproximación guardada. No identifica qué
parámetro interno decidió esos polígonos ni prueba cómo los seguirá un actor.
La propuesta de elevar barreras en Geometry altera transitabilidad y no se aplica.
No se añade ningún parámetro GenParams no verificado ni se cambia la tolerancia.
''',encoding='utf-8')
sources=['checkpoint_kit7_navigation_failure.py','orchestrate_nav_kit7_fifo_v4.js','orchestrate_kit7_nav_probe.js','capture_kit7_nav_log.ps1','finish_kit7_nav_probe.py','package_and_deploy_kit7_nav9.py','diagnose_kit7_nav_heights.py','diagnose_kit7_nav_layers.py','inspect_kit7_nav_failed_tiles.py','reconstruct_kit7_nav_height.py','review_kit7_nav_height_diagnosis.py']
for name in sources:save(R/name,'source/'+name)
save(R/'kit7-nav-layer-diagnostic-20261026/failed-source.py','diagnosis/failed-empty-lod-source.py')
(E/'diagnosis/failed-empty-lod.md').write_text('El primer diagnóstico falló al tratar un LOD vacío como una matriz de caras. No produjo veredicto. La revisión v2 omite LOD sin caras y conserva los restantes; fuente original archivada. Sus warnings de proyección de caras verticales no se usan como alturas. No hubo cambio en modelos ni consumidor nativo.\n',encoding='utf-8')
mission=Path(read(D/'frozen.json')['mission'])
for name in ['init.c','queries.csv']:save(mission/name,'mission/'+name)
for label,base in [('generation',G),('runtime',D)]:
    rpt=base/'server.RPT';lines=rpt.read_text(encoding='utf-8',errors='replace').splitlines()
    selected=[line for line in lines if any(term in line.lower() for term in ['error','warning','exception','termination successfully','cannot',"can't compile"])]
    (E/label/'rpt-findings.json').write_text(json.dumps(dict(sha256=sha(rpt),line_count=len(lines),selected_lines=selected,full_rpt_retained_locally=True),indent=2)+'\n')
(E/'README.md').write_text('''# Kit7:607 rutas ejecutadas; altura de navegación todavía FAIL

**FAIL_KIT7_NATIVE_GRAPH**. Pasan607 consultas de conectividad y562 controles
locales de la polilínea XZ. Cuatro waypoints incumplen0,801m de distancia vertical
a Roadway. No hay aceptación global de navegación, actores, barcos ni vista.

| Caso | Error vertical | Exceso sobre0,801m |
|---|---:|---:|
| pieza124derecha/1 |0,852283m|0,051283m|
| junta124derecha/0 |0,875470m|0,074470m|
| pieza133derecha/1 |1,167696m|0,366696m|
| junta133derecha/0 |0,981493m|0,180493m|

La generación propia produjo704535052bytes,966289teselas TESMv9/VAND12 en97min22s.
NM SHA256:13e1ab1567740aca2ff94d6607b6f2c6423b9142674878562bf477994597f80b.
El paquete solo reemplaza NM;6826entradas restantes permanecen byteexactas.
Mundo SHA256:a2919a80ae6da6fc90e75b0ac55d1e9dd4ba4a39f6700b9fec237c7e7683b16c.
Los archivos grandes y los binarios de Bohemia quedan fuera de Git.

La sonda607 se ejecutó en servidor normal propio sin cliente. Cubre139piezas,
138juntas, extremos por ambas orillas y45regresiones anteriores. Conserva los
ocho testigosF y todos los umbrales fijados antes de consultar el motor.
Preparación, tests y revisión del consumidor:
[checkpoint previo](../kit7-navigation-consumer-preparation-20261026/README.md).

En ocho waypoints de las dos zonas, visual y Roadway coinciden; Geometry difiere
menos de0,008m. La altura guardada en los polígonos de tres teselas reproduce
las ocho alturas nativas con residual máximo4,82e-7m. Es evidencia local de una
aproximación vertical del navmesh; no una explicación completa del generador.
La lectura de polígonos es empírica y limitada a esas teselas. No se editó NM.

Ambos runs entraron por FIFO MCP sin preconsulta, terminaron con cierre oficial
propio y liberación de lease; pending0, cleanup[], selfnone. La automatización
periódica sigue pausada. Las comprobaciones estáticas no sustituyen locomoción.

Siguiente: aislar una corrección de generación que conserve cauce, transitabilidad
y tolerancias; repetir después las607consultas con identidad propia. No regenerar
igual ni deformar la orilla para hacer verde el contador. El piloto híbrido de
14vértices publicado aparte sigue sin integrar y no hereda esta navmesh.
''',encoding='utf-8')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8');(D/'handoff-before-runtime-failure.md').write_text(s,encoding='utf-8')
updates={
'updated':'2026-10-26 (generación y sonda607 terminadas;4fallos de altura localizados en la aproximación de navmesh)',
'plan':'Física kit7PASS6801/6801. Grafo:607consultas de conectividad y562corredoresXZPASS,4waypointsFAIL altura; mantener0,801m. Ver plans/ev112-kit7-navigation-consumer-20261026.md.',
'blocker':'Navegación numérica kit7:piece/seam124/133right incumplen0,801m (errores0,852–1,168m); no aceptación global. Otros38/48/71/79 soportes,98/67protegidos,01545/60m y censo global abiertos.',
'next':'Corregir aproximación vertical de navmesh sin modificar rutas/tolerancias ni bloquear taludes. Tres teselas reproducen las8alturas nativas a<1e-6m; no regenerar igual. Piloto híbrido14v aparte sigue pendiente de integración. Vista/locomoción pendientes.',
'cleanup':'Generación57c47974 y sonda4bbd2dce cerradas oficialmente; selfnone/pending0/cleanup[]. Sin proceso propio activo. AutomatizaciónPAUSED; lanzamientos nuevos por FIFO MCP sin consultar antes el banco.',
'handoff':E.relative_to(W).as_posix()+'/README.md; evidencia nativa y diagnóstico retenidos conFAIL explícito.',
'deployed':'P:/Mods/@DayZ_Baltic_EV112_Kit7NavV9: mundoa2919a80ae6da6fc90e75b0ac55d1e9dd4ba4a39f6700b9fec237c7e7683b16c,piloto3d9550bf,agua97edcafe. Kit7Overlap preservado. NMpropia cargada;4fallos altura, vista pendiente.'}
for k,v in updates.items():s,n=re.subn('^'+k+':.*$',lambda m:k+': '+v,s,count=1,flags=re.M);assert n==1
p.write_text(s,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='KIT7_NATIVE_HEIGHT_FAILURE_CHECKPOINT',files=len(manifest),bytes=sum(v['bytes'] for v in manifest.values()))))
