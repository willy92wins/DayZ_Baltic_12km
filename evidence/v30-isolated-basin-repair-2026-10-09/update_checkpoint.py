from pathlib import Path
import json,hashlib
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290');B=Path(__file__).parent
def read(p):
    with p.open(encoding='utf-8',newline='') as f:return f.read()
def write(p,s):
    with p.open('w',encoding='utf-8',newline='') as f:f.write(s)
updates={
'status':'BASE_1_0_NO_ACEPTADA. EV54 candidato de trabajo: mejora Nazia y41masas aisladas, fuente/cobertura/censo nativo completos PASS. Restan contornos, grupos bajos compartidos, residual global, lagos yTB.',
'candidate':'@DayZ_Baltic_IsolatedBasinsV1 EV54: mundo f3d6d58ea6d80042b23cd8e2958a14b653d1c903e82cc9f7f7b446992cd61c55; agua3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14; terreno73f4cc82192a6042eee30da3e1aeca90b0c4fb578f0ac9e38e31b3a8852556d2. E:/DayZ-Baltic-Build/v30-isolated-basin-repair-20261009/candidate contiene P/F nuevos; no regenerarlos de niveles antiguos. EV28 referencia intacta.',
'smoothing':'EV25 global vigente; EV53r1 Nazia integradoEV54:141vertices, esquina49.345->44.217grados, energia1m-10%, pliegues>30:13->2, area/topologia/niveles exactos dentro de tolerancia. EV51/52 yEV53 inicial se conservan FAIL. Msta/Volkhov ylagos pendientes; no barrido de parametros.',
'land_artifacts':'EV49 B sin cuatrocharcas reproduce2853muestras anomalas comunesA/B/A; vientoB no identico, limita amplitud causal. EV54 traslada conjuntamente29grupos/41masas,122objetos y11062vertices, fondo minimo1.005m;3grupos/4masas excluidos por politica/protecciones. Comparacion fresca puente6frames:alertas6.285%->0.173%, control0.1%; mejora local, no cierre global del shader.',
'global_detection':'EV54 indice actualizado8380418caras:435zonas secas bajas>=1m2,797413.34m2; no435fallos confirmados. Consumidor97725caras analiticas+320GEOS+451puntos PASS. Punto marcado sube1.520457->1.870457m y sale de la banda. Geometria exacta no equivale a render global.',
'runtime_lock':'EV54 run1da582ee-fc5e-476f-9dec-7a0efdd8fb83:4194304vertices+1205planos nuevos PASS, error1.53e-5m;25clases mojadas sin presencia y296escalares sin bandera inventariados. Capturas cargadas sinCUA. Lease expiro antes del primer cierre: readoptado propio, cierre orderly, release y banco libre.',
'remaining':'007/020:Msta/Volkhov ycontornosglobales.010texturaslocalesNazia/finalTB;016resto435zonas indice y29de70objetivos bajos no reparados;019streaming. EV44:45interrupciones de arroyo por reserva vial aun sin reparar.017grandeslagos niveles reservados;014TB/navmesh/IA tras geometria.25diferenciasdeclase mojada y296escalares nativos requieren clasificacion, no ocultarlas.',
'git':'Branch claude/codex-handoff-review-74f290. Checkpointe9eac80 EV48; siguiente checkpointEV49-54 propio. Sin push ni subagentes.',
'next':'Continuar desdeEV54 y camposP/F nuevos. Metodo conjunto EV53r1 resuelveNaziasin empeorar talud; llevar el mismo contrato aMsta/Volkhov, conservando excepciones bajas. Revisar grupos compartidos/protegidos y435zonas del indice. Texturas finales/TB antes de navmesh. No reabrir biseccion de charcas ni calibracion nativa ya resueltas.',
'handoff':'EV49-54 preservados en evidence/v30-isolated-basin-repair-2026-10-09/README.md ydirectorios vinculados. Capa accepted-terrain-layer.npz reproduce terreno/P/F byte a byte desdeEV25. EV54 nuevo candidato de trabajo, EV28 referencia preservada; base1.0 sigue incompleta.'}
p=W/'HANDOFF.md';s=read(p);lines=s.splitlines(keepends=True);inside=False
for i,line in enumerate(lines):
    if '<!-- LIVE-STATE:START -->' in line:inside=True
    if '<!-- LIVE-STATE:END -->' in line:inside=False
    if inside and ':' in line:
        key=line.split(':',1)[0]
        if key in updates:lines[i]=key+': '+updates[key]+ ('\r\n' if line.endswith('\r\n') else '\n')
write(p,''.join(lines))
p=W/'bugs.md';s=read(p);at=s.find('\n',s.find('#'))+1;s=s[:at]+'\nEstado vigenteEV54 (09-10): candidato `IsolatedBasinsV1`, mundo `f3d6d58e`. Nazia mejora forma y talud;41masas aisladas conservan profundidad/huella al elevarse. Cobertura404484celdas y censo4194304vertices/1205planos PASS. Alertas temporales del punto puente6.285%->0.173%, mejora local sin cierre global. EV49 sin charcas conserva efecto; no retirarlas. Msta/Volkhov, grandeslagos, crucesviales, indiceglobal, streaming yTB/navmesh siguen abiertos. Evidencia: `evidence/v30-isolated-basin-repair-2026-10-09/README.md`.\n'+s[at:];write(p,s)
p=W/'evidence/v30-global-water-risk-2026-10-09/bug-status-current.md';s=read(p).replace('vigente hasta EV48','vigente hasta EV54');lines=s.splitlines(keepends=True)
rows={
'007':'EV53r1 Nazia enEV54: energia1m-10%, esquina49.345->44.217, pliegues>30:13->2; fuente/cobertura/native PASS. | Msta/Volkhov, grandeslagos y contorno global aun abiertos.',
'016':'EV49 B sin cuatrocharcas mantieneefecto. EV54 mejora local puente:6.285%->0.173% muestras anomalas; no identifica shader. |435zonas del indice bajo actualizado,797413m2: revisar por geometria/intencion; no435fallos confirmados.',
'018':'EV54 corrige41de70masas bajas del censo mediante traslacion conjunta; fondo>=1.005m, profundidades/huella exactas,1205planos nativos PASS. |29objetivos restantes comparten soporte o fallan politica/protecciones. Bajos/Narva no se cierran globalmente.',
'020':'NaziaEV53r1 mejora fuente y vista enmotor; integradoEV54. | Msta/Volkhov pendientes;0431/0452/0456tier1500 fuera del diseño.'}
for i,line in enumerate(lines):
    if line.startswith('| '):
        key=line.split('|')[1].strip()
        if key in rows:lines[i]='| '+key+' | '+rows[key]+' |\n'
s=''.join(lines)+'\nEV54 es el candidato de trabajo; EV28 se conserva como referencia. Fuente, agua compilada y censo del motor comprobados; no aceptacion global. Banco libre tras cierre orderly. Ver README EV54 para identidades, límites y rechazosEV49-53.\n';write(p,s)
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md');s=read(session);s+='\n## Continuacion EV49-54\n\nCandidato de trabajo `@DayZ_Baltic_IsolatedBasinsV1`, mundof3d6d58e, terreno73f4cc82, agua3946db8b. NaziaEV53r1+41masas aisladas. Fuente, cobertura404484celdas y lectura4194304vertices/1205planos PASS; error1.53e-5m. Comparacion puente6.285%->0.173% alertas secas, local sin cierre de shader. EV49 contraprueba sincharcas conserva efecto; strictwind falla solo para amplitud. EV51/52/53 inicial rechazados conservados. Indice nuevo435zonas>=1m2/797413m2, no fallos confirmados.\n\nRun1da582ee-fc5e-476f-9dec-7a0efdd8fb83 cerrado orderly tras readoptar lease caducado; banco libre. SinCUA, subagentes ni push. Capa acumulada de terreno/P/F con replay byte-exacto. Informe ymanifest: `'+str(W/'evidence/v30-isolated-basin-repair-2026-10-09/README.md')+'`. Base1.0 incompleta; continuarHANDOFF LIVE-STATE, Msta/Volkhov, grupos protegidos/compartidos,435riesgos,lagos,45cruces,streaming yTB->navmesh.\n';write(session,s)
print('Updated live state, current bug dispositions and session evidence; task remains active.')
