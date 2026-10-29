## Dictamen: **SOUND-with-fixes — CONVERGE**

Modelo accesible: `muse-wonder-1.0`. La identidad efectivamente servida debe registrarse desde `run.usage`, no desde esta autodeclaración.

La partición conjunta de nueve slots es el diseño correcto: no puede reconstruirse multiplicando marginales de terreno y agua. El ejemplo está bien derivado: para `B=1`, `H=W=x/6`, el corte `x=6` divide el área 72 en 54/18; resulta `ABOVE + SELECTED_WATER_ONLY_BELOW = 54` y `BELOW + SELECTED_WATER_AT_OR_ABOVE = 18`, con los demás slots en cero. Los caps por cara acumulados, la fase de cabeceras anterior al código, la distinción `SOURCE_GRID_NW_SE_ASSUMPTION` frente a terreno compilado y la no equivalencia con exposición real están correctamente planteados.

### Hallazgos que deben cerrarse en el contrato

1. **La orientación fila/Z y la diagonal no quedan fijadas por `H=x/6`.**  
   Anclas: [pilot_surface_refinement_ev112.py](/E:/DayZ-Baltic-Build/shape-repair-20261025/council-expanded-20261029/tools/quality/pilot_surface_refinement_ev112.py:7) define `OFF/TRI`; las líneas 70-80 fijan filas mediante `top=(n-1)*6` y la diagonal NW-SE. El fixture propuesto es insensible a una inversión de filas y apenas discrimina la diagonal contraria.  
   **Consecuencia:** productor y consumidor podrían compartir la misma interpretación transpuesta y coincidir en un resultado fuente falso.  
   **Mínimo cambio:** congelar antes del código al menos un fixture literal asimétrico en X/Z, con resultado distinto bajo inversión de filas, y otro de una celda cuyos cuatro vértices produzcan particiones distintas con diagonal NW-SE y NE-SW.

2. **La independencia del consumidor queda debilitada si comparte el array `heights` ya decodificado.**  
   Ancla: el plan declara compartidos “I/O, NumPy/zlib y Budget”, aunque exige recorrido propio.  
   **Consecuencia:** un error común de nombre, orden o interpretación del array contaminaría ambos recorridos; la comparación detectaría discrepancias geométricas, pero no ese error de carga.  
   **Mínimo cambio:** el consumidor debe reabrir y decodificar en su propio proceso/sesión el NPZ pinado y los pilotos, construyendo sus índices de celda y planos sin recibir `heights`, celdas ni pares del productor. Pueden compartirse primitivas selladas de lectura, dejando constancia de ese residuo común.

3. **La semántica existencial del agua debe escribirse como unión, no como suma de pares.**  
   Ancla: definición propuesta de `SELECTED_WATER_AT_OR_ABOVE`, `SELECTED_WATER_ONLY_BELOW` y `NO_SELECTED_FOOTPRINT`.  
   **Consecuencia:** con huellas solapadas de distinta altura, restar pares individualmente puede mover área entre “sólo inferior” y “a igual/mayor altura”.  
   **Mínimo cambio:** definir por punto de la cara: `G = unión(water_i ∩ {W_i≥B})`, `F = unión(water_i)`, slots superiores desde `G`, “sólo inferior” desde `F\G` y ausencia desde el complemento de `F`. Incluir solape parcial de dos aguas de alturas opuestas como oráculo literal.

4. **La igualdad marginal con Q03C1 debe fijarse por cara, no sólo por el agregado de la cápsula.**  
   Ancla: el resultado Q03C1 aportado contiene sumas globales `37.45741951018598 / 3.0365742489692926 / 457.8056221008301 m²`, pero la exigencia del plan es por cara.  
   **Consecuencia:** errores compensados entre caras podrían conservar el total y aun así falsear los nueve slots individuales.  
   **Mínimo cambio:** pinar en el contrato el artefacto/hash que contiene los 1520 triples racionales por cara y usar ésos en la comparación. Inventariar además **19 oráculos Q03C1, no 20**.

5. **Los caps deben abarcar también la fase de arreglo del consumidor.**  
   Ancla: el plan limita fragmentos y vértices “por cara”, pero el consumidor construye un arreglo de rectas de lados, `B-H` y `W-B`.  
   **Consecuencia:** contar sólo polígonos del productor permitiría agotar memoria o tiempo en celdas/aristas del arreglo sin violar formalmente el contador.  
   **Mínimo cambio:** aplicar los mismos techos acumulados por cara a rectas vivas, celdas del arreglo, vértices y piezas en ambos caminantes, sin reinicio al pasar de celda, terreno o agua. Si se exceden, `RESOURCE_INCONCLUSIVE` o parcial verificado; no ampliar caps. Con el máximo histórico Q03C1 de 4515 operaciones por cara, la producción de 120 s es plausible, pero no debe prometerse `FULL`.

6. **Faltan reglas para contactos de área cero e IDs testigos.**  
   Ancla: se piden IDs de celda/cara y mínimos/máximos `B-H` en los vértices de la partición.  
   **Consecuencia:** una celda tocada sólo en un borde o vértice podría entrar como testigo positivo en un caminante y no en el otro, sin alterar áreas. Lo mismo aplica a caras de lecho o agua con proyección XZ degenerada.  
   **Mínimo cambio:** IDs y extremos proceden únicamente de intersecciones de área positiva; los contactos frontera tienen área cero y no crean slot ni testigo. Una cara de lecho sin plano `B(XZ)` bien definido impide el estado completo de 1520 caras, sin asignarle silenciosamente nueve ceros “verificados”.

7. **La finitud de `heights` no puede cerrarse en la fase de cabeceras.**  
   Ancla: esa fase prohíbe cargar arrays, pero exige `heights` finito `f4/f8` de `2048x2048`.  
   **Consecuencia:** mezclar ambas puertas permitiría afirmar antes de tiempo una propiedad que sólo puede comprobarse al decodificar.  
   **Mínimo cambio:** la fase de cabeceras congela exclusivamente nombre, `descr`, orden Fortran, forma y esquema completo de miembros; la finitud se verifica al cargar en productor y consumidor. Cualquier miembro o descriptor no congelado produce rechazo, sin crear infraestructura genérica adicional.

Con esos siete cierres incorporados literalmente al contrato, el plan **converge** y puede pasar a autoría. No procede prometer `FULL`, exposición, aceptación nativa ni localización fotográfica.
