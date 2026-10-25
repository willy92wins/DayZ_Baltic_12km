"""Record completed EV95 readback and global screen without terrain promotion."""
from pathlib import Path
import hashlib,json,re,shutil
G=Path(__file__).resolve().parent
P=G/'global-operator-prototype'
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
OUT=W/'evidence/v30-global-bank-extension-2026-10-10/native-global-screen-checkpoint'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
groups={
 'native':(G/'build-wide-slope',['collect_native_snapshot.py','verify_native.py','native-reference.json','native-run-provenance.json','native-capture.json','native-snapshot.log','native-verification.json','runtime-rpt-excerpt.log']),
 'screen':(P/'global-dry-unconstrained-screen',['PLAN.md','screen.py','independent-review.json','run-01/receipt.json']),
 'a-only':(P/'global-dry-unconstrained-screen/a-only',['PLAN.md','a_only_operator.py','test_a_only_operator.py','fixture-report.json','benchmark_a_only.py','independent-review.json','measurement/run-01/measurement.json'])}
for root,names in groups.values():
 for name in names:
  if not (root/name).is_file():raise FileNotFoundError(root/name)
if OUT.exists():raise FileExistsError(OUT)
OUT.mkdir(parents=True)
records=[]
for prefix,(root,names) in groups.items():
 for name in names:
  src=root/name;digest=sha(src);dst=OUT/prefix/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
  if sha(src)!=digest or sha(dst)!=digest:raise ValueError('copy drift')
  records.append({'source':str(src),'copy':str(dst.relative_to(OUT)),'sha256':digest,'bytes':src.stat().st_size})
refs=[]
for src in [P/'global-dry-unconstrained-screen/run-01/unaccepted-continuous-vector.npz',G/'build-wide-slope/candidate/terrain.npz']:
 refs.append({'path':str(src),'sha256':sha(src),'bytes':src.stat().st_size})
(OUT/'manifest.json').write_text(json.dumps({'copied':records,'external':refs},indent=2)+'\n',encoding='utf-8')
(OUT/'README.md').write_text('''# EV95 native readback and completed global diagnostic

EV95 native run ebf539c0-ae17-404c-ae41-ff75037ad9f1 passed the complete 4,194,304-vertex readback, 1,212 point checks and 1,205 water-plane references, with eight negative controls. Source snapshot was absent before launch and is bound to the exact process, PBOs and orderly close. No nominal or dynamic dry-class anomaly occurred at this sampled wave phase; 24 source-water nodes lacked water presence and 349 unflagged scalar queries still require classification. This does not close dynamic-envelope, subcell or graphical defects.

The prior screen memory refusal was preflight only. After memory became available, the same reviewed script completed one PCG diagnostic in 48.18 seconds, 265 iterations, peak 1.17 GB. The unconstrained objective decreased 69,217.20 to 53,659.57, but physical box, D8 and face constraints failed: the vector is not accepted terrain. A separate reviewed monotonic rollback path is being prepared; no unconstrained vector is packaged.

A-only operator fixtures and one measurement passed, peak 488 MB, exact-equivalent tested equations. This archive supersedes the pending-runtime and blocked-screen status in the earlier checkpoint, whose history remains intact. BASE 1.0, full-map relief, gray water and dynamic water remain open.
''',encoding='utf-8')
shutil.copyfile(Path(__file__),OUT/Path(__file__).name)
handoff=W/'HANDOFF.md';text=handoff.read_text(encoding='utf-8')
updates={
 'status':'BASE_1_0_NO_ACEPTADA. EV95 preview aislada compilada y empaquetada; identidad OPRW, 996PAA/7968mips y lectura nativa completa PASS. Agua dinámica, render gris y relieve de toda la superficie siguen abiertos.',
 'runtime_lock':'19:18 UTC: run propio EV95 ebf539c0 cerrado ordenadamente y retirado; lease liberada, owner null, self none, pending0, banco libre. Releer estado antes del siguiente uso. No nueva prueba gráfica válida.',
 'wide_relief':'EV95 composición40c174e3: 66.058 alturas cambiadas frente B, consumidor b0b7c872 PASS17/17. Worldf1a148ca/OPRW03dfa1c3,996PAA/7968mipsPASS. Readback nativo f01f9076 PASS4.194.304vértices/1212puntos/1205planos, maxerror1.52588e-5m,8negativos. 0agua sobrecls0 a fase muestreada;24ausencias frenteclase y349consultassinflags por clasificar. Sin aceptación dinámica/gráfica ni de toda superficie.',
 'global_operator':'Cotas globales b0c44997 verificadas para2712136variables/8380418caras. Normalfusionado0.4708s; A-onlyf1e8ddd9 medido488MB y0.135s/acción. Screen1dd4b4fe completado una vez trasliberarseRAM:48.18s,265CG,pico1.17GB,recibof66d7d49/vectorf7412e6f. Objetivo69217.20→53659.57 pero raw32 viola cajas/D8/15caras; NOterrenoaceptado. Builderglobalrollbackmonótono preparado en revisión, ninguna llamada real. ADMMglobal no lanzado.',
 'wet_bank':'Oredezh original1c2a6b8b mejora foco47.95→37.20° pero Fractionexacto falla20incidencias/5aristas≈1.12micrometros. Enumeración10nodos y conversor121±1ULP terminales sinfactible. Certificado283c2592 incompatibilidadP76/P80, no inviabilidadfísica. RobusthalfULP LP inviablediagnóstico, sin nuevaADMM. PreparaciónMILP sobre dominiofloat32real con mismoslímites físicos; consumidor completo preparado,noejecutado.',
 'next':'Revisar builderglobalrollback y ejecutar una unidad acotada si pasa; validar candidato con consumidor independiente completo. Revisar formulaciónMILPfloat32 del piloto sin relajar cruces. Clasificar24anomalías nativas y retomar discriminadorgráfico cuando escritorio válido. BASE1.0 noaceptada.',
 'git':'Branch claude/codex-handoff-review-74f290; checkpoints conversion-global-bounds (38copias/1ref) y native-global-screen (19copias/2refs) preparados. Consultar HEAD y verificación de blobs. Sin push.'}
for key,value in updates.items():
 pattern='^'+re.escape(key)+':.*$'
 if len(re.findall(pattern,text,re.M))!=1:raise ValueError(key)
 text=re.sub(pattern,key+': '+value,text,flags=re.M)
handoff.write_text(text,encoding='utf-8',newline='\n')
note='\n\n### 2026-10-10 19:21 UTC — EV95 native and completed global screen\n\n'+(OUT/'README.md').read_text(encoding='utf-8')+'\nArchive: '+str(OUT)+'\n'
for dst in [G/'WORKING_STATE.md',Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-10-dayz-baltic-bank-relief.md')]:
 with dst.open('a',encoding='utf-8') as f:f.write(note)
print(json.dumps({'copies':len(records),'external':len(refs),'checkpoint':str(OUT)}))
