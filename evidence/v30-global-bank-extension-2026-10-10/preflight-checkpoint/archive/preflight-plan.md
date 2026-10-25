# EV93 preflight por ventana — sin nueva autoría

Root aprueba esta preparación readonly dentro del plan EV93. No habrá llamada a solver ni cambio de alturas.

Se reutiliza un módulo aislado del preflight EV90 hash-pinned, sustituyendo explícitamente solo WINDOW=(r−8,r+9,c−8,c+9), CORE=(r−6,r+7,c−6,c+7) y FOCUS=(r,c) durante cada consulta y restaurando los tres atributos en finally. Sus funciones de cotas, cruces, P9, F parcial y entierro bajo envolvente inferior mantienen fórmulas y tolerancias. El lector de caras se adaptará al índice EV93 verificado; se comparará con el escaneo directo antes de aplicarlo a la cola. El índice conserva las caras positivas de área pequeña, pues EV90 usa área>0, mientras EV87 usa área>1e−12.

Para el piloto (840,370), exigir igualdad de celdas por clase, dominio, cotas float32, cruces, guard, testigos y certificados de entierro con el preflight congelado. Para otras ventanas, conservar los estados de no factibilidad/indeterminación y las causas; no congelar de forma indiscriminada todo campo P/F ausente para convertir un inconcluso en PASS. Las caras desconocidas no enterradas rechazan la ventana; no se resuelve alterando su agua o las protecciones. Los casos sin variables o intervalos vacíos se clasifican sin ejecutar optimizador.

El guard se reconstruye por incidencia completa con `author_ev91.collar_guard`; D8 con `author_ev91.descent_constraints`, ambos revisados y fijados por SHA. Las cotas del guard quedan exactamente en B. La prueba de caja no acredita factibilidad acoplada ni ganancia de suavizado. Los 85 nodos/43guard del piloto no se imponen globalmente.

Ejecutar una pasada sobre los 703 centros de la primera capa, sin repetir parámetros ni reemplazar centros rechazados. Ledger JSONL incremental y resumen final con número procesado/pendiente; presupuesto inicial de cómputo 10 minutos. Si expira, conservar lo procesado y reanudar desde el índice siguiente con los mismos hashes, sin repetir ventanas. Esta pasada solo prepara dominios; ninguna cantidad de READY equivale a corrección geométrica, agua resuelta o aceptación del mapa.
