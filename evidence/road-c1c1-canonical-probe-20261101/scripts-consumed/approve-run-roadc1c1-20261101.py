from pathlib import Path
import json,hashlib
R=Path('E:/DayZ-Baltic-Build/shape-repair-20261025');D=R/'road-c1c1-local-author-20261101';V=R/'road-c1c1-code-review-20261101'
suite=json.loads((R/'road-c1c1-suite-r3-20261101/completion.json').read_bytes());assert suite['rc']==0 and suite['reason'] is None
fix=json.loads((D/'correction-completion-final.json').read_bytes());assert fix['within_budget']
for n,h in fix['files'].items():assert hashlib.sha256((D/n).read_bytes()).hexdigest()==h
assert hashlib.sha256((D/'contract.json').read_bytes()).hexdigest()=='3d7f5b6ad2630107dfa1b2643c1b0d0da3170c1a04192580809c17ad6f0cd075'
adjudication='''# Adjudicación RoadC1C1

Muse Wonder1.0 nativo132.531s SOUND-with-fixes. Identidad servida run.usage y terminal completo guardados. Codex executor e integrador comparten contexto; postimagen no releída por otra familia.

F1 aceptado: pin fixture completo y rechazo PIN_SCHEMA del consumidor. SuiteR0 28PASS/1ERROR no fue gate verde.
F2 parcialmente refutado: el preparador ya leyó lstat/tag/os.readlink reales antes del contrato; los tests simulados no pretendían certificar junction real. La función nueva comprobó el alias/canónico reales contra el contrato congelado: MATCH, sin normalización ni repin. Esto no promete identidad continua.
F3 aceptado: consumidor liga comando/cwd/raíz y árbol observado del preflight, revalida imágenes observadas, cada STARTED al comando/tiempo/logger del recibo, perfiles antes/después y métricas presupuestarias declaradas. Todos los prerequisitos CLOSED exigidos para aceptación completa. El preflight valida raíz/argv y descendencia observada; la allowlist de herramientas de compilación se aplica a brazos nativos. RSS/disk del recibo no son una segunda instrumentación independiente. Se añadió repro propio de journal incorrecto que R0 aceptaba. No atribuir ese hallazgo a Muse.
F4 aceptado en intención: reconstrucción propia por sustitución simultánea, cardinalidad y equivalencia XML; se rechaza importar la transformación del productor por independencia. Ambas usan XML/biblioteca estándar.
Firma: Authenticode Valid observado; chainBuilt=false se conserva y no se afirma cadena válida. El primer preparador WindowsPowerShell falló al cargar módulo; el segundo añadió aserción chainBuilt no requerida y paró. Recuperación sólo leyó resultado guardado; contrato anterior a código. No causa global inferida.

Una corrección de74.332s dentro180: R1 omitió inserción por patrón de salto de línea, negativos lo detectaron; dos casos además pararon DISK_FREE en TEMP de C. La misma ventana corrigió inserción y trasladó fixtures a E; guardas reales y contrato intactos. R2 32PASS; último método añadido cubre preflight/perfil y R3 33PASS2.421s sin skips. C observado2725011456B libres, E400829521920B; no limpieza ajena.

Máximo autorizado una sonda aislada, no DayZ ni mapa. p48/controles/council y scripts previos intactos. Hipótesis: ruta canónica permite superar el rechazo anterior sin desactivar el guard; cualquier nuevo fallo se conserva sin retry ni ampliación.
'''
(V/'adjudication.md').write_text(adjudication,encoding='utf-8')
files={n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in [*fix['files'],'contract.json','oracle.json','oracle-c1c1.json','delta-oracle.json','preflight-local.py']}
(D/'approval.json').write_text(json.dumps({'status':'INTEGRATED_FOR_ONE_COMPILE_PROBE','files':files,'review_seconds':132.531,'suite_methods':33,'suite_seconds':suite['seconds'],'correction_seconds':fix['seconds'],'external_postimage_review':False},indent=2))
src=(R/'run-roadc1c-pair-20261029.py').read_text();src=src.replace('road-c1c-local-author-20261029','road-c1c1-local-author-20261101').replace('road-c1c-real-20261029','road-c1c1-real-20261101').replace('road-c1c-probe-20261029','road-c1c1-probe-20261101').replace('probe_road_compile_c1c.py','probe_road_compile_c1c1.py').replace('observe_road_compile_c1c.py','observe_road_compile_c1c1.py')
target=R/'run-roadc1c1-pair-20261101.py';assert not target.exists();target.write_text(src,encoding='utf-8')
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/handoff-astra-map-review-6d301c')
header='# RoadC1C1 sonda propia autorizada y preparada\n\nSeguir run-roadc1c1-pair-20261101.py y road-c1c1-real-20261101, no duplicar. Contrato3d7f5b6a intacto; Muse132.531s adjudicado,33testsR3 PASS2.421s. Una corrección74.332s. Writer930/observador120, copy180, ayudas30 y brazos300; sin retry. No DayZ/run/lease/mapa.\n\n'
for p in [W/'HANDOFF.md',R/'ACTIVE-WORK.md']:p.write_bytes(header.encode()+p.read_bytes())
print(json.dumps({'ready':str(target),'contract':files['contract.json']}))
