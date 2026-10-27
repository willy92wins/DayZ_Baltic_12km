from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-config-types-code-review-20261027';O.mkdir(exist_ok=False)
paths=[W/'plans/ev112-kit7-native-config-types-20261027.md',W/'missions/BalticNavConfigTypes.BalticTrial/init.c',W/'tools/navigation/verify_nav_config_types_ev112.py',W/'tools/navigation/test_nav_config_types_ev112.py',R/'prepare_kit7_config_types_runtime.py',R/'orchestrate_kit7_config_types_probe.js',R/'capture_kit7_config_types_log.ps1',R/'finish_kit7_config_types_probe.py',R/'verify_c_orderly_close.py',R/'capture_owned_server_identity.ps1',R/'copy_owned_server_rpt.ps1',R/'kit7-native-config-types-20261027/script-validator.json',R/'kit7-native-config-types-20261027/coordinator-controls.json',R/'kit7-native-config-types-20261027/command-flow-controls.json',Path('P:/scripts/3_game/global/game.c')]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p):sha(p) for p in paths};(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Revisión independiente OPERATIVA, Fable5.1 READ ONLY, una lane, no council. Solo Read/Glob/Grep; sin editar ni ejecutar procesos/MCP/Git/subagentes. Máximo900palabras, veredicto SOUND/SOUND-with-fixes/NEEDS-WORK, anclas y FIN_REVISION. Fuentes en E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-config-types-code-review-20261027/source-hashes.json. Revisa implementación de plan ya revisado: 9 lecturas config en servidor Nav8 intacto, consumidores y lifecycle. No cambia mapa/NM/PBO/config, ni benchRAM ni607. Getter script no demuestra conversión del cargador; no inventar código nativo. Comprueba wire schema, controles(int/float/text/inexistente), permiso de observar errores getter, archivo RPT completo y atribución inconclusa, identidad/hash antes/después y cierre estricto. FIFO directo sin prelease/preconsulta; adopta solo propio, heartbeat y observer, cierre/release finally. Un intento,300sarranque+120scaptura+600sobserver. Suite lector15tests pasó, 1EnforcePASS;13casosflow/2mutantes y8completionPASS. Modificación de stockinventory exact previa a lanzamiento además hashes. Tests son mocks, no aceptan comportamiento nativo. Codegeneration bootstrap ya consumido excepto hash stock aún puede estar acabando; no ejecutar preparador. Señala fallos concretos; no exigir reescrituras adyacentes ni ciclos ilimitados. Identifica limitaciones materiales, sin reducir tolerancias. Tu review anterior tomó como hecho no probado ParamEntry/mensajes exactos del loader; no repetir.
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
