"""Checkpoint the observed contact-repair outcome, preserving all failed gates."""
from pathlib import Path
import gzip,hashlib,json,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-overlap-native-20261026';E=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-contact-repair-20261026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=read(O/'full/result.json');assert f['points']==6801 and f['identity_bound'] and f['inputs_unchanged']
assert f['status'] in ('SERVER_PROBE_PASS','FAIL')
passed=f['status']=='SERVER_PROBE_PASS';assert passed==(f['failure_count']==0)
for kind in ('calibration','full'):
 c=read(O/kind/'cleanup.json');assert c['close']['run_retired'] and c['self']['state']=='none' and not c['own_run_present'] and not c['cleanup_degraded'] and not c['pending_commands'] and not c['error'] and not c['cleanup_error']
 assert read(O/kind/'log-capture.json')['sha256']==sha(O/kind/'native.log')
assert read(O/'calibration/result.json')['status']=='FRESH_VANILLA_CALIBRATION_PASS'
for p,h in read(O/'accepted.json')['inputs'].items():assert sha(Path(p))==h,p
E.mkdir(parents=True,exist_ok=False)
def save(p,n):
 raw=p.read_bytes();out=E/(n+'.gz' if len(raw)>250000 else n);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(gzip.compress(raw,mtime=0) if len(raw)>250000 else raw)
for n in ('deployment.json','prelaunch.json','accepted.json','points.json'):save(O/n,n)
for kind in ('calibration','full'):
 for p in sorted((O/kind).glob('*.json')):save(p,kind+'/'+p.name)
 save(O/kind/'native.log',kind+'/native.log')
 raw=O/kind/'server.RPT';lines=raw.read_text(encoding='utf-8-sig',errors='replace').splitlines()
 assert any('Termination successfully completed' in s for s in lines)
 diag=dict(rpt_sha256=sha(raw),binding=read(O/kind/'rpt-binding.json'),termination_marker=True,diagnostics=[s for s in lines if '(E):' in s or '(W):' in s],note='Filtered original RPT; raw launch command retained locally only.')
 (E/kind/'rpt-diagnostics.json').write_text(json.dumps(diag,indent=2)+'\n')
for folder,label in [('kit7-contact-only-review-20261026','contact-review'),('kit7-binary-comparator-review-20261026','comparator-review')]:
 V=R/folder
 for name in ('source-hashes.json','review-brief.md','completion.json'):
  save(V/name,label+'/'+name)
 if (V/'accepted.json').exists():save(V/'accepted.json',label+'/accepted.json')
 rev=read(V/'review-response.json');(E/label/'fable-review.md').write_text(rev['result']+'\n',encoding='utf-8')
 (E/label/'provenance.json').write_text(json.dumps(dict(response_sha256=sha(V/'review-response.json'),modelUsage=rev['modelUsage'],is_error=rev['is_error'],permission_denials=rev.get('permission_denials')),indent=2)+'\n')
for folder in ['kit7-contact-only-build-20261026','kit7-contact-only-negative-controls-20261026']:
 for p in sorted((R/folder).glob('*')):
  if p.is_file() and p.suffix in ('.json','.log'):save(p,'offline/'+folder+'/'+p.name)
for name in ['author-report.json','overlap-report.json','binary-review.json','compiled-contact-review.json','records.json']:
 save(R/'river-kit7-contact-only-20261026'/name,'candidate/'+name)
save(R/'package-kit7-contact-only-20261026/verification.json','package-verification.json')
for name in ['kit7-contact-only-discovery.json','kit7-native-contact-diagnosis-20261026/neighbours.json']:
 save(R/name,'discovery/'+Path(name).name)
for name in ['discover_kit7_contact_only.py','screen_kit7_contact_neighbours.py','build_kit7_contact_only.py','verify_kit7_contact_only_compiled.py','package_kit7_contact_only.py','package_kit7_contact_only_v2.py','test_kit7_non_geometry_comparator.py','test_kit7_non_geometry_comparator_v2.py','test_kit7_contact_only_refusals.py','accept_kit7_contact_only.py','prepare_kit7_contact_only_native.py','seal_kit7_overlap_native.py','consume_kit7_overlap_native.py','capture_kit7_water_log.ps1','capture_owned_server_identity.ps1','copy_owned_server_rpt.ps1','finish_kit7_overlap_survey.js','checkpoint_kit7_contact_repair.py']:
 save(R/name,'executed-source/'+name)
# Rejected experiments are evidence only, never deployment candidates.
for folder in ['kit7-rv-overlap-build-20261026','kit7-rv-capped-build-20261026']:
 for p in (R/folder).glob('*.json'):save(p,'rejected/'+folder+'/'+p.name)
for p in (R/'discarded-cap-experiment-20261026').glob('*'):
 if p.is_file():save(p,'rejected/partition-source/'+p.name)
for kind,path in read(O/'deployment.json')['missions'].items():save(Path(path)/'init.c','producer/'+kind+'/init.c')
outcome='PASS: 6.801 puntos, cero fallos' if passed else f"FAIL: {f['failure_count']} fallos en 6.801 puntos"
body=f"""# Kit7 — reparación localizada de colisión

Resultado nativo: **{outcome}**. Calibración fresca:0,039991446m,
5aciertos vanilla y289controles vacíos. Se mantienen las mismas6801muestras,
productores y tolerancias de la sonda anterior que falló19contactos.

Solo cambia Geometry de19modelos. Las otras182piezas yconfig son byteexact;
las139poses son idénticas. Componentes8623→8623;caras263552→265384(+0,695%);
vértices149022→149938. Máximo por componente72vértices/140caras.
Solape horizontal local de1/512m, conservando las seis cotas de bbox exactas.
El overlay completo de fuente y compilado pasa con los umbrales originales.

Los LOD fuente ajenos aGeometry son byteexact. Para el compilado se comparan
todos los campos decodificados: Roadway conserva caras orientadas, multiplicidad,
vértices y etiquetas de superficie; solo se canoniza el orden de caras/secciones.
Los campos desconocidos que el reader descarta no quedan cubiertos.
El comparador rechaza seis mutaciones locales, LOD ausente, resolución cambiada
yNaN con payload distinto. La revisión Fable y su corrección de tests se conservan.

Dos candidatos anteriores quedan rechazados: anclas que excedían el coste y
anclas con exceso horizontal0,019326562m². La variante final elimina esas anclas
innecesarias; no usa la partición experimental archivada. No se relajó ningún gate.

La coincidencia original de los19fallos con vértices compartidos es evidencia
de localización. El mecanismo interno de precisión del motor sigue siendo hipótesis.
No se deriva aceptación visual, navegación, actor, rendimiento ni calidad global.
El censo de terreno conserva268picos,1144depresiones y4transiciones pendientes.

Ambos runs propios quedaron cerrados oficialmente, sin cliente, sin comandos
pendientes ni limpieza degradada. Paquete piloto3d9550bf; mundo10e09e3f sin cambios.
"""
(E/'README.md').write_text(body,encoding='utf-8')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8');(O/'handoff-before-checkpoint.md').write_text(s,encoding='utf-8')
updates={
 'updated':f'2026-10-26 (reparación contacto kit7: {outcome})',
 'plan':('Física kit7 corregida y repetida PASS6801. Siguiente navegación propia según plans/ev112-kit7-navmesh-generation-20261026.md.' if passed else f"Repetición kit7 FAIL{f['failure_count']}/6801; continuar diagnóstico antes de navegación."),
 'next':('Revisión/manifest final del coordinador y generación NM9 kit7; después estructura, paquete exacto y rutas propias.' if passed else 'Diagnosticar únicamente los fallos restantes sin cambiar muestras ni umbrales. Navegación sigue bloqueada.'),
 'cleanup':'Calibración y repetición6801 cerradas oficialmente, selfnone,pending0,cleanup[]. Sin cliente. Consultar estado vivo antes de lanzar.',
 'deployed':'P:/Mods/@DayZ_Baltic_EV112_Kit7Overlap: mundo10e09e3f,piloto3d9550bf,agua97edcafe; paquete anterior Kit7Native preservado. NMpropia pendiente.',
 'handoff':E.relative_to(W).as_posix()+'/README.md; evidencia previa conservada.',
 'blocker':('Contactos kit7 corregidos con sonda propia PASS. ' if passed else f"Persisten{f['failure_count']}contactos kit7. ")+'Navkit7/vista pendientes; otros38/48/71/79 soportes,98/67protegidos,01545/60m y censo global abiertos.'}
for k,v in updates.items():s,n=re.subn('^'+k+':.*$',lambda m:k+': '+v,s,count=1,flags=re.M);assert n==1
p.write_text(s,encoding='utf-8')
p=W/'README.md';s=p.read_text(encoding='utf-8');old='La sonda de agua/colisión mide6.801puntos: detecta19fallos de contacto del kit7,\nya localizados para corregir; navegación y vista conjunta siguen pendientes.'
assert old in s
new=('La corrección de colisión del kit7 supera los6.801puntos de la sonda nativa,\nsin cambiar muestras ni umbrales; navegación propia y vista conjunta siguen pendientes.' if passed else f"La corrección localizada del kit7 reduce los fallos de contacto a{f['failure_count']} en6.801puntos;\nla comprobación sigue abierta junto a navegación y vista conjunta.")
p.write_text(s.replace(old,new),encoding='utf-8')
p=W/'bugs.md';s=p.read_text(encoding='utf-8');old='sonda6801con19fallos de contacto kit7 (agua/terreno/Roadway sin fallos), navegación y vista propias pendientes.';assert old in s
new=('reparación local19Geometry y repetición6801PASS, navegación y vista propias pendientes.' if passed else f"reparación local19Geometry, repetición6801con{f['failure_count']}fallos; navegación y vista propias pendientes.")
p.write_text(s.replace(old,new,1),encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='OBSERVED_CONTACT_REPAIR_CHECKPOINT',native_status=f['status'],failure_count=f['failure_count'],files=len(manifest),bytes=sum(v['bytes'] for v in manifest.values()))))

