from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-onload-package-code-review-20261027';O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-kit7-onload-numeric-pilot-20261027.md',W/'tools/navigation/package_nav8_onload_config_ev112.py',W/'tests/test_nav8_onload_config_ev112.py',W/'tests/fixtures/nav8-onload/original.cpp',W/'tools/playtest/attach_navmesh.py',R/'kit7-onload-numeric-plan-review-20261027-v2/adjudication.json']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión independiente SOLO EMPAQUETADOR, Fable5.1 READ ONLY, una lane no council. Solo Read/Glob/Grep; no escribir/ejecutar/MCP/subagentes. Máximo650palabras, SOUND/SOUND-with-fixes/NEEDS-WORK, anclas yFIN_REVISION. Fuentes E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-onload-package-code-review-20261027/source-hashes.json. Plan previoSOUND-withfixes integrado. Herramientanueva cambiaúnicamenteOnLoadstringtrue->int1 desdeworldac088...; mismoNM yWRPhashesfijos, decode/compile/decode ycontrolnuloBYTEigual, scopeycomparaciónindependiente detokens, empaquetadoFileBank/paridadtodoselementos yprops, relecturaconfigempaquetado. 14tests pasadosincluyendofixtureliteralNav8hashconstante. Revisa bugsconcretos/falsepass. Noaprobarsonda/RAMtodavíanoescritos: esta fase terminaenPBOnuevoE: sin sustituir/desplegaroriginal. Posterior deploymentrelectura y607/RAM condicionados aparte. Pregunta siaseguraaislamientodelflagynohaycambiossilenciosos almaterialWRP/NM. Losnegativoscontenedorhash/extraentrypodránvalidarseconmutacionesfixturepequeñoantesdelempaquetado; indica si faltaalgo crítico. No imponerrewritedelparseradjacente sinfalloconcreto. No confundirconfiggetter conloader.
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
