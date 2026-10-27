from pathlib import Path
import hashlib,json,re
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav-payload-cost-20261027-v2'
E=W/'evidence/navigation/kit7-nav-payload-cost-20261027'
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def sha(p):
 with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not E.exists()
result=read(D/'result.json');controls=read(D/'controls.json')
assert controls['status']=='PASS_CENSUS_CONTROLS' and controls['tests']==9
assert controls['source_sha256']==result['script_sha256']==sha(R/'census_kit7_nav_payload_cost.py')
assert all(sum(a['accounting'].values())==a['bytes'] for a in result['artifacts'])
review=read(R/'kit7-joint-height-ram-next-review-20261027/response.json')
assert not review['is_error'] and not review.get('permission_denials') and 'claude-fable-5-1' in review['modelUsage']
planreview=R/'kit7-config-types-plan-review-20261027'
assert read(planreview/'adjudication.json')['status']=='ACCEPTED_AFTER_REVIEW'
E.mkdir(parents=True)
def save(p,name):
 dest=E/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
for name in ('result.json','controls.json','waypoint-populations.json'):save(D/name,name)
for name in ('census_kit7_nav_payload_cost.py','test_kit7_nav_payload_cost.py','review_kit7_joint_height_ram_next.py','review_kit7_config_types_plan.py'):
 save(R/name,'source/'+name)
for name in ('failed-source.py','failure.json'):save(R/'kit7-nav-payload-cost-20261027'/name,'rejected-attempt/'+name)
for folder,prefix in [('kit7-joint-height-ram-next-review-20261027','next-step'),('kit7-config-types-plan-review-20261027','config-plan')]:
 for name in ('fable-review.md','adjudication.md','adjudication.json','source-hashes.json','completion.json'):
  if (R/folder/name).exists():save(R/folder/name,'reviews/'+prefix+'/'+name)
save(Path(__file__),'source/'+Path(__file__).name)
table=[]
for a in result['artifacts']:
 table.append(f"|{a['label']}|{a['tiles']}|{a['zero_polygon_tiles']}|{a['one_polygon_tiles']}|{a['bytes']}|")
(E/'README.md').write_text('''# Censo del coste serializado de navegación

Lectura de los cuatro NM reales por SHA256. **Diagnóstico, no optimización ni
perfil de memoria del proceso.** No se ha cambiado el mapa, el NM, los PBO ni
ninguna tolerancia. No se ha iniciado DayZ en esta unidad.

|Malla|Teselas|Con cero polígonos|Con un polígono|Bytes totales|
|---|---:|---:|---:|---:|
'''+ '\n'.join(table)+'''

Nav8 tiene un84,62% de teselas de un polígono. No hay teselas declaradas vacías
que justifiquen una poda. La contabilidad por prefijos y resto de payload
cuadra con el tamaño de cada archivo, pero no revela las asignaciones del
heap ni predice cuánto ahorraría una variante. Los totales de polígonos y
vértices coinciden con inspectores archivados; nueve controles positivos y
negativos pasan. La primera tentativa rechazó una suposición incorrecta de
orden de coordenadas; se conserva y se sustituyó por unicidad y cobertura.

Fable confirmó el censo y señaló que otro ancho aún carece de discriminador.
Su propuesta de regla por esquinas queda sin adoptar: un éxito retrospectivo
no la haría oráculo y su fallo no demostraría que todo ancho es inviable.
Además, el censo real contiene1255/1257/1248waypoints para8/12/12,5m; varias
rutas tienen3–16puntos. No son simplemente607rutas de dos extremos.

La siguiente sonda propuesta comprueba una diferencia real de configuración:
Baltic declara dos flags como texto "true" y Chernarus como número1. Solo se
observarán sus getters nativos sobre el Nav8 intacto. Una diferencia numérica
no probará cómo consume esos campos el cargador ni que cause el excesoRAM.
El plan está revisado; implementación y prueba nativa siguen pendientes.

Nav8 conserva607PASS de altura y FAILRAM. El original12,5 conservaPASSRAM y
cuatroFAILaltura. Nav12 conserva tresFAILaltura. El council ampliado sigue
en cola; este trabajo es el diagnóstico del pendiente actual.
''',encoding='utf-8')
p=W/'HANDOFF.md';old=p.read_text(encoding='utf-8');new=old
updates={'updated':'2026-10-27 (Nav8 funcional; RAM pendiente; censo de payload y plan de lectura de config revisados)', 'plan':'plans/ev112-kit7-native-config-types-20261027.md. Sonda de getters sobre Nav8 intacto; plan revisado, implementación y ejecución pendientes. No nueva generación.', 'next':'Implementar y revisar la sonda de nueve lecturas de configuración nativa; FIFO directo solo al estar preparada. No atribuir RAM al tipo string sin aislar el consumidor. Mantener607PASS y .801/.011/2.1; council ampliado después.', 'cleanup':'Sin run DayZ ni lease nuevo en el diagnóstico de payload. Runs anteriores cerrados. Seguimiento de pendientes y council ampliado ACTIVE, actualizado por petición27-10.', 'handoff':E.relative_to(W).as_posix()+'/README.md; contraste Chernarus y resultados Nav8/Nav12/original12,5 preservados.'}
for key,value in updates.items():new,count=re.subn('^'+key+':.*$',lambda _:key+': '+value,new,count=1,flags=re.M);assert count==1,key
assert p.read_text(encoding='utf-8')==old;p.write_text(new,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='COST_DIAGNOSTIC_CHECKPOINTED',files=len(manifest))))
