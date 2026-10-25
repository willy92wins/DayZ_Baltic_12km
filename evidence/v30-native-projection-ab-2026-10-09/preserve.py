from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-native-projection-ab-2026-10-09'
D.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in B.iterdir() if p.is_file() and p.suffix not in ['.npz']]
for phase in ['A-start','A-setup','A-unpause','A-late','A-stable']:
    files+=list((B/'captures'/phase).glob('*.jpg'))
receipt=[]
for p in files:
    dst=D/p.relative_to(B);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(p,dst)
    assert sha(p)==sha(dst);receipt.append(dict(path=str(p.relative_to(B)),sha256=sha(p),bytes=p.stat().st_size))
(D/'preservation.json').write_text(json.dumps(receipt,indent=2)+'\n')
path=W/'HANDOFF.md';txt=path.read_text(encoding='utf-8')
changes={
'proyeccion nativa aun pendiente.':'proyeccion nativa confirmadaEV48(error reservado0.000161px).',
'runtime_lock: EV35 last known run closed orderly and lease released. Current session_status fails Transport closed on both exposed connectors; current bank occupancy UNKNOWN. Reconnection requested; do not bypass lifecycle or launch via a local client.':'runtime_lock: EV48 reconexion funcional. A yB cerrados orderly; lease liberado y session_status final banco libre. Computer Use detenido por Escape fisico durante preparacionB; sin medicionB ni retornoA. Reobservar antes de nuevos runs.',
'git: Branch claude/codex-handoff-review-74f290. Checkpoint39bcc23 preservesEV35–43; next ownEV44–47checkpoint. No push or subagents.':'git: Branch claude/codex-handoff-review-74f290. Checkpoint6354222 preservesEV44–47; siguiente checkpoint propioEV48. No push or subagents.',
'next: MCP reconnection required -> EV28+ProjectionProbeV1: native GetScreenPos confirmation, stable A baseline, then EV41 pond omission B and returnA. Full-map low dry targets inEV45/components.csv and native-index.npz. EV47 rejected onlycorner_max, real2–4msegments; no parameter sweep or failed promotion. Resolve native terminal topology before new shape candidate.':'next: EV48 confirma proyeccion nativa559.439464px; no repetir ajuste visual. ReanudarEV41 A/B/A con referencia estable; B anterior sin medir por paradaComputerUse. EV45/components.csv y native-index.npz contienen objetivos globales. EV47 rechazado por esquina real; resolver topologia terminal antes de nuevo candidato.',
'handoff: Full-map numerical low-dry indexEV45 and source crossing attributionEV44 complete in their stated scope. EV46/47 rejected, not deployed. No run launched while MCP Transport closed. EV41/43 diagnostics ready, current occupancy unknown. EV28 remains production; full map/base1.0 NOT completed.':'handoff: EV48 completa proyeccion nativa y referenciaA de6frames33.869s;4360alertas secas en cohorte, no diagnostico de shader. CUA activa ventana y recupera referencia; luego detenido porEscape duranteB, no mas entradas. Runs cerrados, banco libre. EV28 intacto; mapa/base1.0 NO terminado.'}
for old,new in changes.items():
    assert old in txt,old
    txt=txt.replace(old,new,1)
path.write_text(txt,encoding='utf-8')
path=W/'evidence/v30-global-water-risk-2026-10-09/bug-status-current.md';txt=path.read_text(encoding='utf-8')
txt=txt.replace('vigente hasta EV47','vigente hasta EV48',1)
txt=txt.replace('Confirmar proyección nativa y bisecciónEV41; MCP Transport closed, sin fix gráfico promovido.','EV48 confirma proyección nativa y referenciaA; B sin medir tras paradaCUA porEscape. BisecciónEV41 pendiente, sin fix gráfico promovido.',1)
txt=txt.replace('Causa del streaming intermitente abierta; no defecto de mipmaps encontrado.','EV48 recupera cielo/texturas al activar ventana porCUA; mecanismo interno abierto y no defecto de mipmaps encontrado.',1)
txt=txt.replace('EV35–43: no producción promovida, EV28 exacto por hashes frescos. EV41 y sondaEV43 preparados sin ejecución. ConectorTransport closed: ocupación actual del banco desconocida. Candidatos rechazados conservan evidencia; no aceptación de base.','EV35–43: sin producción promovida. Estado actualizadoEV48: sondaEV43 ejecutada; bisecciónEV41 incompleta. Candidatos rechazados conservan evidencia; no aceptación de base.',1)
txt=txt.replace('EV44–47 preservados. El censo no visual cubre toda la malla; no sustituye la comprobación del fallo gráfico ni repara por sí solo los cruces. MCP desconectado; pruebas de motor preparadas pero pendientes. EV28 intacto, base sin terminar.','EV44–48 preservados. El censo no visual cubre toda la malla; no sustituye comprobar el fallo gráfico ni repara cruces. MCP reconectado; EV48 confirma proyección y A estable. B se interrumpe porEscape deComputerUse antes de medir; cierre ordenado y banco libre. EV28 intacto, base sin terminar.',1)
path.write_text(txt,encoding='utf-8')
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md')
with session.open('a',encoding='utf-8') as f:f.write('\n\n## EV48 — proyección nativa y referencia estable\n\nMCP reconectado y paquetes por hash exactos. Focal nativa559.439464px; cinco puntos reservados error máximo0.000161px,257muestras de12puntos. A inicialmente magenta/sin materiales; quitar pausa no basta, activar ventana conComputerUse recupera cielo/texturas. Seis frames33.869s:4495alertas secas,4360en cohorte concontrol9202muestras; no identifica shader. B preparado con4objetos omitidos y camara exacta, sin medir: ComputerUse comunica Escape físico. No más entradas; ambos runs cerrados orderly, lease liberado,banco libre. EV41 sigue incompleto sin retornoA; EV28 no cambia, base no terminada. Evidencia W/evidence/v30-native-projection-ab-2026-10-09. Checkpoint propio sin push; continuar toda superficie tras nueva petición.\n')
print(json.dumps(dict(preserved=len(receipt),destination=str(D),reports_updated=True),indent=2))
