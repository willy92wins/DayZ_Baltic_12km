from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-onload-numeric-plan-review-20261027-v2';O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-kit7-onload-numeric-pilot-20261027.md',W/'tools/navigation/package_nav8_config_ev112.py',W/'tools/playtest/attach_navmesh.py',W/'tools/performance/compare_server_baseline_ev112.py',R/'kit7-native-config-types-20261027/result.json',R/'kit7-native-config-types-20261027/identity-verification.json',R/'kit7-native-config-types-20261027/script-config-observations.json',R/'kit7-nav8-ram-ab-20261027/comparison.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión independiente PLAN Fable5.1, READ ONLY, una lane, NO council. Solo Read/Glob/Grep, no procesos ni ediciones ni MCP. Máximo750palabras, SOUND/SOUND-with-fixes/NEEDS-WORK, anclas, FIN_REVISION. Fuentes E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-onload-numeric-plan-review-20261027-v2/source-hashes.json. Sonda anterior validada: ambos flags Baltic stringtrue devuelven int/float0, Chernarusnum1=>1. No mensajeconversiónRPT, avisoszonasfueramarcadores, nogetterwarning. Nuevo plan soloOnLoadnum1,mismoNMNav8 ygeometry,modexperimentalnuevo. Objetivo:607PASS+RAMcontraChernarus, sinatribuircausalidadcomparandohistóricos. Crítica independiente: aislamiento config/roundtripbyteparity, positivosnegativos, adecuaciónRAMABBAABactual, riesgosnavislasfuera607 ypromociónlocalúnicamente. No insistir en repetirbloquehistoricoA/Bsolo para probar causa si noafirmamoscausa; síseñalar si unoraclelocal deja riesgoinaceptable paraelalcanceexperimental. Propón mejoras necesarias acotadas, no bucles/councilnuevos. Presupuesto explícito, sin rebajatolerancias. La implementaciónvendrádespués deplanaceptado, noaprobarcódigoaúnnoescrito.
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
