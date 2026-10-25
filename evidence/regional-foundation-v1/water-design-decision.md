# Agua regional: decisión derivada de ensayos

Se mantienen materiales vanilla y superficies horizontales. No se adoptan los
modelos reconstruidos e inclinados del experimento `water_geometry_v1`. Para
ajustar orillas se añaden mallas horizontales de autoría procedural propia,
sin copiar geometría instalada; adopción regional condicionada a prueba WRP.

Hechos locales: el estanque horizontal dinámico y el persistido en WRP registran
agua a6m, respetan la huella y soportan una lancha propulsada sin cambios de pose.
El constructor `CreateStaticObjectUsingP3D` usa radianes en este entorno: .5729387
produce32.826969grados; .0099996667 produce una pendiente próxima al1%.
`SetOrientation` recibe grados. La orientación inclinada permite flotación y
propulsión, pero `SurfaceIsPond` devuelve false. No cumple el gate funcional
completo y no se incorpora a la base.

El modelo reconstruido plano reproduce el estanque vanilla. Alterar la Y de sus
vértices manteniendo el objeto horizontal no produjo una superficie hidráulica
inclinada: la consulta devolvió5.74001m en todo el eje muestreado. Esto demuestra
la respuesta de ese modelo concreto; no demuestra cómo está implementado todo
el motor. El objeto creado por la clase del experimento tiene además una ruta
de modelo con separadores duplicados: su resultado negativo se excluye de la
comparación geométrica. El objeto creado por ruta P3D directa sí cargó.

Implementación candidata: lagos horizontales separados por cota;
transiciones de río con piezas horizontales recortadas y superpuestas, limitando a
0.05m el salto entre piezas. Es una aproximación por escalones pequeños, no una
lámina matemática continua. Antes de adoptarla: clasificación positiva, muestra
de juntas y propulsión real a través del salto máximo. Cualquier salto mayor o
discontinuidad visual exige corregir la discretización. El modelo local de agua
no puede sustituirse por DSM: fondo, superficie y orilla se calculan por separado.

El inventario de unión completa describe **sistemas conectados**, no lagos de
cota única: Peipus, Narva y sus conexiones quedan en un mismo componente. Para
asignar cotas se separan polígonos lacustres y embalses de ríos/canales antes de
unir duplicados. No usar la mediana de todo el componente como cota común.

Fuentes leídas: `P:/scripts/3_game/global/game.c:679,1181–1187`,
`P:/dz/water/config.cpp:167–171`; ensayos locales `water-pose-v2.log`,
`slope-boat-v3.log`, `water-geometry-v1.log` y las dos pruebas de estanque plano.

## Contornos y tamaño de piezas

`water-shape-v1.json`:507 consultas, la forma L pequeña dejó seco el recorte.
Las variantes200m escalada y horneada mantuvieron alturas de agua correctas,
pero `SurfaceIsPond` solo cubrió parte de la huella. No se aisló la causa interna.
Misma forma dividida en48.02m a escala1 (`shape-boat-v3.json`):936 consultas de
agua,529 alrededor de un hueco seco,116 muestras de lancha;89.45m sin daño,
85 con propulsión. Las68 piezas son mallas propias, no modelos vanilla editados.
La primera prueba WRP falló en controles exteriores. Se aisló el desplazamiento
por bounding_center del ODOL: sumar ese centro a la pose estática manteniendo
las mismas mallas resolvió el fallo en `static-shape-v2.json`,89.41m de lancha
sin daño y todos los controles. Se adopta esta colocación para la integración
regional; editor nativo y visual regional siguen pendientes.

Unión al mar: controles de fondo-12m, mar0.850742m, estanques a0.45/0.75/1.25m.
La altura efectiva fue max(mar,estanque); los controles exteriores permanecieron
al nivel del mar. Esto permite una transición baja solapada en las desembocaduras;
no acredita todavía su anchura y profundidad regional.
