from pathlib import Path
import hashlib,json,shutil,gzip,re
B=Path(__file__).parent
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-full-mipmap-audit-2026-10-09';E.mkdir(exist_ok=False)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def copy(a,b):
    b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b);assert sha(a)==sha(b)
for name in ['plan.md','audit_mipmaps.py','preserve_and_checkpoint.py']:copy(B/name,E/name)
report=json.loads((B/'mipmap-verification.json').read_text());assert report['status']=='PASS_CURRENT_AND_PRIOR_MIP_FILE_INTEGRITY'
raw=(B/'mipmap-verification.json').read_bytes();(E/'mipmap-verification.json.gz').write_bytes(gzip.compress(raw,mtime=0))
assert gzip.decompress((E/'mipmap-verification.json.gz').read_bytes())==raw
for p in (B/'native-controls').iterdir():copy(p,E/'native-controls'/p.name)
(E/'summary.json').write_text(json.dumps({k:v for k,v in report.items() if k not in ['current','previous']},indent=2)+'\n')
(E/'README.md').write_text('''# EV30 — integridad de mipmaps completa

Se consumen los PBO desplegados EV28 y EV25,2048 texturas por paquete y16384 mipmaps por paquete. Las cadenas512 a4, los formatosDXT1/DXT5, los offsetsOFFS, payloads y longitudes descomprimidas pasan. No niveles truncados/vacios ni alpha inesperada. Los582 payloads anteriores identicos reutilizan el mismo resultado por hash.

Todos los niveles mayores actuales se contrastan con ImageToPAA: diferencia maxima2/255 entre decodificadores. Doce niveles inferiores64/16/4 se extraen manteniendo sus bloquesDXT y se leen tambien con ImageToPAA; diferencias<=2/255. Truncado, offset adulterado y nivel final omitido son rechazados. Referencia vanilla con la misma cadena y formatos preservada por hash. LZO local, sin instalar dependencias ni modificar el lector.

No hay evidencia de mipmap ausente o corrupto como causa del gris intermitente: ambos paquetes pasan. Esto comprueba archivos, no streaming nativo ni residencia GPU. El informe completo comprimido conserva cada nivel y media; no constituye aceptacion estetica ni cierre019. La consulta web a la especificacion de Bohemia devolvio403; el resultado se apoya en codigo local leido, archivos vanilla y consumidor nativo, no en esa pagina inaccesible.
''',encoding='utf-8')
(E/'preservation.json').write_text(json.dumps({str(p.relative_to(E)):sha(p) for p in E.rglob('*') if p.is_file()},indent=2)+'\n')
B29=Path('E:/DayZ-Baltic-Build/v30-current-geometry-review-20261009');E29=W/'evidence/v30-current-geometry-review-2026-10-09';E29.mkdir(exist_ok=False)
for name in ['check_deferred_lakes.py','deferred-lakes-current.json']:copy(B29/name,E29/name)
(E29/'README.md').write_text('''# EV29 — comprobar los lagos reservados sobre el terreno actual

El consumidor original de los terraplenes se reaplica a EV25. Cero vertices de ambos anillos0–36m cambiados frente a EV16; curvatura y p90 identicos. La pasada general preservo estos lagos reservados: no hay mejora de forma que permita cerrar017. No se construye otra propuesta ni se cambia su nivel. Las dos decisiones reservadas del plan siguen pendientes. El intentoEV19 conserva su FAIL original.
''',encoding='utf-8')
path=W/'HANDOFF.md';old=path.read_bytes();s=old.decode('utf-8')
updates={
'status':'BASE_1_0_NO_ACEPTADA. Petición viva: terminar toda la superficie, arreglos y comprobaciones. EV28 satélite/máscara completos; EV25 mejora taludes. Contorno restante, residual gráfico, lagos y TB siguen abiertos.',
'candidate':'Preview @DayZ_Baltic_CurrentSurfaceV1 (EV28): mundo b69265c5feb99d1bda7a5c9f02282818d0ffe4cd26f89f3a095c128e62d374f3; agua 3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14; terreno fb36ec4c2203b6c936c8823078250f71082fbf43d9b1ba410049f735f890a0e6. Solo texturas respecto a EV25; 5.361 entradas y WRP exactos. Sin promoción TB/base.',
'render':'019 gris/tiles intermitente, mecanismo abierto. EV30 verifica todos los mipmaps de EV25/28: 16.384 por paquete, controles nativos/negativos PASS; no defecto de archivo encontrado. EV28 carga sin foco manual, largo R3 limitado por bruma. Ticket fb-20261008-233507-8b1c existente.',
'runtime_lock':'Banco libre. Run EV28 b690cc87-1c6f-465f-adba-ee070db236f4 cerrado orderly cliente/servidor; lease liberado, owner nulo/cero runs. EV28 no nueva travesía ni censo: WRP y agua idénticos a EV25.',
'remaining':'007 contornos/remates y zonas protegidas; 010 fuentes de toda la superficie EV28 PASS, aceptación visual final pendiente; 011/015 distancia limitada por bruma/coste; 016 residual gráfico; 019 streaming intermitente. 020 EV27 Volkhov descartado por global_over30; Msta y dos arroyos reales pendientes, stream0452/0456 excluidos tier1500 no son errores. 017 EV29 confirma ambos terraplenes exactos, niveles reservados pendientes. 014 TB/navmesh/IA después de geometría aceptada; EV18 consumidores conservan su ámbito.',
'git':'Rama claude/codex-handoff-review-74f290; checkpoint EV27–30 propio tras 0e5ffbc, sin push ni subagentes. No revisión externa atribuida.',
'next':'Aislar distancia de dibujo nativa con candidato EV28 exacto y ajustes temporales de prueba; no preferencias persistentes. Los mipmaps no explican019. No repetir solver Volkhov/Msta ni subir cotas de charcas sin mecanismo nuevo. Dos grandes lagos esperan decisión. Después de geometría aceptada, TB/Generate Layers y navmesh/IA.',
'handoff':'EV27 FAIL preservado (29 vértices, cuatro giros>30 adicionales), no desplegado. EV28 superficie completa:150.847.524px,3.968solapes,34.445.765px interiores compilados sin mezcla;4.323mezclas DXT de borde. EV29 lagos intactos. EV30 todos los mipmaps actuales/anteriores pasan integridad; no cierre de streaming. Seguir autónomamente; no entregar base como terminada.'}
for key,value in updates.items():
    s,n=re.subn(r'(?m)^'+re.escape(key)+r':[^\r\n]*',lambda m:key+': '+value,s,count=1);assert n==1,key
assert path.read_bytes()==old;path.write_bytes(s.encode('utf-8'))
path=W/'bugs.md';old=path.read_bytes();s=old.decode('utf-8')
s,n=re.subn(r'(?m)^Checkpoint 09-10:[^\r\n]*','Checkpoint 09-10: estado vigente en HANDOFF.md y evidence/v30-global-water-risk-2026-10-09/bug-status-current.md. Candidato EV28 CurrentSurfaceV1, no base aceptada. EV27 descartado; EV28 superficie completa y EV30 mipmaps pasan en su ámbito. EV29 confirma lagos reservados intactos. Banco libre, todos los runs cerrados y lease liberado. Las narraciones siguientes son históricas.',s,count=1);assert n==1
s=s.replace('Actualización vigente, 09-10: **HaloFixV3**','Snapshot anterior, 09-10: **HaloFixV3**',1)
assert path.read_bytes()==old;path.write_bytes(s.encode('utf-8'))
path=W/'evidence/v30-global-water-risk-2026-10-09/bug-status-current.md';old=path.read_bytes();s=old.decode('utf-8')
rows={
'010':'EV28 usa terreno/plano actuales: 1.024 satélites y máscaras,150.847.524px/3.968solapes PASS; compila/decodifica todo. Cambian754/712PAA, resto exacto. | 4.323mezclas DXT de borde inventariadas. Vistas cargadas; aceptación global final/TB pendiente.',
'017':'EV19 propuesta rechazada. EV29 reaplica el consumidor a EV25: ambos terraplenes0–36m exactos frente aEV16, sin mejora atribuible. | Niveles de los dos grandes lagos reservados al usuario; no bajados ni aceptados.',
'019':'EV28 carga sin foco manual. EV30:16.384mipmaps por paqueteEV25/28, offsets/payload/decodificación completos y controles PASS. | Causa del streaming intermitente abierta; no defecto de mipmaps encontrado. Ticket de foco existente fb-20261008-233507-8b1c.',
'020':'EV16 mejora diez cajas. EV27 descubre el remate poligonal Volkhov omitido; propuesta rechazada por cuatro giros>30 adicionales. Msta exacto. | Volkhov/Msta y stream0207/0431 pendientes. stream0452/0456 tier1500 excluidos del diseño, no contornos perdidos.'}
for ident,value in rows.items():
    s,n=re.subn(r'(?m)^\| '+ident+r' \|[^\r\n]*',lambda m:'| '+ident+' | '+value+' |',s,count=1);assert n==1,ident
s=s.replace('# Revisión de los veinte fallos: EV16/18/23 actuales','# Revisión de los veinte fallos: vigente hasta EV30',1)
assert path.read_bytes()==old;path.write_bytes(s.encode('utf-8'))
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md')
entry='''\n\n## EV27–30 — remate rechazado y superficie completa\n\nEV27 descubre el corte poligonal del Volkhov omitido por profiles.npz. Una propuesta29vertices mejora localmente, pero añade4muestras>30 al consumidor global: FAIL, no desplegado. Dos no_contour anteriores son cursos tier1500 excluidos, no fallos. EV28 reconstruye1024satelites/mascaras usando agua compilada por hash;150.847.524pixeles y3968solapes pasan;34.445.765interiores compilados sin mezcla,4323mezclasDXT de borde registradas. CurrentSurfaceV1 mundo b69265c5, agua3946db8b; WRPcfcbbd0c y terrenofb36ec4c exactosEV25. Run b690cc87 carga enR1/R3/tesela27,21, largo limitado por bruma, cierra orderly y libera lease. EV29 confirma bancos de ambos lagos reservados exactos, sin mejora. EV30 consume todos16384mipmaps por paqueteEV25/28: integridad/decodificacion pasan, no se atribuye019 a un mip ausente. Sigue base no aceptada, pendientes de forma, niveles reservados, residual, distancias y TB/navmesh. Sin subagentes ni push; continuar autonomamente.\n'''
old=session.read_bytes();assert b'## EV27' not in old;session.write_bytes(old+entry.encode('utf-8'))
print(json.dumps(dict(status='EV27_TO_EV30_CHECKPOINT_SAVED',evidence=str(E))))
