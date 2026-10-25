# EV112 — contacto RV en vértices del piloto T

Continuación autorizada de la corrección de ríos y terreno. Unidad acotada a
los cinco modelos que fallan en la sonda T; no cambia criterios de aceptación.

## Evidencia

El run `d40948fd-5a1b-47a1-8778-8c64a84aa163` completó 2823 puntos. Cinco
fallan en RV Geometry, aunque Bullet, agua, terreno y Roadway responden.
La calibración vanilla repetida conserva el margen de 0,039991446 m.
En el run `e989a3c3-ab4a-4e8c-bce6-02182f80f9a8`, los cinco puntos fallan
10 veces cada uno en la coordenada exacta y pasan las 48 posiciones próximas
de cada rejilla (desplazamientos de 1, 5 y 20 mm). Coinciden con vértices MLOD
a menos de 0,5 micras. Logs y diagnóstico en
`E:/DayZ-Baltic-Build/shape-repair-20261025/runtime-t-20261025`.

[EXACT] `P:/scripts/3_Game/global/dayzphysics.c:199` declara RaycastRV con
`ObjIntersectGeom`, radio 0 y salida de contacto. La documentación de la firma
identifica Geom como Geometry. [HIPÓTESIS] Precisión de intersección en aristas
compartidas; no se conoce todavía el mecanismo interno del motor.

## Candidato y validación

[DESIGN] Crear la suma de Minkowski de cada componente convexo de esos cinco
modelos con un cuadrado horizontal de semilado 1/512 m. Rehacer su envolvente
convexa, conservar componentes y masa por componente, recalcular normales.
La expansión simétrica conserva el centro del bounding box y las alturas de
sus extremos; usa la rejilla exacta de los modelos existentes. Desplazamiento
horizontal máximo 2,763 mm. El interior original queda contenido. Esta variante
evita desplazar el centro del modelo, riesgo de una expansión radial arbitraria.

Conservar byte a byte los LOD visual, Memory y Roadway, los otros 57 modelos,
configuración, WRP, terreno, agua y poses. No desplazar muestras ni ampliar
tolerancias. Candidato separado; T se conserva.

Puertas: cierre, orientación y convexidad del MLOD guardado; cobertura completa
del lecho por la unión superior de colisión con los límites existentes de ±2 cm
verticales y 1 cm horizontales; conteo de componentes idéntico y coste en caras
registrado. Verificar ODOL y poses contra el WRP existente después de compilar.
Repetir los 2823 controles congelados y las 300 muestras diagnósticas. Los controles
externos al lecho de la rejilla son diagnóstico, no agua/colisión esperada inventada.

Revisión independiente con Fable 5.1 según el plan principal. Hasta tres candidatos
con mecanismo o discriminador concreto; dos sin progreso cambian el diagnóstico.
No cerrar contacto de cliente, conducción, rendimiento, navegación o aceptación
visual por aprobar rayos de servidor. La navmesh v6 rechazada por el motor que
espera v9 sigue siendo una incidencia separada.

## Resultado de U1 y reducción U2

U1 pasa los 2823 controles sin modificar el consumidor y los 300 rayos de la
rejilla diagnóstica (RV y Bullet identifican el modelo). Fable 5.1 revisó el
operador y pidió reducir el coste y clasificar contactos contra el ODOL.
La nueva herramienta mide distancias en las coordenadas float32 y la pose
existente: uno de cinco contactos está a una ULP o más de una arista de la
cara superior; cuatro quedan por debajo. El motor pasa los cinco. Este
resultado no establece el algoritmo interno ni una causa raíz concluyente.

U2 conserva el operador de U1 solo en componentes cuya huella está a 1/512 m
o menos de los contactos fallidos, más los que contienen extremos X/Z del
modelo. Estos últimos conservan la expansión simétrica del bbox y las poses
existentes. Son 46 componentes de 2035 en cinco modelos. Los restantes
componentes conservan coordenadas exactas; masa por componente comprobada
después de guardar. Aumento de caras global: 317708→318910 (+0,3783 %), frente
a 367014 de U1 (+15,52 %). El PBO ocupa 8341171 bytes frente a 8325853 de T.
Este coste geométrico no es una medición de FPS.

La cobertura completa del MLOD, los 62 ODOL, las 62 poses y las juntas de agua
pasan sus verificadores existentes. U2 repitió la misma sonda (2823/2823) y
rejilla (300/300 RV y Bullet con modelo), ambas sin fallos. Queda preparado
para la revisión personal. Suite completa:132 PASS, cero errores/skips.
La corrección local
de contactos no sustituye el resto del plan de ríos y relieve.
