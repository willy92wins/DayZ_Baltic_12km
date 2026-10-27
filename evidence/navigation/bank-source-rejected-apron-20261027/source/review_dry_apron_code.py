from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'dry-apron-code-review-20261027';O.mkdir(exist_ok=False)
paths=[R/'pilot_dry_apron.py',R/'test_dry_apron_pilot.py',W/'tools/water/continuous_stream_pilot_v31.py']+[W/p for p in ['plans/ev112-dry-apron-offline-pilot-20261027.md','product-spec.md','tools/navigation/inspect_navmesh_v9_ev112.py','evidence/navigation/kit7-nav-payload-cost-20261027/result.json','evidence/navigation/kit7-post-load1-diagnostic-20261027/README.md']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''READ ONLY revision de código acotada, noeditar/comandos/Git/MCP/subagentes. Fable5.1; maximo600palabras, SOUND/SOUND-with-fixes/NEEDS-WORK, FIN_REVISION. Fuentes E:/DayZ-Baltic-Build/shape-repair-20261025/dry-apron-code-review-20261027/source-hashes.json. Plan ya revisado/adjudicado; revisa SOLO pilotoarraysaislado antesdeejecutar, no reabrirdiseño.
Código pilot_dry_apron.py mantiene fuentes porhash, no modificamapa:salidanuevaarraybed;mismafunciónhistóricaASTfair_support500iterpeso.002;priorlinealq4/18,baseqwet<=4exacta,XY/sourceallarraysintactas,proteccionesoriginalesconguardareal y60m;groundarchivado815ef8b7; piso hist1/1024+2e-6, floor>ceilingyquantintervalfueraantesdesolver;dirquantize. Gatesfisicosdependiente realesXZydiscreteenergyweight0 antes/después. NoPBO/NMG/run niRAM, comparación14XYZconnavviejasoloDESCRIPTIVA. Tests7 geometríacuantización/guardas/pendienteconocida/nonfinite/collapsed. Fuentesroadsrootexternascomparadashashauthor-report. Noafirmarcurvaturafísicaniaceptaciónvisualporenergygrid. Buscarfallosconcretos,contradiccionesplan,dominiosprotegidos,NOOP/intervalos,ybeneficiosquenoseanreales. No pedir pruebas nativas antesdeun pilotoofflinequepuedeREJECTED. Cualquierfallohazrepro concreto. Máximo una correccióndecódigo; nohaybarridoperfilespesos.'''
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
