# Adjudicación del council

Las revisiones son propuestas independientes, no instrucciones ni prueba de que todos sus hallazgos sean ciertos. Los informes originales se conservan por familia. Fuentes completas, recibos, probes y fallos de transporte: `E:/DayZ-Baltic-Build/qc-council-20261024`.

| Idea / hallazgo | Decisión y evidencia |
|---|---|
| PASS sin muestras, NaN en altura y expectativa desconocida | Reproducidos en baseline-repros.json. Corregidos y cubiertos con positivos y negativos. No aceptar columnas/superficies desconocidas. |
| Cobertura recalculada con la misma máscara | Corregido: digest EV112 fijado 40517384…; cambiar cadena o selección rechaza. Se publican29789 estaciones excluidas, no PASS. |
| Cruces exactos de aristas viales | Implementado consumidor independiente: R tiene15 fallos, S3 cero. Pendiente por gradiente planar evita cancelación numérica en intervalos diminutos. Pruebas silla/diagonal/rampa/cresta entre muestras. |
| Simetría forzada de sección transversal | Rechazada como requisito: P11 exige rango total3cm. El reparador usa todas las diferencias de pares, sin exigir un centro artificial. S1/S2 rechazados; S3 es el candidato seleccionado. |
| Multi-escala y prominencia | Implementadas métricas6/12/24/48m, planos/rampas como negativos de falsa alarma y escalón/pico como positivos de señal. Prominencia nativa separada. Sin límite estético nuevo. |
| Desaparición de defectos protegidos por exclusión | Inventarios OPEN por reserva, plataforma, presa, kit, puentes, piloto, charcas y disco015-45. No se declaran aceptados. |
| Agua en planta que está enterrada | Consumidor MLOD de centro/bed/terreno implementado. Verifica todos los centros húmedos entre los extremos originales, no solo unos puntos cómodos. S3 pasa ambos pilotos. No prueba todos los puntos continuos ni receptores. |
| Extremos controlados solo por author-report | Cerrado con reconstrucción independiente desde EV107 y sites-d fijados por SHA. Mutante que acorta extremos falla. No usar extremos de lattice como sustituto del cauce original. |
| Aprons secos tratados como fallos de agua | Rechazado:6m fuera de los extremos originales son una transición seca deliberada. Se inventarían, pero no se les impone agua. El primer diagnóstico amplio se conserva como ensayo no válido para el tramo requerido. |
| Cierre de colisión inferido del signo de volumen | Corregido: aristas apareadas y orientadas, degenerados/duplicados, conexión de caras y volumen no nulo.33060 componentes MLOD pasan; lámina abierta y cara invertida no. |
| Comparación binaria unidireccional | Corregido para visual/Geometry/Roadway, más recuento de caras y componentes contra MLOD. Verificado sobre el PBO realmente desplegado742fcc…, no solo el recompilado9ebcd…. |
| Angulosidad/anchura del cauce | Diagnóstico del piloto y49 sitios construidos, desde centros de modelos colocados. No adoptar15grados/m,6mHausdorff ni otros cortes sin referente. No aceptar globalmente el río por continuidad2D. |
| Dos extremos por cuerpo ocultan todas las ramas | Vacío real de cobertura global, no falso PASS del inventario que ya se declara no aceptación. Receptores y ramas quedan OPEN; ni el diámetro BFS ni un esqueleto sin calibrar prueban todas las conexiones. No cambiar silenciosamente la hidrografía. |
| Matrices forestales, orientación, escala y NaN | Reutilizados límites G5 de Livonia:1e-6 para ortogonalidad/escala, determinante positivo y cuantiles por modelo. R/S3: cero defectos medidos de esos tipos en2560922 registros. |
| Soporte forestal no finito | Confirmado hueco del consumidor: disc_min devuelve+Inf si ningún triángulo cubre el disco; el gap−Inf pasaba. Ahora falla dentro del dominio o queda INCONCLUSO si cruza el borde.3727 discos pendientes, mismos IDs en R/S3; no eliminación ni clamp inventado. |
| Copa completa en toda exclusión | No sustituir la base/tronco G1/G4 por copa sin criterio: puede prohibir copas legítimas sobre agua/camino. La geometría vial completa ya está en G1. Revisión visual/densidad por bioma siguen separadas. |
| Faltan protecciones de R por no estar en SOURCE-PACKET | Refutado por stage_visual_road y continuation-D: la omisión del paquete leído no demuestra ausencia en el pipeline. Se reejecutan las protecciones para S3. |
| Congelar platform en la reparación vial | Refutado: build_v30:386-407 define precisamente la plataforma de carretera. Es fija en la tarea de ríos, reparable en P11; no es una plataforma de edificio.51 vértices de S3 corresponden a esa plataforma. |
| Hacer secos los controles expect=ground | Rechazado: son controles de cota, incluidos apoyos y relieve, sin afirmación de agua. Enum explícito y test que conserva esta semántica. |
| Sonda Q786 podría aceptar R1037 | Refutado: recuento e IDs exactos lo rechazan. Sigue siendo útil vincular log/run/artefacto en el cierre de motor; Q no se atribuye a R/S3. |
| Exigir que impacten todos los rayos de calibración vanilla | Rechazado: misión recorre rejilla32×32m; el positivo real tiene5 impactos sobre el modelo y284 misses exteriores. Una fracción arbitraria invalidaría el control. Es calibración de margen, no prueba completa de colisión del modelo. |
| Diferencias contra Chernarus implican FPS | Rechazado. PresentMon permanece DESCRIPTIVE_ONLY; A/B y carga multijugador requieren motor, mismo hardware/ajustes/escenas. Auditoría estática no demuestra rendimiento. |
| Restar una firma de rejilla al relieve | No adoptado como corrección automática: carece de definición/calibración que pruebe que no borra defectos reales. Comparación descriptiva vanilla y revisión visual pendientes. |

## Revisión de implementación

Fable5.1 revisó independientemente los consumidores y el candidato: **SOUND-with-fixes**. Se cerraron cobertura fijada, test de diagonal no paralelo, silla que discrimina triangulación, grado/chord y coordenadas, comparación de cobertura entre consumidores, extremos EV107, componentes contra MLOD, pliegues de agua y validación de bed para colisión. El informe de bosque ya fue corregido para persistir la incertidumbre del borde. No se repitió una ronda solo para obtener otra aprobación.

Las sugerencias de congelar la plataforma vial y forzar todos los rayos de calibración se rechazaron por los mecanismos de las fuentes indicadas. Orden de LOD fijo es el esquema de este autor de4LOD, no una API genérica ni un PASS si falta uno. No se afirma motor, navegación, calidad visual ni optimización final.
