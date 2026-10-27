"""Preserve a rejected Nav12 experiment and read-only diagnosis."""
from pathlib import Path
import gzip,hashlib,json
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
D=R/'kit7-nav12-consumer-20261027';G=R/'nav-kit7-12m-preparation-20261027';N=R/'navmesh-kit7-12m-v9-20261027';P=R/'package-kit7-nav12-v9-20261027'
E=W/'evidence/navigation/kit7-nav12-rejected-20261027'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    with Path(p).open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
assert not E.exists()
result=read(D/'result.json');comparison=read(D/'height-comparison.json')
assert result['status']==comparison['status']=='FAIL_KIT7_NATIVE_GRAPH'
assert len(result['cases'])==607 and len(result['height_issues'])==3 and not result['local_failures']
assert read(D/'identity-verification.json')['status']=='PASS_BOUND_NATIVE_PROBE_INPUTS'
clean=read(D/'cleanup.json')
assert clean['close']['run_retired'] and clean['close']['graceful'] and clean['self']['state']=='none'
assert not clean['own_run_present'] and not clean['cleanup_error'] and not clean['error'] and not clean['cleanup_degraded'] and clean['pending_commands']==0
assert read(G/'completion.json')['status']=='GENERATION_STAGE_COMPLETE_PENDING_VALIDATION'
assert read(G/'budget-verification.json')['status']=='PASS_PERSISTED_GENERATION_BUDGET'
assert read(N/'inspection.json')['status']=='EMPIRICAL_V9_PREFIX_AND_COVERAGE_PASS'
package=read(P/'verification.json');assert package['status']=='PASS_NAVMESH_PACKED_BYTE_PARITY' and package['original_entries_unchanged']==6826
for p,h in read(D/'deployment.json')['inputs'].items():assert sha(p)==h,p
assert (D/'queries.csv').read_bytes()==(R/'kit7-nav-consumer-20261026/queries.csv').read_bytes()
E.mkdir(parents=True)
def save(p,name):
    raw=p.read_bytes();compressed=len(raw)>250000
    dest=E/(name+'.gz' if compressed else name);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(gzip.compress(raw,mtime=0) if compressed else raw)
for label,base in [('runtime',D),('generation',G)]:
    for p in base.rglob('*'):
        if p.is_file() and p.suffix in {'.json','.jsonl','.log','.csv','.js'} and 'synthetic-controls' not in p.parts and '-before-lifecycle.' not in p.name:
            save(p,label+'/'+p.relative_to(base).as_posix())
for name in ('generation.json','inspection.json'):save(N/name,'generation/native/'+name)
for name in ('verification.json','deployment.json'):save(P/name,'package/'+name)
for name in ('compare_kit7_nav12_results.py','checkpoint_kit7_nav12_rejected.py'):save(R/name,'scripts/'+name)
folders=['kit7-nav12-height-diagnostic-20261027','kit7-nav12-layer-diagnostic-20261027','kit7-nav12-tile-diagnostic-20261027','kit7-nav12-height-reconstruction-20261027','kit7-nav-after12-screen-20261027','kit7-nav-detail-census-20261027','kit7-grid-vertex-diagnostic-20261027','kit7-corner-faces-20261027']
for folder in folders:save(R/folder/'result.json','diagnostics/'+folder+'.json')
for name in ('diagnose_kit7_nav12_heights.py','diagnose_kit7_nav12_layers.py','inspect_kit7_nav12_failed_tiles.py','reconstruct_kit7_nav12_height.py','plan_kit7_nav_after12.py','census_kit7_nav_detail.py','diagnose_kit7_grid_vertices.py','diagnose_kit7_corner_faces.py'):save(R/name,'scripts/'+name)
review=read(R/'kit7-after-nav12-review-20261027/response.json');assert not review['is_error'] and 'claude-fable-5-1' in review['modelUsage']
(E/'review').mkdir();(E/'review/fable.md').write_text(review['result']+'\n',encoding='utf-8')
for n in ['source-hashes.json','completion.json']:save(R/'kit7-after-nav12-review-20261027'/n,'review/'+n)
save(W/'plans/ev112-kit7-navv9-ram-diagnostic-20261027.md','review/reconciled-plan.md')
(E/'README.md').write_text('''# Nav12 rechazado: tres fallos nuevos de altura

La generación y la sonda nativa terminaron con identidad y cierre verificados.
Las607 consultas conservan coordenadas y tolerancias. Nav12 corrige las cuatro
alturas originales, pero introduce estos errores contra el límite0,801 m:

- piece116left:0,856856 m.
- piece116right:0,923148 m.
- seam116right:0,818588 m.

Las562 continuidades y ocho testigos F pasan. Resultado global de la sonda:
FAIL_KIT7_NATIVE_GRAPH. RAM12 no ejecutada por este fallo. No usar como solución.

Los polígonos del NM reproducen las seis alturas nativas con error inferior a
5,65e-7 m. Visual,Geometry y Roadway coinciden en los waypoints fallidos; la
aproximación del NM explica sus alturas. No se ha aislado la decisión interna
del generador. El estimador de dos diagonales no predice aceptación.

En el vértice diagnóstico(9132,11280), el máximo visual es agua. Su grava visual
y Roadway coinciden a1,91014218 m y Geometry a1,90833567 m. No se identificó
un defecto de grava que permita una corrección física justificada.

Nav8 sigue siendo la corrección funcional publicada:607 PASS,máximo0,711963 m,
con cuatro fallos originales cerrados. Sus seis pasadas RAM siguen FAIL.
Siguiente discriminador: bloque diagnóstico del original12,5, preservando sus
cuatro fallos. No se hereda aceptación ni se regeneran anchos a ciegas.
Actores,barcos,cliente,FPS y aceptación global permanecen pendientes.

La revisión Fable se conserva íntegra como opinión, con límites corregidos en
review/reconciled-plan.md. No se adoptan sus inferencias de causalidad exclusiva,
redondeo<=0,05 m, fallo global, condición previa cumplida ni repetición automática.
Los diagnósticos de censo y esquina son posteriores a esa revisión.
''',encoding='utf-8')
manifest={p.relative_to(E).as_posix():dict(sha256=sha(p),bytes=p.stat().st_size) for p in E.rglob('*') if p.is_file()}
(E/'MANIFEST.json').write_text(json.dumps(manifest,indent=2)+'\n')
h=W/'HANDOFF.md';lines=h.read_text(encoding='utf-8').splitlines()
updates={'updated:':'updated: 2026-10-27 (Nav8 funcional publicado; Nav12 rechazado por tres alturas nuevas)',
'plan:':'plan: plans/ev112-kit7-navv9-ram-diagnostic-20261027.md. Medir el control original12,5 antes de otra generación; diagnóstico separado, cuatro FAIL preservados. Sin rebajar tolerancias.',
'blocker:':'blocker: Nav8 cierra los cuatro fallos y pasa607, pero falla RAM1.26591/1.24133. Nav12 introduce tres alturas nuevas0.856856/0.923148/0.818588 contra0.801 y queda rechazado. No se ejecutó RAM12. Visual,actores y global siguen pendientes.',
'cleanup:':'cleanup: Generación y sonda607 Nav12 cerradas oficialmente; leases liberados, sin procesos propios pendientes al cierre. Nav8 cerrado. Automatización anterior PAUSED; próximo control diagnóstico por FIFO.',
'next:':'next: Completar revisión del corredor navv9diag y seis pasadas RAM nuevas ABBAAB del paquete original12,5. DIAGNOSTIC_ONLY, nunca aceptación funcional. Una pasada inválida detiene el bloque; sin repetición favorable.',
'deployed:':'deployed: Nav8 funcional conservado; Nav12 af12bfe3ed48c6d436ed2f22bf8057d28a8e96d2de402ef3c36ae09862bfc87d rechazado; NavV9 original a2919a80ae6da6fc90e75b0ac55d1e9dd4ba4a39f6700b9fec237c7e7683b16c restaurado por hash solo para diagnóstico.',
'handoff:':'handoff: evidence/navigation/kit7-nav12-rejected-20261027/README.md; Nav8funcional y RAMFAIL conservados en sus checkpoints anteriores. Evidencia privada completa en E:/DayZ-Baltic-Build/shape-repair-20261025.'}
for prefix,value in updates.items():
 ids=[i for i,line in enumerate(lines) if line.startswith(prefix)];assert len(ids)==1,prefix;lines[ids[0]]=value
h.write_text('\n'.join(lines)+'\n',encoding='utf-8')
print(json.dumps(dict(status='REJECTED_NAV12_EVIDENCE_PRESERVED',files=len(manifest),path=str(E))))
