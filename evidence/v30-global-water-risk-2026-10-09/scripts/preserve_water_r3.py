"""Preserve the completed physical correction before the separate render investigation."""
from pathlib import Path
import json,hashlib,shutil
W=Path(r'C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290')
E=W/'evidence/v30-global-water-risk-2026-10-09';B=Path('E:/DayZ-Baltic-Build/v30-global-water-risk-20261009')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
gate=json.loads((E/'scalar-r2-temporal-runtime-verification.json').read_text())
assert gate['status']=='PASS_SCALAR_TEMPORAL_CONTROLS'
last=next(p for p in gate['series']['results'] if p['id']==9077)
assert last['positive_depth_samples']==0 and last['pond_true']==0
ref=json.loads((E/'halo-r3-deploy.json').read_text());manifest=[]
def copy(a,b):
    b.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(a,b);assert sha(a)==sha(b)
    manifest.append(dict(source=str(a),copy=str(b.relative_to(E)),sha256=sha(b)))
for pattern in ('*.py','*.ps1'):
    for a in B.glob(pattern):copy(a,E/'scripts'/a.name)
for name in ('missions','complete-risk-halo-r2','complete-risk-halo-r3'):
    for a in (B/name).rglob('*'):
        if a.is_file() and a.suffix in ('.c','.csv','.json') and a.name!='grid.csv':copy(a,E/name/a.relative_to(B/name))
for a in B.glob('compiled-domain-discrepancies-halo*.json'):copy(a,E/a.name)
for folder in ('halo-fix-v3','halo-fix-v4'):
    for a in (B/folder).glob('*addonbuilder.log'):copy(a,E/'build-logs'/(folder+'-'+a.name))
(E/'preserved-files-r3.json').write_text(json.dumps(manifest,indent=2)+'\n')
text='''# Detección global y reparación de agua — 09-10

La revisión automática ya cubre los 4.194.304 vértices, las 8.380.418 caras nativas y todas las piezas de agua compiladas. **El defecto visual señalado junto al puente continúa abierto**: su punto calibrado está físicamente seco, incluso con la ondulación adicional. La base 1.0 sigue sin aceptar.

Preview actual: `@DayZ_Baltic_HaloFixV3`. Terreno `e7daa6c6`, mundo `b30ca647`, agua `4ac3cb01`; identidades completas en `halo-r3-deploy.json`. Conserva C1R3P y añade once cambios de altura: diez esquinas secas inundadas y un rebaje de 6 cm en un fondo que se descubría. Mantiene fondo >=1 m, todos los apoyos de corredores, carreteras, plataformas y controles históricos.

La fuente final no contiene vértices secos bajo los planos nominales de los estanques ni agua nominal sobre caras completamente secas. El censo de motor vuelve a leer toda la altura con error máximo de 0,015 mm. No detecta agua nominal sobre tierra seca; quedan 32 indicadores de ausencia en vértices de clase húmeda para clasificación, no 32 ríos sin agua. Las consultas de profundidad registran también los casos con indicadores de presencia falsos; no los ocultan.

Se corrigieron dos errores de generación: invalidación incompleta de teselas vecinas que leen el halo y reutilización de `full_48` aunque su halo tuviera otro nivel. El paquete retira 50 tiras/esquinas obsoletas y recompila 114 modelos. Cinco juntas reciben un solape de 1 mm dentro de su dominio; 150,04 m de líneas compartidas pasan la comprobación continua sobre ODOL, excluyendo el último milímetro que termina contra tierra. Roadway y LOD visible coinciden en las piezas nuevas; los 538 modelos del piloto visual se conservan.

La primera preview de halos pasó los centros pero falló puntos a 2 cm: se conserva ese FAIL. R2 repara la junta completa; 120 puntos x 62 muestras en calma y viento 20 m/s pasan. El nuevo diagnóstico sin depender de flags descubre un charco adicional en 2250/6696, con 0,54–0,64 m de profundidad y 15,31 m² sobre tierra seca. R3 corrige ese único vértice; la repetición de 351 puntos x 62 muestras mantiene los controles y deja seco el charco reparado.

Los otros 230 casos del diagnóstico anterior son contactos intermitentes del oleaje con orillas: 13 pertenecen a la franja de playa y 217 a estanques. Se conservan como inventario temporal, no se declara una envolvente máxima ni ausencia global de contacto del agua. El auditor fuente registra 12.580 vértices secos a menos de 35 cm de un plano vecino y 360 secos bajo el máximo de mar medido; son riesgos clasificados, no autorización para subir todas las playas.

La protección de conectividad distinguió los charcos no deseados: se eliminaron nueve componentes aislados, cuyos únicos vértices sumergidos estaban clasificados como secos y medidos antes del cambio. Los otros 830 cuerpos conservan el criterio de área y continuidad. El antiguo FAIL que protegía incluso esos charcos se conserva; la excepción exige identidad previa, clase seca y medición, y rechaza una partición de canal.

El residual del usuario sigue en x=2718,48525 z=6812,81287, suelo 1,520454 m. La ondulación nativa medida llega a 0,882279 m y el estanque compilado está a 5,515 m. Mar apartado elimina el efecto; amplitud, subdivisión y plano cercano no lo resuelven. Detalle medio–máximo–medio fue INCONCLUSO. Ninguno demuestra causa de LOD. Está preparada una prueba aislada que colorea los materiales de orilla y orilla húmeda; debe confirmar controles gráficos positivos antes de sacar conclusiones. Sus mods son diagnósticos, nunca parte de la entrega.

Para repetir el censo fuente, usar `tools/terrain/audit_water_risk_v30.py` con `--source`, `--source-sha`, `--out` nuevo y los tres argumentos `--water-source`, `--water-sha`, `--water-manifest`. Los datos exactos están en `complete-risk-halo-r3/report.json`. El generador nativo y su verificador están en `scripts/prepare_last_pocket_runtime.py`, `scripts/verify_halo_r3_fullwater.py` y las misiones conservadas. El control analítico independiente cubre una cara de 4,5 m², su eliminación y rechazo de un hash incorrecto.

Evidencia principal: `halo-r3-fullwater-verification.json`, `scalar-r2-temporal-runtime-verification.json`, `last-nominal-pocket-verification.json`, `targeted-pocket-removal-verification.json`, `halo-fix-r2-package.json`, `compiled-domain-inventory-halo-r2.json`, `pond-risk-consumer-controls.json` y los CSV/logs originales. Las diez discrepancias geométricas no triviales restantes son los cinco solapes de junta autorizados; las intersecciones minúsculas siguen inventariadas, no aceptadas por tamaño.

Los intentos D1/D2 de elevar toda la transición continúan retirados. Pendientes del plan general: forma global de orillas/cauces/taludes, juntas visuales fuera del piloto, residual visual de tierra, teselas, finales cuadrados y los demás IDs abiertos. El ticket de foco ya existe: `fb-20261008-233507-8b1c`. No hay cierre global de los veinte fallos.
'''
(E/'README.md').write_text(text,encoding='utf-8')
updates={
'candidate:':'candidate: @DayZ_Baltic_HaloFixV3, terreno e7daa6c62cde457b666507ec7eae7e6d16015ad714028585fdb352ace678e52c. Mundo b30ca647abb85568301ec960ece4d2113c562d339b115ba798a9301e1af29e82; agua 4ac3cb01770dbbd825df24bd4e5869869a56188cf40acc17cb882ecb2f86539b. Preview aislada; no base aceptada ni promoción a TB.',
'global_detection:':'global_detection: Censo fuente 4.194.304 vértices/8.380.418 caras y nativo completo PASS, error máximo 0,015 mm. HaloFixV3 no tiene tierra seca bajo planos nominales de estanque ni área de estanque sobre caras completamente secas. Se corrigieron 50 tiras obsoletas, cinco microjuntas completas y diez esquinas secas inundadas; 351x62 controles/diagnósticos. Registrar también profundidad positiva sin flags: 230 contactos intermitentes de orilla siguen inventariados. No cierra el residual visual del puente.',
'water:':'water: 538 LOD visibles unidos del piloto conservados. Reparación adicional de halos: 114 modelos nuevos, 50 instancias obsoletas retiradas, cinco juntas con 150,04 m de continuidad comprobada en ODOL y vecindades físicas PASS. No equivale a extensión visual global: 6.431 instancias cambiarían >1 mm, 333 >0,35 m, máximo 1,95 m. No promediar cuerpos distintos.',
'runtime_lock:':'runtime_lock: Censos Halo V1/V2/V3 y temporales cerrados por lifecycle; ver halo-and-scalar-lifecycle.json y last-pocket-lifecycle.json. Comprobar session_status fresco antes de lanzar. No usar un estado histórico para asumir el banco libre. Ticket de foco existente, no duplicar.',
'next:':'next: Unidad física HaloFixV3 verificada. Continuar el defecto visual en el punto calibrado: diagnóstico de materiales shore-material-reference.json y misión BalticShoreDiagnosticV1 preparados, aún no concluidos. Censo completo y CSV ya evitan revisar globalmente a capturas. Después continuar juntas visuales globales, smoothing/finales, resto de bugs, TB/Generate Layers y navmesh según plan.',
'git:':'git: Rama claude/codex-handoff-review-74f290; unidad EV7-EV10 y generadores/auditor preparados para commit local. No push. La revisión de 71131f5 no cubre estos cambios.'}
p=W/'HANDOFF.md';lines=p.read_text().splitlines()
for key,value in updates.items():
    idx=[i for i,line in enumerate(lines) if line.startswith(key)];assert len(idx)==1;lines[idx[0]]=value
p.write_text('\n'.join(lines)+'\n')
p=W/'bugs.md';lines=p.read_text().splitlines();assert lines[2].startswith('Actualización vigente, 09-10:')
lines[2]='Actualización vigente, 09-10: **HaloFixV3** conserva C1R3P y repara halos obsoletos, cinco microjuntas y diez esquinas secas inundadas. Censo automático global 4.194.304 vértices/8.380.418 caras, lectura nativa completa y 351x62 controles/diagnósticos. No queda tierra seca bajo planos nominales de estanques en la fuente; 230 contactos intermitentes de orilla siguen inventariados. El residual visual junto al puente continúa físicamente seco y **016 abierto**. 007 forma global, 015 juntas visuales globales, 019 teselas y 020 finales siguen abiertos. Ticket de foco fb-20261008-233507-8b1c existente. Evidencia actual: `evidence/v30-global-water-risk-2026-10-09/README.md`. Ninguna variante es base 1.0; las entradas posteriores son históricas.'
p.write_text('\n'.join(lines)+'\n')
session=Path('C:/Users/guill/ObsidianVault/AI/30_Sessions/2026-10-09-dayz-baltic-censo-global.md')
session.write_text('# Baltic: detección global y reparación física de agua\n\nPetición viva: continuar autónomamente smoothing/base y fallos; detectar agua sobre tierra sin recorrer todo a capturas. Sin subagentes ni push.\n\nUnidad completada: auditor completo de vértices/caras, censos nativos, comparación de todas las piezas compiladas, corrección de halos y juntas, diez esquinas secas inundadas y un fondo que se descubría. HaloFixV3: mundo `'+ref['files']['narva_trial.pbo']+'`, agua `'+ref['files']['baltic_water_v30.pbo']+'`, terreno `'+ref['terrain_sha256']+'`. Controles de topología, carreteras, calado y metadatos conservados; 351x62 muestras finales. No se declara cierre visual ni base 1.0.\n\nLección de evidencia: SurfaceIsPond=false no basta para dar un punto por seco; el censo registra profundidades positivas sin flags y contrasta geometría compilada. También es insuficiente comprobar solo el centro de una junta: el fallo persistía a 2 cm. La protección de cuerpos de agua no puede proteger sin distinguir los charcos que el encargo pide retirar; excepción fijada por identidad, clase seca e inventario anterior, con negativos de canal real.\n\nHandoff y pruebas: ['+str(E/'README.md').replace('\\','/')+']('+str(E/'README.md').replace('\\','/')+'). Estado vivo en HANDOFF del worktree codex-handoff-review-74f290. Próximo: aislar capas gráficas en el residual calibrado del puente, con la prueba diagnóstica de materiales preparada; después pendientes globales, TB y navmesh. El ticket de foco ya existe.\n',encoding='utf-8')
print(json.dumps(dict(preserved_files=len(manifest),live_state_updated=True,source_hashes_verified=True)))
