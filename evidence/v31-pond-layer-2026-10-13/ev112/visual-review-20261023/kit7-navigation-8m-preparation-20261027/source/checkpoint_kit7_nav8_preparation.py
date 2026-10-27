from pathlib import Path
import gzip,hashlib,json,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'nav-kit7-8m-preparation-20261027';E=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-navigation-8m-preparation-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
dep=read(D/'launch-inputs.json');assert dep['status']=='READY_AFTER_CODE_REVIEW' and all(sha(Path(p))==h for p,h in dep['inputs'].items())
tests=read(D/'release-tests/result.json');assert tests['status']=='PASS_PREPUBLICATION_TARGETED_TESTS' and all(sha(Path(p))==h for p,h in tests['sources'].items())
E.mkdir(parents=True,exist_ok=False)
def save(p,n):
 raw=p.read_bytes();out=E/(n+'.gz' if len(raw)>250000 else n);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(gzip.compress(raw,mtime=0) if len(raw)>250000 else raw)
for n in ['launch-inputs.json','generation-controls.json','generation-controls-deadline.json','wrong-baseline.json','wrong-baseline.stderr.log','request-preflight.json']:save(D/n,n)
for p in (D/'release-tests').iterdir():save(p,'tests/'+p.name)
for folder,label in [('kit7-nav8-plan-review-20261027','plan-review'),('kit7-nav8-code-review-20261027','code-review')]:
 v=R/folder
 for n in ['completion.json','source-hashes.json','brief.md']:save(v/n,label+'/'+n)
 for n in ['adjudication.md','accepted.json','reviewed-plan.md']:
  if (v/n).exists():save(v/n,label+'/'+n)
 if (v/'reviewed-source').exists():
  for p in (v/'reviewed-source').iterdir():save(p,label+'/reviewed-source/'+p.name)
 rv=read(v/'response.json');assert not rv['is_error'] and not rv['permission_denials']
 (E/label/'fable-review.md').write_text(rv['result']+'\n',encoding='utf-8')
 (E/label/'provenance.json').write_text(json.dumps(dict(response_sha256=sha(v/'response.json'),modelUsage=rv['modelUsage'],is_error=False,permission_denials=[]),indent=2)+'\n')
for n in ['orchestrate_kit7_nav8_generation.js','test_kit7_nav8_generation.cjs','prepare_kit7_nav8_generation.py','fix_nav8_deadline.py','seal_kit7_nav8_generation.py','check_nav8_wrong_baseline.py','record_nav8_release_tests.py',Path(__file__).name]:save(R/n,'source/'+n)
for n in ['verification.json','original.cpp','config.cpp','roundtrip.cpp','compile.log','decode-candidate.log','filebank.log']:save(R/'package-kit7-nav8-input-20261027'/n,'package/'+n)
for folder,label in [('kit7-nav-tile-width-screen-20261027-v2','diagnostic-eight-points'),('kit7-all-nav-tile-width-screen-20261027','diagnostic-local-routes')]:save(R/folder/'result.json',label+'/result.json')
(E/'README.md').write_text('''# Kit7: experimento de navegación de8m preparado

Los cuatro fallos nativos de altura siguen abiertos. Este commit valida las
herramientas y el paquete de entrada del nuevo ensayo; no declara corregidas
las rutas ni contiene una nueva navmesh aceptada.

El único cambio del mundo es GenParams.tileWidth12.5→8. Compilación y nueva
decodificación conservan la semántica de toda la configuración restante;
6826entradas permanecen byte a byte. WRP, modelos, agua y tránsito no cambian.
El NM12.5m conservado en la entrada no es el resultado8m propuesto.

Pruebas finales:14del generador/inspector,3de configuración y7del observador
Windows, incluidas salidas reales de procesos de prueba. El coordinador pasa
19casos y rechaza5mutantes. Un paquete base con hash falso se rechaza antes de
crear salida. Esto no sustituye evidencia del motor DayZ.

Fable5.1 revisó plan y código como SOUND-with-fixes. El presupuesto quedó en
18000s, con observador18300s, sin cambiar los defaults. El límite del bucle se
corrigió para usar tiempo transcurrido:1901respuestas rápidas ya no cancelan
una generación sana y el vencimiento real sí cancela la generación propia.
Fuentes revisadas y resultados previos se conservaron. TIMEOUT es INCONCLUSO.

Siguiente: generación nativa por FIFO MCP, inspecciónTESMv9/VAND12 de8m,
empaquetado sin otros cambios y las mismas607consultas/562corredores, con
0,801m de altura intactos. Después se repetirá RAM frente a Chernarus. Ninguna
predicción offline, éxito de empaquetado o prueba simulada cierra los4fallos.
No aceptación visual, de actores, barcos, FPS ni globalEV112.
''',encoding='utf-8')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8');(D/'handoff-before-nav8.md').write_text(s,encoding='utf-8')
updates={'updated':'2026-10-27 (variante nav8m preparada y probada; cuatro fallos nativos anteriores siguen abiertos)','plan':'Corregir4alturas sin rebajar0,801m: ensayo aislado tileWidth12.5→8, WRP/modelos exactos. Ver plans/ev112-kit7-nav-height-refinement-20261027.md. Herramientas validadas; aún sin aceptación nativa8m.','next':'Continuar coordinador8m por FIFO MCP y validar estructura/paquete/mismas607consultas. Estado operativo vivo en R/ACTIVE-WORK.md; no duplicar solicitudes o generación. Después RAM A-B-B-A-A-B contra Chernarus.','cleanup':'Runs anteriores57c47974/4bbd2dce cerrados oficialmente. Nueva generación8m usa FIFO sin precheck, adopción/heartbeat/cierre propios. Consultar R/ACTIVE-WORK.md para ejecución actual; automatización antiguaPAUSED.','handoff':E.relative_to(W).as_posix()+'/README.md; fallo nativo anterior preservado en kit7-navigation-runtime-20261026.'}
for k,v in updates.items():s,n=re.subn('^'+k+':.*$',lambda m:k+': '+v,s,count=1,flags=re.M);assert n==1
p.write_text(s,encoding='utf-8')
m={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()};(E/'MANIFEST.json').write_text(json.dumps(m,indent=2)+'\n')
print(json.dumps(dict(status='VALIDATED_TOOLS_NATIVE_HEIGHTS_STILL_OPEN',files=len(m),bytes=sum(v['bytes'] for v in m.values()))))
