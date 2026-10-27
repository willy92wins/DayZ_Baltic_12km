from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-config-types-plan-review-20261027';O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-kit7-native-config-types-20261027.md',R/'package-kit7-nav8-input-20261027/config.cpp',R/'chernarus-current-config-20261027/config.cpp',Path('P:/scripts/3_game/global/game.c'),R/'kit7-nav-payload-cost-20261027-v2/result.json',R/'kit7-nav-payload-cost-20261027-v2/controls.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión independiente de PLAN, Fable5.1 READ ONLY, una lane, no council. SOLO Read/Glob/Grep; sin escrituras, procesos, MCP, Git, subagentes. Máximo800palabras, SOUND/SOUND-with-fixes/NEEDS-WORK con anclas y FIN_REVISION. Lee fuentes de E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-config-types-plan-review-20261027/source-hashes.json. Codex integra. Pregunta: ¿merece la sonda nativa propuesta, sin tocar PBO, para distinguir el ConfigGetInt de filterIsolatedIslands(string true) de Chernarus(número1)? No afirmamos que cargador use ese getter ni que sea causa RAM. Plan separa conversión de efecto y noautoriza modificar propiedad. Nav8mismaNM/geom607PASS peroRAMFAIL; el censo0tilesvacíos no es profiler. Revisa diseño, controles, erroresdelgetter, alcance y decisión posterior. Si esto noaporta nada más que configdecodificado, dilo con mecanismos reales; no inventes fuente nativadelcargador. APIsdegame.cpor líneas citadas; archivo grande,lecturas acotadas. Tu revisión anterior sugiere heurística deesquinas; Codex no la adopta aún por nohaberoráculoindependiente yporque falloheurístico nopermitecerrartodoelejedeanchos. LosPtotal reales son1255/1257/1248en8/12/12.5 yhayrutas3-16waypoints, no asumir todosdos. No pedir autorización nueva para sondareadonlyya dentrodelencargo. No implementes.
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
