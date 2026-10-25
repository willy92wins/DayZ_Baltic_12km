# Margen local frente al oleaje en trece puntos de orilla

Continuación de P2/P9/P14 y de `water-ground-rebuild-v1.md`, dentro del alcance
autorizado de terminar terreno y navegación antes del mapeado.

La serie del motor `evidence/v30-water-temporal-2026-10-03/runtime-v2-result.json`
registra 151 muestras durante más de 301 segundos en los mismos trece fallos
congelados: la pieza pond existe en todas las muestras, pero la profundidad cambia
de signo. Después de consultar presencia, el plano sin ola es constante. La
superficie con ola explica la profundidad; consultar el plano antes de presencia
puede devolver el del mar. No usar esa lectura anterior para cambiar niveles.

[DESIGN] Rebajar exclusivamente vértices de agua alrededor de esos puntos,
con núcleo de 9 m y transición suave hasta 24 m. Objetivo local: 0,201 m bajo
el plano nominal en los trece puntos, frente a oscilaciones observadas próximas
a 0,13 m. Límite de rebaje: 0,45 m; fondo alterado nunca más profundo de 1,20 m
bajo el plano mínimo de sus piezas. No elevar agua, modificar XY ni tocar tierra
seca, playas, plataformas, canales navegables protegidos o reserva. En Narva solo
las cuatro huellas de laguna ya autorizadas permiten la excepción al círculo.
Estos márgenes son un ajuste local, no una envolvente universal del agua DayZ.

Fuente única: NPZ40d8cfd9 y referencia temporal V2 congelada. Mantener intactos
metadatos, piezas, las referencias previas y sus FAIL. Una sola construcción;
comprobar el bloque completo después: delta acotado, protecciones, caras nativas
sin nuevos taludes mayores de35°, cobertura vial histórica y lectura temporal
en motor. Cambios en suelo exigen nueva navmesh antes de aceptar el paquete.

La comprobación espacial final incluye las orillas vecinas y las muestras secas
congeladas. La tierra seca exacta y el menor lecho no prueban por sí solos que el
contorno visual sea satisfactorio. Se mantiene esa revisión visual pendiente.

La primera construcción02d997b4 rebajó127vértices, pero su revisión falló:
siete muestras secas perdían su resguardo50mm y una cara previamente>35°
empeoraba0,07°. No desplegada; archivos y FAIL conservados en `v30-wave-margin`.
Corrección de diseño: proyectar el mismo campo radial sobre restricciones
explícitas de esas orillas secas y de cada cara nativa afectada. Objetivo deseado
201mm; mínimo181mm, todavía por encima del descenso de ola observado~130mm
y de la consulta a10mm sobre el lecho. Mantener intactos los criterios runtime
anteriores y comprobar el mínimo real después en el motor. No se amplía el área
editable ni el rebaje máximo. Una resolución SLSQP de hasta250iteraciones,
sin bucle de reintentos ni cambios automáticos de umbrales.

## Resultado del bloque

La resolución inicial terminó con `Positive directional derivative for linesearch`,
sin emitir candidato. Un diagnóstico lineal separado demostró que las mismas
restricciones de puntos permiten un mínimo común de 0,1936986 m: no era prueba
de incompatibilidad geométrica. Se retiraron desigualdades constantes de caras
sin vértices editables y se suministró un punto inicial factible, sin cambiar
límites, ámbito ni criterios. La nueva resolución convergió.

`E:/DayZ-Baltic-Build/v30-wave-margin-constrained/terrain_v30.npz`,
SHA `d5dadae846bcc60ecb4e03afbdb8db2e833ca209a54a3228a376682a51482f65`,
modifica126vértices, rebaje máximo0,381866m. `review.json`:
**PASS_LOCAL_WAVE_MARGIN_GEOMETRY**;463muestras secas,23canales exactos,
sin taludes>35° nuevos o empeorados;76.536estaciones viales/100cadenasPASS.
ASC `ed3b12f27d2a45426f899632f45b7714e098c8152eea61bc03a80c82448a1fff`.
No importado, empaquetado ni probado en motor; requiere navmesh actualizada.
El diagnóstico lineal y el primer FAIL se conservan en `v30-wave-margin/`.
