## Veredicto: NEEDS-WORK — NO_CONVERGE en su forma actual

La recuperación acotada es la dirección correcta y no exige repetir C1A, pero el plan contiene un límite que hace imposible la única ejecución prevista.

### Hallazgos bloqueantes

1. **Cap de lectura incompatible con el corpus pinado.**  
   El manifiesto suma **27.766.367 bytes**, pero la ejecución permite leer **≤16 MiB**. La rutina agotaría el presupuesto antes de procesar los 4.775 textos. Debe sustituirse ese cap por el total exacto derivado del manifiesto pinado; cualquier desviación de tamaño seguirá siendo `SOURCE_CHANGED`.

2. **Los caps de extracción pueden producir una recuperación parcial presentada como completa.**  
   No queda definido qué ocurre si un texto supera **128 strings**, el conjunto supera **32.768 strings distintas** o la salida supera **4 MiB**. Cualquiera de esos eventos debe abortar con resultado parcial/inconcluso y prohibir `RECOVERED_QUOTED_MATERIAL_REFERENCES_ONLY`. No debe truncarse la tabla ni continuar “hasta donde quepa”.

3. **Los pines mostrados están elididos.**  
   `78d24eba...` y `f3eb0ab1...` no bastan como identidad ejecutable. Antes de cualquier lectura deben incorporarse los SHA completos del reporte, del material del contraejemplo y de la reconciliación, junto con la raíz histórica exacta.

4. **“Reglas C1A” no puede permanecer como referencia externa.**  
   Deben reproducirse dentro del contrato las reglas concretas de namespace, normalización de `/` y `\`, sensibilidad a mayúsculas, raíces admitidas y rechazo de traversal/drive. Una referencia a C1A no cierra esas decisiones.

5. **La gramática de comillas escapadas está indefinida.**  
   En rutas Windows, `\` es separador y no necesariamente escape. Hace falta una regla léxica byte a byte para distinguir contenido, cierre y secuencia ambigua; la secuencia ambigua debe dar `UNKNOWN_QUOTE_GRAMMAR`, nunca intentar repararla. El oráculo debe incluir una ruta citada con backslashes.

6. **La reconciliación de “cantidad de usos” carece de oráculo independiente.**  
   C1A descartó las cadenas no seleccionadas, por tanto no existe un total previo contra el que conciliar. La reconciliación válida es: 4.775 archivos leídos, hash/tamaño coincidentes por archivo, y las dos cadenas del contraejemplo localizadas exactamente en las líneas 9 y 14, en Stage0/Stage1. No debe afirmarse una conciliación global de strings.

7. **Alcance de localización ambiguo fuera de PNG/PAA/RVMAT.**  
   Debe definirse el estado de candidatos con otras extensiones, incluidos los `.xyz` del oráculo, y de referencias sin slash. Estas últimas pueden quedar `LITERAL_NOT_RESOLVED`, pero deben contarse como no resueltas, no como ausencia de dependencia.

### Aspectos sólidos que deben conservarse

- No reabrir WRP, PBO, P3D, alturas, texturas ni configs bin/core.
- No sustituir PNG por PAA y limitar la localización a `lstat`: `LOCATED_NOT_READ` no implica validez ni identidad instalada.
- `SOURCE_CHANGED` sin relectura correctiva ni cambio de pin.
- Una sola ejecución, sin retries ni CLI productivo.
- `build_ready=false`, `dependency_closure=NOT_EVALUATED` y `compiled_terrain_decoder=NOT_VERIFIED` en todos los resultados.
- C1B requiere contrato y revisión propios; nada aquí prueba compilación, terreno ni decoder OPRW.

Con el cap corregido al total pinado, abortos explícitos ante cualquier overflow, pines completos y reglas léxicas/namespaces autocontenidas, el plan pasaría a **CONVERGE** para recuperar únicamente referencias textuales citadas, sin cerrar dependencias.

END_ROADC1A1_REVIEW
