"""Preserve EV80 evidence and update the current project state; no large builds or shared memory."""
from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
D=W/'evidence/v30-mixed-bank-relief-2026-10-10'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda n:json.loads((B/n).read_text())
assert read('review-luna/report.json')['status']=='PASS_EV80_CONSUMER'
assert read('compiled-package-review.json')['status']=='PASS_EV80_COMPILED_PACKAGE_REVIEW'
assert read('native-verification.json')['status']=='PASS_COMPLETE_NATIVE_READBACK'
assert read('changed-mips.json')['status']=='PASS_ALL_CHANGED_MIPS'
close=read('lifecycle-close.json')
assert close['close']['graceful'] and not close['final']['owner_present'] and not close['final']['box_occupied']
assert not D.exists()
D.mkdir(parents=True)
for p in sorted(B.iterdir()):
    if p.is_file() and (p.suffix in {'.py','.json','.md','.png','.log'} or p.name=='terrain-delta.npz'):
        shutil.copy2(p,D/p.name)
for folder in ['review-luna']:
    (D/folder).mkdir()
    for p in (B/folder).iterdir():
        if p.is_file() and p.suffix in {'.py','.json','.md'}:shutil.copy2(p,D/folder/p.name)
rpt=Path('P:/DayZ_MCP_dev/_server/profiles/DayZDiag_x64_2026-10-10_04-27-24.RPT')
lines=rpt.read_text(errors='replace').splitlines()
(D/'runtime-rpt-excerpt.log').write_text('\n'.join(lines[:54]+['...']+lines[-5:])+'\n')
(D/'runtime-rpt-identity.json').write_text(json.dumps({'path':str(rpt),'sha256':sha(rpt),'size':rpt.stat().st_size},indent=2)+'\n')
summary='''# Suavizado global de taludes EV80 — 10-10-2026

EV80 está desplegado en `P:/Mods/@DayZ_Baltic_MixedBankPreviewV1` y la lectura de alturas de todo el mapa pasa. Es una mejora geométrica comprobada, no la aceptación de la base 1.0 ni del render del agua.

- Fuente: EV79; candidato `0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b`. Dos agentes Luna: autoría y consumidor independiente. Se corrigieron fallos de implementación antes del único cálculo completo; los intentos inválidos están registrados y nunca produjeron un terreno utilizable.
- Alcance: vértices de tierra libres a 96 m o menos de ríos/arroyos, participantes en quiebros >30°. 4329 evaluados, 2591 editados; delta −0,2194 a +2 m. Metadatos, soporte mojado, P/F, reservas, plataformas y sus protecciones exactos.
- Consumidor independiente: energía angular de las bisagras modificadas −21,22%; p99 seco de ribera 5,00489→4,98207°. Cero quiebros nuevos >30°, cero máximos peores en 330 sectores modificados. Quiebros mixtos >30°: 4693→3384. El informe residual distingue grados de libertad y protecciones; no equivale a haber eliminado todos los taludes poligonales.
- Modelos compilados: 10429 caras físicas y 14978 visibles intersectadas en 1335 celdas; 0 m² de agua ganada o perdida. Los 18033 objetos y materiales del WRP son idénticos a EV79.
- Superficie: 459 teselas regeneradas con su margen, 565 intactas por identidad de entradas, 2308 solapes sin diferencias. Cambian 720 píxeles de máscara y 3401 de satélite. Compresión: 2410 píxeles húmedos de borde no-grava inventariados; ninguno en el interior a >=4 píxeles del borde. No afirmar cero sobre toda la huella.
- Paquete: 132 PAA y el WRP cambian; 6694/6827 entradas exactas. 1056 mipmaps nuevos verificados, con controles negativos. Revisión independiente del PBO fuente/desplegado en PASS.
- Motor: run `fea3ba4e-88a5-48ae-92f3-c10732f9e192`, solo servidor y sin file patching. 4194304 vértices, 1212 puntos y 1205 planos; error máximo 1,52588e−5 m. Siete negativos detectados. Los puntos de control y sus planos no cambian respecto a EV79.
- Inventario nativo: 25 flags ausentes de agua de diseño, 317 escalares sin flag y 3 lecturas dinámicas en playa. Las tres playas conservan altura 0,8000–0,8032 m, bajo el mar en la fase muestreada; ninguno de los 5 flags A o 88 escalares Q añadidos cae en un vértice editado. No es un cierre del shader ni una comparación de fases iguales.
- RPT conserva mensajes de entorno/animación y stack PluginItemDiagnostic; no se declara limpio. Censo completo y cierre orderly confirmados, lease liberado y banco libre.

Diagnóstico posterior: de los 3384 quiebros residuales, 3167 tocan el selector original y 217 quedan íntegramente fijados por protecciones en sus esquinas de ribera. El replay único de 89,844 s reproduce exactamente las alturas EV80. Los 1275 rechazos p99 pasan los invariantes locales con un ULP hacia la altura previa; no se aplicaron al replay ni se guardó el margen angular original por coordenada. No equivalen a imposibilidad geométrica. La aplicación conjunta requiere un candidato y consumidor separados: plan EV81 en `E:/DayZ-Baltic-Build/v30-mixed-bank-float32-20261010/plan.md`. EV80 sigue vigente hasta que pase ese proceso.

Identidades de distribución: mundo `ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038`; agua `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`; OPRW `3ae8f82cfc7279cec5c58dd8f253b9da79bfbfe52004695ebe02cb5587383680`.

Pendientes: rectángulos grises y agua aparente sobre tierra (sin causa local aislada), contornos mojados/giros/finales, niveles protegidos y excepciones EV68, decisión sobre grandes lagos, Terrain Builder y después navmesh. No reabrir pruebas visuales inválidas como si hubieran concluido. El ticket de foco ya existe; esta sesión no lo duplicó. EV79 anterior se conserva para rollback; EV68 sigue sin promoción.

Los NPZ/PBO completos permanecen en E:/P: identificados por hash. Aquí se conserva el delta reversible, scripts, resultados y referencias. La figura es geometría offline. Sin push.
'''
(D/'README.md').write_text(summary,encoding='utf-8',newline='\n')
manifest=[]
for p in sorted(D.rglob('*')):
    if p.is_file():manifest.append(dict(path=p.relative_to(D).as_posix(),sha256=sha(p),bytes=p.stat().st_size))
(D/'manifest.json').write_text(json.dumps({'files':manifest,'candidate_sha256':read('authoring.json')['candidate_sha256']},indent=2)+'\n')
handoff=W/'HANDOFF.md';text=handoff.read_text(encoding='utf-8')
updates={
 'status:':'status: BASE_1_0_NO_ACEPTADA. EV80 suaviza taludes a escala de mapa; consumidor, paquete y lectura nativa completa PASS. Render del agua y contornos mojados siguen abiertos. EV68 separado, sin promoción.',
 'candidate:':'candidate: @DayZ_Baltic_MixedBankPreviewV1 EV80. Mundo ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038; agua 3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14; terreno 0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b. EV79/72 conservados; aspecto artístico pendiente.',
 'smoothing:':'smoothing: EV79 quitó 58 crestas secas fuertes Narva. EV80 procesa 4329 nodos libres y cambia 2591; quiebros mixtos >30 pasan 4693→3384, energía incidente −21,22%, p99 seco 5,00489→4,98207. Sin nuevos >30 ni máximos peores en 330 sectores. Diagnóstico residual y discriminador numérico en evidencia EV80; no asumir que el resto es ineditable.',
 'runtime_lock:':'runtime_lock: EV80 run fea3ba4e-88a5-48ae-92f3-c10732f9e192 SERVER_ONLY cerrado orderly; lease liberado, owner null/self none/banco libre. Ningún run pendiente de foco.',
 'surface:':'surface: EV80 459 teselas regeneradas/2308 solapes PASS; 132 PAA+WRP cambian, 6694 entradas intactas, 1056 mips PASS. Motor 4194304 vértices/1212 puntos/1205 planos PASS, error 1,52588e−5m. Tres flags dinámicos en playas intactas bajo la fase de mar; 25 flags ausentes y 317 escalares inventariados. No cierre gráfico.',
 'git:':'git: Branch claude/codex-handoff-review-74f290; checkpoint previo 66b8f48. Evidencia EV80 en evidence/v30-mixed-bank-relief-2026-10-10; consultar git log para checkpoint actual. Sin push.',
 'next:':'next: Usar el diagnóstico residual EV80 y numeric-boundary-plan.md antes de otra autoría. Distinguir rechazo float32 de límite real, sin relajar gates; continuar riberas/contornos y render gris. Ver estado del discriminador en evidencia. No repetir EV78 rechazada ni promover EV68.',
 'handoff:':'handoff: evidence/v30-mixed-bank-relief-2026-10-10/README.md + manifest. EV80 geometría, paquete y motor PASS; base1.0 abierta. Mantener fondo/calado/agua/carreteras/plataformas y pruebas separadas de render.'}
start=text.index('<!-- LIVE-STATE:START -->');end=text.index('<!-- LIVE-STATE:END -->')
block=text[start:end].splitlines()
for i,line in enumerate(block):
    for key,value in updates.items():
        if line.startswith(key):block[i]=value;break
text=text[:start]+'\n'.join(block)+'\n'+text[end:];handoff.write_text(text,encoding='utf-8',newline='\n')
bugs=W/'bugs.md';old=bugs.read_text(encoding='utf-8');note='> Actualización EV80 (10-10): taludes globales, 2591 vértices y quiebros mixtos >30 de 4693 a 3384. Consumidor independiente, paquete y lectura nativa completa PASS; sin nueva exposición de agua ni cambios de ingeniería. Persisten 3384 quiebros mixtos, contornos mojados y render gris. Las tres lecturas dinámicas de playa son sobre alturas intactas; no cerrar agua sobre tierra por ello. Evidencia: `evidence/v30-mixed-bank-relief-2026-10-10/README.md`.\n\n'
bugs.write_text(note+old,encoding='utf-8',newline='\n')
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-10-dayz-baltic-bank-relief.md')
with session.open('a',encoding='utf-8') as f:f.write('\n## Continuación EV80\n\n'+summary.split('\n\n',1)[1]+'\nEvidencia durable: '+str(D)+'\n')
print(json.dumps({'evidence':str(D),'files':len(manifest),'bytes':sum(x['bytes'] for x in manifest)},indent=2))
