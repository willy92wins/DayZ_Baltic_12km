# EV40 — liberar apoyos secos de orilla, niveles conservados

Cambio de mecanismo explícito tras EV19/39: la banda terrestre exterior no contiene la cresta completa. EV39 reduce la curvatura solo3,98%/2,43%; no se promueve ni se prolonga su solver. La máscara heredada de soporte de agua no es una prohibición del usuario. Este lote permite bajar sus vértices SECOS, siguiendo la petición de suavizar orillas y terraplenes, y conserva todos los mojados.

PLAN: rumbo §3 niveles reservados, §4 línea de agua medida, §7 física/visual. Niveles y fondos exactos. Carreteras, plataformas, corredores de navegación y periferia intactos. Celdas con distintos planos físicos incidentes protegidas para no cambiar contactos entre masas.

Una solución,60barridos/600s, una reparación de implementación. Mismo método de caras nativas EV25, descenso≤1,5m. Suelo exterior EV39; los apoyos secos pueden bajar hasta max(1,8m, todos los planos P/F incidentes+0,0501m), sin rebajar una excepción existente. Signos húmedo/seco de cada vértice/triángulo exactos. No se cambia clase, nivel ni lecho. Desplazamiento máximo de cruces≤4,1m, mismo límite EV16. Cada banco: curvatura≥10% menor, p90cresta no mayor, RMSde quiebros nativos menor. Contorno local medido para evitar dientes nuevos. Ningún signo/topología podrá esconderse por reclasificación.

Después de fuente PASS: comprobar cobertura compilada de todas las celdas alteradas y completar piezas mínimas solo si faltan, siguiendo EV16; satélite/máscara afectados recalculados; terreno/objetos reales leídos en motor. No aceptación de niveles nuevos ni de base completa. FAIL no admite otra variación de radio/peso.
