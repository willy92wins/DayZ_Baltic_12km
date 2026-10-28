# Carreteras B1 — consumidor, pivote y corredor completo

Estado: REVISADO_PARA_DESCUBRIMIENTO. Fable5.1 nativo, 68.469s, adjudicado 29-10.
Codex ejecutor/integrador por petición
viva de preparar carreteras mientras continúan las pruebas. Traza P5/P9/P10/P11.
No autoriza colocar carreteras globalmente ni ejecutar una misión sin revisión.

## Descubrimiento que cambia la siguiente prueba

El catálogo A y las caras B0 se conservan sin repetir sus extractores. La tabla
completa del WRP0da63d3f ya sellada (5509 modelos/2578398 instancias) contiene
cuatro modelos de puente/28 instancias y cero modelos roads/parts. La consulta
por nombre sobre todo el catálogo está guardada en road-wrp-reference-reuse-20261029.
La ausencia sólo corresponde a objetos: no se ha decodificado RoadNetwork ni
demostrado su ausencia. No atribuir 28 instancias a 28 cruces. Las clases en
config instalada (1c7aad19) declaran piezas estáticas; eso no prueba consumidor.

B0 no puede resolver el pivote de asf1_25/asf2_25/asf1_10 100 a partir de poses
inexistentes en esa tabla. Tampoco sirven como oráculo sus nombres, bbox o los
TXT antiguos FTT sin importación certificada. Cualquier piloto necesita observar
el consumidor realmente escogido y su pose. Evitar otro censo idéntico de assets.

## Unidad propuesta y resultado esperado

1. Investigación sólo lectura acotada a la vía de exportación/importación actual:
   capas de formas y bibliotecas de Terrain Builder, config mundo y recibos.
   El lector 0WZD actual sólo admite alturas/materiales/objetos y EOF. No repetir
   esa lectura ni extender compiled_arrays para buscar RoadNetwork. Localizar
   la instrucción real que introduce piezas; citar archivo/línea y formato, sin
   inventar lectura completa OPRW desde un buscador de modelos. Contrastar con
   la tabla compilada sellada y recibos de Terrain Builder/Binarize existentes.
2. Elegir un único piloto de consumidor observado: WRP_OBJECT o WRP_ROADNET.
   Si el mecanismo sigue UNKNOWN, terminar INCONCLUSIVE_CONSUMER y diseñar un
   experimento específico; no generar poses como si el pivote fuera conocido.
   Un objeto creado por script sólo demuestra esa vía, no automáticamente WRP.
3. En una unidad posterior, para la vía demostrada, preparar tres poses de B0:
   identidad, giro90 y pieza curva en identidad (no trayectoria curva). Leer centro local
   y matriz; contrastar la superficie mundial completa Visual/Roadway bajo las
   hipótesis de pivote. Conservar ambas si la evidencia no discrimina; no elegir
   la que mejor encaja en el terreno. Binario y prueba nativa requieren plan
   posterior propio, sin compartir el mundo/control de la pareja B3G.

Consumidor de la salida: generador del corredor R-PAVE-49. Necesita transformación
local->mundo justificada, calzada/material de apoyo y máscara completa de pieza.
No se permite llamar ancho útil a bbox12/9m; separa calzada, arcén y Visual.
Las máscaras B0 privadas se reutilizan por hash; no publicar geometría vanilla.

## Aplicación después de resolver el consumidor

Cuatro pilotos vigentes: seco49 (5296,6000), cruce49/arista301 cerca del personaje
(4789.51465,5516.52197), Narva71 y extremo kit118/cadena76. Las coordenadas de
personaje sólo localizan feedback; el cruce se deriva de geometría carretera/agua.
El perímetro de ensayo debe incluir toda la huella de piezas y los accesos hasta
terreno conectado, no sólo eje ni corredor histórico8m. Retener cruces en nodos,
microhuecos, extremos y superposiciones con lecho/agua/objetos.

P9: fondo1m/calado geométrico mínimo0.95m/corredor24m y exclusiones previas según
decisiond510af67. No inventar máximo de oleaje, gálibo o barco mediano. P11 mantiene
cross0.03m, grade0.065 y chord0.03m; las exclusiones del gate histórico (agua48m,
Narva470m, extremos18m) siguen NO EVALUADAS para cruces y accesos.
Los23.9566664m² de lecho expuesto son evidencia en banda8m; no un área sobre la
huella física completa, ni una reparación. Primero conflicto/soporte, luego
pavimentado aislado y conducción. P10 preserva la base antes de mapeado global.

## Presupuesto y negativos antes de código

Revisión de esta unidad180s; descubrimiento consumidor120s/2GiB con rutas cerradas
por la revisión y una salida nueva. No recensoA/B0 ni búsqueda de todo el disco.
Si aparece formato desconocido, guardar ancla y alcance incompleto; no parsear
permisivamente ni convertir ausencia de coincidencias en ausencia de red vial.
Tras fuente confirmada, plan concreto de transformaciones y código revisado
antes de cualquier autoría. No DayZ/lease/WRP/PBO nuevo en esta primera unidad.

Negativos mínimos del futuro consumidor: eje sin pavimento, bbox con arcén no
transitable, pivote recentrado aplicado dos veces, matriz traspuesta, giro90,
LOD ausente, punto de personaje fuera del cruce, puente cercano sin cobertura,
contacto sólo parcial del ancho, acceso cortado y agua coincidente con lecho.
Preservar como controles el corredor49 local y pasos diseñados, sin generalizar
su visto bueno visual a toda la red. Decisiones de ancho/clase nuevas sólo cuando
existan alternativas materiales concretas, sin repetir permisos ya concedidos.

## Adjudicación y cobertura de esta ejecución

Anclas verificadas: tools/terrain/wrp0wzd.py:3-9,49;
tools/terrain/package_visual_forest_ev112.py:30-73,117-119. H1 = pos - R.T @ bc;
H2 sin transponer y H3 doble recentrado, sólo hipótesis. No trasladar la guarda
forestal de 5 mm a certificación vial. Centro horizontal no nulo no basta para
probar orientación; si los datos no discriminan, NO_DISCRIMINA/UNKNOWN.
W/tb ausente: consultar tb del checkout principal del mismo proyecto y
stage-kit7-fc-20261026/root/dayz_baltic_12km_dev/tb, más recibos package-kit7.
Recorrer metadatos con máximo10000entradas; leer sólo texto de interés <=2MiB
por archivo y <=20MiB total. Listar exclusiones. B0 sólo por hashes, no extracción.
La ejecución termina tras inventario/anclas y no implementa poses del paso3.
Recibo de adjudicación: road-b1-plan-review-20261029/adjudication.md.

R0 del descubrimiento consumido: límite de 10000 entradas alcanzado en 2.641s; no informe ni aceptación. R1 conserva 120s/2GiB y 10000 entradas, reduce a tb/narva_trial y tb/regional_road_network_v29 del checkout principal más stage-kit7 y recibos. Excluye data, navmesh, compiled, out, Cache y Layers; registra exclusiones. Busca formas/plantillas y metadatos; no un censo de texturas. No eleva ausencia de texto a inexistencia de red. Inventario persistido antes de leer B0. Hipótesis: los enlaces del proyecto permiten identificar la vía sin recorrer capas raster.
