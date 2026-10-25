from pathlib import Path
import hashlib,json,shutil
B=Path(__file__).parent;R=B.parent
W=Path('C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert json.loads((B/'native-verification.json').read_text())['status']=='PASS_COMPLETE_NATIVE_READBACK'
assert json.loads((B/'lifecycle-close.json').read_text())['graceful']
E=W/'evidence/v30-bank-relief-2026-10-10';E.mkdir(exist_ok=False)
manifest=[]
def copy(src,dst):
    dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,dst)
    assert sha(src)==sha(dst);manifest.append(dict(source=str(src),file=dst.relative_to(E).as_posix(),sha256=sha(dst),bytes=dst.stat().st_size))
for root,label in [(R/'v30-bank-relief-review-20261010/luna-geometry','geometry-review'),(R/'v30-bank-relief-smoothing-20261010','rejected-ev78'),(B,'ev79'),(R/'v30-mixed-bank-feasibility-20261010','mixed-feasibility')]:
    for p in sorted(root.iterdir()):
        if p.is_file() and (p.suffix in ('.py','.ps1','.md','.json','.csv','.png','.log') or p.name=='terrain-delta.npz'):
            copy(p,E/label/p.name)
    if (root/'review-luna').exists():
        for p in (root/'review-luna').iterdir():
            if p.is_file():copy(p,E/label/'review-luna'/p.name)
for p in (B/'missions/BalticNarvaDryBankFullWaterV1.BalticTrial').iterdir():
    if p.name in ('init.c','risks.csv'):copy(p,E/'ev79/mission'/p.name)
copy(B/'package/world-addonbuilder.log',E/'ev79/world-addonbuilder.log')
report='''# Taludes ribereños EV78/79 — 10-10

EV79 corrige las crestas secas de Narva en un paquete aislado, con consumidor independiente y lectura nativa completa PASS. Base1.0 y aspecto gráfico no aceptados.

- Descubrimiento: 59 diedros>30° completamente secos en la banda96m;58 estaban inmóviles por máscaras históricas de Narva (56 sin otro bloqueo), no por agua/ingeniería. Se reconstruyeron las protecciones por sus componentes, conservando sus solapes. Narva estaba autorizada por Guillermo.
- EV78 amplio rechazado y nunca desplegado: aunque reducía energía24.63%, subía p99, creaba4pliegues>30 y aumentaba máximos en69sectores. No se relajaron gates.
- EV79:12362vértices, delta±2m;58pliegues secos Narva>30 pasan a0; banco global59→1 (restante borde). p995.22233→5.00489°, energía incidente−64.98%, cero pliegues fuertes nuevos y cero sectores modificados con máximo peor. Agua/carret./plataformas/P/F y toda metadata exactos. Exposición física/visible de modelos compilados:0m² ganados/perdidos.
- Superficie:18teselas regeneradas incluyendo padding,90solapes exactos,22PAA cambian,176mips validados;6804de6827entradasPBO idénticas.2048PAA/2048PNG de referencia cotejados. MezclaDXT de237píxeles húmedos en borde inventariada,0interior.
- Motor server-only:4194304vértices/1212puntos/1205planosPASS, máximoerror1.52588e-5m;0 anomalías físicas de tierra seca en muestra.26flags húmedos ausentes vs24previos:23comunes,3nuevos/1retirado, todos en alturas intactas.321escalares sinflag vs302previos:96nuevos/77retirados, ninguno en altura cambiada. Fasesdeonda distintas; no son un cierre del shader. Sietenegativos del consumidorPASS.
- RPT no se declara limpio: hay mensajes de configuración de entorno/animación y stack PluginItemDiagnostic; el censo completó y las entradas de configuración del PBO quedaron byteexactas. No se usa ausencia de errores como prueba.
- Run0db4e884-97a5-40d2-b414-1366b630b0a3 cerrado orderly; lease liberado y caja libre. EV77 anterior agotó autorestorefase9 sin ejecutar wire, banco estaba libre al retomar: diagnóstico gráfico INCONCLUSO, no prueba de causa ni corrección.

Paquete: `P:/Mods/@DayZ_Baltic_NarvaDryBankPreviewV1`. Mundo `df00806c598181e9ddca160781790cd0edc9314095262f6f106a87ed4d464213`; agua `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`; terreno `dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c`; WRP `fee7cad702d5d2278697976654fd62e2ba0f2afbd4ab7c7d9f26369c15099f76`.

La imagen native-bank-comparison.png muestra triángulos reales en escala1:1, offline, sin textura/render DayZ. No elimina la necesidad de aceptación visual final. La copia durable lleva scripts, delta reversible, hashes y evidencias; NPZ/PBO grandes quedan en E:/P: con identidad fijada. No push.

Pendientes: rendergris/agua aparente sobre tierra (016/018/019), contornos mojados/giros/finales (007/020), grandeslagos/EV68excepciones sinpromover,TB/navmesh despuésdegeometría. Censo restante:4768pliegues no4/4secos,3317wet-dry y1451dry-dry por soporte vecino; no agua profunda. Hay3focos de factibilidad, dos mejoran con un nodo. EV80 diseña selección global de crestas libres y límites angulares directos; sigue en curso, sin transferirle PASS deEV79.
'''
(E/'README.md').write_text(report,encoding='utf-8')
(E/'manifest.json').write_text(json.dumps(dict(files=manifest),indent=2)+'\n')
hand=W/'HANDOFF.md';text=hand.read_text(encoding='utf-8')
updates={
'status:':'status: BASE_1_0_NO_ACEPTADA. EV79 suaviza crestas secas Narva, consumidor geometrico y motor completoPASS; rendergris y contornos mojados abiertos. EV68 propuesta separada sin promocion.',
'candidate:':'candidate: @DayZ_Baltic_NarvaDryBankPreviewV1 EV79: mundo df00806c598181e9ddca160781790cd0edc9314095262f6f106a87ed4d464213; agua3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14; terreno dbc59ec542206984060e1d9f13112680694336b5a69bb4269cfe5136cfa0a22c. EV72 anterior preservado. Vista artistica pendiente.',
'smoothing:':'smoothing: EV79 libera SOLO proteccion generica Narva ya autorizada, preserva controles/ingenieria/agua.12362vertices ±2m;58diedros secos>30 Narva→0,banco global59→1;banco p995.22233→5.00489,energia incidente−64.98%,0nuevos>30/0sectores con maximo peor. EV78 amplio RECHAZADO:4nuevos>30,69sectorespeores. EV80 global acotado en curso.',
'runtime_lock:':'runtime_lock: EV79 run0db4e884-97a5-40d2-b414-1366b630b0a3 SERVER_ONLY cerrado orderly,lease liberado,ownernull/selfnone/boxfree. EV77 anterior ya no ocupaba banco;logphase9autorestaurado,sinwire:INCONCLUSO. No hay run pendiente de foco.',
'surface:':'surface: EV79 18teselas regeneradas/90solapes/176mipsPASS;22PAA+WRPcambian,6804entradasintactas. Motor4194304vertices/1212puntos/1205planosPASS,maxerror1.52588e−5m,0anomaliasfisicassecas.26flagsausentes y321escalaressinflag inventariados; diferencias vsEV73 ningunaenalturaeditada,faseonda distinta. No cierre grafico.',
'render:':'render: EV73/74rectanguloscon tierra texturada;detallemedio/extremo/medio noelimina. Luna alinea2cortes conbordesP3D,sin diferencia material/flags. EV76gris345/345/control378/378fondobajomar:factorcompartido. EV75terrenos rechazados. EV77wireINCONCLUSO auto-restaurado,sinreferenciavalida. No causa aislada.',
'git:':'git: Branch claude/codex-handoff-review-74f290; checkpoint previo dacf089. Nueva evidencia EV78/79/mascaras/factibilidad en evidence/v30-bank-relief-2026-10-10; consultar git log para checkpoint actual. Sin push.',
'next:':'next: Continuar EV80 en E:/DayZ-Baltic-Build/v30-mixed-bank-constrained-20261010/plan.md: sourceEV79, nodos secoslibres incidentes>30, restricciones angulares explicitas y consumidor independiente. Dos Luna existentes autor/revisor; no importarEV78 fallida. Base1.0 sigueabierta.',
'handoff:':'handoff: evidence/v30-bank-relief-2026-10-10/README.md y manifest; EV79geom/motorPASS, EV80en curso. Ver planes locales y agentes antesdereiniciartrabajo. Manteneragua/fondo/calado/carret./plataformas; no promoverEV68.'}
lines=text.splitlines();inside=False
for i,line in enumerate(lines):
    if line=='<!-- LIVE-STATE:START -->':inside=True
    elif line=='<!-- LIVE-STATE:END -->':inside=False
    elif inside:
        for prefix,value in updates.items():
            if line.startswith(prefix):lines[i]=value;break
hand.write_text('\n'.join(lines)+'\n',encoding='utf-8')
bug=W/'bugs.md';old=bug.read_text(encoding='utf-8')
note='> Actualización EV78/79 (10-10): 58 crestas secas fuertes de Narva corregidas (0 restantes>30 allí), sin nuevos pliegues fuertes ni máximos por sector peores.12362vértices; fuente/exposición compilada/superficie/PBO y lectura nativa4194304vértices PASS.0anomalías físicas secas en muestra; shader y contornos mojados NO cerrados. EV78 amplio rechazado. EV77 wire terminó inconcluso; no espera humana activa. Evidencia: `evidence/v30-bank-relief-2026-10-10/README.md`. EV80 selección global con límites angulares en curso.\n\n'
assert note not in old;bug.write_text(note+old,encoding='utf-8')
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-10-dayz-baltic-bank-relief.md')
assert not session.exists();session.write_text(report+'\nEstado vivo: '+str(hand)+'\n',encoding='utf-8')
print(json.dumps(dict(evidence=str(E),files=len(manifest),bytes=sum(q['bytes'] for q in manifest),session=str(session)),indent=2))
