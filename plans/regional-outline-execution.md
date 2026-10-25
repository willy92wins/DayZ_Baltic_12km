# Ejecución del terreno regional y navmesh base

Petición viva30-09: hacer el grueso del terreno/outline y navmesh. Se ejecuta
P1–P13 y la propuesta de relieve selectivo aceptada. Sin mapeado de poblaciones
o vegetación. Base nativa0.2 conservada como rollback, no editar su proyecto.

## Orden, entregables y puertas

1. **Protecciones y outline:** extraer reserva de los PBF ya descargados y
   contrastarla con referencia geográfica/cobertura. Congelar costa, agua,
   humedales, delta, islas, piloto Narva y red viaria principal como máscaras
   trazables. Producir plano y GeoPackage/SHP de planificación para el editor.
2. **Relieve regional:** candidato derivado del WRP nativo aceptado, conservando
   exactas las cotas del agua y del piloto mientras se diseña el agua elevada.
   Colinas amplias en A/B según P12, interior ondulado, transición suave al área
   natural y valles. Ningún delta en máscara protegida. No inventar alturas
   hidráulicas por multiplicar el DSM. Generar ASC, raster de delta, perfiles,
   estadísticas de pendiente y verificaciones independientes.
3. **Corredores y agua:** fijar una red principal continua de carreteras como
   reserva de trazado, con alturas de ingeniería progresivas y conflictos de
   cruces identificados. Diseñar por sistema cotas de lago/lecho/agua mínima y
   máxima. Agua elevada requiere ensayo del asset/consumidor antes de aceptar
   la región. No bajar todos los lagos al mar ni tapar islas para un PASS.
4. **Integración nativa:** copia completa y acotada del proyecto TB, importación
   del candidato, guardado/reapertura/export. Comparar todos los vértices y
   registros de objetos con el delta congelado. Mantener SAT1M y materiales.
5. **Navmesh:** WRP/PBO de generación fijados por hash; servidor de datos propio,
   Generate all, guardar archivo nuevo, reempaquetar verificando el resto de las
   entradas. La NM previa solo sirve para bootstrap, nunca aceptación del nuevo
   relieve. Gate de cobertura y consultas/actores en sectores representativos.
6. **Carga y entrega:** carga cliente/servidor con paquete aislado, vistas de
   costa/SPB/reserva/colinas/Narva y medición comparada con0.2. Misión limpia y
   editable archivado. No publicar como1.0 ni acreditar80–100 sin esos ensayos.

## Revisión previa del plan

- Dominio: relieve/cauces/conexiones/reserva/navmesh, dentro del producto actual.
- No cambia recorte/XY. Las cotas de diseño son objetivos, no un algoritmo de
  escalado global. Fuentes inmutables, nueva carpeta por candidato.
- El snapshot de agua local no prueba lagos elevados ni conectividad regional.
  Es un gate propio que permanece visible aunque pasen altura y navmesh.
- Navmesh se genera después del WRP; no reutilizar evidencia de locomoción del
  baseline como aceptación del candidato. P10 exige regeneración tras mapeado.
- Agua, reserva y carreteras pueden competir con una colina: se reduce/diseña
  la colina; no se modifica silenciosamente una prioridad de producto.
- Presupuesto: una preparación regional y una importación; si falla un gate,
  conservar FAIL y aislar ese mecanismo antes de otra variante. No ajustar
  tolerancias retrospectivamente. No hay límite arbitrario al trabajo autorizado.

## PASS / FAIL / INCONCLUSO

PASS por etapa, no por número de checks: máscaras/rutas conservadas, deltas
exactos, transiciones medidas y geometría nativa persistida; NM ligada al WRP,
carga y consumidores reales. Negativos: baseline sin nuevo relieve y corrupción
en una muestra protegida deben fallar el verificador del candidato.

FAIL si hay modificación fuera de la máscara, pérdida de isla/conexión,
inundación nueva, export incompleto, NM de otro WRP o falta de registro final.
INCONCLUSO si faltan niveles de agua/consumidor o si la caja de pruebas está
ocupada. No cerrar procesos ajenos para completar esta fase.

Estado de arranque: MCP sin lease propio, sesión externa CF/LF_VStorage en2312;
preparación GIS/TB independiente disponible, servidor de datos/juego en espera.

## Ajuste de transición tras el discriminador V1

V1 conserva todas las protecciones pero la doble atenuación a330m mantiene el
sur en30.09m. Aislar carreteras no cambia ese resultado; retirar cauces o
humedales sí. No se adopta esa retirada: contradice las prioridades de agua.
Se sustituye la atenuación por una envolvente de incremento limitada a0.60m/m,
con arranque curvo de36m y suavizado de24m. Son pendientes de ladera; las
carreteras permanecen intactas en esta capa y siguen pendientes de rasante.
El incremento nunca supera la distancia disponible al valle protegido.
Se mantienen exactamente las mismas máscaras de V1 y las cotas objetivo como
techo, sin obligar a llegar a100–160m donde la hidrografía no deja espacio.
Aceptar offline solo con identidad de todas las protecciones, ausencia de
nuevas pendientes superiores a35grados en el terreno modificado y contraste
de perfiles. Esto no acepta todavía agua elevada ni navegación regional.

## Resultado geométrico V2/V3 y gate nativo

V2 no se acepta: el gradiente centrado ocultaba80 triángulos por encima de35°
(máximo38.689°). El verificador usa ahora ambos triángulos reales de cada celda.
V3 reduce únicamente incrementos de V2 mediante una envolvente vecinal de2.88m
por6m y conserva pendientes nativas preexistentes. Convergió en29 iteraciones;
29.507 vértices se redujeron frente a V2, sin modificar ninguna protección.
Máximo regional109.5685m; máxima pendiente afectada34.1696°. Positivo V3 y
negativos baseline/corrupción en reserva ejecutados. PASS solo geométrico offline.

La primera exportación después de importar/guardar/reabrir conservó las cotas
anteriores: FAIL con1.672.627 diferencias frente al candidato. Materiales,
cabecera y objetos exactos. Hay que aplicar el raster al heightfield del mapframe;
verlo en la escena no prueba que sea el terreno exportado. Se conserva ese FAIL
en evidence/regional-outline-v3/native-export-first.json. No empaquetar ese WRP.

## Integración y discriminador de navegación

Mapframe Processing/Rebuild aplicó el ASC al heightfield. Guardar, cerrar,
reabrir y exportar conservó los4.194.304 vértices exactos, materiales y3 objetos.
WRP persistido9bf50853; compilado0a993128. Navmesh propia35a5ec29 generada sobre
ese WRP:60.025 teselas. PBO regional e5c6865a, baseline0.2 sin modificar.

Gate runtime congelado:279/279 alturas coinciden; todas las consultas encuentran
navmesh, pero26 exceden2m de distancia3D y cuatro de seis rutas fallan por Y de
los extremos. No relajar la tolerancia. La persecución V1 tuvo deriva del objetivo;
V2 lo mantuvo fijo pero agotó90s en la subida. No atribuir ese comportamiento a
navmesh sin aislar percepción/estímulo.

[HIPÓTESIS] La teselación de50m puede representar con demasiada simplificación
las cimas. Ensayo único: tileWidth25, mismo WRP, agente, filtros, muestras y
verificador. Parámetro real en config.cpp:47 y guía oficial de Bohemia consultada
30-09-2026, https://community.bohemia.net/wiki/DayZ:Generating_navigation_mesh.
La pestaña Parameters local aparece vacía; se cambia solo el valor de config,
recompilando y comprobando las6826 entradas restantes idénticas. Generación nueva
y guardado separado. Registrar bytes/tiempo, no adoptar solo por encontrar caminos.
Si no mejora, conservar resultado y cambiar de discriminador, no encadenar tamaños.

Outline de planificación exportado en derived/outline-v3: áreas, carreteras SHP
en metros TB, áreas GeoJSON en WGS84 y plano evidence/regional-outline-v3/outline.png.

Resultado tile25,30-09:3/279 discrepancias frente a26;4/6rutas frente a2.
NM111.656.712bytes frente a31.310.232. No aceptación todavía. Conservar ambos
FAIL. Última comparación de resolución:12.5m, mismo WRP y contrato, para medir
si supera2m y cuánto cuesta. Se justifica por mejora medida, no por asumir la
causa interna. No extender automáticamente a más resoluciones si falla.
Computer Use solo en bloques de inicio/guardado; fuera durante generación y logs.

Comparación de coste antes de elegir candidato: misma misión existente
`BalticTerrainPerf`, servidor sin clientes/CE/IA y sin data-server, 30s de
calentamiento +120s medidos, un run25 y otro12.5. Registrar memoria residente,
privada y tiempo CPU del PID con inicio comprobado; conservar logs completos.
Es una pareja descriptiva en escritorio compartido, no un benchmark causal
ni una prueba de capacidad80–100. No promover a base activa mientras falten
locomoción regional y agua/rasantes; guardar el candidato en checkpoint separado.

Resultado12.5:279/279 muestras y6/6 rutas PASS. Repetir una sola vez el consumidor
físico V2 sobre el nuevo paquete, misma misión y addon de cliente, con fuente
idéntica por SHA y verificador sin cambios de criterio. Conservar cualquier
FAIL y no deducir causa a partir de la mera mejora del grafo. La sonda incluye
cámaras temporales y un objetivo humano inmóvil; no es recorrido de jugador.

## Discriminador de estímulo, después de NM12.5

V2 sobre NM12.5 conserva TIMEOUT: el control local pasa, pero la etapa1 permanece
en mind0 y se aleja del eje. No demuestra obstáculo de navegación. Fuente leída:
P:/scripts/3_game/noise.c:7 admite multiplicador externo; P:/dz/data/config.cpp:
4182–4185 define Rifle_Base NoiseShoot con strength100. No se asume que esa
fuerza equivalga a metros de alcance. La meta está a110m y tras la cima.

EnsayoV3 acotado: única variable funcional, multiplicador AddNoisePos1→4.
Mismo paquete12.5, misma misión salvo identidades/registro, mismos puntos,
90s/etapa y aceptación física. IA sin overrides de velocidad, orientación o
posición después del spawn; objetivo humano inmóvil. No tocar el terreno.
PASS solo si el verificador físico completo pasa; si solo cambia el estado
mental o vuelve a fallar, conservar resultado sin más barrido de intensidades.
No es prueba de percepción vanilla con intensidad normal ni benchmark de IA.

## Corrección del contrato de locomoción en terreno abierto

V3 con estímulo4 ya cruzó la cima en la ida, desviándose más de14m del eje.
Conserva FAIL bajo el contrato previo:4m laterales se heredaron del paso de
Narva de8m, pero no hay carretera de8m en esta colina. Es un error de intención
del ensayo; no equivale a que el infectado no pueda recorrer la ladera.

Nuevo ensayo independienteV4, fijado antes de ejecutarlo: P10/P12 requieren
locomoción física por el relieve, no alineación a un eje ficticio. Mismos
spawns y metas, estímulo4 y límite90s. Requerir llegar a<=4m en3D de la meta,
recorrido medido<=3×distancia directa (mismo factor previo de rutas del grafo),
salud positiva, muestras continuas<=1s, contacto físico -0.2..0.5m sobre suelo
y objetivo estabilizado<=2m. La desviación lateral se informa, no se confunde
con conducción. Aceptar solo tras nuevo run completo, nunca reclasificar V3.

Se detectaron valores de mind fuera del rango vanilla justo tras el spawn.
No acreditan respuesta: el verificador exige muestras en0..4 tras1s y alguna
en1..4. Fuente del rango: ZombieBase.Init, zombiebase.c:54. Tampoco se usará
un valor fuera de rango para iniciar/terminar fases del nuevo ensayo.
