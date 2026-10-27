from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'chernarus-nav-height-code-review-20261027';O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-kit7-chernarus-height-reference-20261027.md',W/'missions/BalticChernarusNavHeightRef.ChernarusPlus/init.c',W/'tools/navigation/verify_chernarus_nav_height_reference.py',W/'tools/navigation/test_chernarus_nav_height_reference.py',R/'prepare_chernarus_nav_height_runtime.py',R/'orchestrate_chernarus_nav_height_probe.js',R/'finish_chernarus_nav_height_probe.py',R/'capture_chernarus_nav_height_log.ps1',R/'test_chernarus_nav_height_probe_flow.cjs',R/'test_chernarus_nav_height_probe_command.cjs',R/'chernarus-nav-height-reference-20261027/anchors.json',R/'chernarus-nav-height-reference-20261027/extent-check.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión operacional independiente READ ONLY, Fable5.1 nativo. SOLO Read/Glob/Grep. No procesos, escritura, Git, MCP, subagentes ni mensajes al usuario. Máximo900 palabras; SOUND/SOUND-with-fixes/NEEDS-WORK con defectos concretos y archivo/línea. Codex ejecuta por autorización autónoma del usuario.
Lee las fuentes en E:/DayZ-Baltic-Build/shape-repair-20261025/chernarus-nav-height-code-review-20261027/source-hashes.json, acotadamente. Plan ya revisado y conciliado, ahora revisar código y contrato antes de un único run. El runtime actual está preparándose/hashing; deployment/frozen/accepted aún NO existen y se sellarán después de revisión con todos los inputs y todos los PBO stock. No reportar su ausencia como bug: lanzamiento exige accepted y hashes. Todos los PBO vanilla se revalidan antes y después, inventario exacto; host identity inspecciona solo -mod bridge, count1; vanilla inventory separado.
Objetivo diagnóstico readonlyChernarus24long_straight con48rutas q+-6,z+-6 +NONE. Sin clientes/CE/spawn, no cambiaBaltic gate .801/.011/2.1, no aceptación niactorproof. Datos históricos solo locators; modelo/3Dposiciónactual<=.05 y exact1. Todos los49 preservados; ancla ausente aborta INCONCLUSO, no sustitución. Positiveunfound/endpointXZ>2.1 se preservan noncomparable. EndpointY motorSurfaceRoadYLEGACY+.2 difiere deBalticofflinemaxroofground+.2 y se declara. Extremos dentro deRoadway deODOLactual. EjesModelToWorld10m parafloatprecision. Verificar APIs reales si duda enP:/scripts/3_game/{ai/aiworld.c,global/game.c,entities/object.c}; no asumir APIs nuevas.
17 controles Python PASS,13lifecyclemock +2mutantes y8commandPASS; scriptvalidator1filePASS. Revisa falsosverdes, anclaje, parseo, comparación y release. Coordinator y strictidentity/observer/close provienen deNav12 probado, conmisión/log/count49 ysinBalticmods. CaptureterminaalENDinclusoabort, consumer rechazaEND!=49. No interpretar SurfaceRoadY-GroundY=0 comoimposibilidad deNavY-RoadY>.801: matemáticamentepueden diferir, ya reconciliado enplan. Falta raisedroad limita subcomparación, no invalida general. No sugerir más familias,actorclientniotrogrid enesta review.
''' 
(O/'brief.md').write_text(brief,encoding='utf-8')
args=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
start=time.monotonic()
with (O/'response.json').open('wb') as out,(O/'stderr.log').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
 try:p.communicate(brief.encode(),timeout=300)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=30);raise
assert all(sha(Path(k))==v for k,v in before.items())
(O/'completion.json').write_text(json.dumps(dict(returncode=p.returncode,seconds=time.monotonic()-start,inputs_unchanged=True),indent=2)+'\n')
print('FABLE_EXIT',p.returncode);raise SystemExit(p.returncode)
