from pathlib import Path
import json, hashlib, shutil
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
ROOT=Path('E:/DayZ-Baltic-Build')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=json.loads((ROOT/'v30-native-cap-profile-20261009/authoring.json').read_text())
failures=[dict(features=r['features'],before=r['before'],after=r['after'],retained_area=r['area_after_m2']/r['area_before_m2']) for r in rows['reports']]
assert all(r['after']['p90_degrees']>r['before']['p90_degrees'] and r['after']['max_degrees']>r['before']['max_degrees'] for r in failures)
(ROOT/'v30-native-cap-profile-20261009/adjudication.json').write_text(json.dumps(dict(status='REJECTED_SHAPE_REGRESSION_NOT_DEPLOYED',candidate_sha256=sha(ROOT/'v30-native-cap-profile-20261009/candidate/terrain.npz'),failures=failures,reason='The native contour consumer rejects every target. No global acceptance or package attempted.'),indent=2)+'\n')
exact=json.loads((ROOT/'v30-hydro-design-census-20261009/exact-sections.json').read_text())
assert exact['counts']=={'EXACT_DRY_CONFIRMED':45,'SAMPLED_FALSE_ALARM_WATER_PRESENT':4} or exact['counts']=={'SAMPLED_FALSE_ALARM_WATER_PRESENT':4,'EXACT_DRY_CONFIRMED':45}
unprotected=[r for r in exact['rows'] if r['original_gap']['attribution']=='UNATTRIBUTED']
assert len(unprotected)==3 and all(r['physical_dry_sections']==0 for r in unprotected)
(ROOT/'v30-stream-connectivity-repair-20261009/adjudication.json').write_text(json.dumps(dict(status='WITHDRAWN_FALSE_ALARM_NO_PRODUCTION_CHANGE',candidate_sha256=sha(ROOT/'v30-stream-connectivity-repair-20261009/candidate/terrain.npz'),reason='Exact native polygon sections find water between the discrete lateral samples. The seven-vertex lowering has no confirmed defect to fix.',exact_adjudication_sha256=sha(ROOT/'v30-hydro-design-census-20261009/exact-sections.json')),indent=2)+'\n')
specs=[('v30-hydro-design-census-20261009','v30-hydro-design-census-2026-10-09',['census.py','census.json','attribute.py','attribution.json','exact_sections.py','exact-sections.json','preserve_checkpoint.py'],'''# EV36 — censo no visual de cauces de diseño

77 cursos construidos, 101.602 estaciones a 1 m. El primer muestreo lateral señaló 49 intervalos; la intersección exacta con los triángulos nativos confirma 45 y retira cuatro falsos positivos, incluidos los tres sin protección. La anchura mínima de esos tres es 1,1171 / 0,5561 / 0,9466 m. Una prueba adversaria demuestra el aliasing del muestreo lateral.

Los 45 intervalos restantes tocan reservas viales o plataformas. Presencia de una reserva no prueba por sí sola causalidad ni autoriza cortar carreteras: se conserva el inventario. Estas secciones no acreditan conectividad longitudinal ni render. Los 19 corredores navegables conservan su comprobación separada EV18.

stream_0431 tiene tier1500, excluido por el constructor (mínimo2500), igual que0452/0456. No es un remate perdido ni pendiente de reparación.
'''),('v30-stream-connectivity-repair-20261009','v30-stream-connectivity-repair-2026-10-09',['plan.md','author.py','authoring.json','delta.npz','adjudication.json'],'''# EV37 — propuesta retirada: no había hueco demostrado

La propuesta bajaba siete vértices hasta 5,5 cm. EV36 exacto demuestra que sus dos alarmas eran aliasing del muestreo. Se retira sin construir ni desplegar. No es una reparación conseguida.
'''),('v30-native-cap-profile-20261009','v30-native-cap-profile-2026-10-09',['plan.md','author.py','authoring.json','delta.npz','adjudication.json'],'''# EV38 — reprofilado de remates rechazado

68 vértices, un cambio de clase. El contorno nativo empeora p90 y máximo en Msta, Nazia y Volkhov; Nazia pierde además un 31 % del área local. No se empaqueta ni integra. Candidato y hash retenidos en scratch, delta reproducible preservado. No se abre una segunda variante de radios o cotas.
''')]
for source,name,files,note in specs:
    src=ROOT/source;dest=W/'evidence'/name;dest.mkdir(exist_ok=False)
    manifest=[]
    for name in files:
        shutil.copy2(src/name,dest/name);assert sha(src/name)==sha(dest/name)
        manifest.append(dict(path=name,sha256=sha(dest/name)))
    (dest/'README.md').write_text(note,encoding='utf-8')
    (dest/'manifest.json').write_text(json.dumps(dict(source=str(src),files=manifest),indent=2)+'\n')
print('EV36 exact census preserved; EV37 withdrawn; EV38 rejected. No production changes.')
