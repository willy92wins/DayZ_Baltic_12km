# Navegación regional — 2026-09-29

Servidor de datos propio: run d413c757-9ae6-4aa2-8583-9f5b50bcf87c,
misión empty.BalticTrial, PBO53bf52b5. WRP compilado exacto:
d12ae049599b804c46df91a7bac46e8a530c7ade1ad149188524aed768479d5c.

NavMeshGenerator recibió parámetros y completó60025/60025 tiles en2m11s,
3701 full tiles,127625 polígonos,312165 vértices,44 offmesh links; filtrado de
islas completado. `navmesh-generation.txt` conserva el estado accesible y
`navmesh-generation.jpg` su captura. No confundir el dato de tamaño en memoria
del generador con el tamaño del archivo guardado.

Archivo guardado22:26:53:
`tb/regional_clearance_v1/navmesh/baltic_regional_v1.nm`,36317332 bytes,
SHA2560fc26281e3cf2908b9f95f937521d758808007a83f9f837e4e81a034a5b161fe.
El run de datos cerró normalmente; lease liberado y caja vacía comprobada.

Empaquetado sin Binarize: se reemplaza únicamente la navegación previa propia
2bb43e22...;6826 entradas restantes idénticas. Paquete sin material exterior
ebc60f4f..., variante con material exterior e370c74e.... Ambos conservan el WRP
de generación. Recibos completos copiados junto a este documento.

Carga cliente/servidor y caminos útiles de IA siguen siendo gates separados.
La generación no prueba acceso de IA a través del puente ni a todas las islas.

Actualización posterior: ebc60f4f cargó la nueva navegación en cliente y servidor;
no apareció Unable to load navmesh. Permanecen avisos de motor conocidos, no
declarar RPT limpio. `outside-client.RPT`/script y recibos de run conservan evidencia.
Consultas servidor903eee89 yfa1a7778: FindPath encuentra cruce oeste→este y retorno,
controles locales positivos y filtro sin polígonos negativo. Son consultas de
grafo, no actor caminando. Muestra61 puntos por sentido: el acceso oriental tiene
error máximo respecto SurfaceRoadY0.833077m. El verificador fijó0.8m y falla;
no ampliar el umbral a posteriori. SampleNavmeshPosition no documenta aquí una
garantía de distancia3D: no concluir que la API incumple maxDistance ni que un
infectado se atascará. La próxima aceptación necesita locomoción real de IA.
