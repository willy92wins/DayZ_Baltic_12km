from pathlib import Path
import hashlib,json,re
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'package-kit7-nav8-onload-20261027';X=R/'kit7-onload-package-execution-20261027';V=R/'kit7-onload-package-code-review-20261027'
E=W/'evidence/navigation/kit7-nav8-onload-package-20261027'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def save(p,name):
 target=E/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(p.read_bytes())
assert not E.exists()
v=read(D/'verification.json');assert v['status']=='PASS_ISOLATED_NAV8_ONLOAD_CONFIG_PACKAGE' and v['unchanged_entries']==6826 and v['changed_entries']==['config.bin'] and v['null_roundtrip_byte_equal'] and v['native_type_verified'] is False
assert v['pbo_sha256']==sha(D/'Addons/narva_trial.pbo')
assert read(X/'completion.json')==dict(returncode=0,inputs_unchanged=True,scope='OFFLINE_ONLY_NOT_DEPLOYED')
for p,h in read(X/'frozen.json')['inputs'].items():assert sha(p)==h,p
E.mkdir(parents=True)
for name in ('verification.json','original.cpp','noop-source.cpp','noop.cpp','config.cpp','roundtrip.cpp','packed-config.cpp','compile-noop.log','compile.log','decode-original.log','decode-noop.log','decode-candidate.log','decode-packed.log','filebank.log'):save(D/name,name)
for name in ('completion.json','frozen.json','test_nav8_onload_config_ev112.py.stderr.log','test_nav8_onload_package_contract.py.stderr.log'):save(X/name,'execution/'+name)
for name in ('fable-review.md','adjudication.md','adjudication.json','completion.json','source-hashes.json','reviewed-packager.py'):save(V/name,'review/'+name)
for name in ('build_kit7_nav8_onload.py','review_kit7_onload_package_code.py'):save(R/name,'source/'+name)
save(W/'plans/ev112-kit7-onload-numeric-pilot-20261027.md','source/reviewed-plan.md')
save(Path(__file__),'source/'+Path(__file__).name)
(E/'README.md').write_text('''# Nav8Load1: paquete experimental aislado

**PASS offline de empaquetado; motor y RAM pendientes.** Cambia solo
filterIsolatedIslandsOnLoad de texto"true" al literal1. El tipo nativo todavía
no se afirma: requiere ConfigGetType0 y texto/int/float1 en el motor.
GenParams y tileWidth8 permanecen. No se regenera navegación.

- Mundo candidatoSHA f0e0e6b99da08b48f62ee47fa72b8905a5c9843bee4a30cefa18f517ddb1f603.
- NM360a7348… y WRP0da63d3f… idénticos a Nav8;6826entradas preservadas bytea byte.
- Solo cambia config.bin. Propiedades PBO idénticas; config final reextraído
  y decodificado de nuevo, delta independiente de un único token en clase exacta.
- Control nulo por la misma escrituraPython+CfgConvert: binoriginal idéntico.
-14tests deconfig/fixture real y12contratos de contenedorPASS. Estos últimos
  usan herramientas externas simuladas; la paridad real se prueba en el build.
- Revisión independiente Fable5.1 integrada; preservados informe y código revisado.

Paquete local en E:/DayZ-Baltic-Build/shape-repair-20261025/package-kit7-nav8-onload-20261027.
No se publica el PBO ni se sustituye Nav8. Todavía no está desplegado.
Próximo paso: preparar despliegue nuevo con relectura de entradas desde destino
más sonda deconfig+607 y revisión operativa. Solo si pasa, seis mediciones RAM
NUEVAS contraChernarus. Ningún PASS offline concede aceptación de navegación,
memoria, actores ni cobertura global. Nav8 original conserva607PASS/RAMFAIL.
''',encoding='utf-8')
p=W/'plans/ev112-kit7-onload-numeric-pilot-20261027.md';old=p.read_text(encoding='utf-8');assert 'Código nuevo aún pendiente de revisión.' in old
p.write_text(old.replace('Código nuevo aún pendiente de revisión.','Empaquetador revisado y paquete offlinePASS; despliegue y código de sonda/RAM\naún pendientes. Evidencia evidence/navigation/kit7-nav8-onload-package-20261027.'),encoding='utf-8')
p=W/'HANDOFF.md';old=p.read_text(encoding='utf-8');new=old
updates={'updated':'2026-10-27 (Nav8 funcional/RAM abierto; sonda flags completa; Nav8Load1 empaquetado offline y sin desplegar)','plan':'plans/ev112-kit7-onload-numeric-pilot-20261027.md. Solo OnLoad literal1, mismo NM; revisión de plan y empaquetador integradas. Paquete f0e0e6b9… offlinePASS. Sonda/RAM pendientes.','next':'Preparar despliegue aislado @DayZ_Baltic_EV112_Kit7Nav8Load1 y revisión de sonda config+607. Releer PBO destino; no lanzar hasta sellar. Si607PASS, RAMABBAAB nuevo contraChernarus.','handoff':E.relative_to(W).as_posix()+'/README.md; diagnóstico de getters y estados Nav8/Nav12/original12,5 preservados.'}
for key,value in updates.items():new,count=re.subn('^'+key+':.*$',lambda _:key+': '+value,new,count=1,flags=re.M);assert count==1,key
assert p.read_text(encoding='utf-8')==old;p.write_text(new,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='ONLOAD_PACKAGE_CHECKPOINTED',files=len(manifest))))
