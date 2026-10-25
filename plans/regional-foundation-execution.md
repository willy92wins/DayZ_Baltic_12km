# Base regional: agua, rasantes y navegación

Petición viva: continuar autónomamente hasta completar la base de terreno y
navmesh. Parte de `4ff154b`, candidato 0.3; conserva base 0.2 y fuentes originales.
Asiento de esta sesión: executor e integrador. P2/P3/P5/P9/P10/P11/P12/P13.

## Orden y aceptación

1. Verificar agua elevada vanilla con un ensayo aislado: objeto dinámico primero,
   después objeto persistido en WRP. Medir SurfaceY, SurfaceIsPond, GetWaterDepth
   a distintas Y; no inferir superficie del agua sumando variables sin contrastar
   su semántica. Fondo separado y lancha propulsada sin cambios de pose por frame.
2. Inventario regional único de cuerpos y rutas; unir relaciones anidadas,
   conservar islas, delta y reserva. Cotar por sistema con transiciones navegables.
   DSM representa superficie, no fondo. Diseñar corredores alrededor de las islas
   cuando una ampliación centrada las invade. Todo cambio tiene máscara y delta.
3. Seleccionar conexiones principales trazables de OSM. Preparar corredores de
   terreno con perfil longitudinal continuo, caída transversal controlada y
   acuerdos suaves. No rellenar cauces en los cruces: reservar vanos y accesos.
   Piezas físicas, ciudades, vegetación y decoración permanecen para el mapeado.
4. Importar candidato regional en copia TB; Rebuild del heightfield, guardar,
   reabrir, exportar y comparar todos los vértices/objetos. Conservar SAT1M y
   materiales aceptados. No Generate Layers como atajo para reconstruir alturas.
5. Generar navmesh nueva para ese WRP, empaquetar y vincular por SHA. Consultas
   y rutas en los sectores, locomoción física representativa, agua y cruces.
6. Carga cliente/servidor, inspecciones regionales y coste descriptivo comparable.
   Archivar fuentes/editable/paquete/misión limpia y registrar límites reales.
   Base sin mapeado no prueba capacidad de 80–100 jugadores ni CE/vegetación.

## Ensayo inicial de agua elevada

Fuente instalada leída: `P:/dz/water/config.cpp:167–171`, clase
`StaticObj_water_pond_50x50m`. ODOL pond_50x50 y lake_50x50: huella 52×52m,
Geometry vacío con `class=pond`, Roadway `water_ext.paa`; river_24_24:24×24m
con ligera pendiente visual/Roadway. Lectura mediante odol_reader instalado.
Estas propiedades no acreditan todavía flotación ni registro del agua.

Crear misión temporal separada y colocar una plataforma de agua a Y=6m sobre
Peipus, por encima del mar y del terreno. Control fuera de la plataforma y
mediciones antes/después; después lancha dentro, propulsión y cruce de juntas.
La prueba dinámica negativa no descarta el objeto estático en WRP: distinguir
ambos mecanismos y conservar el resultado. No modificar el paquete entregable
por un resultado meramente visual o por existencia del objeto.

PASS: agua elevada detectada y altura coherente en múltiples Y, interior y
juntas; control exterior diferente; lancha asentada, propulsada, sin daño ni
teletransporte. FAIL: agua ausente, plano sólido, caída al mar, fugas fuera de
huella, saltos o discontinuidad. INCONCLUSO: datos incompletos o consumidor no
ejecutado. Ante fallo aislar el mecanismo; no variar cotas al azar.

Computer Use: preparación y pruebas sin control; bloques breves anunciados
solo para editor/generador, reiniciar su sesión al terminar cada bloque.

## Corrección de islas y pruebas regionales, continuación 30-09

El consumidor ampliado detectó que respetar huecos en los modelos de agua no
garantizaba tierra emergida: 200/283 representantes protegidos del combinado v4
quedaban bajo su objetivo local de resguardo. El candidato v9 añade soporte de
islas y conserva todos los vértices de rasante; ASC SHA256
`335554a6ea06f8546eeac5444aec7597eaf45df18be0c69b0baab48a573947b2`.

La construcción inicial elevaba triángulos completos hasta agua+0.35m. Eso
reducía el lago217 de901 a189 puntos mojados sobre965 interiores. Se rechazó
como solución final. En47 vértices próximos a ese lago se sustituye el borde
artificial elevado por condiciones sobre los polígonos realmente interceptados:
orilla a cota de agua o superior; interior de isla a una celda del borde con
resguardo0.35m, igual que los representantes de las283 islas. No cambia ningún
polígono de agua, el recorte ni las rasantes. La malla6m sigue aproximando orillas;
v9 recupera785/965 puntos mojados allí, no reproduce literalmente cada metro.
Los fallos del problema con borde uniformemente elevado se conservan.

Verificación independiente mediante ecuaciones de plano de cada triángulo:
`protected-island-native-plane-v9.json`,283 islas, sin invasión por debajo de la
cota local salvo redondeo float32 de1.11e-6m.239 lagos con cinco puntos interiores
mojados cada uno;79420 muestras de corredores con profundidad>=3m; geometría y
rasantes pasan sus gates previos. Son resultados offline, no aceptación nativa.

La misión de consumo regional congela81212 consultas agua/tierra,314 consultas
de navmesh y15 rutas antes del motor. V2 compiló pero terminó incompleta por
campos vacíos que string.Split omite; se conserva FAIL. V3 usa un cero explícito
en ese campo de las filas secas. Comprobar primero el mapa anterior como negativo,
después el nuevo WRP/NM. No desplazar consultas para esconder fallos.

## Ajuste técnico del agua, 30-09

Los planos rectangulares vanilla invaden zonas contiguas cuando las orillas son
irregulares. El ensayo `water-shape-v1.json` confirma una huella cóncava propia
con el material vanilla, incluidos controles secos. Se preparan superficies
horizontales recortadas, con islas, horneadas a escala1 y sin copiar mallas ODOL.
Son infraestructura de agua, anterior al mapeado de edificios y vegetación.
Adopción condicionada a clasificación, flotación, juntas y prueba estática WRP.
Las variantes de200m, escalada4 y horneada a escala1, detectaron que SurfaceIsPond
y la altura del agua no coinciden en todo el modelo. No queda aislada una causa
de escalado. La división de la misma forma en piezas48.02m, escala1, sí pasó:
936 mediciones de agua,529 alrededor de un hueco seco,116 de lancha,89.45m sin
daño. Adoptar ese tamaño validado para la siguiente prueba estática; no inferir
un límite universal del motor ni aumentar piezas para ahorrar objetos sin prueba.
