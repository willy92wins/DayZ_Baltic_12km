from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'bank-attribution-pilot-review-20261027';O.mkdir(exist_ok=False)
paths=[R/'attribute_bank_source.py',R/'bank-source-attribution-20261027/result.json',W/'plans/ev112-bank-source-attribution-20261027.md',W/'tools/water/continuous_stream_pilot_v31.py']+[W/p for p in ['plans/ev112-dry-apron-offline-pilot-20261027.md','product-spec.md','tools/navigation/inspect_navmesh_v9_ev112.py','evidence/navigation/kit7-nav-payload-cost-20261027/result.json','evidence/navigation/kit7-post-load1-diagnostic-20261027/README.md']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión READ ONLY independiente, sin editar/comandos/Git/MCP/subagentes. Fable5.1. Maximo700palabras, dosveredictos ATRIBUCION yPLANPILOTO SOUND/SOUND-with-fixes/NEEDS-WORK, FIN_REVISION. Fuentes E:/DayZ-Baltic-Build/shape-repair-20261025/bank-attribution-pilot-review-20261027/source-hashes.json.
Atribución ejecutada14puntos(7FAIL/7PASS) -> todosq±6OUTER_APRON. Residuo fuente/motor<4.84e-7.5fixturesplanar/q-station/outside/degenerate/topology. Archivo fuente9d8caf0f yautor8b340a2a como histórico. PBO3d9550bf yODOLscorrectosporhashcomparaciónentries; esta cadena+comparaciónlocalNOprueba todaautoríaPBO. Geometrycapprevio~.002peroláminaW ywater_extW-.25separados. q6paramétriconodistanciafísicafuera4. Modelo topologíafunciónASTexactafuente, maxheightno seleccióndeYobjetivo; si 2carasencimaquedantodas. Revisarambigüedad/límites.
Planpiloto nuevo: UNpriorlinealexterior entreq4/18; mismofair_supportactual, agua/interior/XY/terreno/proteccionesexactos. Soloarraysaisladas,sinMLOD/PBO/NMG/DayZ; no bajaoráculos, NO compararYnavvieja comoPASS. Hipótesisgeométricaautorizadaporpeticiónusuario suavizarríos/terreno, dentrodelimitaciones. Gateofflinecurvatura ypendientemaxnoempeoran,cotastrascuantización. Unsolver500iter15min, cero barrido. Revisa viabilidad de cotas, proteccionesoriginales ycuantización; si cambiaforma deproductoprotegidaexplicarmotivoexacto. No proponerotraanchura okeydesconocida. No exigirprometerque nuevaspolígonosconservenY. Fuentecontractfair_support68-89 yperfil286-319 están verificados. Siplanrechazado señalarrepro/invarianteconcreta; noaprobarbuildruntime todavía.'''
(O/'brief.md').write_text(brief,encoding='utf-8')
args=['C:/Users/guill/.local/bin/claude.exe','--print','--safe-mode','--model','claude-fable-5-1','--effort','medium','--tools','Read,Glob,Grep','--allowedTools','Read,Glob,Grep','--output-format','json','--no-session-persistence']
start=time.monotonic()
with (O/'response.json').open('wb') as out,(O/'stderr.log').open('wb') as err:
 p=subprocess.Popen(args,cwd=W,stdin=subprocess.PIPE,stdout=out,stderr=err,creationflags=0x08000000)
 try:p.communicate(brief.encode(),timeout=300)
 except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=30);raise
assert all(sha(Path(k))==v for k,v in before.items())
(O/'completion.json').write_text(json.dumps(dict(returncode=p.returncode,inputs_unchanged=True,seconds=time.monotonic()-start),indent=2)+'\n')
print('FABLE_EXIT',p.returncode)
