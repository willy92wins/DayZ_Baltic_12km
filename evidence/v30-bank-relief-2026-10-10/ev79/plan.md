# EV79 — corregir las crestas secas bloqueadas de Narva

Cambio concreto del plan EV78 tras consumidor FAIL, sin incorporar su terreno: mantener fuente EV71/72 b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36 y concentrar la intervención en Narva. La petición viva autoriza ajustar sus orillas, preservando puentes, carreteras y fondo. `luna-geometry/mask-scope-audit.py/json` reconstruye las uniones antiguas bit a bit: 58/59 diedros fuertes totalmente secos están bajo la máscara genérica Narva; 56 no tienen otra protección y dos tocan controles temporales. No son soportes mojados ni ingeniería. El diedro restante pertenece al borde del mapa.

## Selección y límites fijados antes de calcular

Dominio = suelo clase0 a <=96 m de cls3/5/6 dentro del radio620 m del puente (2417.1428225906,6889.8850822322), o t.narva. Reconstruir las protecciones por sus componentes; retirar de esta selección SOLO `narva_old_guard` y `t.narva`. Mantener corridor24, summits, controles temporales, margen66 m/11 vértices, cls!=0, water, playa/mar, grandes lagos, soporte exacto de las caras realmente mojadas P/F/mar máximo0.85 y halo3x3 reserva/plataforma. No restar una máscara a una unión porque borraría solapes protegidos.

Mismo método geométrico EV78, K nativo con regularización1/16, cap2 m quintic en18 m y60 barridos/600s. Límite inferior por vértice = max(fuente-cap,min(fuente,1.8),min(fuente,max(P,F,0.85) incidente+1e-4)). Caras con pendiente <=max(35°,fuente), tolerancia de consumidor1e-4 grados ya fijada. Una ejecución; no barrido de parámetros. EV78 queda rechazado como evidencia y su auditoría compilada se interrumpe porque ya no puede aceptarse.

## Aceptación independiente

Conservar todos los gates EV78, incluido p99 banco/interior no peor, cero nuevas aristas>30°, máximo de cada sector modificado no peor, energía angular incidente al menos5% menor. Reconstruir la selección sin importar autoría. Añadir descenso del máximo y de cantidad>30 en el subconjunto seco de Narva, y tabla antes/después de los anclajes localizados. Controles positivos y negativos pasan por el consumidor real. Si falla, no empaquetar ni cambiar tolerancias.

La cota húmeda, calado, fondo, objetos y P/F permanecen exactos; esto no elimina las 4768 aristas mixtas húmedo/seco ni demuestra el shader. Auditar exposición de los modelos compilados solo en caras del terreno cambiadas: fuera de ellas la identidad de altura y objetos prueba exposición idéntica. Comprobar la selección de cara mediante todos los vértices, y controles de clipping. Después comparar entradas del satélite a1 m; regenerar teselas afectadas si cambia banda de orilla. Solo empaquetar tras PASS y verificar el WRP compilado/PBO desplegado. Validación de aspecto en motor sigue separada.

No promoción EV68, sin push, sin aceptación de toda base1.0. Entregar candidato reversible, evidencia del rechazo anterior y pendientes vivos.
