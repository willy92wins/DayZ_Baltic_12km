"""Checkpoint the rejected numerical candidate and reconcile current bug states."""
from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-mixed-bank-float32-2026-10-10'
r=json.loads((B/'review-luna/report.json').read_text())
assert r['status']=='FAIL_EV81_CONSUMER'
failed=[k for k,v in r['gates'].items() if not v]
assert set(failed)=={'zero_new_edges_over30_vs_EV80','bank_p99_and_over30_nonworse_vs_EV80','modified_sector_maxima_nonworse_vs_EV80'}
assert not D.exists()
D.mkdir(parents=True)
for p in B.iterdir():
    if p.is_file() and (p.suffix in {'.py','.md','.json','.log','.png'} or p.name=='terrain-delta.npz'):
        shutil.copy2(p,D/p.name)
(D/'review-luna').mkdir()
for p in (B/'review-luna').iterdir():
    if p.is_file() and p.suffix in {'.py','.md','.json','.log'}:shutil.copy2(p,D/'review-luna'/p.name)
summary='''# EV81 rechazado; EV80 continúa vigente

Se corrigió una causa numérica aislada: propuestas válidas en doble precisión quedaban al otro lado del límite al convertirlas a float32. Se permite probar uno y dos valores representables hacia la altura anterior, conservando todas las tolerancias y controles. Un recorrido de 81,453 s procesó los 4329 nodos; 4005 cambios, 1382 rescatados con un ULP. Agua y metadatos idénticos.

El consumidor independiente rechaza el candidato: frente a EV80 aparecen seis aristas nuevas >30°, p99 seco de ribera 4,982072→5,004888° y máximo del sector (29,16) 41,671232→42,647964°. El detalle y coordenadas están en `review-luna/review.md`. La mejora total (3384→2819 pliegues mixtos; energía afectada −17,6975%) no anula esas regresiones.

Mecanismo leído: la autoría limita ángulos contra EV79 (`author.py`, solve_node), por lo que puede perder mejoras que EV80 ya alcanzó. El fallback corrige cuantización, pero no cambia esa referencia. No es un defecto del consumidor ni una infracción de agua. EV81 no se empaquetó ni se lanzó en DayZ; no se generó otra variante. EV80 permanece en `P:/Mods/@DayZ_Baltic_MixedBankPreviewV1`, mundo ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038.

Siguiente diseño a revisar, no implementado: separar el terreno vigente que fija los límites angulares del terreno original que fija el presupuesto total ±2 m. Partir de EV80, no reconstruirlo desde EV79; conservar exactamente sus mejoras y las protecciones actuales. Requiere un nuevo plan con fixture que falle al comparar únicamente con EV79, antes de calcular. No relajar el criterio ni promover una combinación parcial sin consumidor.

Base 1.0 sigue abierta: agua gris a distancia, residual de agua aparente sobre tierra, formas mojadas y finales, grandes lagos/excepciones pendientes, Terrain Builder y navmesh final. Los números de geometría y la lectura nativa EV80 no son aceptación visual.
'''
(D/'README.md').write_text(summary,encoding='utf-8',newline='\n')
handoff=W/'HANDOFF.md';text=handoff.read_text(encoding='utf-8');lines=text.splitlines()
for i,line in enumerate(lines):
    if line.startswith('smoothing:'):
        lines[i]=line+' EV81 cuantización rechazada: seis >30 nuevos, p99 y un sector peores frente a EV80; sin paquete/motor.'
    elif line.startswith('next:'):
        lines[i]='next: EV81 rechazado, sin otra variante. Revisar diseño incremental desde EV80 con límites angulares EV80 y presupuesto acumulado EV79, antes de autoría; mantener gates. Continuar diagnóstico separado del render gris y contornos mojados; no promover EV68. Ver evidence/v30-mixed-bank-float32-2026-10-10/README.md.'
    elif line.startswith('git:'):
        lines[i]='git: Branch claude/codex-handoff-review-74f290; EV80 validado en f480943; checkpoint EV81 rechazado y conciliación de bugs posterior, consultar git log. Sin push.'
handoff.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')

# Update the actual status column; do not leave a newer paragraph over stale live claims.
status={
'007':('EV80 VALIDADO; TALUDES Y CONTORNOS AÚN ABIERTOS','EV80: 2591 vértices; 4693→3384 quiebros mixtos >30, cero nuevos; paquete y lectura nativa completa PASS. EV81 rechazado por regresión. Ver evidence/v30-mixed-bank-relief-2026-10-10/README.md y evidence/v30-mixed-bank-float32-2026-10-10/README.md.'),
'009':('COBERTURA COMPILADA CONTINUA; ASPECTO GLOBAL PENDIENTE','EV12/EV80: cobertura física/visible de agua verificada y preservada por identidad/exposición compilada; no cerrar los gaps visuales reportados por ese resultado. HANDOFF water/render.'),
'010':('SUPERFICIE COMPLETA Y ACTUALIZADA PASS; ACEPTACIÓN VISUAL PENDIENTE','EV72 superficie completa; EV79/80 actualizan toda huella afectada con padding, solapes y mips verificados. EV80: 459 teselas regeneradas y PBO exacto. No es cierre visual. evidence/v30-mixed-bank-relief-2026-10-10/README.md.'),
'011':('MEJORAS DE RELIEVE VERIFICADAS; FORMA GLOBAL ABIERTA','EV79/80 reducen crestas y taludes con métricas por sector. Persisten contornos poligonales; no cerrar el aviso del usuario ni declarar toda la superficie aceptada. evidence/v30-mixed-bank-relief-2026-10-10/README.md.'),
'012':('CONTRATO 0,95 M ACEPTADO; GEOMETRÍA CONSERVADA; FÍSICA FINAL PENDIENTE','Decisión08-10: conservar fondo1m y calado nominal>=0,95m. 19corredores/36494caras, mínimo0,955609m en evidence/v30-navigation-contract-2026-10-08. EV79/80 conservan agua y soportes protegidos; no heredar aceptación física global.'),
'015':('COBERTURA GLOBAL VERIFICADA; RENDER Y CRUCES ABIERTOS','EV12: 404484celdas, cero hueco físico y residuo visible3,8464e-12m²; EV80 no altera agua ni exposición compilada. Persisten discontinuidades de render y45cruces de reserva inventariados. HANDOFF water/remaining.'),
'016':('ABIERTO: RESIDUAL VISUAL; CENSO GLOBAL SEPARADO','EV71:408zonas de riesgo geométrico, no defectos confirmados. EV80:3lecturas dinámicas sobre playa intacta;0nominales sobre seco en censo. Las capturas reportadas no quedan cerradas por ello. evidence/v30-mixed-bank-relief-2026-10-10/native-difference-classification.json.'),
'018':('FONDOS/EXCEPCIONES PENDIENTES; RECTÁNGULOS SIN CAUSA AISLADA','EV68 sin promoción; excepciones647/651 y grupos protegidos pendientes. EV76: fondo bajo mar en ROIgris y controlondulado, factor compartido. No atribuir los rectángulos actuales solo al fondo. HANDOFF render/remaining.'),
'019':('ABIERTO: STREAMING GENERAL Y RECTÁNGULOS DE AGUA SEPARADOS','EV73/74 reproducen rectángulos con tierra texturada; detalle2/4/2 no elimina. Dos transiciones coinciden con bordesP3D, correlación. EV77 wire inconcluso y cerrado, sin espera activa. Ticket foco fb-20261008-233507-8b1c existente. HANDOFF render/runtime_lock.'),
'020':('FINALES Y CONTORNOS MOJADOS ABIERTOS','EV80 mejora taludes de tierra y conserva soporte mojado; no modifica ni acepta los finales de Msta/Volkhov. Pendiente consumidor de forma y aceptación en motor. HANDOFF remaining.')}
bugs=W/'bugs.md';lines=bugs.read_text(encoding='utf-8').splitlines();seen=[]
for i,line in enumerate(lines):
    if line.startswith('Estado vigente EV72/73'):
        lines[i]='Estado vigente EV80 (10-10): candidato MixedBankPreviewV1, terreno0a18c562, mundoec3785d1 y agua3946db8b. Geometría, superficie, paquete y4194304alturas nativas PASS. EV81 rechazado; no hay run activo. Base1.0 abierta. HANDOFF LIVE-STATE y las columnas de estado siguientes mandan sobre historias anteriores.'
    if line.startswith('| BALTIC-'):
        parts=line.split('|');ident=parts[1].strip().removeprefix('BALTIC-');seen.append(ident)
        if ident in status:
            new,why=status[ident];parts[2]=' '+new+' ';parts[4]=' Actualización10-10: '+why+' Historia conservada: '+parts[4].strip()+' ';lines[i]='|'.join(parts)
assert len(seen)==20 and len(set(seen))==20
bugs.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
(D/'bug-status-review.json').write_text(json.dumps(dict(status='RECONCILED_20_REPORTED_IDS_NOT_GLOBAL_PASS',reviewed_ids=seen,updated_ids=list(status),unchanged_ids=[i for i in seen if i not in status],limits=['Unchanged IDs retain their dated evidence and limits, not a new runtime test','No open visual, navigation-final or load criterion was promoted to PASS by documentation']),indent=2)+'\n')
manifest=[dict(path=p.relative_to(D).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest(),bytes=p.stat().st_size) for p in sorted(D.rglob('*')) if p.is_file()]
(D/'manifest.json').write_text(json.dumps(dict(files=manifest,candidate_rejected_sha256=r['candidate_sha256']),indent=2)+'\n')
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-10-dayz-baltic-bank-relief.md')
with session.open('a',encoding='utf-8') as f:f.write('\n## EV81 rechazado y registro de fallos conciliado\n\n'+summary+'\nEvidencia: '+str(D)+'\n')
print(json.dumps(dict(evidence=str(D),files=len(manifest),failed_gates=failed,bugs_reviewed=len(seen)),indent=2))
