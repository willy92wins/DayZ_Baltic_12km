**Veredicto: SOUND-with-fixes** como diagnóstico. El paquete offline **no está aceptado todavía**; faltan cinco gates ejecutables, todos sin reimplementar Binarize. Dos campos quedan INCONCLUSO semántico y se aceptan por envolvente, descomposición y mismo compilador, no por fórmula.

**Lo que la evidencia sí sostiene**

- Control bbf4 contra ODOL vigente: LOD0/1/2 exactos campo a campo, LOD3 sólo reorden canónico de caras y secciones. Es reproducción semántica, no byte a byte. Esa reordenación la hereda el candidato y sólo la juzga la sonda DayZ.
- Candidato: caras de los cuatro LOD iguales al MLOD en pose WRP, centro exacto, Memory exacto, contacto 0 en 1520 prismas, masa 9120, bounding box sin cambio en model_info.
- Bisección complementaria por XOR es correcta: prueba que todos los bytes distintos entre fuentes están en slots Y o en el bloque de normales y en ninguna otra parte.
- COM e inercia: recomputación independiente da error relativo del mismo orden en control y candidato, y la media local coincide con COM reportado a 2e-10 en Y. Eso es suficiente: el comparador explica el candidato tan bien como explica el control.

**Falsos PASS o puntos ciegos del analizador**

1. `water_source_faces_included` y `geometry_exact_source_at_Wrp_pose` en los records son literales True, no mediciones. Están respaldados por el assert de multiconjunto de caras, pero un lector del JSON no lo sabe. Fix: derivarlos de contadores reales por rol.
2. El discriminador de aislamiento salta todo campo donde control==candidato. Si un build diagnóstico introdujera un cambio nuevo en un campo que la pareja comparte, no se vería. Fix: exigir que para todo campo, Y-only y N-only tomen exactamente el valor de control o el de candidato, y listar excepciones.
3. Normales sólo se comprueban en LOD0. Aceptable porque LOD3 no reporta cambio de normales, pero debe constar como alcance.
4. Las estadísticas ST (dot, normas, orientación) son idénticas a 16 dígitos en ambos lados. Es coherente si los extremos están en vértices no cambiados, y vale como envolvente, pero no dice nada vértice a vértice sobre los 124 cambiados.
5. `size_of_rest_data` marcado como interacción es esperado, no una anomalía: los streams van comprimidos y su tamaño depende de los bytes de posiciones y normales a la vez. El analizador no lo explica y lo deja como "unresolved".

**Gates mínimos para aceptar el PAQUETE OFFLINE**

- **G1 Composición.** PBO nuevo = PBO vigente con una sola entrada sustituida. Leer ambos con read_pbo: mismo orden de entradas, misma cabecera y prefijo, config.bin byte-idéntico, las 200 entradas restantes con sha idéntico, entrada sustituida con sha 351424ab. Contraprueba: una copia con dos entradas cambiadas debe fallar.
- **G2 Cierre de diferencias.** Campos cambiados entre ODOL vigente y candidato ⊆ (vigente vs control) ∪ (control vs candidato). Cualquier campo fuera de esa unión bloquea. Esto cierra "no hay tercera fuente de cambio".
- **G3 size_of_rest_data.** Para cada LOD de candidato y control: valor == declared_end menos posición del lector tras leer el campo. El lector ya tiene parsed_end y declared_end. Con eso el campo pasa de "interacción" a "tamaño serializado verificado".
- **G4 ST sin layout.** Tres subpruebas sobre st_raw como slots de 8 bytes: (a) los 721 slots no cambiados son byte-idénticos en control, candidato, Y-only y N-only; (b) descomposición: en vértices donde sólo cambió Y, candidato == Y-only; donde sólo cambió N, candidato == N-only; donde cambiaron ambos se cuenta como interacción esperada y se reporta el número; (c) bajo la hipótesis de dos vectores 10 bits, etiquetada como hipótesis, signo de det[T,B,N] igual al de control en cada uno de los 124 vértices (UV no cambia, la quiralidad no debe cambiar), y normas y productos dentro del rango de control. Contraprueba: alterar un byte de st_raw en memoria y comprobar que (a) y (c) fallan.
- **G5 area_over_tex.** Sección 1 (agua) byte-idéntica en los cuatro builds. Sección 0: Y-only == candidato exacto, y cambio relativo acotado por debajo de 1e-3 en ambos valores. La fórmula queda INCONCLUSO explícito.

**INCONCLUSO exacto que permanece tras los gates**

- Layout semántico de ST: sólo hipótesis. Lo que se demuestra es que cambia únicamente donde cambia su entrada y que conserva la envolvente de control.
- Fórmula de area_over_tex: el ratio de áreas de sección (1.000113) no coincide con los ratios de los valores reportados (1.000176 y 1.000359). No es escala de área simple. Queda acotado numéricamente y dependiente sólo de Y.
- Ambos campos los produjo el mismo Binarize que generó los 200 payloads y el control demuestra que ese Binarize reproduce la semántica vigente. El riesgo residual es un comportamiento del compilador disparado por la nueva geometría, no observable sin runtime. Se asume y se enuncia.

**Correcciones de reporte antes de empaquetar**

- Sustituir los dos literales True por conteos medidos.
- Añadir el chequeo de "todo campo ∈ {control, candidato}" al aislamiento.
- Registrar sha de los dos ODOL diagnósticos en el report de aislamiento, no sólo en receipts.
- Declarar que LOD3 cambia de orden respecto al vigente también en el control, para que la sonda DayZ lo tenga como hipótesis a observar.

No confundir con fallo del paquete: visual humana, RAM y regresiones globales siguen abiertas y son posteriores al paquete, no requisitos suyos.

FIN_REVISION
