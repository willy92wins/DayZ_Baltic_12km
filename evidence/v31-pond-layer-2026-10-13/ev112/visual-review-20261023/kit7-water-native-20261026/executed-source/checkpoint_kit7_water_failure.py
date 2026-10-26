"""Preserve the complete failed native gate without laundering it into acceptance."""
from pathlib import Path
import gzip,hashlib,json,re
R=Path(__file__).parent;O=R/'kit7-water-native-20261026';W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
E=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-water-native-20261026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
f=read(O/'full/result.json');assert f['status']=='FAIL' and f['failure_count']==19 and f['points']==6801 and f['identity_bound'] and f['inputs_unchanged']
assert len(f['failures'])==19 and all(x['site']=='kit-7' for x in f['failures'])
assert all(set(x['why']) <= {'RV bed collision missing/wrong','Bullet margin differs from vanilla >1cm'} for x in f['failures'])
for kind in ('calibration','full'):
 c=read(O/kind/'cleanup.json');assert c['close']['run_retired'] and c['self']['state']=='none' and not c['own_run_present'] and not c['cleanup_degraded'] and not c['pending_commands'] and not c['error'] and not c['cleanup_error']
 assert read(O/kind/'log-capture.json')['sha256']==sha(O/kind/'native.log')
assert read(O/'calibration/result.json')['status']=='FRESH_VANILLA_CALIBRATION_PASS'
E.mkdir(parents=True,exist_ok=False)
def save(p,n):
 raw=p.read_bytes();out=E/(n+'.gz' if len(raw)>250000 else n);out.parent.mkdir(parents=True,exist_ok=True);out.write_bytes(gzip.compress(raw,mtime=0) if len(raw)>250000 else raw)
for n in ('deployment.json','prelaunch.json','accepted.json','points.json','consumer-clock-fix.json','consumer-clock-fix-attempt1.json','consumer-tests.log'):save(O/n,n)
for kind in ('calibration','full'):
 for p in sorted((O/kind).glob('*.json')):save(p,kind+'/'+p.name)
 save(O/kind/'native.log',kind+'/native.log')
 rptroot=O/kind/('after-recovery' if kind=='full' else '.')
 raw=rptroot/'server.RPT';lines=raw.read_text(encoding='utf-8-sig',errors='replace').splitlines()
 assert any('Termination successfully completed' in s for s in lines)
 diag=dict(rpt_sha256=sha(raw),binding=read(rptroot/'rpt-binding.json'),termination_marker=True,diagnostics=[s for s in lines if '(E):' in s or '(W):' in s],note='Filtered original RPT; no raw command line publication.')
 (E/kind/'rpt-diagnostics.json').write_text(json.dumps(diag,indent=2)+'\n')
V=R/'kit7-water-review-20261026'
for name in ('source-hashes.json','review-brief.md','completion.json'):save(V/name,'review/'+name)
rev=read(V/'review-response.json');(E/'review/fable-review.md').write_text(rev['result']+'\n',encoding='utf-8')
(E/'review/provenance.json').write_text(json.dumps(dict(response_sha256=sha(V/'review-response.json'),modelUsage=rev['modelUsage'],is_error=rev['is_error'],permission_denials=rev.get('permission_denials')),indent=2)+'\n')
names=['prepare_kit7_water_native.py','accept_kit7_water_native.py','capture_kit7_water_log.ps1','capture_owned_server_identity.ps1','copy_owned_server_rpt.ps1','finish_kit7_water_survey.js','consume_kit7_water_native.py','consume_kit7_water_native_v2-attempt1.py','consume_kit7_water_native_v2.py','screen_kit7_water_controls.py','screen_kit7_contact_controls.py','replay_kit7_water_regression.py','diagnose_kit7_native_contacts.py','checkpoint_kit7_water_failure.py']
for name in names:save(R/name,'executed-source/'+name)
for name in ['kit7-water-controls-discovery-20261026.json','kit7-contact-controls-discovery-20261026.json','kit7-regression-replay-20261026.json']:save(R/name,'discovery/'+name)
for p in (R/'kit7-native-contact-diagnosis-20261026').glob('*.json'):save(p,'diagnosis/'+p.name)
save(W/'missions/BalticVisualProbeV1.BalticTrial/init.c','producer/full/init.c')
save(Path(read(O/'deployment.json')['missions']['calibration'])/'init.c','producer/calibration/init.c')
body="""# Kit7 — sonda completa: 19 fallos de contacto
La prueba nativa del 26 de octubre mide **6.801 puntos** y devuelve **FAIL**.
La calibración nueva mide0,039991446m de margen vanilla con5aciertos y289controles
vacíos. Las4.749muestras de regresión F pasan; los19fallos están en el kit7 nuevo.

No fallan agua,terreno ni Roadway. En18puntos RV atraviesa el lecho y alcanza
el terreno aunque Bullet detecta el modelo; en otro, RV alcanza una cara
11,7mm inferior a la superior detectada por Bullet. Todos19coinciden con
vértices exactos del ODOL a la pose usada. Es un candidato de precisión en
bordes compartidos, **no una causa interna del motor demostrada**.

Se conservan los logs completos, expectativas congeladas, calibración,
paquetes, identidad run/PID/creación, revisión Fable y fuentes ejecutadas.
El consumidor no relaja criterios para hacer pasar la prueba.

La reserva MCP caducó al pausar el coordinador durante el contexto; el productor
terminó6801puntos. Se re-adoptó el mismo run/PID, se verificó la identidad
y se cerró oficialmente sin relanzarlo. El primer cleanup fallido queda
preservado junto al recibo de recuperación. Estado final propio: lease libre,
cero comandos pendientes y ninguna limpieza degradada.

Siguiente: candidato aislado de solape local de1,95mm en Geometry de19modelos,
con revisión y gates de cobertura,coste,poses y motor. No cambiar muestras.
La navmesh del kit7 espera al gate físico. Ningún PASS visual,cliente,FPS
o global se deriva de esta sonda.
"""
(E/'README.md').write_text(body,encoding='utf-8')
p=W/'HANDOFF.md';s=p.read_text(encoding='utf-8');(O/'handoff-before-water-checkpoint.md').write_text(s,encoding='utf-8')
updates={'updated':'2026-10-26 (sonda6801terminada:19fallosRV/Bullet enkit7; correcciónlocal encurso)','plan':'Unidad agua nativa terminada FAIL19/6801; seguir plans/ev112-kit7-rv-contact-20261026.md antes de navegación. Alturas/frontera previas PASS muestreado conservadas.','blocker':'19contactoskit7 fallan;18RV atraviesan hasta terreno y uno alcanza cara inferior. Agua/terreno/Roadway y4749F sin fallos. Navkit7 condicionada a corrección. Otros38/48/71/79 soportes,98/67protegidos,01545/60m y vista global siguen abiertos.','next':'Solape Geometry local19modelos, conservar182ODOL+config y mundo exactos; overlay/ODOL/poses/coste antes de calibración y repetir6801sin cambios.','cleanup':'Sonda6801completa; lease expirado recuperado adoptando mismoPID56116/run28ea0f2f. Cierre oficial retirado,selfnone,pending0,cleanup[]. Sincliente. Consultar estado vivo antes de lanzar.','handoff':str(E.relative_to(W)).replace('\\','/')+'/README.md; kit7-native-20261026 conserva alturas/frontera aprobadas.'}
for k,v in updates.items():s,n=re.subn('^'+k+':.*$',lambda m:k+': '+v,s,count=1,flags=re.M);assert n==1
p.write_text(s,encoding='utf-8')
p=W/'README.md';s=p.read_text(encoding='utf-8');old='Agua/colisión propia y navegación\nsiguen pendientes.';assert old in s;s=s.replace(old,'La sonda de agua/colisión mide6.801puntos: detecta19fallos de contacto del kit7,\nya localizados para corregir; navegación y vista conjunta siguen pendientes.');p.write_text(s,encoding='utf-8')
p=W/'bugs.md';s=p.read_text(encoding='utf-8');old='agua/física, navegación y vista propias pendientes.';assert old in s;s=s.replace(old,'sonda6801con19fallos de contacto kit7 (agua/terreno/Roadway sin fallos), navegación y vista propias pendientes.',1);p.write_text(s,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()};(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
p=R/'ACTIVE-WORK.md';old=p.read_text(encoding='utf-8');p.write_text('# ESTADO ACTUAL — kit7 física FAIL19, 26-10-2026\n\nCell87 terminó por lease_expired; run28ea0f2f completó6801 y se re-adoptó/cerró oficialmente, selfnone/pending0/cleanup[]. NO está activo. Resultado FAIL19soloRV/Bullet kit7, revisión Fable del plan de solape local en curso: kit7-rv-contact-review-20261026. Candidato aún no ejecutado. Navegación borrador bloqueada por gate físico. Evidencia W/'+str(E.relative_to(W)).replace('\\','/')+'.\n\n## Historia\n'+old,encoding='utf-8')
print(json.dumps(dict(status='FAILED_GATE_PRESERVED',files=len(manifest),bytes=sum(v['bytes'] for v in manifest.values()))))

