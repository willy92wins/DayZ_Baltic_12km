# Cauces y puentes navegables

## Separar las referencias

Un DSM suele describir la superficie visible del agua, no el fondo. En Baltic,
`tools/prepare_prototype.py:84–106` generaba batimetría sintética exclusivamente
en el océano. El inventario de lagos en `:141–162` era una referencia sin objetos
de agua colocados. No deducir profundidad jugable de un polígono ni de azul en
el satélite. La auditoría local está en `evidence/navigation/baseline-waterways.json`.

Las relaciones OSM pueden anidarse: Lake Peipus incluye casi íntegramente otras
dos relaciones del mismo sistema. Unir antes de contar área o generar superficies,
conservando referencias y niveles por cuerpo. Los huecos/componentes diminutos de
la unión pueden ser residuos geométricos; no tratarlos todos como islas reales.

Separar lagos/embalses de ríos/canales antes de asignar cotas. Una unión de toda
el agua puede conectar Peipus con Narva: ese componente describe un sistema
hidrológico, no una única lámina horizontal. Conservar ambas vistas: unión para
contar superficie e islas; masas separadas y conexiones para diseñar niveles.

## Agua elevada: consulta, registro y flotación

[IN-GAME CONFIRMED, Baltic,30-09-2026] El pond_50x50 vanilla horizontal registró
agua a6m sobre terreno1.39m tanto creado dinámicamente como persistido en un WRP
diagnóstico. Una lancha propulsada cruzó juntas y conservó salud600. La huella
medida corresponde a52m, no a50m; comprobar escala y solape del modelo instalado.
Fuentes: `evidence/regional-foundation-v1/elevated-water-{dynamic,static}-v1.json`
y sus logs por SHA. El WRP diagnóstico se derivó de una exportación; no prueba
un nuevo guardado de objetos desde Terrain Builder.

En esas mediciones GetWaterDepth cambió al variar la Y de consulta: se comportó
aproximadamente como superficie con onda menos Y. No equivale a profundidad
hasta el fondo salvo que se consulte desde el fondo medido. Registrar SurfaceY,
superficie con/sin onda y clasificación, con controles fuera de la huella.
Contratos instalados: `scripts/3_game/global/game.c:1181–1187`.

[IN-GAME CONFIRMED, Baltic 01-10] El orden de consultas cambió el resultado:
en 627 puntos, dos lecturas de GetWaterSurfaceHeightNoFakeWave antes de
SurfaceIsPond/SurfaceIsSea dieron 544 cotas incorrectas; después de clasificar,
ninguna. El ensayo invirtió el orden manteniendo los puntos. Esto acredita la
dependencia observada, no una explicación interna de caché. Bajo el puente,
154 puntos devolvían Pond=false aunque la consulta 3D a la cota del agua
registraba fresh_water_ext líquido y profundidad positiva. La alternativa debe
exigir tipo líquido, máscara de agua y altura de consulta acotada; un nombre
de superficie aislado no demuestra agua navegable.

La sonda V4 con ese orden pasó 81.212 muestras congeladas de agua/tierra en
el WRP nuevo; el mundo anterior falló 80.629. Las 79.420 muestras de canal
mantuvieron al menos 3.04081m de calado. Es cobertura puntual y consulta,
no flotación, render ni paso físico. Evidencia: `evidence/overnight-2026-10-01/`
`water-query-order-v1/analysis.json`, `diagnostic-consumer-v4/verification.json`
y `consumer-v4-old-world-negative/`; consumidor
`missions/BalticFoundationConsumerV4.BalticTrial/init.c:54–71`.

El constructor CreateStaticObjectUsingP3D y SetOrientation no compartieron
unidades:0.5729387 en el constructor produjo32.826969grados; .0099996667 produjo
aproximadamente .572939grados. SetOrientation recibió grados. Confirmar unidades
mediante GetOrientation/ModelToWorld en el consumidor real; no deducirlas del
nombre ypr. Fuente contractual: `game.c:679`; discriminador local
`water-pose-v2.log` y `slope-boat-v3.log`.

La pieza inclinada permitió propulsión, pero SurfaceIsPond devolvió false.
Deformar la malla y dejar el objeto horizontal tampoco fue equivalente: en ese
modelo la consulta devolvió una altura constante. No generalizar un mecanismo
global del motor a partir de esos ensayos, ni aceptar el agua solo por verse azul
o soportar un barco. El control plano reconstruido sí registró agua.

Una alternativa local pasó el consumidor: piezas horizontales con salto0.05m,
centros cada25m, escala0.5. El barco vacío recorrió89.24m hacia arriba y cruzó
cuatro juntas;936 muestras de agua,116 de movimiento,salud600. Fuente:
`stepped-water-v1.json`, hash del log918dbc64. No acredita apariencia, regreso,
tripulación, WRP ni continuidad regional. No presentar esa discretización como
una superficie matemática continua.

## Verificar el canal completo

En malla triangular, comprobar solo eje o vértices interiores puede dejar un
triángulo somero atravesando el canal. Una prueba conservadora enumera todos los
triángulos que intersecan su polígono útil y exige profundidad en sus tres
vértices: la interpolación convexa acota el resto. Congelar la referencia y
rechazar también el terreno anterior y un tapón somero insertado como negativo.

El soporte geométrico puede ensanchar la modificación más allá del canal útil.
Medir conflicto con islas/orillas antes de aplicar un buffer regional uniforme;
el margen de diagonal de una celda no autoriza eliminar esos elementos.

Los accesos del puente deben proteger la curva del río, no únicamente una franja
recta perpendicular al tablero. Baltic V1 dejó cinco vértices de talud dentro
del cauce; V2 protegió el agua pero abrió un escalón de2.64m en el empalme este.
La intersección de conjuntos de vértices demostró que canal y empalmes podían
corregirse por separado. V3 pasó ambas puertas sin reducir profundidad ni
relajar tolerancia. Caso: `tools/navigation/verify_narva_navigation.py` y
`tests/narva_navigation_v{1,2,3}/verification.json` del proyecto.

## Gálibo y evidencia del barco

Medir la colisión bajo las vigas, no solo cota del tablero. Pilas y orientación
local deciden el hueco. En los modelos instalados examinados, metal/piedra usan
el ejeZ longitudinal y madera el ejeX; no generalizar ese resultado a todos los
assets. Leer y transformar Geometry/Roadway del modelo concreto.

La silueta estática del barco no demuestra su calado flotando, su tripulación
ni movimiento. Una reserva para un futuro barco mediano es un sobre de diseño,
no un asset medido. Probar desplazamiento mediante física, profundidad, salud
y paso de tripulantes; SetPosition/SetVelocity por frame no acreditan navegación.

[IN-GAME CONFIRMED, alcance local] En Baltic V3,172 vértices y tres cotas de
tablero coincidieron con la geometría prevista; el terreno anterior fue rechazado.
La lancha vacía mantuvo salud y motor activo pero avanzó solo3.248m en180s.
Separar PASS de geometría y prueba de movimiento INCONCLUSA; acelerador, motor
encendido o velocidad total no prueban avance horizontal ni paso bajo un puente.
Fuente: `evidence/navigation/runtime-verification.json` y su log por SHA.
El primer fallo de compilación del bridge quedó superado en el ensayo posterior;
no conservarlo como bloqueo vigente. No promover las medidas locales como
parámetros universales ni presentar una lectura ModelToWorld como colisión.

Cuando el barco no avanza, medir marcha actual/futura y neutra, RPM y hélice
antes de excavar más. En el control Baltic en mar abierto de fondo-12m,
170 muestras conservaron salud600 pero marcha1=neutra1, RPM700 y hélice0:
subir el acelerador hasta0.75 no acreditó propulsión. GetClutch devolvió un
entero fuera de escala; esa lectura quedó inutilizable, no se dedujo acople.
Fuente: evidence/navigation/calibration-v1/analysis.json. Un desplazamiento
por deriva tampoco debe aceptar el gate de propulsión.

[EXACT: contrato de fuente] transport.c:251–262 indica que
otros sistemas pueden cambiar las entradas y recomienda aplicar Setters desde
OnInput. BoatScript:342–345 solo llama super. Si se ensaya un controlador propio,
aislarlo por instancia y medir que el callback ejecuta; no afirmar que resolvió
el fallo hasta observar transmisión y avance reales. No modificar scripts vanilla.

[IN-GAME CONFIRMED: control acotado] En Baltic, el siguiente ensayo con Setters
en OnInput y solicitud repetida de marcha avanzó89.278m entre muestras, sin daño,
con85 muestras consecutivas de propulsión. Mismo mapa/embarcación; no se aisló
el efecto de callback frente a la frecuencia de ShiftTo. GetThrottle leído
desde CallLater devolvió0 pese a RPM/hélice/movimiento medidos: guardar también
la solicitud y su fase temporal, no tomar ese readback aislado como falta de input.
Evidencia: calibration-input-v2/analysis.json, log9b29af8f. Es mar abierto y barco
vacío; no sustituye la prueba del río, la tripulación ni el paso bajo puente.

## Agua recortada y colocación estática

[IN-GAME CONFIRMED, ensayo Baltic30-09] Mallas horizontales procedurales con
material pond_moss_1 y Roadway water_ext conservaron un recorte cóncavo y un
hueco seco. Piezas de48.02m a escala1:936 consultas,529 controles alrededor del
hueco y116 muestras de lancha,89.41m sin daño en la variante WRP corregida.
Las variantes200m, escalada y horneada, registraron altura de agua pero no toda
la clasificación SurfaceIsPond: no generalizar un tamaño máximo del motor.

La pose usada por CreateStaticObjectUsingP3D no se trasladó literalmente al
0WZD: los controles exteriores se inundaron. En esos modelos ODOL55,
bounding_center no era cero en las piezas recortadas. Manteniendo modelos,
terreno y orientación, sumar ese centro a la traslación WRP de cada pieza
resolvió todos los controles. Native Object.GetPosition confirmó la pose nueva.
Esto aísla la colocación de ese formato/ensayo; para otra rotación, escala,
importador o tipo de modelo, verificar su transformación completa, no sumar
vectores sin considerar los ejes. Evidencia: static-shape-v1 FAIL y
static-shape-v2 PASS, más correct_static_water_origins.py en el proyecto Baltic.

La unión al mar se midió con fondo-12m y planos0.45/0.75/1.25m frente a mar
0.850742m: GetWaterSurfaceHeightNoFakeWave devolvió max(mar,plano). Los controles
fuera de huella mantuvieron el mar. Una boca de río puede solapar por debajo del
mínimo marino, pero aún exige profundidad, continuidad y revisión visual.

## Rasantes y conducción: continuidad

[IN-GAME CONFIRMED: paso local con lancha vacía] El ensayo posterior Baltic
route-input-server-v1 registró226 muestras continuas, paso a ambos lados del
puente bajo el vano central, llegada al destino y salud600 intacta. No acreditar
el cruce solo por llegar: contrastar la trayectoria con el plano del puente,
posición lateral bajo el vano, corredor y transmisión. Seis negativos rechazan
END ausente, deriva sin hélice, daño, hueco temporal, salto de posición y distancia
declarada falsa. El run anterior llegó pero tenía una pausa antes del arranque;
conservar su FAIL estricto, sin relajar continuidad. Una repetición solo servidor
pasó; esto no aísla la causa de la pausa ni verifica tripulación o imagen cliente.


[MECHANISM VERIFIED: medición geométrica] La pendiente máxima no basta para
describir una carretera lisa: medir cambio de rasante, caída transversal,
desviación dentro de cada tramo y discontinuidades terreno/pieza/puente.
El piloto Baltic no tenía escalón calculado en las juntas y mostró menos de1cm
de desviación sobre cuerda6m; aún requería conducción vanilla con velocidades
representativas. Fuente: `tools/navigation/audit_approach_smoothness.py` y
`evidence/navigation/approach-smoothness.json`. No convertir esos valores
observados en tolerancias universales ni declarar el vehículo validado.

Extender el muestreo más allá del extremo diseñado hasta la conexión con la
futura vía. Baltic hasta280m tenía desviaciones de cuerda6m menores1cm; hasta
320m aparecieron13.4cm y cambios de pendiente de6.27pp, en terreno exterior
sin preparar. Una rampa suave no acredita la carretera que continúa tras ella.
Fuente: evidence/navigation/approach-outer-transition.json y approach-profiles.png.

El muestreo espaciado puede omitir caras empinadas de la malla nativa, incluso
con rasante central suave. En el ajuste Baltic V10 se limitaron los gradientes
de todos los triángulos del corredor y se verificó aparte cada 0.25m en 33
líneas transversales. Medir la pendiente también con la distancia horizontal
real de cada línea desplazada: en curvas no coincide exactamente con la del
eje. Conservar los candidatos fallidos; el PASS geométrico no prueba conducción.
Fuentes: `tools/navigation/prepare_narva_foundation_crossing.py:112–161`,
`verify_narva_foundation_crossing.py:37–70` y `tests/regional_foundation_combined_v10/`.

[IN-GAME CONFIRMED, Baltic 01-10] La prueba posterior V3 recorrió con un
CivilianSedan vacío los accesos y el puente225m de Narva en ambos sentidos,
aproximadamente1.019km por sentido. Conservó salud1000 y cuatro contactos de
rueda, sin intervalos en el aire; error máximo de contacto4.06mm, velocidad
máxima26.9km/h y parada<=0.2m/s durante5.4s. Dieciocho negativos rechazaron
daño, rueda ausente, vuelo, teleport, tiempo discontinuo, deriva sin mando,
colocación falsa y terminal incompleto. No acredita conducción humana, otras
carreteras ni velocidades mayores. Evidencia: `evidence/overnight-2026-10-01/`
`foundation-drive-v3/runtime-complete/{verification,negative-controls}.json`.

La variante anterior completaba el viaje pero fallaba el spawn por24cm. Un
registro por etapas situó la desviación ya al volver de CreateObjectEx,
antes de orientar o añadir componentes. Se corrigió una sola vez con
SetPosition antes del asentamiento y se repitió con los mismos criterios.
No confundir esa preparación inicial con forzar pose o velocidad durante
el recorrido. El ensayo no aisló el mecanismo interno de la creación.
Fuentes: `missions/BalticFoundationDriveV3.BalticTrial/init.c:59–77`,
`foundation-drive-v3/runtime-complete/placement.log`; API local
`P:/scripts/3_game/entities/object.c:300`.

Después de ensanchar un río, repetir la comprobación de apoyos y extremos del
puente. En Baltic, los extremos del puente anterior quedaron sobre agua aunque
el canal tenía profundidad suficiente. La ampliación local y sus rampas deben
respetar agua/islas y verificarse antes de regenerar navegación. Nueve tramos
y tablero11m fueron un candidato local, no una receta universal; importación,
colisión, recorrido bajo pilas y tripulación son comprobaciones separadas.

## Orden de integración

### Islas y orillas en una malla finita

Un hueco correcto en el modelo de agua no garantiza una isla emergida: medir
también el terreno frente a la cota local. En Baltic, 200/283 representantes
quedaban bajo el resguardo diseñado aunque los polígonos no se solapaban.
Conservar polígonos y validar planos de triángulos nativos sobre sus
intersecciones con tierra; un raster de centros puede omitir islas pequeñas.

Elevar todo triángulo que toca tierra puede rellenar agua contigua. El combinado
v8 redujo un lago de969m² a189/965 muestras mojadas. El ajuste v9 mantuvo la
orilla al nivel del agua y resguardo0.35m en el interior de la isla, recuperando
785/965 muestras. No es reproducción exacta de la orilla ni receta universal.
Comprobar de nuevo calado, pendientes y rasantes después de cada soporte de
isla. Evidencia offline: `protected-island-native-plane-v9.json`,
`lake-217-island-tradeoff-v9.json`, `combined-geometry-v9.json` del proyecto Baltic.

### Archivos de entrada de las sondas

`P:/scripts/1_core/proto/enstring.c:396–421` implementa `string.Split` e inserta
solo fragmentos de longitud positiva. No conserva columnas vacías de CSV.
En Baltic, la sonda V2 compiló y leyó80615 filas húmedas, pero terminó
`MALFORMED_WATER_INPUT` al primer campo vacío de una fila seca. Usar un centinela
explícito para columnas sin valor y comprobar esquema, total y marcador final;
conservar el FAIL incompleto. V3 corrigió el formato y completó en el motor
81212 consultas agua/tierra y314 de navegación, con15 rutas. Contra el terreno
anterior, el verificador devolvió el FAIL de alturas esperado. Evidencia Baltic:
`consumer-v3-baseline-water.log`, `consumer-v3-baseline-nav.log` y
`consumer-v3-baseline.json`. Esto acredita el lector y ese control negativo;
no acredita el nuevo terreno, aún pendiente de importación en aquel ensayo.
Un lint sin errores no acredita el lector del motor.

Para comparaciones milimétricas, verifica también la precisión del registro.
En Baltic, concatenar las componentes escalares redujo coordenadas cercanas a
10km a una sola cifra decimal; `vector.ToString()` conservó seis decimales.
Dos registros del mismo tick redujeron el error de SurfaceY de3.50/6.58mm a
0.004/0.097mm al usar las coordenadas precisas. Se conservó el FAIL del registro
antiguo, porque las coordenadas omitidas del resto de filas no se recuperan.
La nueva sonda mantuvo el umbral2mm, añadió el vector preciso y controles de
esquema y truncación. Fuente: `evidence/overnight-2026-10-01/regional-boat-v1/`
`runtime-complete/position-rounding-discriminator.json` y
`regional-boat-v2-controls.json`. No atribuir ese error a la malla ni relajar
el umbral del terreno sin aislar antes la serialización.

### Dependencia de la navegación

La navegación depende del terreno y los obstáculos. Si se prepara antes del
mapeado, etiquetarla como base y regenerarla después de los objetos. Un `.nm`
anterior puede permitir el arranque de un ensayo, pero no valida su WRP nuevo.
Mantener visible esa distinción en el manifiesto del paquete.

Con perfiles compartidos, localizar el RPT por misión/mods del run, no solo
por fecha más reciente. En Baltic, una sesión distinta escribió Chernarus
después del intento BalticBoat: leer solo el último archivo sugería falsamente
que el launcher había ignorado parámetros. El RPT correcto conservaba todos.

### Construir recorridos largos a partir de ejes fluviales

No concatenes features suponiendo que solo se conectan por sus extremos.
En el ensayo offline Baltic del 01-10, el recorrido de Narva construido así
contenía 211 intersecciones de segmentos no adyacentes; dos features recorrían
varias veces los mismos segmentos. Se rechazó antes de lanzar el motor.

Para obtener un canal principal, divide la red en sus intersecciones y solapes
y calcula el camino entre los extremos elegidos sobre esas aristas existentes.
Comprueba que el resultado es simple, conectado y no añade segmentos fuera de
la red fuente. Conserva la ruta rechazada, los extremos, procedencia y longitud
antes/después. No desplazar agua o terreno para corregir la ordenación de una
ruta de prueba. La misma cautela aplica a ramales del delta.

La prueba Baltic de esta transformación tiene controles analíticos de ramal
repetido, conexión interior y red desconectada. Fuentes: proyecto Baltic,
`tools/navigation/prepare_full_river_consumer.py`, `tests/test_full_river_trace.py`
y `evidence/overnight-2026-10-01/full-river-preparation-attempt01.json`.
Esto acredita la preparación geométrica; el recorrido físico sigue siendo
un gate distinto. Tramos solapados recorridos por embarcaciones independientes
acreditan su cobertura conjunta, no un viaje único de extremo a extremo.

### Marcadores terminales frente a medidas físicas

[IN-GAME CONFIRMED, Baltic 01-10] La prueba regional V3 completó ocho viajes
con lancha vacía, ida y vuelta independientes en sectores de Narva, Luga, Neva
y delta, sin pérdida de salud. Se contrastaron continuidad, trayectoria,
transmisión y terreno con el registro real y la referencia congelada. No es
prueba de todos los ríos, tripulación ni embarcaciones medianas.

El marcador heredado `ARRIVED_AND_STOPPED` significaba quitar entradas y esperar
diez segundos. La velocidad final medida seguía entre 0.31 y 0.36m/s: acredita
llegada y liberación del mando, no parada completa ni estacionamiento. Dar
prioridad a velocidad, duración y posición medidas sobre el nombre del marcador.
Si el criterio exige parada, declarar antes su umbral y tiempo de permanencia.
Evidencia: `evidence/overnight-2026-10-01/regional-boat-v3/runtime-complete/`
`verification.json` y `terminal-speed-observation.json` del proyecto Baltic.

[MECHANISM VERIFIED, cadencia de la sonda] Un límite sobre el salto de índice
de objetivo debe tener en cuenta la frecuencia de control y de registro. La
sonda fluvial larga Baltic controla cada100ms y puede avanzar un objetivo por
tick, pero registra cada500ms. En una curva de Narva pasó111→114 entre dos
muestras separadas0.5s, con movimiento continuo de unos0.68m. El gate de salto
máximo2 falló aunque la proximidad a todos los puntos y la salud pasaron.
Se conserva el FAIL. Para un nuevo ensayo, registrar cada transición y validar
su orden; no inferir saltos físicos ni alterar el cauce por una serie submuestreada.
Fuentes: `missions/BalticFullRiverV2.BalticTrial/init.c:58,96-106,122-134` y
`evidence/overnight-2026-10-01/full-river-v2/case6-target-order-observation.json`.

El ensayo largo completó12 tramos solapados sobre26.600558km distintos, con
9PASS y3FAIL (el salto anterior y dos derivas terminales). Todos visitaron sus
puntos sin perder salud. La cobertura no convierte el agregado en PASS ni
demuestra viaje único, retorno, tripulantes o casco mediano.
