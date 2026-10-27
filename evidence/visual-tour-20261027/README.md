# Visita visual y carencias de revisión — 27-10-2026

Guillermo revisa en juego la versión Kit7Nav8Load1 y rechaza tres síntomas:

- **NARVA-VIS-01 / 007:** relieve emergente en L delante de la presa.
- **NARVA-VIS-02 / 015:** puente desalineado. Medir eje previsto, empalmes y accesos antes de determinar giro o desplazamiento.
- **NARVA-VIS-03 / 007:** orillas con rectas, esquinas y círculos demasiado regulares. La imagen anotada señala bordes aguas arriba, ambas márgenes y apoyos junto a la presa.

**Encargo explícito:** detectar y reparar procedimentalmente TODOS los casos equivalentes; no una colección de retoques locales. Estos ejemplos son regresiones obligatorias de la siguiente revisión de generación y validación.

## Mecanismo leído y lo que aún falta

`tools/quality/shape_patterns_ev112.py:128` busca componentes rectangulares cerrados; `:153` exige apoyo en los cuatro lados. No es un detector general de aristas abiertas en L/U. `tools/quality/screen_shapes_ev112.py:223` etiqueta Narva y otros dominios, pero no los elimina del censo. No atribuir el fallo a una máscara sin reproducción.

`shape_patterns_ev112.py:36` examina rutas simplificadas; no certifica toda silueta visible de la orilla ni todas las crestas someras. `tests/test_shape_patterns_ev112.py:47` rechaza círculos como negativos del detector de RECTÁNGULOS: eso no es una prueba de naturalidad de círculos.

La cobertura era insuficiente para el objetivo visual. Falta asociar cada defecto a sus coordenadas y capa, y confrontarlo con el censo guardado para distinguir ausencia de detección de hallazgo no resuelto. La causa de generación aún no está aislada. No declarar resuelta esta revisión porque existieran límites escritos o un estado REVIEW_REQUIRED.

## Trabajo requerido antes de aceptar

1. Consumir el terreno y modelos realmente compilados, extraer siluetas de ambas orillas y crestas visibles de aguas someras. Etiquetar dominios, sin ocultarlos por estar protegidos.
2. Añadir cobertura de L/U, aristas abiertas/conectadas, rectas largas y combinaciones recta-arco de radio constante. Examinar varias escalas y rotaciones; evitar depender de la teselación o del número de vértices. Círculo o recta aislados no equivalen siempre a defecto: registrar evidencia y distinguir estructuras diseñadas.
3. Validar los puentes contra un referente independiente: trazado de carretera, tangentes y continuidad de ambos accesos, posición y orientación en el WRP desplegado, soporte, gálibo, navegación y conducción.
4. Construir regresiones de estos casos reales y controles naturales/diseñados; el estado actual debe rechazarse por el motivo correcto. Diseñar/revisar un plan mecánico y presupuesto antes de corregir. No rebajar tolerancias existentes ni usar ruido aleatorio como certificado de naturalidad.
5. Corregir la generación por clases de defecto, regenerar y censar TODO el universo aplicable; preservar agua, extremos, topología, apoyos y protecciones. Validación independiente y nueva revisión visual a igual escala.

El piloto seco NPZ validado offline NO está materializado en esta versión. No confundirlo con lo observado. Las capturas originales permanecen locales en la carpeta de evidencia del build; hashes y versión en feedback.json. La imagen anotada sin ruta local permanece en la conversación.

## Kit-118: segunda parada rechazada

Run `216a08f4-9e0c-4c03-9245-d22f9aea1d33`, mismo mod y hashes de la primera parada, aparición en X8253/Z9038. Guillermo comunica dos veces el mismo reporte; se deduplica en **dos defectos**, no cuatro. Evidencia: [kit118-feedback.json](kit118-feedback.json).

- **KIT118-VIS-01 / 007:** «los lechos del río sobresalen mucho». Se exige comprobar procedimentalmente el volumen visible completo del lecho frente al terreno circundante y al agua real, con perfiles, pendientes de transición y silueta. Que Visual y Geometry coincidan entre sí no acredita su integración con el entorno.
- **KIT118-VIS-02 / 020:** «en el extremo solapa con la carretera». Se exige comprobar ambos extremos completos de todos los cauces contra el corredor real de carretera y sus accesos en el mundo compilado, sin limitarse al eje o al centro de las piezas. Clasificar los cruces intencionados y comprobar su continuidad, soporte y gálibo; no excluir todo contacto carretera/río.

Guillermo los clasifica expresamente como **errores de revisión**. Convertirlos en regresiones del generador y del consumidor independiente, dentro del alcance procedimental global ya exigido. El caso actual debe producir rechazo por su defecto real. Identificar aún la capa y el extremo exactos; no hay medición de altura ni captura de kit118 en este reporte, por lo que no se inventan coordenadas precisas ni tolerancias nuevas. No se ha implementado una reparación ni cerrado la validación. La visita sigue abierta, con el lease liberado para el usuario.

## Cauce continuo65: tercera parada rechazada

Run `c8e1b441-b374-4c27-9290-f305ce251453`, aparición X5162.107422/Z5864.658203, mismas tres PBO verificadas por hash antes del arranque. Guillermo señala: «esto esta como antes, el lecho sobresale demasiado y queda raro».

**CONT65-VIS-01 / 007** reproduce el síntoma reportado en **KIT118-VIS-01** en otro cauce. Mantener ambos como casos reales independientes para los controles de integración del lecho con terreno y agua. La repetición no demuestra por sí sola una causa común de generación; se debe aislar el mecanismo. El control debe cubrir la envolvente completa, sus transiciones y la silueta a diferentes alturas, además de la coincidencia entre geometría visual y colisión. [Reporte](continuous65-feedback.json).

Hasta la tercera parada se registraron seis observaciones rechazadas; dos corresponden al mismo patrón de lecho saliente. No equivalen a seis mecanismos distintos ni a un censo global. No hubo reparación ni aceptación visual nueva. Revaluar el plan de materialización MLOD pendiente frente a estos casos antes de implementarlo; los gates offline del piloto seco siguen limitados a sus invariantes y no acreditan esta integración visual.

## Carretera49: carretera bien localmente, río adyacente rechazado

Run `cbcf20d3-72bb-4e4a-8508-207f1e022b63`, aparición X5295.7/Z5999.9. Guillermo aclara que **la carretera está bien**, con pavimentado pendiente. Esta observación se limita al tramo visto: no acredita conducción ni todas las carreteras y no cierra005.

**ROAD49-RIVER-VIS-01 / 007:** rechaza el río a la derecha de su vista por estar formado por zigzags. Exige detectarlos y corregirlos procedimentalmente en toda la red, convirtiendo los trazados artificiales en curvas continuas y naturales. Conservar la intención del cauce, anchuras, extremos, receptores, cruces, topología del agua y protecciones; sigue vigente el rechazo de círculos demasiado regulares en Narva. No basta con redondear cada codo de una escalera ni sustituirla por arcos uniformes.

Identificar el río en los datos desplegados y confrontarlo con el censo de formas guardado: falta aislar si el control no lo detectó o si quedó señalado sin resolver. No inferir su ID ni sus coordenadas exactas de la palabra «derecha». El encargo de corrección queda en los planes; durante la visita no se cambia generación ni se declara corregido. [Reporte](road49-feedback.json).

## Cruce adicional señalado durante la misma sesión

Guillermo se desplaza y señala un posible puente ausente. Confirma que su personaje está en el punto mirando al cruce. Lectura MCP: **X4789.51465/Y2.95008/Z5516.52197**; dirección de cámara hacia el suroeste. El cruce exacto se derivará de carretera y agua; la posición del personaje no se presenta como su centro.

**CROSSING-VIS-01 / 015**, posible ausencia pendiente de confirmación. El puente más cercano en la lista EV110 está a809.6m y el cruce más cercano en el censo histórico EV106 a606.1m. Esto señala una posible carencia de cobertura, no demuestra la ausencia en el WRP actual. La consulta nativa devolvió80 de108objetos dentro de55m, por lo que no certifica un inventario completo; el rayo impactó al propio personaje y se descarta como prueba del cruce.

Regresión requerida: inventariar intersecciones carretera/agua de forma independiente de los puentes generados, contrastar TODAS con el WRP compilado y continuidad real del paso, clasificar cruces intencionados/noresueltos y mantener excepciones explícitas. No convertir «todos los puentes de la lista pasan» en «todos los cruces están resueltos». Sin reparación durante la visita. [Ubicación y límites](additional-crossing-feedback.json).

Aclaración posterior de Guillermo: **la carretera está partida por el río**, no es sólo una sospecha abstracta de puente ausente. CROSSING-VIS-01 pasa a RECHAZO VISUAL DE CONTINUIDAD confirmado por el usuario. Falta identificar el mecanismo y medir el cruce; la ausencia de puente sigue siendo una hipótesis técnica, no el estado del defecto. Exige revisión geométrica de todos los demás cruces y de las orillas tanto de ríos como del mar. La carretera49 bien localmente no exime este otro tramo roto.
