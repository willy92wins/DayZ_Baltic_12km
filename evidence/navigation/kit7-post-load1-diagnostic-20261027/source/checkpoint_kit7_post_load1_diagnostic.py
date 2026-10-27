from pathlib import Path
import json,hashlib,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c');A=R/'kit7-post-load1-vertex-surfaces-20261027';B=R/'kit7-post-load1-chords-20261027';V=R/'kit7-post-load1-diagnostic-review-20261027';E=W/'evidence/navigation/kit7-post-load1-diagnostic-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
F=R/'kit7-post-load1-nav8-review-20261027';C=R/'kit7-post-load1-nav8-fans-20261027'
assert read(F/'adjudication.json')['status']=='ACCEPTED_AFTER_REVIEW'
for p,h in read(F/'source-hashes.json').items():assert sha(Path(p))==h,p
assert not E.exists();review=read(V/'response.json');assert not review['is_error'] and not review.get('permission_denials') and 'claude-fable-5-1' in review['modelUsage']
assert read(V/'completion.json')['returncode']==0 and read(V/'adjudication.json')['status']=='ACCEPTED_AFTER_REVIEW'
for p,h in read(V/'source-hashes.json').items():assert sha(Path(p))==h,p
for d in [A,B,C]:assert read(d/'completion.json')['returncode']==0 and read(d/'completion.json')['inputs_unchanged'] and read(d/'completion.json')['dayz_runs']==0
assert read(A/'result.json')['point_count']==52 and read(B/'result.json')['failed_samples']==3
E.mkdir(parents=True)
def save(p,name):
 t=E/name;t.parent.mkdir(parents=True,exist_ok=True);t.write_bytes(p.read_bytes())
for name in ['result.json','completion.json','budget.json']:save(A/name,'vertices/'+name)
for name in ['result.json','completion.json','generator-help.json','generator-help.stdout.log','generator-help.stderr.log']:save(B/name,'chords/'+name)
for name in ['source-hashes.json','completion.json','adjudication.json']:save(V/name,'review/'+name)
for name in ['source-hashes.json','completion.json','adjudication.json']:save(F/name,'nav8-review/'+name)
(E/'nav8-review/fable-review.md').write_text(read(F/'response.json')['result'],encoding='utf-8')
for name in ['result.json','completion.json','publication-errata.json']:save(C/name,'nav8-fans/'+name)
(E/'review/fable-review.md').write_text(review['result'],encoding='utf-8')
for name in ['diagnose_kit7_post_load1_vertices.py','diagnose_kit7_post_load1_chords.py','diagnose_kit7_post_load1_nav8_fans.py']:save(R/name,'source/'+name)
save(Path(__file__),'source/'+Path(__file__).name)
save(W/'plans/ev112-kit7-post-load1-diagnostic-20261027.md','source/reviewed-plan.md')
(E/'README.md').write_text('''# Kit7: diferencias de altura dentro de los polígonos

**Diagnóstico local; aún no hay mecanismo de generación ni corrección verificados.**
No se inició DayZ, no se generó ni cambió ninguna malla y no se modificaron límites.
Se reutilizó la reconstrucción empírica archivada; no se creó un decodificador
VAND12 general ni se extrapoló el layout a todo el mapa.

Se ampliaron las superficies empaquetadas a52coordenadas de6modelos. Son48
observaciones de vértices de las mallas8/12m;31tienen Roadway del kit,17no.
Ninguna está bajo el terreno. En las31comparables, la diferencia nav-Roadway es
positiva: 0,0194–0,1200m para8m y0,0110–0,1598m para12m. Los17casos sin Roadway
se conservan con terreno y sus límites. Los5puntos anteriores se reproducen con
la misma implementación, no son un control independiente. Los6controles de
superficie nativa sí son independientes: residuo máximo observado4,0e-7m.

Los seis waypoints Nav12 se reconstruyen con su único triángulo del abanico
geométrico, sin escoger el triángulo por su coincidencia con Y nativa. En los
tres fallos, la descomposición local da:

|Consulta/índice|Error nativo|Diferencia superficie–cuerda|Sesgo interpolado de vértices|
|---|---:|---:|---:|
|piece116left/1|0,856856m|0,993497m|+0,136642m|
|piece116right/1|0,923148m|1,017099m|+0,093951m|
|seam116right/0|0,818588m|0,916121m|+0,097533m|

Los tres casos PASS de Nav12 comparten esta interpolación: errores0,552710,
0,555381 y0,081625m, por debajo del mismo umbral. No se postula otro mecanismo.

La cuerda interpola las superficies conocidas en las XY de los vértices; no es
la superficie real dentro del polígono. La diferencia entre ambas, menos el
sesgo positivo de los vértices, reproduce el error observado. Esto contradice
la explicación simple de vértices hundidos en estos casos y localiza la
aproximación en el interior de esos polígonos. No identifica cómo el generador
selecciona/simplifica polígonos ni qué parámetro lo corrige.

Se contrastó después la geometría8m ya archivada de12teselas, sin nuevo
decodificador binario. Finitud, pertenencia de vértices, límitesXZ y cardinalidad
comprobados. Los seis puntos nativos deNav8 tienen exactamente la mismaXY y
superficie consultada queNav12; su abanico reconstruye Y con residuo máximo
4,1887e-7m. Los tres fallosNav12 quedan en0,004105/0,101196/0,020752m conNav8.
Se conservan dos contraejemplos: piece116right/0 empeora0,555381→0,651269m y
seam116right/1 empeora0,081625→0,711670m. No hay mejora monótona ni predicción
para otra rejilla, y este contraste no resuelveRAM. En cada caso solo había
un triángulo candidato; no se probó una selección entre superficies superpuestas.

Límites: superficies nativas en6waypoints, no en todas las esquinas; otros objetos
no inventariados: en la esquina(9137,9;11268) se usa terreno1,634m al no
haberRoadway conocida; otra superficie omitida alteraría la descomposición.
Detalle local de8/12m, sin cobertura de12,5m ni global. Roadway
aquí es el LOD del kit fluvial; no demuestra carreteras del mapa. No hay ahorro
RAM medido ni base para modificar binarios, subir vértices o probar otro ancho.

La ayuda del generador instalado, verificada por SHA y ejecutada con --console
--help, no muestra controles de refinamiento en su CLI. Esto no prueba que no
existan en otros canales. La [documentación primaria de Bohemia](https://community.bistudio.com/wiki/DayZ:Generating_navigation_mesh)
expone GenParams y recomienda conservar los parámetros de generación salvo el
nombre de archivo y la semilla; no ofrece en esa página un control de detalle
que permita especificar una corrección. Consulta2026-10-27. No se inventa una API.

La triangulación en abanico presupone convexidad, que no se comprueba en este
lector; los residuos la validan solo numéricamente en los seis puntos. El gate
binario no se reejecuta: se hereda del script archivado
[diagnose_kit7_grid_vertices.py](../kit7-nav12-rejected-20261027/scripts/diagnose_kit7_grid_vertices.py),
su JSON por hash y [deployment-parity.json](../kit7-nav8load1-native-20261027/deployment-parity.json),
que liga la malla360a… con la corrida Load1 cerrada. Los puntos nativos proceden
de esa corrida, no de esta reconstrucción. Los tres diagnósticos comparten el
mismo presupuesto de30min de la fase vertex-surfaces; no se reinició el plazo.
publication-errata.json corrige la terminología de límites de los resultados
crudos, que se conservan byte por byte.

La coincidencia entre superficie nativa y empaquetada en los seis puntos
permite interpretar la diferencia de cuerda como una propiedad geométrica local;
no es una medida adicional independiente del lector.

Siguiente gate: verificar una vía para conservar la fidelidad local con menor
coste, mediante definiciones del generador o del formato y un plan nuevo
revisado. El diagnóstico termina INCONCLUSIVE_NO_VERIFIED_MECHANISM; el resultado
local de interpolación no es aceptación. Nav8Load1 mantiene config+607PASS y
RAM incompleto; el council ampliado sigue detrás del trabajo vigente.
''',encoding='utf-8')
p=W/'plans/ev112-kit7-post-load1-diagnostic-20261027.md';old=p.read_text(encoding='utf-8');anchor='Estado: PLAN_REVISADO_SOUND_WITH_FIXES.';assert anchor in old;p.write_text(old.replace(anchor,'Estado: EJECUTADO_DIAGNOSTICO_LOCAL_INCONCLUSO. Evidencia: evidence/navigation/kit7-post-load1-diagnostic-20261027. Se ampliaron52XY; los tres errores Nav12 se descomponen numéricamente dentro de sus polígonos. Mecanismo del generador/control corrector no verificados. Estado del plan aprobado: PLAN_REVISADO_SOUND_WITH_FIXES.',1),encoding='utf-8')
p=W/'HANDOFF.md';old=p.read_text(encoding='utf-8');new=old
updates={'updated':'2026-10-27 (config+607PASS; RAM interrumpido; diagnóstico52XY local completado, mecanismo corrector pendiente)','plan':'plans/ev112-kit7-post-load1-diagnostic-20261027.md ejecutado con diagnóstico local inconcluso. No hay nuevo candidato ni API correctora verificada.','next':'Seguir ACTIVE-WORK.md: definir y revisar una vía verificable que conserve fidelidad local con menor coste; no repetir bloques consumidos ni probar otro ancho a ciegas. Council sigue en cola.','handoff':E.relative_to(W).as_posix()+'/README.md. 52XY/48vértices;31comparables aRoadway con sesgo positivo0.011–0.160m. ErroresNav12 de0.819–0.923m se localizan numéricamente dentro de polígonos; no causa del generador ni ahorro RAM probado.'}
for k,v in updates.items():new,count=re.subn('^'+k+':.*$',lambda _:k+': '+v,new,count=1,flags=re.M);assert count==1,k
assert p.read_text(encoding='utf-8')==old;p.write_text(new,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()};(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(dict(status='LOCAL_VERTEX_CHORD_DIAGNOSTIC_CHECKPOINTED',files=len(manifest))))
