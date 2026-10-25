"""Archive a completed unit; no traversal of package junctions or large generated data."""
from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).parent
A=B.parent/'v30-mixed-bank-incremental-20261010'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-incremental-bank-relief-2026-10-10'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
for path,status in [('review-luna/report.json','PASS_EV82_CONSUMER'),('surface-verification.json','PASS_EV82_AFFECTED_SURFACE'),('compiled-exposure.json','PASS_COMPILED_EXPOSURE'),('review-luna/compiled-package-review.json','PASS_EV82B_COMPILED_PACKAGE_REVIEW'),('changed-mips.json','PASS_ALL_CHANGED_MIPS'),('native-verification.json','PASS_COMPLETE_NATIVE_READBACK')]:
    assert read(B/path)['status']==status,path
close=read(B/'lifecycle-close.json')
assert close['close']['graceful'] and close['release']['released'] and not close['final']['owner_present'] and not close['final']['box_occupied']
assert (B/'review-luna/native-evidence-review.md').is_file()
assert (B/'residual-review/residual-diagnosis.md').is_file()
assert not D.exists()
D.mkdir(parents=True)
extensions={'.py','.json','.md','.log','.ps1','.csv','.png'}
for sub in ['', 'review-luna','residual-review']:
    src=B/sub;dst=D/sub;dst.mkdir(parents=True,exist_ok=True)
    for p in sorted(src.iterdir()):
        if p.is_file() and (p.suffix in extensions or p.name=='terrain-delta.npz'):
            assert p.stat().st_size<8_000_000,p
            shutil.copy2(p,dst/p.name)
mission=B/'missions/BalticIncrementalBankFullWaterV1.BalticTrial'
(D/'mission').mkdir()
for name in ['init.c','risks.csv']:shutil.copy2(mission/name,D/'mission'/name)
large=[B/'candidate/terrain.npz',B/'candidate/plane.npy',B/'candidate/visible-field.npy',mission/'grid.csv']
deployment=read(B/'deploy.json')
large += [Path(deployment['mod'])/'Addons'/n for n in deployment['files']]
(D/'external-artifacts.json').write_text(json.dumps({'files':[{'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size} for p in large],'note':'Full terrain/PBO/grid stay in hash-pinned build storage; delta and reproducible tools are versioned.'},indent=2)+'\n')
rejected=D/'rejected-EV82-A';rejected.mkdir()
names=['author.py','authoring.json','plan.md','ev82-fixture-test.json','terrain-delta.npz','root-author-review.json']
names += [p.name for p in A.glob('*provenance.json')]
names += ['review-luna/verify.py','review-luna/report.json','review-luna/review.md']
for name in names:
    p=A/name
    if p.is_file():
        target=rejected/name;target.parent.mkdir(exist_ok=True,parents=True);shutil.copy2(p,target)
(rejected/'README.md').write_text('# EV82-A rechazado\n\nDos referencias de 30.000000014/30.000000015 grados escaparon al clasificador del autor y pasaron a 31.4417/36.2322 grados. El consumidor rechazó el candidato. No se empaquetó ni se lanzó en DayZ. EV82-B corrige exclusivamente ambas clasificaciones; conserva la tolerancia del consumidor. Ver plan y fixture de B.\n',encoding='utf-8')
summary=(B/'root-validation-notes.md').read_text(encoding='utf-8')
(D/'README.md').write_text(summary+'\n\nDiagnóstico residual: `residual-review/residual-diagnosis.md`. Revisión independiente: `review-luna/review.md`, `compiled-package-review.md` y `native-evidence-review.md`. EV80 permanece disponible para rollback. No hay aceptación visual ni push.\n',encoding='utf-8')
manifest=[dict(path=p.relative_to(D).as_posix(),sha256=sha(p),bytes=p.stat().st_size) for p in sorted(D.rglob('*')) if p.is_file()]
(D/'manifest.json').write_text(json.dumps({'candidate_sha256':deployment['terrain_sha256'],'files':manifest},indent=2)+'\n')
for q in manifest:assert sha(D/q['path'])==q['sha256']
handoff=W/'HANDOFF.md';text=handoff.read_text(encoding='utf-8')
updates={
 'status:':'status: BASE_1_0_NO_ACEPTADA. EV82-B suaviza taludes; geometría, superficies, paquete y lectura nativa completa PASS. Formas residuales y render siguen abiertos. EV68 sin promoción.',
 'candidate:':f"candidate: @DayZ_Baltic_IncrementalBankPreviewV1 EV82-B. Mundo {deployment['files']['narva_trial.pbo']}; agua {deployment['files']['baltic_water_v30.pbo']}; terreno {deployment['terrain_sha256']}. EV80 conservado para rollback; sin aceptación artística.",
 'smoothing:':'smoothing: EV79 quitó 58 crestas secas Narva; EV80 redujo quiebros mixtos 4693→3384; EV82-B los reduce a 2597 con 3046 cambios incrementales, 4091 acumulados frente a EV79. Energía incidente −13,50% frente a EV80; 0 nuevos >30 y 0 máximos de sector peores. El banco seco aumenta media cuadrática 1,38948→1,42257; p99 apenas baja. No es mejora uniforme. EV81 y EV82-A rechazados; B repara clasificación angular sin relajar consumidor.',
 'runtime_lock:':'runtime_lock: EV82-B run 2d06c106-f70d-48ae-aff5-ab17fb42c8f9 SERVER_ONLY terminado orderly; lease liberado, owner null/self none, banco libre. Ningún run pendiente de foco.',
 'surface:':'surface: EV82-B 462 teselas/2324 solapes PASS; 91 PAA+WRP cambian, 6735 entradas intactas, 728 mips PASS. Motor 4194304 vértices/1212 puntos/1205 planos PASS, error 1,52588e−5 m. Fase actual: 0 flags secos, 25 clase agua sin presencia, 339 escalares; añadidos 2 A/275 Q sobre alturas intactas. No cierre gráfico.',
 'git:':'git: Branch claude/codex-handoff-review-74f290; previo91870b8. Checkpoint EV82-B en evidence/v30-incremental-bank-relief-2026-10-10;consultar gitlog. Sin push.',
 'next:':'next: Usar diagnóstico residual EV82-B y sondeo local de factibilidad antes de otro diseño. El detector >30 no cubre facetas menores ni tramos rectos largos. Plan EV82-B agotado; no otra autoría sin criterios nuevos revisados. Contornos mojados/render mantienen fallos abiertos; no promover EV68.',
 'handoff:':'handoff: evidence/v30-incremental-bank-relief-2026-10-10/README.md + manifest; EV82-B geometría, paquete y motor PASS; rechazo A documentado. Base 1.0 abierta; conservar contratos y pruebas de render separadas.'}
start=text.index('<!-- LIVE-STATE:START -->');end=text.index('<!-- LIVE-STATE:END -->')
block=text[start:end].splitlines()
for i,line in enumerate(block):
    for key,value in updates.items():
        if line.startswith(key):block[i]=value;break
handoff.write_text(text[:start]+'\n'.join(block)+'\n'+text[end:],encoding='utf-8',newline='\n')
bugs=W/'bugs.md';text=bugs.read_text(encoding='utf-8');lines=text.splitlines()
for i,line in enumerate(lines):
    if line.startswith('Estado vigente EV80 (10-10):'):
        lines[i]='Estado vigente EV82-B (10-10): IncrementalBankPreviewV1; mundo b11c825b, terreno f9fb23de, agua3946db8b. Geometría/superficie/PBO/lectura nativa completa PASS. EV81 y EV82-A rechazados; banco libre. Base1.0 abierta. LIVE-STATE y columnas actuales mandan sobre historia.'
    if line.startswith('| BALTIC-'):
        cells=line.split('|');bug=cells[1].strip()
        notes={
          'BALTIC-007':'EV82-B: quiebros mixtos3384→2597; no nuevos>30; quedan facetas/contornos. No aceptación visual.',
          'BALTIC-011':'EV82-B: geometría nativa completa PASS; suavizado no uniforme y detector>30 no cubre relieves amplios/rectos. Diagnóstico residual publicado.',
          'BALTIC-010':'EV82-B:462teselas afectadas,2324solapes,728mips,91PAA+WRP y lectura nativa PASS; apariencia pendiente.',
          'BALTIC-016':'EV82-B:0m² exposición nueva,0flagssecos en fasecensada; no cierra anomalías visuales ni todaenvolvente de oleaje.',
          'BALTIC-009':'EV82-B conservaP/F ysoportemojado;0m² exposición añadida/perdida y1205planosnativos PASS. Discontinuidad visual abierta.',
          'BALTIC-019':'EV82-B91PAA modificados y728mips PASS; sin prueba gráfica nueva, rectángulos grises/streaming siguen abiertos.',
          'BALTIC-020':'EV82-B no altera finales ni contornos mojados; siguen pendientes. No cerrarlos por suavizado de taludes.'}
        if bug in notes:
            cells[4]=' Actualización10-10 EV82-B: '+notes[bug]+' Evidencia: evidence/v30-incremental-bank-relief-2026-10-10/README.md. '+cells[4].lstrip()
            if bug=='BALTIC-010':cells[2]=' SUPERFICIE EV82-B PASS; VISUAL PENDIENTE '
            if bug=='BALTIC-007':cells[2]=' EV82-B VALIDADO; TALUDES Y CONTORNOS AÚN ABIERTOS '
            lines[i]='|'.join(cells)
bugs.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-10-dayz-baltic-bank-relief.md')
with session.open('a',encoding='utf-8') as stream:stream.write('\n## EV82-B completado como mejora geométrica\n\n'+summary+'\n\nEvidencia durable: '+str(D)+'\n')
print(json.dumps(dict(evidence=str(D),files=len(manifest),bytes=sum(q['bytes'] for q in manifest)),indent=2))
