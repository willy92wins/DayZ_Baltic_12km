# Sesión autónoma de ocho horas — 01-10-2026

Petición viva de Guillermo: continuar el mapa durante ocho horas con Computer
Use autorizado y un reset si el uso restante llega al 5 % o menos. Asiento de
esta sesión: executor/integrador. Ventana: 04:42:43–12:42:43 Europe/Madrid;
02:42:43–10:42:43 UTC. Heartbeat de este chat cada 30 minutos, id
`baltic-sesi-n-de-8-horas`. La planificación no acredita ejecución ni resultados.

## Alcance y orden

Se continúa `regional-foundation-execution.md`, trazado a P2/P3/P5/P9–P13.
Primero base íntegra de terreno, hidrografía y navegación. Edificios, vegetación
colocada y vías físicas siguen después según P10. El cierre distingue base
terminada de mapa íntegramente mapeado. No variar encuadre, XY de San Petersburgo,
reserva, frontera de Narva ni dimensiones humanas de vías y assets.

1. Reanclar editable V9, procesos y entorno. Exportar después de reapertura
   real, comparar heightfield, materiales y poses. V9 ya está importado: no
   repetir su importación por instrucciones históricas.
2. Resolver explícitamente la precisión de exportación antes del paquete.
   Conservar el FAIL estricto. [DESIGN] Si la reapertura confirma persistencia,
   separar comparación exacta y contrato geométrico: tolerancia máxima 1e-6m
   solo en la última fila/columna del heightfield y en Y de los dos tramos
   exteriores identificados. Todo el interior, XY, rotación, escala, modelos,
   IDs y materiales permanece exacto. Justificar este límite frente al paso6m
   y verificar positivos y negativos: mundo antiguo, desplazamiento1mm,
   cambio de interior, rotación, material y truncación. No epsilon global ni
   reemplazo silencioso del resultado anterior. Congelar contrato y fuentes
   antes del ensayo; si no se cumple, investigar y corregir.
3. Crear biblioteca nativa `Baltic_Water_V2` e importar `water_absolute_v2.txt`
   en altura absoluta. Esperados 10.152 aguas y tres puentes, total10.155.
   Guardar/exportar/reabrir/exportar, lectura completa de ambas exportaciones
   y todos los modelos/poses contra el manifiesto. Preservar SAT1M.
4. Compilar en staging nuevo y comprobar WRP, materiales, dependencia de agua
   y PBO realmente desplegado. NM anterior solo bootstrap identificado.
5. Generar NM nueva tileWidth12.5 desde el WRP exacto, guardar y verificar;
   reempaquetar y arrancar sin depender de una navegación ajena/antigua.
6. Consumidor regional V3 sin mover muestras, lancha y cruces, IA física,
   cliente y observaciones visuales a varias distancias. Corregir defectos
   con discriminadores y evidencia; conservar cada FAIL.
7. Medir carga descriptiva, archivar editable completo y paquete reproducible;
   actualizar handoff y aprendizaje verificado en skills. No acreditar80–100
   jugadores por servidor vacío o IA sintética.

## Ejecución y parada

Cada bloque deja evidencia y próxima acción en
`evidence/overnight-2026-10-01/state.json` y LIVE-STATE. Preparar rutas antes de
Computer Use, observar antes de actuar y liberar su sesión al pasar a trabajo
offline o espera. Escape físico revoca ese bloque. DayZ MCP requiere protocolo
de lease/lifecycle; no tocar procesos de propiedad desconocida ni infraestructura
compartida sin necesidad y alcance verificados. `diagnostics/` es ajeno.

Consultar uso al inicio de bloques y antes de tramos largos. Hay autorización
para un reset; su clave idempotente y resultado viven en state.json. Ventana no
informada no equivale a cuota agotada. Releer uso antes de consumirlo para evitar
duplicar un reset ya aplicado por la UI. Una respuesta incierta se recupera con
la misma clave. No consumir un segundo reset por inferencia.

Hasta la hora límite se sigue trabajando mientras existan pasos útiles
autorizados. Si un frente está bloqueado, continuar otros independientes;
no declarar cerrado el mapa ni insistir sobre acciones rechazadas. Al completar
el mapa íntegro antes, o alcanzar12:42:43, detener nuevas operaciones, cerrar
solo runs propios, liberar control/lease y dejar handoff con PASS/FAIL/INCONCLUSO.
Desactivar el heartbeat al cierre. No publicar ni contactar con terceros.

## Orden de diagnostico durante bloqueo del dialogo, 03:20 UTC

La exportacion inicial completa supera el contrato congelado, pero el segundo
archivo no existe: la UI pierde foco frente a otras aplicaciones y la ventana
mstsc captura entrada; escribir mediante type_text agota timeout y Guardar no
produce archivo. No se acepta persistencia por dos copias del mismo export.
Se conserva el gate de reapertura para la entrega. Mientras se recupera la UI,
se permite un paquete separado DIAGNOSTIC_ONLY_FIRST_EXPORT_STALE_NAV, obtenido
del primer WRP medido, con SAT1M/dependencias congeladas y navegacion antigua
identificada. Su uso es probar agua y terreno en el consumidor regional antes
de una generacion NM costosa. Ningun PASS de carga/agua cerrara persistencia,
navmesh ni la entrega; el helper normal de staging/build mantiene sus dos gates.
Fuentes, build y despliegue diagnosticos nuevos; no modificar baselines jugables.

## Continuacion diagnostica V10, 05:03 UTC

V10 esta importado/rebuilt/guardado y su primer WRP pasa su gate propio completo
(9puentes+10152aguas). Reapertura real observada, segundo export retenido por foco
inestable del dialogo frente a otras apps. El mismo aislamiento diagnostico
anterior se aplica a V10: staging/build nuevos con estados DIAGNOSTIC_ONLY,
gateV10 completo y dependencias congeladas; no tocar builder normal ni declarar
persistencia/nav/release. Sirve para empezar NM del WRP exacto y probar el cruce.
Si la reapertura ulterior cambia contenido, esa NM se invalida para entrega.
