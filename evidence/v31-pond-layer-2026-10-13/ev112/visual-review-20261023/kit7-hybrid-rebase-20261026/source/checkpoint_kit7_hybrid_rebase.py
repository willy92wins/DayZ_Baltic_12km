"""Publishable evidence for the isolated offline correction, never native acceptance."""
from pathlib import Path
import csv,gzip,hashlib,json
import numpy as np
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-hybrid-pilot-20261026';V=R/'kit7-hybrid-rebase-review-20261026'
E=W/'evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-hybrid-rebase-20261026'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
validation=read(O/'validation.json');review=read(V/'review-response.json');report=read(O/'candidate/report.json')
assert validation['status']=='OFFLINE_GUARDS_PASS_PENDING_REVIEW_STAGE_NATIVE'
assert validation['roads']['status']=='PASS' and validation['all_protected_audit']=='PASS'
assert validation['water_merge']['status']=='WATER_FOOTPRINT_EXACT'
assert review['is_error'] is False and not review['permission_denials'] and set(review['modelUsage'])=={'claude-fable-5-1'}
assert (V/'accepted.json').is_file() and read(V/'accepted.json')['status']=='ACCEPTED_OFFLINE_UNIT'
for mapping in [read(V/'accepted.json')['inputs'],read(O/'inputs.json')]:
    for p,h in mapping.items():assert sha(Path(p))==h,p
counts=validation['finding_counts'];assert counts['baseline']=={'native_spike':268,'native_pit':1144,'rectangular_terrain_transition':4}
assert counts['candidate']=={'native_spike':267,'native_pit':1144,'rectangular_terrain_transition':4}
assert report['changed_vertices']==14 and all(report['checks'].values())
E.mkdir(parents=True,exist_ok=False)
def save(p,name):
    raw=p.read_bytes();target=E/(name+'.gz' if len(raw)>250000 else name);target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(gzip.compress(raw,mtime=0) if len(raw)>250000 else raw)
for name in ['inputs.json','receipt.json','validation.json','baseline-shape-screen.json','candidate-shape-screen.json','terrain-comparison.png']:
    save(O/name,name)
for name in ['report.json','all-protected-audit.json']:save(O/'candidate'/name,'candidate/'+name)
for name in ['merge-verification.json','bury-report.json']:save(R/'kit7-hybrid-pilot-merged-20261026'/name,'water/'+name)
save(R/'kit7-hybrid-pilot-roads-20261026/review.json','roads/review.json')
for name in ['source-hashes.json','completion.json','accepted.json','adjudication.md']:save(V/name,'review/'+name)
for p in (V/'reviewed-source').glob('*'):save(p,'review/reviewed-source/'+p.name)
(E/'review/fable-review.md').write_text(review['result']+'\n',encoding='utf-8')
(E/'review/provenance.json').write_text(json.dumps(dict(response_sha256=sha(V/'review-response.json'),modelUsage=review['modelUsage'],is_error=False,permission_denials=[]),indent=2)+'\n')
for name in ['result.json','stdout.log','stderr.log','routing-negative.json','routing-negative.log']:save(R/'kit7-hybrid-rebase-tests-20261026-v2'/name,'tests/'+name)
for name in ['run_kit7_hybrid_pilot.py','test_kit7_hybrid_rebase.py','validate_kit7_hybrid_rebase.py','audit_kit7_hybrid_all.py','merge_kit7_hybrid_relief.py','plot_kit7_hybrid_rebase.py','compare_kit7_existing_hybrid.py','review_kit7_hybrid_rebase.py','accept_kit7_hybrid_rebase.py','test_kit7_hybrid_routing_negative.py','checkpoint_kit7_hybrid_rebase.py']:
    save(R/name,'source/'+name)
save(R/'kit7-existing-hybrid-rebased-diagnostic.json','diagnostic/existing-hybrid.json')
base=R/'river-kit7-merged-byteexact-20261026/terrain-buried.npz';candidate=O/'candidate/terrain.npz'
h0=np.load(base)['heights'];h=np.load(candidate)['heights'];coords=np.argwhere(h!=h0);assert len(coords)==14
with (E/'changed-vertices.csv').open('w',newline='') as f:
    writer=csv.writer(f);writer.writerow(['row','col','x_m','z_m','before_m','after_m'])
    for r,c in coords:writer.writerow([int(r),int(c),int(c*6),int(12282-r*6),float(h0[r,c]),float(h[r,c])])
(E/'README.md').write_text('''# Un pico protegido corregido en candidato aislado

El modo híbrido existente ahora puede trabajar sobre una base nueva, sin
requerir retener un candidato anterior. Se conserva el solver y todos sus
controles. La regresión real reproduce el fallo del modo por cotas y la
solución híbrida, con29tests correctos.

En x1140,z5256 se ajustan14vecinos libres, hasta0,594243m; el ápice queda fijo.
Su prominencia baja a0,299900055m y la energía pura de164,129606 a161,897188.
Las protecciones y coronas se rederivan y verifican; bury no añade cambios,
la huella del agua permanece exacta y pasan77559muestras de carreteras.
El censo completo del candidato pasa de268 a267picos; mantiene1144pozos y
4transiciones rectangulares. Esos hallazgos siguen abiertos.

![Comparación de malla y sección](terrain-comparison.png)

Esto es validación offline de un candidato separado. No cambia el paquete
kit7 que se está generando/probando: allí siguen268picos. No acredita bosque,
composición WRP, compilación, motor, navegación ni inspección visual del
retoque. No se heredan las pruebas nativas del kit7 anterior.
Los CSV, fuentes, fixture y hashes permiten revisar el cambio concreto;
los grandes terrenos NPZ permanecen fuera de Git.
''',encoding='utf-8')
handoff=W/'HANDOFF.md';text=handoff.read_text(encoding='utf-8')
section='''
## Candidato aislado: rebase híbrido1171,190 (26-10-2026)

Ver plans/ev112-rebased-hybrid-relief-20261026.md y evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/kit7-hybrid-rebase-20261026/README.md.
14vecinos corregidos;29tests,coronas,agua,carreteras y censo offlinePASS. Candidato
267picos/1144pozos/4rectángulos, sin aceptación global. NO desplegado ni integrado:
kit7 nativo sigue268picos y su generación/607 no se heredan. Candidato preparado
en E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-hybrid-pilot-merged-20261026.
Faltan bosque,stage,binario y sonda propias antes de integrar esta modificación.
'''
assert '## Candidato aislado: rebase híbrido1171,190' not in text
handoff.write_text(text.rstrip()+'\n'+section,encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in sorted(E.rglob('*')) if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps(dict(status='ISOLATED_OFFLINE_CHECKPOINT',files=len(manifest),bytes=sum(v['bytes'] for v in manifest.values()))))
