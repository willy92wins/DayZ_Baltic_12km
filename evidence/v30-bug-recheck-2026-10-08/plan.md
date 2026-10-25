# Revisión de los veinte fallos registrados

Encargo vivo: comprobar todos los fallos reportados y corregir los que sigan presentes, además del smoothing ya preparado. Base: commit b8cffc8 y NPZ combinado a292b6c3; no equivale a aceptación final.

1. Trazar BALTIC-001..020 a su consumidor y versión. Volver a medir las invariantes geométricas sobre la preview combinada; conservar los FAIL históricos y distinguir cambio autorizado de contrato de regresión.
2. Separar defectos del mapa de defectos del diagnóstico. Las esquinas de planos sustituidos se contrastan con las piezas realmente empaquetadas. El índice de teselas es una heurística de color, no una observación de carga de texturas.
3. Reparar los defectos reproducidos sin cambiar recorte, niveles aprobados, reserva ni requisitos de navegación. Para cada reparación: una variante y una corrección como máximo; si aparece incompatibilidad de requisitos, documentar su punto concreto en vez de relajar la puerta.
4. Pruebas: consumidor independiente del productor, control positivo operativo y negativo que reproduzca el fallo, hashes de los artefactos, y motor cuando el resultado depende del motor. Las pruebas de coche/IA/lancha de otra geometría no cierran la geometría actual por herencia.
5. Actualizar bugs.md e informe por ID. Terrain Builder y navmesh final dependen de geometría aceptada; la revisión independiente y las decisiones de niveles pendientes conservan su estado.

Fuentes: product-spec.md P9/P10/P14; plans/v30-rumbo-agua-1.0.md pasos 4, 7–9 y revisión del contrato de navegación del 07-10; bugs.md; evidence/v30-bounded-integration-2026-10-08.

## Reparación local de oleaje

La repetición actual reproduce fondo expuesto en los puntos 765 y 1176 con pieza presente. Propuesta: rebajar las orillas secas que participan en sus triángulos nativos, con transición coseno de 12 m, máximo 0,25 m y margen nominal objetivo 0,201 m. Conserva todos los vértices de agua y sus niveles; tierra editada por encima de 1,4001 m y de cada plano adyacente +0,0501 m. Reserva, plataformas y Narva permanecen fijos. Una propuesta y una corrección como máximo.

Aceptación: consumidor triangular independiente, metadatos exactos, carreteras PASS, ninguna cara mixta nueva/empeorada por encima de 35 grados, desplazamiento local del borde nominal inferior a 4 m. El paquete debe diferir solo en el WRP. Repetir 302 muestras en calma/tormenta sobre los mismos 17 puntos: los dos fallos reproducidos deben mantener pieza presente y profundidad positiva en todas; los puntos que ya son tierra no deben pasar a agua por esta corrección. No cierra visualmente todas las orillas del mapa.
