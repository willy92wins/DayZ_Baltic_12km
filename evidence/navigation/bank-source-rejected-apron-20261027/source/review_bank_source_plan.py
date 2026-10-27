from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'bank-source-plan-review-20261027';O.mkdir(exist_ok=False)
paths=[W/p for p in ['plans/ev112-bank-source-attribution-20261027.md','product-spec.md','tools/navigation/inspect_navmesh_v9_ev112.py','evidence/navigation/kit7-nav-payload-cost-20261027/result.json','evidence/navigation/kit7-post-load1-diagnostic-20261027/README.md']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revision independiente READ ONLY, sin editar/comandos/Git/MCP/subagentes. Fable5.1, maximo600palabras SOUND/SOUND-with-fixes/NEEDS-WORK, FIN_REVISION. Lee el plan nuevo W/plans/ev112-bank-source-attribution-20261027.md (W es el worktree del source-hashes.json en E:/DayZ-Baltic-Build/shape-repair-20261025/bank-source-plan-review-20261027). La fase de formato ya cerrada ypublicada ff3e9d0, NO reabrirla. Esta faseatribuyesieteFAIL y sietePASS a fuente/LODreal y banda deperfil antesdeproponercorrección deorilla/apoyo. NO cambia activos ni regenera ni tocaagua. Source surfaces.npz tiene bed,water,axis,station,level ylas copias collision-only deberían mantenerlas; comprobaciónporhashyconsumidornativo antesdeusarlas. SieteFAILoriginal/Nav12; toleranciasintactas, fuente-motor0.002soloatribución. Contrastaaplicacióntriángulos/bandas/agua vsRoadway/integridad. qparamétriconoesdistanciafuera4porcurvatura; wetvisual<=2.25,2.25..4laderabanco; fixedsolver<=4 noestodoagua. Presupuesto15min0runs0generaciones. Noaprobarcambiofísico,pedirsoloarreglosnecesariosdeesteplanread-only; fuente APIrealcontinuous_stream_pilot_v31.py. Siestaatribuciónyasehizoenunaevidenciaconcreta, citarla para no repetir.'''
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
