from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'dry-bank-domain-plan-review-20261027';O.mkdir(exist_ok=False)
paths=[R/'pilot_dry_apron.py',R/'dry-apron-linear-pilot-20261027/result.json',W/'tools/water/continuous_stream_pilot_v31.py']+[W/p for p in ['plans/ev112-dry-bank-domain-pilot-20261027.md','product-spec.md','tools/navigation/inspect_navmesh_v9_ev112.py','evidence/navigation/kit7-nav-payload-cost-20261027/result.json','evidence/navigation/kit7-post-load1-diagnostic-20261027/README.md']]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''READ ONLY Fable5.1, noeditar/comandos/Git/MCP/subagentes. Maximo650palabras SOUND/SOUND-with-fixes/NEEDS-WORK, FIN_REVISION. Fuentes E:/DayZ-Baltic-Build/shape-repair-20261025/dry-bank-domain-plan-review-20261027/source-hashes.json. Plan nuevo debejuzgarse ANTESdecódigo.
Piloto previoREJECTED: energy561.733→562.120peor,345iter; bajaYmax.078; ninguna integración. AdemásCodexdetectóreproCAP:201puntosdonde min(s,L-s)<6 modificados−.02539, anteriorfixed_exact solo validaba su propia máscara; registrarerrorrealymantenerrechazo,no arreglarrelanzarviejo.
Nueva hipótesis fuente:mantener|q|<=4impidealisar la ladera seca2.25..4; examinar TODAorillaseca|q|>2.25hasta18 conpriorlineal2.25→18, mismo.002/500sinbarrido. Agua/lecho|q|<=2.25exactos,anchura4.5,nivelwater/W-.25caladoinmutables,cap<=6entero fijo+protecciones reales. Baselineoriginal9d8,nocandidaterechazado. Consumidorpreservacionesindependientede máscaraautor:mutantesCAPinterior,lecho,XY,water. Soloarraysaisladas15min, noPBO/NMG/run,energiaypendientegatesintactos,14XZdescriptivosnuncaPASS. Ámbitoes suavizarorillasecaautorizadoporusuario; si hay contradicción deproducto protegida concreta, señalarla. Este es cambio de dominio (nopesos), noquierodeclararcorrectomientrasalgoempeore. SalidaOFFLINE_CANDIDATE_ONLYoREJECTED; buildrequiereotroplanrevisado.
Revisa si este experimento es razonable o viola un hecho, API/máscaras, quécontratoCAPindependiente falta ycriteriosclaros. No pedircouncilampliado ni repetirscriptsconsumidos. Preserva hecho:PASSyFAILcompartenq6;noasumircausainterna delgenerador.'''
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
