from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'nav8-storage-plan-review-20261027';O.mkdir(exist_ok=False)
paths=[W/p for p in ['plans/ev112-nav8-storage-feasibility-20261027.md','product-spec.md','tools/navigation/inspect_navmesh_v9_ev112.py','evidence/navigation/kit7-nav-payload-cost-20261027/result.json','evidence/navigation/kit7-post-load1-diagnostic-20261027/README.md']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revision independiente READ ONLY. No editar, ejecutar comandos, Git, MCP ni subagentes. Fable5.1 nativo revisa; Codex integra. Maximo900palabras, SOUND/SOUND-with-fixes/NEEDS-WORK y FIN_REVISION.
Lee el plan E:/DayZ-Baltic-Build/shape-repair-20261025/../shape-repair-20261025/nav8-storage-plan-review-20261027/source-hashes.json y sus fuentes. Plan de lectura25min para evaluar costes/viabilidad antes de otro candidato. Nav8 607PASS pero RAMFAIL;12m3FAIL y12.5m4FAIL. Load1 interrumpido: no repetir. Diagnostico local confirma abanicos en6XZ, no algoritmo generador. Faltan contrato VAND12 completo y mecanismo. Se propone contraste upstreamDetour7 vsDayZ12 y longitudes de colas empiricas sin escritorNM ni cambios binarios/generacion/partida. Critica si es callejon sin salida; identifica la alternativa mas simple que pueda verificarse con fuentes, NO inventes APIs/keys/formatos. No confundir tamano serializado con heap. No bajar tolerancias ni declarar soporte completo por formulas. Revisa alcance, presupuesto y condicion de rechazo. Mantener propuestas tecnicas acotadas; el council ampliado solo despues del trabajo pendiente. FUENTES en source-hashes.json.
'''
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
