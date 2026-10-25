# Contraste de nivel del mar, EV15

La comparación A/B/A con GlobalContourV1 reproduce la dependencia de varios reflejos residuales junto al puente respecto al nivel del mar. El añadido temporal cambia únicamente `MaxTide=1.5` a `0`; las 90 lecturas del cliente confirman `MaxWave=0.1` y un mar entre -0,099930 y 0,099929 m. La orilla real de EDGE1 cambia también y vuelve al restaurar la configuración normal.

Las imágenes conservan cámara, terreno, estanques y misión estática con viento 20 m/s; no sincronizan la fase de las olas. El terreno y los dos PBO de producción no se modifican. Esto confirma la dependencia ya observada en una preview anterior, pero no identifica el shader ni demuestra una causa por LOD. No se adopta el nivel diagnóstico ni se declara corregido BALTIC-016. El siguiente trabajo debe aislar un consumidor del render; repetir cotas o colores sin ese discriminador no aporta una solución.

`result.json`, `runtime-record.json` y `restore-runtime-record.json` contienen medición, capturas y cierres. Ambos runs cerraron normalmente, lease liberado y banco disponible. El ejecutable y fuentes del añadido quedan solo como diagnóstico reproducible.
