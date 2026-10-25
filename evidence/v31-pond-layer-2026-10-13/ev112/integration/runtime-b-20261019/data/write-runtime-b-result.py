from pathlib import Path
import json,datetime
O=Path(__file__).parent
C=json.loads((O/'runtime-b-closure.json').read_text(encoding='utf-8'));R=json.loads((O/'build-review-closure-runtime-b.json').read_text(encoding='utf-8'))
assert C['status']=='AUTHORIZED_SERVER_SCOPE_COMPLETED_WITH_EXPLICIT_PENDING' and all(C['checks'].values())
now=datetime.datetime.now().astimezone().isoformat()
base18=C['bridge_01518']['baseline'];cur18=C['bridge_01518']['current']
wet18=f"{base18['wet']}/{base18['under']}→{cur18['wet']}/{cur18['under']}"
lines=[
'# EV112 — servidor completado; vista personal preparada',
'',
f"Cierre {now}. Corregidos los cuatro controles nuevos detectados por la primera sonda. El paquete final supera los controles obligatorios del servidor y la comprobación temporal. **El AND estricto y G8 del kit permanecen FAIL por {C['concrete_pending_count']} labios/juntas de hormigón**, pendientes no bloqueantes según el plan §5. No se ha cambiado ningún umbral ni concedido una excepción nueva.",
'',
'| Comprobación | Resultado |','|---|---|',
f"| Sonda completa | {C['probe_rows']} filas válidas, capturadas antes de cerrar el servidor |",
f"| Kit obligatorio | {C['kit_required']['passed']}/{C['kit_required']['total']} PASS; {C['kit_unclassified_reference_points']} puntos adicionales son referencias sin expectativa juzgada |",
f"| Hormigón vanilla | {C['concrete_pending_count']} pruebas secas pendientes; mismos IDs que en la primera sonda: {C['concrete_same_ids_as_first_probe']} |",
f"| Puentes | {C['bridge_passed']}/{C['bridge_sites']} PASS, sin regresión frente a EV110; 015-18 {wet18} puntos mojados |",
f"| Orillas | {C['shores']['wet_ok']}/{C['shore_wet_total']} mojadas, {C['shores']['dry_ok']}/{C['shore_dry_total']} secas; {C['shores']['islet_pairs_ok']}/{C['shores']['islet_points']} parejas de islote |",
f"| Presa | {C['dam_rows']}/{C['dam_points']} puntos; consumidor independiente PASS |",
'| Temporal | 30 muestras de los mismos 8 puntos: cuatro corregidos y controles conformes en todas las muestras |',
f"| Revisión independiente OT7 R2 | {R['verdict']}; cero críticos/mayores abiertos |",
'| Vista personal | 16 archivos instalados y comprobados por hash; ruta y solicitud de lanzamiento preparadas. Cliente no lanzado |',
'',
'## Corrección física y prueba',
'',
'La primera sonda y el diagnóstico temporal demostraron que cuatro controles cambiaban de signo con el oleaje. Se descartó sustituir la profundidad por flags/NoFakeWave: esa propuesta producía 190 rechazos adicionales. También se descartó el candidato A, que reducía el margen del control seco vecino del islote. No hubo permiso adicional ni waiver para estos controles.',
'',
'La capa reproducible `tools/terrain/apply_engine_water_margins_v31.py` cambia exactamente cuatro vértices del terreno C: un eje del kit baja 0,15 m, dos restos de lecho suben 0,19 m y un vértice enteramente submarino baja 1,577194 m. La última corrección conserva la costa local y la altura del control seco vecino. Todas las máscaras, la huella de agua y el grafo de conectividad permanecen idénticos. Pendiente máxima incidente: 23,1373°; ninguna protección tocada. Los dominios completos de c2–c7 permanecen idénticos.',
'',
'| Punto global / tipo | Profundidad primera sonda (m) | Profundidad final (m) | Rango temporal final (m) |',
'|---|---:|---:|---|']
for key,v in C['corrected_points'].items():
 a,b=v['temporal']['depth_range'];lines.append(f"| {key} / {v['kind']} | {v['depth_before']:.8f} | {v['depth_after']:.8f} | {a:.8f} .. {b:.8f} |")
lines += ['',f"La discrepancia máxima suelo motor/NPZ entre las cuatro familias de la sonda es {max(v['maximum'] for v in C['ground_match'].values()):.8f} m. Esto vincula la carga observada al terreno corregido en los puntos muestreados; no decodifica toda la matriz binarizada.",
'',
'## Paquete y validación offline',
'',
'Se conservan exactamente los 2.561.015 registros de bosque y los 2.578.916 objetos totales. El staging conserva los registros byte por byte; la lectura independiente del WRP compilado vuelve a verificar modelos, IDs y matrices. G1 y G4 del bosque se ejecutaron de nuevo sobre el terreno B; los cinco consumidores del bosque pintado usan el PBO final. Las seis puertas de superficie pasan contra las PAA empaquetadas. El agua se conserva por identidad de las cuatro arrays de huella y de su PBO.',
'',
'Las 45 etapas conocidas, las 50 etapas de holdout y los seis positivos/25 negativos del bosque AE se heredan por identidad de fuente/registros y por la nueva ejecución de los consumidores afectados. No se reutilizan semillas como si fueran nuevas ni se declara un PASS global de todas las ventanas.',
'',
f"- Mod: `{C['mod']}`.",f"- Mundo SHA256: `{C['world_sha256']}`.",f"- Agua SHA256: `{C['water_sha256']}`.",f"- Terreno SHA256: `{C['terrain_sha256']}`.",f"- Fuente de corrección: commit `{R['source_commit']}`; sin push.",
'',
'El paquete anterior permanece intacto. El lanzador público funcionó; no se renovó su bundle ni se modificó el registro de Steam.',
'',
'## Pendientes y alcance',
'',
'- **015-45:** disco protegido de 60 m pendiente, nunca PASS.',
'- **Hormigón:** las juntas/labios conservan su FAIL estricto. Su solución está fuera del cierre no bloqueante aprobado en §5; no se confirma aquí su comportamiento en Chernarus.',
'- **Calzadas:** p90≤0,03 m corresponde al dominio central aceptado. Los 1.491 vértices exteriores con agua (538 en tramos G2) conservan sus métricas, hasta 0,11791 m.',
'- **Fases:** G9/G11 del kit sobre el terreno final siguen FAIL, idénticos medida por medida a C. El G7 histórico de orillas conserva cuatro vértices C7 sustituidos por la fase posterior. Los intentos fallidos y sus logs se conservan.',
'- **Bosque:** G8 sin exenciones por ventana, con exclusiones estructurales de Narva/kit/puentes. Permanecen las limitaciones de 124 traslaciones fuera del recorte de mutaciones, tres filas diagnósticas de juncos G9 y el fallo regional G2/G3. La identidad G9 compara 243.157 objetos a 20 m del borde, no a 40 m.',
'- **Motor:** la prueba temporal abarca aproximadamente un minuto con clima fijo. No acredita todos los climas, humedad del jugador, aceptación visual, FPS ni capacidad para 80–100 jugadores.',
'',
'## Continuidad y evidencia',
'',
f"Sonda final: `{C['probe_run_id']}`. Diagnóstico final: `{C['temporal_run_id']}`. Ambos capturados antes del cierre ordenado, retirados y con lease liberado. Las dos ejecuciones originales también se cerraron. No queda run ni lease propio.",
'',
'Para la vista: `personal-view-runtime-b/README.md`, `route.json` y `launch-request.json` en el build. Misión instalada `BalticBasicEV112.BalticTrial`, aparición en Narva. Comprobar disponibilidad del banco y adoptar la ejecución propia después del lanzamiento público; mantener heartbeat durante la visita.',
'',
'Evidencia original y final en `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/`: `runtime-b-closure.json`, `deploy-runtime-b.json`, `build-review-closure-runtime-b.json`, `runtime-capture-runtime-b-20261019/`, `runtime-eval-runtime-b-20261019/`, `water-temporal-runtime-b/` y `water-fix-b/`. Los recibos anteriores `reviewed-ae-awaiting-runtime` y la primera sonda se conservan como historia, no como estado actual.',
'',
'La documentación global del vault conserva fallos de enlace y un pin del generador ajenos a esta tarea. Este cierre no los convierte en PASS ni modifica gobernanza global; valida sus propios enlaces y conserva el contenido ajeno de la parada Baltic.', '']
out=O/'RUNTIME-B-RESULT.md';assert not out.exists();out.write_text('\n'.join(lines),encoding='utf-8');print(out)
