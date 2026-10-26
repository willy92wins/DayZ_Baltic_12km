from pathlib import Path
import hashlib,json,subprocess,time
R=Path(__file__).parent;W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
O=R/'kit7-nav-height-review-20261026';O.mkdir(exist_ok=False)
paths=[R/'kit7-nav-consumer-20261026/result.json',R/'kit7-nav-consumer-20261026/runtime.log',R/'kit7-nav-consumer-20261026/reference.json',R/'kit7-nav-height-diagnostic-20261026/result.json',R/'kit7-nav-layer-diagnostic-20261026-v2/result.json',R/'kit7-nav-layer-diagnostic-20261026-v2/config.cpp',W/'missions/BalticKit7NavV1.BalticTrial/init.c',W/'tools/navigation/verify_kit7_nav_ev112.py',W/'plans/ev112-kit7-navigation-consumer-20261026.md']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before={str(p):sha(p) for p in paths}
(O/'source-hashes.json').write_text(json.dumps(before,indent=2)+'\n')
brief='''Juicio técnico acotado READ ONLY por Fable5.1 CLI nativo. Codex es executor/integrador, tú revisor independiente. Solo Read/Glob/Grep, sin procesos, MCP, subagentes, Git ni escrituras en ningún lugar. Máximo600palabras; una respuesta final con hechos/hipótesis, discriminadores baratos, posible corrección mínima y límites. No se solicita council nuevo ni cambio de producto.
Proyecto W=C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c. Lista precisa de evidencia en E:/DayZ-Baltic-Build/shape-repair-20261025/kit7-nav-height-review-20261026/source-hashes.json. Esta revisión aporta alternativas de diagnóstico; no aprueba un arreglo no construido. Modelo/ruta comprobados hoy en las revisiones anteriores; confirmar identidad en respuesta del CLI.
Kit7: navmesh regenerada con mundo y piloto actuales, empaquetada byteexact salvo NM. Sonda nativa607completa:607consultas de pathPASS,562corredoresXZPASS,4waypointsFAIL altura (piezas124/133orilla derecha). Tolerancia0.801m NO se relajará. Terrain y Roadway consultados en mismos XZ; Roadway coincide con packed, visual y Geometry dentro0.008m, pero navmeshqueda0.85-1.17mabajo en los cuatro. No es causa raíz todavía. ValoresQdemuestranque SampleNavmeshPosition ya devuelveybaja; FindPathusaesosmismos puntos. GenParamsreales12.5m,cellSize1=.25,2/3=.1. No inventar semántica deparámetros ni proponer regenerarigual.
Investiga fuente concreta y propone cómo aislar mecanismo: geometría ignorada/parcial, simplificación vertical, capa subyacente, caché o test. Distinguir el hecho de que física6801puntos pasó del contrato geométrico fallido. Hay antecedente local en C:/Users/guill/.codex/skills/dayz-terrain-workflow/references/navmesh-bootstrap.md líneas320-350: alturas geométricas erradas con actores que cruzaban; eso NO permite declarar nuestra malla PASS ni suponer causa. Usuario quiere corregir fallos hasta pasar y ya autorizó pruebasautónomas. No justificar green mediante cambiar rutas/tolerancias ni mover navwaypointsenlector. Sugiereunexperimentoaislado yquéresultado lo refutaría. Navegación/paqueteactualintactos; noprocesonativovivo.
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
