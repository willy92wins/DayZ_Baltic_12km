# Piloto acotado de curvas R1

Autoridad: plans/v30-rumbo-agua-1.0.md, paso 5; reviews/2026-10-04-council-rumbo-agua/ARBITRAJE.md:95–99. Base congelada: commit 90c4dfc, Floor095Preview, terreno 05a9d681 y agua JunctionR2. Los 14 modelos vanilla de la biblioteca coinciden por SHA256 con DZ.

Primero se prueban dos colocaciones offline, sin editar ni desplegar el terreno. A: escala uniforme 4, marcos de extremo reales, cadena de rectas y curvas de la biblioteca. B: mismo encadenado con escala variable dentro del rango actual 3,2–4. La búsqueda es finita y determinista; la pose inicial puede desplazarse lateralmente ±3,5 m. No se usan ángulos nominales del nombre: se leen los marcos medidos.

Criterios antes de motor:
- Área de doble lámina de piezas / unión de huellas ≤1 %, misma definición de compare_channel_joints_v30.layered.
- Cero huecos de área >1e-6 m² tanto en los triángulos nativos completamente mojados de las celdas retiradas como en el corredor local de 24 m, con las caras roadway y los planos realmente conservados.
- Se informa por separado el solape con los planos vecinos; no se oculta contando solo las piezas.
- Sin cambios de terreno, clases, niveles, reservas, plataformas ni fuera de R1.
- No introducir caras secas/inundación o pérdida de profundidad respecto al control actual en los puntos congelados de comprobación.

Controles negativos cerrados: retirar una pieza para exponer un hueco, duplicar una pieza para exceder el solape y alterar un hash de modelo. La comparación de métricas no acredita apariencia; si pasa se prepara paquete aislado, lectura en motor y lancha en ambos sentidos. Una corrección como máximo tras las dos variantes. Si no cumple, se registra el FAIL y se continúa con la representación plana prevista por el plan; no se abre una búsqueda indefinida.

R2/R3 y elección visual de arroyos son el siguiente cambio separable. Este piloto no los modifica ni cierra sus pendientes. Ningún PASS offline promueve la base 1.0.

## Alternativa plana autorizada, 08-10

Curvas agotadas: A/B/A1 rechazadas. Guillermo autoriza el reperfilado local de R1 en Narva, conservando puentes, carreteras y fondo acordado (`narva-decision.json`). Se restauran los planos de los tres tramos y se regeneran grupos completos de tesela/nivel, evitando apilar rellenos sobre los estanques recortados.

Perfil local con el método existente: banda y sigma de 18 m, transición quintica entre 12 y 24 m del dominio retirado, metadatos exactos. Fijos: reserva natural, reserva vial, plataformas y vértices de las caras certificadas de los corredores de 24 m. Fondo existente >=1 m nunca baja de 1 m; excepciones bajas previas no se extienden. El permiso de Narva solo se usa en este dominio.

Salida offline: cero huecos en las caras mojadas y en la cobertura esperada de los planos; redundancia de área <=1 % incluyendo estanques vecinos; cero nueva inundación de vértices de tierra; ningún talud mixto >35 grados nuevo o agravado; 19 corredores con >=0,95 m; carreteras PASS. Se miden por separado los cambios de línea de agua en caras mixtas, que son el objeto del perfil autorizado. El test anterior de conservar cada signo en una rejilla de 3 m no sustituye este criterio.

Presupuesto de esta alternativa: un perfil inicial y una reparación guiada por un fallo concreto antes de revisar el diseño; sin barrido de parámetros. Si pasa, paquete aislado con modelos compilados comprobados, lectura de suelo/agua y lancha en ambos sentidos de los tramos afectados; después vistas con textura cargada. Si falla una puerta no se promueve.

Revisión técnica tras el fallo de R3: el perfil inicial pasa R1/R2 y deja 13 esquinas someras en R3 porque se heredó de la pasada de relieve una congelación de toda la reserva. El intento acotado de ajustar solo el lecho agrava taludes y se rechaza. La continuación cambia esa estrategia, sin otro barrido: resolver simultáneamente el lecho y su transición, minimizando la bajada y preservando los límites de pendiente. La petición viva incluye orillas y cauces; P13 pide conservar y contrastar el perímetro de la reserva, no congela sus alturas globalmente. Se ha contrastado la máscara y se limita esta excepción al cauce R3 existente y su orilla inmediata: 60 vértices de agua y 33 de tierra, como máximo 26,8 y 19,4 cm respectivamente. El perímetro, clases, niveles y restantes alturas de la reserva quedan iguales; carreteras, plataformas y corredores siguen fijos. Se anunció este ajuste antes de incorporarlo a la preview. `r3-transition-proposal.json` y `flat-verification-r2.json` contienen la solución y su consumidor independiente. Es una decisión de implementación dentro del encargo, no una nueva aceptación visual de Guillermo.

El verificador informa una diferencia de 0,0000086 grados causada por float32 en una cara ya >35 grados; usa la tolerancia de 0,0001 grados de `discard_steeper_land_faces`, conserva el resultado estricto previo y rechaza diferencias superiores. El negativo de calado muta y remuestrea un triángulo real. La lancha en ambos sentidos aplica al navegable R1; R2/R3 son arroyos y requieren lectura y comparación visual a altura de jugador.
