# EV112 — reducir el coste de colisión del río 131

Petición vigente: corregir ríos/terreno, reforzar controles y avanzar en optimización respecto a Chernarus. Codex ejecuta e integra; Fable 5.1 por CLI nativo revisa de forma independiente. Este piloto conserva la geometría visible y el agua. No modifica los paquetes usados por la generación de navegación F actualmente en curso.

## Descubrimiento verificado

- `tools/water/compact_stream_collision_v31.py:63` divide el bloque rechazado por un solo eje, elegido por su longitud física. `fit_grid` conserva el límite sobre toda la superficie, con refinamiento exacto cuando la cota suficiente es ambigua.
- Diagnóstico externo `E:/DayZ-Baltic-Build/shape-repair-20261025/collision-midpoint-diagnostic-v2/result.json`: buscando ambos cortes centrales, las dos piezas examinadas pasan de 182 a 137 y de 56 a 23 componentes. Caras 3678→3102 y 1396→1100; vértices 2203→1825 y 810→596. En la primera pieza aumenta el máximo individual de 44 a 65 vértices: el algoritmo propuesto limitará también ese coste. El diagnóstico no ha generado P3D ni prueba rendimiento.
- Fuente congelada: `river-131-a/author-report.json`, SHA256 `3dbfcf567cbd549c20beda594eda3719b9d4944add2b244a9ffaf2f004317833`. Cada modelo se liga además a su hash. El autor anterior `author_compact_collision.py` genera sólo Geometry y conserva los otros tres LOD como bytes originales.
- Consumidor independiente `tools/water/review_compact_collision_v31.py:69`: relee los P3D guardados, comprueba cierre, convexidad, asignación completa, LOD restantes exactos y superposición planar global (incluidas juntas entre modelos). Límites finales: vertical 0,02 m, lateral 0,01 m. La unión inferior se certifica en `collision_contact_union_v31.py`.
- U2 corrigió cinco pérdidas reales de contacto mediante 46 componentes ampliados. Sus índices pertenecen a otra partición: no se reutilizan en el candidato nuevo. El control de contacto nativo sigue siendo obligatorio antes de integración.

## Implementación propuesta [DESIGN]

Añadir una función optativa, manteniendo `partition` y sus valores por defecto intactos. Para cada rectángulo del grid: aceptar un hull si cumple tolerancias y límites de complejidad; si no, explorar ambos cortes centrales disponibles con memoización. La hoja 2×2 usa los dos prismas triangulares existentes. Elegir menos componentes, después menos caras y después menos vértices; desempate determinista. No afirmar optimalidad entre todos los cortes posibles.

Por modelo, fijar antes de la búsqueda el máximo de vértices/caras por componente leído del P3D guardado en `river-131-compact-a`, ligado a su `author-report.json` SHA256 `5139587a85879cb30db476f1b21cc1d3c5adc917ab5f44a81657779cfd88b3c1` y al hash de cada modelo. No confundirlo con una recomputación usando el módulo actual (distinto del antiguo2864dbdf). Ningún componente nuevo puede excederlos. La autoría mantiene los presupuestos originales de 0,03 m para la cota superior local y 0,01 m lateral; el centrado cuantizado y la comprobación global posterior de ±0,02 m siguen iguales. Se registran las cinco dimensiones de coste (componentes, caras, vértices, máximos por componente) desde los P3D releídos, por modelo y en total.

Límites mecánicos: una búsqueda por modelo, salvaguarda de 20.000 estados únicos (evaluaciones de `fit_grid` con fallo de caché) y 60 s por modelo, entradas/tolerancias finitas y válidas. Para21×39, el máximo teórico de rectángulos centrales es2925; el cap es defensivo. El tiempo se comprueba antes/después de operaciones y antes de devolver resultado; una operación nativa individual no se interrumpe dentro de scipy. La autoría completa tendrá un timeout externo de1800s. Exceder recursos produce INCONCLUSO con error explícito, nunca aceptación parcial ni relajación. Una pasada completa de los modelos congelados; no variar presupuestos para hacerla pasar. Los archivos se generan en una carpeta nueva fuera del mod desplegado.

Desempate exacto: orden de candidatos fila y después columna; primer mínimo lexicográfico. Registrar versiones de numpy/scipy (Qhull viene con scipy; no inventar versión no expuesta). Probar repetición en dos procesos `-I` frescos, sin caché compartida. No mutar arrays/diccionarios devueltos por memoización: copiar puntos antes de centrar. Añadir rechazo explícito de valores no finitos en el refinamiento exacto de `fit_grid`, demostrado por un control negativo de fallo numérico; no convertir NaN en cota0.

## Validación y puertas

1. Tests de plano/rampa y valle, determinismo, límites de recursos y complejidad, entrada inválida, conservación de cobertura; el consumidor independiente debe aceptar el candidato positivo y rechazar huecos, excesos de altura/laterales y componentes inválidos. Incluir cap inferior al hull de un plano con cobertura completa y cap de estados1 con error sin salida parcial. No basta comparar dos ejecuciones del autor.
2. Relectura de P3D guardados de todo el río. LOD visual/agua/restantes y poses byte exactos. Cierre/convexidad/asignación completa y superposición global PASS, sin omitir juntas. Coste por modelo y total en las cinco dimensiones no mayor que la partición guardada anterior; reducción estricta de componentes totales. Una regresión de coste se declara FAIL del piloto, no se oculta con una etiqueta de optimización. El objetivo lexicográfico no garantiza por sí solo esta puerta de coste.
3. Revisión independiente de código y evidencia con Fable por CLI; resolver hallazgos concretos y repetir sólo las pruebas afectadas por cambios.
4. Compilar por la cadena existente en una carpeta nueva. El despliegue y cualquier sonda nativa esperan al cierre de la generación/sondas F. Repetir consumidor sobre geometría binarizada si la cadena permite recuperarla y usar la sonda completa actual de4749 controles de F, comprobando durante preparación que mantiene los XZ/tipos de los2823 controles originales, más los300 rayos diagnósticos y controles de juntas. No basta repetir cinco puntos. Compact-a pasó el consumidor offline y falló en motor: ningún PASS offline se asciende a contacto nativo. No integrar si falla contacto, agua o identidad del paquete.
5. Cambiar colisión invalida la correspondencia de la navegación recién generada para F. La navegación F conserva su paquete original; cualquier candidato integrado requiere navegación correspondiente antes de recibir aceptación de navegación. No atribuir mejoras FPS/CPU ni capacidad de jugadores a recuentos de geometría.

PASS offline = candidato guardado con reducción de coste y consumidor completo válido. FAIL = contraejemplo o regresión. INCONCLUSO = límite de recursos, compilación/motor pendientes o identidad no demostrada. Ninguna de estas etiquetas cierra EV112 global ni la revisión visual con Guillermo.

## Contactos originales y revisión

Run T `d40948fd-5a1b-47a1-8778-8c64a84aa163`; diagnóstico `e989a3c3-ab4a-4e8c-bce6-02182f80f9a8`. Fuente `runtime-t-20261025/contact-targets.json` y plan `ev112-rv-vertex-contact-20261025.md`:

| ID | Modelo | X | Z |
|---|---|---:|---:|
|56|cs_kit_118_0072.p3d|8273.058594|9003.779297|
|219|cs_kit_118_0288.p3d|8226.964844|9210.511719|
|392|cs_131p0_0_0300.p3d|8538.0|714.0|
|465|cs_131p0_0_0096.p3d|8424.826172|548.021484|
|558|cs_131p0_0_0216.p3d|8488.763672|648.802734|

Tres puntos pertenecen al río131; los dos del kit118 conservan sus modelos U2. Una partición nueva puede crear otras coincidencias. Revisión Fable5.1 nativa `1fa94b51-7144-44f0-b0f6-501a10da54b6`, SOUND-with-fixes: los siete ajustes incorporados aquí antes de implementar. No hubo escrituras del revisor, permisos denegados ni subagentes.

Secuenciación ajustada tras leer `pack_continuous_stream_pilot_v31.ps1`: las escrituras son `packed/`, `temp/`, el log y junctions dentro del candidato nuevo; lee DZ/bin/core y no despliega ni gestiona procesos. Por ello la compilación aislada puede adelantarse durante la generación F. El generador sigue consumiendo los mismos cuatro PBO fijados y el cierre verifica sus hashes. El cambio es de orden de trabajo; los gates y el alcance permanecen.

Revisión de código Fable5.1 `92a940a7-31b4-4ba6-9456-bd17cccc534d`: SOUND-with-fixes. Incorporados rechazo explícito del estado FAIL/incompleto de packing en el consumidor (legacy sin esa declaración conservado), valle con corte columna/dos componentes exactos y plano con nueve estados únicos. Los27modelos pasan coste por modelo y superposición global;224tests antes de esos refuerzos. Compilación, poses y motor pendientes.

## Corrección acotada del centrado tras compilación

[EXACT] A compila y conserva superficies/juntas, pero `existing-pose-parity.json` detecta una pose distinta entre27: `cs_131p0_0_0300.p3d`, delta Y−0,00390625m respecto aU2. `bottom-anchor-diagnostic.json` aísla el cambio: dos componentes nuevos (0036/0039) tienen diez puntos inferiores aY−1,03515625, frente al mínimo anterior−1,02734375. El resto más bajo de esos componentes queda a−0,68359375, con0,34375m de espesor restante tras corregir. La caja global y el centro ODOL cambian en la misma magnitud; no es una atribución basada sólo en el código del autor.

[DESIGN] Variante B separada: desplazar verticalmente sólo esas dos bases planas aY−1,02734375, subiendo exactamente diez vértices0,0078125m; comprobar cierre/convexidad tras guardar. No se presupone equivalencia con una intersección general de semiespacios. Conservar caras/índices, vértices superiores, XZ, masa, número de componentes y coste. Regenerar normales y volumen de los componentes;26modelos yLOD noGeometry del afectado byte exactos. El suelo de contacto superior tiene que conservar todos sus triángulos exactos. No retocar WRP ni poses.

## Rechazo nativo de B y corrección C

B falla el punto697/4749 en la junta0300–0312: RV toca0300 y Bullet0312,
margen proyectado≈0,05167m frente a0,039991m calibrado, tolerancia0,01m. La
rejilla fija300 detecta13 discrepancias más de margen alrededor de392, todas en
0300. Ambos runs cerrados y sus fallos conservados. El PASS de overlay no basta
para el contrato de contacto del motor; no se modifica el consumidor.

[DESIGN] C conserva exactamente los ODOL y fuentes U2 ya probados de0300 y0312.
La optimización pasa a25 modelos; los dos restaurados quedan fuera de esa
transformación. No se tocan XZ de prueba, agua, terreno, poses, visual ni umbrales.
Componer en un paquete nuevo los25 B y los37 U2 restantes, comprobando cada entrada
y config. Para los25 transformados siguen vigentes los límites compact-a; para
los dos conservados, identidad byte a byte con U2. El coste total se compara
también con U2 efectivo, pues contiene la reparación de contacto previa.
Repetir overlay de toda la unión en poses F y los4749+300 controles congelados.
No declarar aceptado si alguno falla. No atribuir causa interna de Bullet a la
aproximación sólo por observar que contacta dos piezas distintas.

Una variante dirigida por este discriminador, sin buscar parámetros. Antes de aceptar: consumidor global completo y coste releído, recompilación, comparación de las27poses existentes (todas exactas) y revisión independiente de la corrección. A se conserva como FAIL de pose. La sonda nativa sigue pendiente y puede descubrir contactos nuevos.

## Resultado de esta unidad — 25-10-2026

C supera overlay compilado,4.749controles completos y300rayos de rejilla, cero fallos.25modelos optimizados+37U2 exactos;1.449componentes frente a2.245U2. Revisión independiente Fable resuelta con procedencia/errata; A yB rechazados preservados. No aceptación de navegación, CCT, visual ni global. Evidencia: [quality-continuation](../evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/quality-continuation-20261025/README.md).
