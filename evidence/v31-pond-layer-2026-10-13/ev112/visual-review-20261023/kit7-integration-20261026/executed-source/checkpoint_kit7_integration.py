from pathlib import Path
import gzip,hashlib,json,re
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
rel='evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-integration-20261026';E=W/rel
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
S=R/'stage-kit7-fc-20261026';U=R/('kit7-world-sized-unit-20261026' if (R/'kit7-world-sized-unit-20261026').exists() else 'kit7-world-quiet-unit-20261026')
source=read(S/'independent-source-review.json');forest=read(S/'forest-support-review-full.json')
context=read(R/'kit7-context-unit-20261026/result.json');pilot=read(R/'package-kit7-fc-pilot-v2-20261026/verification.json');road=read(R/'kit7-road-mesh-20261026.json')
assert source['status']=='PASS_INDEPENDENT_SOURCE_COMPOSITION' and source['inputs_unchanged'] and source['objects']==2578398
assert sha(S/'root/dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp')==source['wrp_sha256']==forest['source_wrp_sha256']
assert forest['status']=='INCONCLUSIVE_BOUNDARY_SUPPORT' and not any(forest['counts'].values()) and forest['boundary_pending']['count']==3727
assert context['status']=='PASS_CONTEXT_GATES_BOUNDARY_PENDING' and context['inputs_unchanged']
assert pilot['status']=='PASS_201_MODELS_BYTE_EXACT_CONFIG_EXTENDED' and pilot['inputs_unchanged']
assert sha(R/'package-kit7-fc-pilot-v2-20261026/Addons/baltic_stream_pilot.pbo')==pilot['pbo_sha256']
assert road['status']=='OFFLINE_MESH_PASS' and road['failure_count']==0
assert read(R/'kit7-config-v2-controls.json')['status']=='PASS_REAL_CONFIG_CONTROLS'
assert read(R/'kit7-source-reader-controls-20261026/result.json')['status']=='PASS_REAL_WRP_MUTANT_CONTROLS'
shapes=read(R/'kit7-integrated-terrain-shapes-20261026.json')
shape_run=read(R/'kit7-integrated-terrain-shapes-20261026.receipt.json')
assert shape_run['returncode']==0 and not shape_run['timeout'] and shapes['inputs_unchanged']
probe=read(R/'probe-kit7-prepared-20261026/points.json');assert len(probe['points'])==2050 and not probe['diagnostics']
first=read(R/'kit7-world-unit-20261026/compile.receipt.json');assert first['timeout'] and first['inputs_unchanged']
retry=read(U/'compile.receipt.json');assert retry['inputs_unchanged']
world_path=R/'package-kit7-fc-world-20261026/verification.json'
world=read(world_path) if world_path.exists() else None
if world:
 receipt=read(U/'readback-package.receipt.json')
 assert retry['returncode']==receipt['returncode']==0 and not retry['timeout'] and not receipt['timeout'] and receipt['inputs_unchanged']
 assert world['status']=='OBJECTS_AND_PAYLOAD_VERIFIED_BOUNDARY_PENDING' and world['objects']['pilot_exact']==201
 assert sha(R/'package-kit7-fc-world-20261026/Addons/narva_trial.pbo')==world['pbo_sha256']
 assert read(R/'kit7-reader-warning-diagnosis.json')['status']=='WARNINGS_OUTSIDE_ACCEPTED_OBJECT_TABLE'
else:
 assert retry['timeout'] or retry['returncode']!=0,'A successful build requires its full readback before checkpoint'
for name in ['kit7-stage-review-20261026','kit7-package-review-20261026','kit7-world-review-20261026','kit7-pilot-v2-review-20261026']:
 c=read(R/name/'completion.json');assert c['exit_code']==0 and c['inputs_unchanged']
E.mkdir(parents=True,exist_ok=False)
def save(p,name=None):
 p=Path(p);raw=p.read_bytes();name=name or p.name
 compress=len(raw)>250000;out=E/(name+'.gz' if compress else name);out.parent.mkdir(parents=True,exist_ok=True);assert not out.exists()
 out.write_bytes(gzip.compress(raw,mtime=0) if compress else raw)
folders=[('kit7-stage-review-20261026','reviews/source'),('kit7-package-review-20261026','reviews/package'),('kit7-world-review-20261026','reviews/world'),('kit7-pilot-v2-review-20261026','reviews/pilot-v2'),('kit7-source-unit-20261026','source-run'),('kit7-context-unit-20261026','context-run'),('kit7-forest-context-20261026','forest-context'),('package-kit7-fc-pilot-20261026','rejected-pilot'),('package-kit7-fc-pilot-v2-20261026','pilot-v2'),('kit7-world-unit-20261026','rejected-world-timeout'),('kit7-world-quiet-unit-20261026','world-retry'),('kit7-source-reader-controls-20261026','source-controls'),('probe-kit7-prepared-20261026','prepared-probe')]
if (R/'kit7-world-sized-unit-20261026').exists():folders.append(('kit7-world-sized-unit-20261026','world-sized'))
if world:folders.append(('package-kit7-fc-world-20261026','world-package'))
for folder,dest in folders:
 for p in sorted((R/folder).iterdir()):
  if p.is_file() and p.suffix.lower() in {'.json','.jsonl','.log','.md','.txt','.cpp'}:save(p,dest+'/'+p.name)
for name in ['stage-report.json','independent-source-review.json','forest-support-review-full.json','baseline-config.cpp']:
 save(S/name,'source-world/'+name)
for name in ['kit7-road-mesh-20261026.json','kit7-config-v2-controls.json','kit7-bank-readonly-status.json','kit7-bank-final-status.json','kit7-shapes-comparison-20261026.json','kit7-compile-budget-evidence.json']:
 save(R/name)
for suffix in ['.json','.log','.receipt.json']:save(R/('kit7-integrated-terrain-shapes-20261026'+suffix))
save(R/'screen_kit7_integrated_terrain.py','executed-source/screen_kit7_integrated_terrain.py')
save(R/'pilot-kit7-fc-20261026/author-report.json','source-pilot/author-report.json')
scripts=['stage_kit7_fc.py','verify_kit7_fc_stage.py','check_kit7_stage_inputs.py','test_kit7_source_reader.py','run_kit7_source_unit.py','prepare_kit7_forest_context.py','run_kit7_context_only.py','package_kit7_fc_pilot.py','package_kit7_fc_pilot_v2.py','test_kit7_config_v2.py','accept_kit7_final_units.py','prepare_kit7_world_compile.py','run_kit7_world_unit.py','package_kit7_fc_world.py','retry_kit7_world_quiet.py','package_kit7_fc_world_quiet.py','checkpoint_kit7_integration.py']
for name in scripts:save(R/name,'executed-source/'+name)
for name in ['retry_kit7_world_sized.py','package_kit7_fc_world_sized.py']:save(R/name,'source-prepared/'+name)
if world:
 save(R/'kit7-reader-warning-diagnosis.json');save(R/'diagnose_kit7_reader_warnings.py','executed-source/diagnose_kit7_reader_warnings.py')
world_text=('Mundo compilado y empaquetado con readback completo de objetos; PBO `'+world['pbo_sha256']+'`. Se conservan todas las entradas salvo el WRP, incluida la configuración exacta F. La NM antigua se conserva como dato, sin aceptación para kit-7.' if world else 'La compilación sigue bloqueada: ambos intentos se conservan sin aceptar un mundo compilado. El paquete de 201 piezas y el WRP fuente sí están verificados.')
summary=dict(status='TECHNICAL_INTEGRATION_NATIVE_PENDING' if world else 'SOURCE_INTEGRATION_WORLD_COMPILE_PENDING',source=source,forest=dict(instances=forest['instances'],counts=forest['counts'],boundary_pending=3727,status=forest['status']),road=road,pilot={k:v for k,v in pilot.items() if k!='models'},world=world,first_compile=first,retry_compile=retry,native_probe_status='PREPARED_NOT_RUNTIME_READY',native_probe_points=2050,client_started=False,limits=['No fresh kit7 native, navigation, client or performance acceptance.','3727 boundary supports remain unknown.','OPRW reader checks object tables, not compiled heights.','Prepared probe still needs binding to combined package and full regression coverage.'])
(E/'SUMMARY.json').write_text(json.dumps(summary,indent=2)+'\n')
body=f'''# Kit-7 integrado sobre F/C — 26-10-2026

**Integración técnica comprobada; aceptación nativa pendiente.** El WRP fuente contiene 2.578.398 objetos: se sustituyen 174 piezas antiguas por 139 de cauce continuo, se retiran 292 conflictos de bosque y se ajusta solo Y de 1.623 árboles. El lector independiente confirma 62 poses previas exactas, 2.576.636 registros conservados byte a byte, 2.918 raíces exteriores intactas y 8.873 archivos laterales exactos. Las alturas fuente coinciden con el terreno canónico.

Los controles negativos corrompen copias WRP reales: altura, objeto movido, ausente y extra; los cuatro se rechazan en el lector esperado. El original permanece intacto. Sobre 2.560.580 objetos de bosque, las once categorías de infracción interior dan cero. Los 3.727 discos de frontera siguen INCONCLUSIVE: la prueba nativa anterior de F no se hereda.

Inventario nuevo de formas nativas del terreno integrado: `{json.dumps(shapes['finding_counts'])}`. Estado REVIEW_REQUIRED; no aceptación visual global. Incluye soportes enterrados y dominios protegidos con atribución explícita; un hallazgo no autoriza cambiar una protección ni demuestra por sí solo un defecto visible.

Contexto y densidad G2/G3/G7/G8 pasan. G2 tiene 68 ventanas desviadas y G3 tiene 29, dentro del criterio agregado calibrado con Livonia; no significa cero desviaciones locales. G8 juzga 475 ventanas y G7 47 turberas, sin fallos. Carreteras: 77.559 secciones y 130.534 intervalos, cero fallos, cobertura P11 congelada. No equivale a carreteras físicas ni conducción aceptadas.

Se descubrieron 35 registros de clase ausentes en el PBO C anterior, que solo declaraba 27 de sus 62 modelos. El primer empaquetado se detuvo antes de producir PBO. La enmienda conserva las 27 clases, repara las 35 ausentes y añade 139: 201 modelos/clases, modelos antiguos y nuevos byte exactos. Configuración decodificada comprobada y cinco mutantes reales rechazados. Es un defecto de registro corregido offline; no se atribuye retrospectivamente un fallo físico no observado.

Piloto combinado: `{pilot['pbo_sha256']}`. Fuente WRP: `{source['wrp_sha256']}`. {world_text}

La primera compilación agotó 900 s con registro extendido. El reintento cambia únicamente ese modo de registro y usa directorios nuevos. Después se encontró que los builds comparables anteriores tardaron 15:40 y 18:30: el presupuesto inicial de 15 minutos era insuficiente como límite general para esta fase. La enmienda preparó un intento de 30 minutos condicionado a otro timeout, sin cambiar checks. **No se ejecutó: el segundo terminó en 584,61 s, seguido de readback/empaquetado en 68,88 s.** El log extendido queda como candidato a contribuir a la demora, sin atribuirle toda la diferencia entre ejecuciones. Los recibos se conservan juntos.

Los tres avisos numéricos del lector se aislaron mediante instrumentación que conserva el resultado de `numpy.linalg.norm`: las 1.305 filas con norma no finita están antes de la tabla aceptada, en bytes explorados por el lector heurístico. Todas las matrices aceptadas son finitas y la comparación completa repetida pasa. Se publica la prueba; no se modificó el lector. El readback OPRW no decodifica alturas compiladas: requieren sonda propia. Tampoco convierte en PASS la frontera del bosque.

Cuatro revisiones independientes de Fable 5.1 por CLI, con fuentes congeladas, precedieron la composición y el empaquetado. Los hallazgos corregidos incluyen enlace completo de inputs, IDs/modelos/poses de obstáculos actuales, cobertura exacta de dependencias, configuración F byte exacta y recibos de timeout. Están los informes originales y los manifiestos de aceptación.

Preparada una sonda inicial de 2.050 puntos, todavía NO lista para lanzar: mantiene el enlace del piloto aislado y requiere el conjunto final, regresión C/F, vértices modificados y frontera. Véase `plans/ev112-kit7-native-verification-20261026.md`. No hubo despliegue, cliente ni mutaciones MCP en esta unidad; el banco seguía ocupado en la última consulta, sin run ni lease propios. No se hereda navegación CNav9 ni rendimiento E/Chernarus.

Los scripts en `executed-source/` son instantáneas de los ejecutados en el directorio local de build; sus rutas y dependencias quedan fijadas en los manifiestos. No son un instalador portable. No se publican PBO, P3D, WRP, texturas ni matrices binarias. Los JSON/logs mayores de 250 kB se comprimen con gzip determinista. Los fallos y la incertidumbre permanecen visibles.
'''
(E/'README.md').write_text(body,encoding='utf-8')
p=W/'README.md';s=p.read_text(encoding='utf-8');old='anterior intacta. Sigue aislado; faltan integración de bosque/WRP y pruebas\npropias en el motor.';assert old in s
s=s.replace(old,'anterior intacta. Ya está integrado en el WRP fuente y el bosque: **292 conflictos\nretirados y 1.623 apoyos ajustados**, con carreteras y contexto forestal comprobados.\nEl paquete combinado declara sus **201 piezas**; faltan las pruebas propias en el motor.\n[Integración técnica y límites]('+rel+'/README.md).')
p.write_text(s,encoding='utf-8')
p=W/'README.md';s=p.read_text(encoding='utf-8');old='La generación de navegación F terminó\nsin una malla válida; sigue pendiente, junto con la locomoción y la cobertura global.';assert old in s
s=s.replace(old,'El primer intento de navegación F terminó\nsin una malla válida; C/F ya dispone de la malla y las 45 consultas indicadas arriba.\nSiguen pendientes la locomoción y la cobertura global.');p.write_text(s,encoding='utf-8')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8')
updates={
'updated':'2026-10-26 (kit7 fuente/bosque/carreteras/piloto201 verificados; mundo '+('técnico verificado' if world else 'pendiente de compilación')+'; motor pendiente)',
'plan':'Unidad kit7-integration-20261026 documentada. Composición según plan de integración y enmienda de35clases; siguiente plans/ev112-kit7-native-verification-20261026.md.',
'blocker':'Kit7 requiere pruebas nativas propias: alturas compiladas, agua/física/regresión,3727apoyos de frontera y navegación. Banco ocupado en última consulta, sin run propio.38/48/71/79 con conflictos de soporte;98/67 protegidos;01545/60m pendiente. No heredar CNav9 ni rendimientoE.',
'validation':'Kit7 fuente2578398objetos,62poses previas y139nuevas;292conflictos bosque retirados,1623Yajustados. Bosque2560580/11categorías interiores0,3727frontera INCONCLUSIVE. G2/G3/G7/G8PASS; carreteras77559secciones/130534intervalos0fallos. Piloto201modelos exactos,27clases preservadas+35reparadas+139nuevas. WRP4mutantes y config5mutantes rechazados.',
'cleanup':'Esta unidad sin lease, sin run propio, sin cliente ni despliegue MCP. Primer compilador terminado por timeout solo su árbol; reintento terminal documentado. selfnone/pending0/cleanup[]; banco ajeno ocupado según recibo.',
'next':'Cerrar binding y cobertura de sonda kit7 según plan nativo; probar mundo/piloto propios cuando banco libre,3727frontera y alturas, regenerar navegación y medir rendimiento del candidato. Vista conjunta pendiente.',
'handoff':rel+'/README.md; sesión C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-26-dayz-baltic-kit7-integration.md.'}
for key,value in updates.items():s,n=re.subn('^'+re.escape(key)+':.*$',lambda m:key+': '+value,s,count=1,flags=re.M);assert n==1,key
p.write_text(s,encoding='utf-8')
p=W/'bugs.md';s=p.read_text(encoding='utf-8');needle='**26-10 kit7:**';assert needle in s
s=s.replace(needle,'**26-10 integración kit7:** fuente/bosque/carreteras y piloto201 verificados;35clases ausentes reparadas,3727frontera y motor propios pendientes. [Evidencia]('+rel+'/README.md). **Historia — 26-10 kit7 aislado:**',1);p.write_text(s,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
note=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-26-dayz-baltic-kit7-integration.md');assert not note.exists()
note.write_text(body+'\nEvidencia: '+str(E)+'\nRecibo de publicación: '+str(R/'publication-kit7-integration-receipt.json')+'\n',encoding='utf-8')
print(json.dumps(dict(status=summary['status'],files=len(manifest),bytes=sum(x['bytes'] for x in manifest.values()))))
