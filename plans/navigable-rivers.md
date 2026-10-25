# Ríos navegables — fase de ingeniería

Petición30-09 de Guillermo: continuar, ríos suficientemente anchos/profundos,
puente final elevado; referencia elegida lancha vanilla con margen para barcos
medianos. P9 amplía la aceptación. No reabrir recorte ni escala global.

Prioridad posterior de Guillermo (P10): terreno e hidrografía regional, integración
nativa y navegación base antes del mapeado. El puente de este piloto es una
herramienta de ensayo de gálibo, no el inicio de una población definitiva.
Una navmesh del terreno vacío solo acredita esa geometría; regenerar después
de colocar edificios, vegetación y vías. No gastar el presupuesto actual en
decoración ni en cerrar la economía del servidor.

## Alcance y controles

1. Medir Boat_01 y los puentes vanilla instalados, conservando hashes. Geometría
   visual/colisión no equivale a calado real flotando ni incluye automáticamente
   todos los pasajeros; registrar esos límites.
2. Auditar ejes OSM de Narva, Neva, Luga y brazos del delta: altura del lecho
   actual, anchura de referencia y continuidad. El DSM no es batimetría. Agua
   elevada sigue pendiente; no asumir que todo polígono está al nivel del mar.
3. Preparar un ensayo reversible alrededor del puente de Narva con cauce ancho,
   lecho profundo, puente elevado y rampas. Preservar fuera de la intervención,
   eje geográfico e islas. No sobrescribir el paqueteebc60f4f aceptado.
4. Importación persistida, WRP y navegación propia para el nuevo terreno;
   prueba real de lancha más regresión del cruce terrestre. Sin PASS de navegación
   por mera geometría ni por mover una embarcación con SetPosition.

[DESIGN] Reserva de ingeniería para barco mediano aún no seleccionado:12m eslora,
4m manga,1.5m calado,4.5m sobre agua. No son medidas de un asset ni promesa para
cualquier barco mediano. Objetivo de ensayo:24m de canal útil,3m de profundidad
al agua mínima,6m libres al agua máxima; curvas y accesos requieren espacio
adicional. Malla6m limita precisión: no validar solo los vértices del centro.
La plataforma inicial9m es candidata, solo si el modelo deja6m libres reales;
vigas, pilas, anchura y rampas deciden modelo y cota definitivos.

Revisión tras medir los seis puentes instalados: el puente metálico25 tiene
pilas dentro del corredor central24m. El ensayo usa tres tramos de25m a escala1,
tablero9m, cauce24m y paso central18m entre pilas. La reserva de manga4m mantiene
7m laterales por lado en ese paso recto. Los75m de puente alejan los terraplenes
del cauce. Cota mínima calculada bajo vigas:6.338m sobre agua máxima1m; es una
predicción de colisión del modelo, pendiente de pose y recorrido en motor.
No afirmar24m libres de obstáculos bajo cada tramo. Modelo y orientación de
cada familia comprobados por LOD; madera usa ejeX, metal/piedra ejeZ.

Reglas de aceptación: cadena de muestras continua dentro del canal útil y al
nivel mínimo de agua; sin triángulos que cierren el cauce. Sección navegable libre
de colisiones al máximo de agua. Recorrido real ida/vuelta, giro, arranque y parada
sin encallar/impactar; registrar salud y posición desde servidor. El paso bajo
puente incluye barco y tripulante. Regresión de terreno seco y paso por carretera.

No rebajar todos los lagos al mar para obtener un PASS. Donde el nivel elevado
o las islas impidan el objetivo, marcar conflicto de diseño antes de modificar.
Narva es el ensayo inicial; completar este sector no acredita todos los ríos.

Discriminador del primer candidato: cinco vértices del talud de acceso quedaron
dentro de triángulos del canal protegido, sobre todo en su curva. Profundidad
FAIL; rampas, empalmes y hueco del modelo sí cumplen. V2 recorta exclusivamente
el peso del terraplén contra el buffer del cauce más el margen de diagonal6m;
se conserva V1 rechazado y se exige nuevamente profundidad y acceso terrestre.
V2 pasa profundidad pero su transición del talud deja2.64m de gap en el empalme
este. El discriminador de compatibilidad muestra0 vértices compartidos entre
los triángulos del canal y los de ambos empalmes. V3 fija solo los vértices de
soporte de esos empalmes a9m; vuelve a exigir todas las puertas sin reducirlas.

V3 pasa las puertas offline. El control de TB escribe el nombre del proyecto
pero no activa Abrir, incluso tras recuperar sesión del control nativo. Para
seguir con un ensayo de motor se permite una copia derivada del0WZD verificado:
sustituir únicamente alturas por el ASC, tres poses del mismo puente y retirar
el estanque diagnóstico. Comparar cabecera/materiales byte a byte y releer las
4.194.304 alturas y poses. No presentar la copia como export nativo ni importación
persistida. Navegación anterior solo para bootstrap de ensayo, pendiente de
regenerar; no aceptar IA ni publicar ese paquete como versión terminada.

Presupuesto inicial: una auditoría offline y un candidato de Narva; identificar
un discriminador si falla antes de iterar. Sin modificaciones regionales masivas
ni repetición de variantes sin información nueva. El estado vivo queda en HANDOFF.

Fuentes leídas: geo_common.py:game_xy/tb_geometry; prepare_prototype.py:84–106,
141–162 (fondos solo del océano, aguas interiores sin generar); instalación
DZ/vehicles/water/config.cpp:42–54 (Boat_01, modelo, combustible y bujía);
reader ODOL.from_file/LOD.read/Polygon.vertex_indices de la skill debinarizer.
