from pathlib import Path
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
def read(p):
    with p.open(encoding='utf-8',newline='') as f:return f.read()
def write(p,s):
    with p.open('w',encoding='utf-8',newline='') as f:f.write(s)
updates={
'status':'BASE_1_0_NO_ACEPTADA. EV61 candidato de trabajo: EV54+Msta/Volkhov+15dominios secos. Geometria/cobertura/nativo PASS; vistas aun con angularidad y aspecto irregular en cauces bajos. Continuar objetivo completo.',
'candidate':'@DayZ_Baltic_StrictDryFloorV1 EV61: mundo1423f25da029ab0524a9d7861c2fbd1b2cda5f97b2244aa27e2a3fc03e3b5580; agua3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14; terreno7bcfae7662acf3f83ff0f52434a3d9c3f1e8af745574b2fdc3ad689db123a990. E:/DayZ-Baltic-Build/v30-strict-dry-composition-20261009/candidate; P/F exactosEV54. EV28/54/57 preservados.',
'smoothing':'EV55Msta20vertices, energia-10%, peor66.28grados igual. EV57Volkhov31vertices, energia-10%abierta/-11.73%isla, RMS9.585->8.623, pliegues>30:28->17; geometria/compilado/nativo PASS. EV56convergenciaFAIL conservado, correccionderivadas converge83iter. Vistas bajas noaceptadas. EV61+1883vertices en15dominios, energiaangular-9.51%,96objetivos a1.8;EV60enteroFAIL,2197objetivos pendientes.',
'global_detection':'EV61 indice8.380.418caras:428zonas>=1m2/795569.19m2, no428defectosconfirmados. Consumidor97483analiticos+320GEOS+444puntosPASS. EV59detecta2760vertices secos editables;2293trasproteccionesEV25,EV61resuelve96. Fuente/compuesto exactos en capa replay.',
'runtime_lock':'EV61servidor sincliente run800d8ccf-9262-4c8b-824b-b9b60219fd14:4194304vertices+1205planosPASS, error1.53e-5m;23diferenciasdeclase y319escalaressinbandera inventariados. Cierreorderly, lease liberado, banco libre. EV57cliente tambiencerrado. SinCUA.',
'remaining':'007/020contornosglobales yaspectodelaguaMsta/Volkhov.010texturaslocalesNazia/Msta/Volkhov/finalTB.016indice428zonas y2197objetivosEV60rechazados.01829de70masasbajas compartidas/protegidas.01545interrupcionesporreserva.017nivelesgrandeslagosreservados.019streaming.014TB->navmesh/IA.',
'git':'Branch claude/codex-handoff-review-74f290. Checkpoint853b241 EV49-54; siguientecheckpointEV55-61 propio. Sinpush/subagentes.',
'next':'ContinuarEV61. Investigar cierre de soporte de grupos bajos fluyentes:Volkhov594 yNazia95; Msta693 pertenece agranlago, no elevargrupoentero. Clasificar bandejadeflags bajo5puntosdepuente con discriminador, no asumirhueco. Contornos/TB/texturas/cruces restantes. No repetirEV15/21/33/34 ninuevocotaD3.',
'handoff':'EV55-61 en evidence/v30-strict-dry-composition-2026-10-09/README.md. Capa accepted-terrain-layer.npz replaybyteexacto desdeEV25 incluyeP/F. EV60FAIL,EV61composicion15/89 explicita. Base1.0incompleta; seguirautonomamente.'}
p=W/'HANDOFF.md';lines=read(p).splitlines(keepends=True);inside=False
for i,line in enumerate(lines):
    if '<!-- LIVE-STATE:START -->' in line:inside=True
    if '<!-- LIVE-STATE:END -->' in line:inside=False
    if inside and ':' in line:
        key=line.split(':',1)[0]
        if key in updates:lines[i]=key+': '+updates[key]+ ('\r\n' if line.endswith('\r\n') else '\n')
write(p,''.join(lines))
p=W/'bugs.md';s=read(p);start=s.index('Estado vigenteEV54');end=s.index('\n',start);s=s[:start]+'Estado vigente EV61 (09-10): candidato `StrictDryFloorV1`, mundo `1423f25d`; Msta/Volkhov y15dominios secos incorporados con evidencia fuente/compilado/nativa. Indice428zonas de riesgo, no defectos confirmados. Base1.0 sigue incompleta. Fuente actual: `evidence/v30-strict-dry-composition-2026-10-09/README.md` y tabla de20IDs en `evidence/v30-global-water-risk-2026-10-09/bug-status-current.md`.'+s[end:];write(p,s)
p=W/'evidence/v30-global-water-risk-2026-10-09/bug-status-current.md';s=read(p).replace('vigente hasta EV54','vigente hasta EV61');lines=s.splitlines(keepends=True)
rows={'007':'EV53Nazía+EV55Msta/EV57Volkhov: fuente/cobertura/nativo PASS;31verticesVolkhov reducen pliegues>30de28a17. EV61+15dominios secos. | Vistas de cauces bajos mantienen angularidad/aspecto irregular. Contornosglobales ygrandeslagos abiertos.','009':'EV61:censo nativo4194304vertices y1205planos PASS sincliente; cobertura404484celdas heredada con447030apoyos exactos. | Noequivale aoleajecompleto/render.23diferenciasdeclase y319escalares diagnosticos inventariados.','016':'EV54mejora local puente6.285%->0.173%;EV61resuelve96objetivos de suelo seco en15dominios sin degradar gates. | Indice428zonas/795569m2, no428fallos.2197objetivosEV60requieren reparacion conjunta; shader sin identificar.','020':'EV55Msta yEV57Volkhov fuente/compilado/nativo PASS; incluyen controlcorrectodeanillos. | Peor esquinaMsta66.28igual; vistasdeaguabaja aun poligonales. Noaceptacionartistica ni cierre.'}
for i,line in enumerate(lines):
    if line.startswith('| '):
        key=line.split('|')[1].strip()
        if key in rows:lines[i]='| '+key+' | '+rows[key]+' |\n'
s=''.join(lines);i=s.index('\nReferencias actuales:');s=s[:i]+'\nReferencia vigente: `../v30-strict-dry-composition-2026-10-09/README.md`. CandidatoEV61 `StrictDryFloorV1`, mundo1423f25d, agua3946db8b, terreno7bcfae76. EV28/54/57preservados. EV56/60FAIL; seleccionEV61explicita. Noaceptacion global de20IDs ni base1.0. Banco libre trascierreorderly.\n';write(p,s)
p=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md');s=read(p);s+='\n## Continuacion EV55-61\n\nNuevo candidatoEV61 StrictDryFloorV1: mundo1423f25d, terreno7bcfae76, agua3946db8b. Msta/Volkhov+15dominios secos. Censo de servidor sin cliente4194304vertices+1205planosPASS, error1.53e-5m. Indice428zonas/795569m2. EV56convergenciafallida yEV60p99fallido conservados;EV61composicion15/89,96de2293objetivos,2197pendientesexactosCSV. VistasEV57siguen mostrando aspectos poligonales de aguabaja. Fuenteactual '+str(W/'evidence/v30-strict-dry-composition-2026-10-09/README.md')+'.\n\nRunsEV57/61cerradosorderly, leases liberados,bancolibre. SinComputerUse/subagentes/push. Objetivoactivo e incompleto: continuarHANDOFF, gruposfluyentes594/95, lago693reservado,cruces,contornosglobales,texturas/TB->navmesh.\n';write(p,s)
print('Updated current state and evidence. Task remains active.')
