**Dictamen: SOUND-with-fixes.** El plan puede pasar a preparar contrato concreto. Las premisas sobre lo que guardan ambos escritores coinciden con el código citado, el dominio de época está bien acotado y las puertas de salida no son tautológicas. Hay cuatro fixes que el contrato debe cerrar antes de autoría, más dos observaciones.

**Fix 1. Ligadura de poses del piloto con instances.npz no está pinada.** El piloto toma la pose en `pilot_visible_surface_ev112.py:190` con el primer índice de `poses['model_index']==mi`. Ese archivo de poses no aparece en la lista de manifests a fijar. El contrato debe exigir que la fuente de poses del piloto sea byte-idéntica, por SHA de sus propios pins, a la fuente de `selected-instances.npz` que leyó el inventario en `deployed_surface_inventory_ev112.py:286`. Sin ese eslabón, unir `instance_id` del piloto con `instances.npz` es exactamente la mezcla de épocas que el plan quiere evitar. Si difiere, INCONCLUSIVE_EPOCH_BINDING.

**Fix 2. El piloto cubre una instancia por modelo, no todas.** Por el `[0]` de la línea 190, cada uno de los 201 modelos queda ligado a una sola pose aunque tenga varias en las 17818. El invariante 3 dice "exactamente una pose guardada" y es correcto, pero la salida por modelo debe distinguir instancias con caras mundiales guardadas de instancias sólo con prototipo local pendiente de Q04. Ese conteo es el discriminador mínimo que avanza la composición: cuántas instancias de lecho quedan realmente medibles sin transformar nada.

**Fix 3. Premisa falsa en invariante 5.** `section` sí se guarda para caras de proxy: META conserva el `si` del hijo y sólo se sobreescriben `model` y `kind` en las líneas 196. Sólo `sequence` y `bone` son UNKNOWN. Además, la clave de unicidad de prototipo no es (modelo, cara): la misma cara se emite dos veces cuando es Roadway y agua Visual a la vez, y una cara hija puede aparecer bajo varios padres. El contrato debe fijar la clave como (model, source_model, face, lod, kind, proxy).

**Fix 4. Tipos declarados a priori.** El invariante 4 fija `float32` para matrices, pero el inventario relee `matrix` sin cast y ninguna fuente muestra su dtype. Los vértices del piloto son `float64` por el `np.zeros` de la línea 218. El contrato debe tomar dtype y shape de las cabeceras NPY y comprobarlos contra las cuentas de `extraction.json` y `models.json`, no declararlos. Igual para padding: un vértice local legítimo puede ser (0,0,0); la fila de padding se identifica por `vertices` y `_n`, nunca por ceros.

**Sobre el presupuesto y la pregunta ZIP.** La expansión sí es justificable desde el formato del escritor, sin inspección separada como unidad propia:

| Array | Forma derivable | Expandido aprox. |
|---|---|---|
| surface-prototypes vertices | (539009,4,3) float64 | 52 MiB |
| surface-prototypes meta | (539009,) META | depende del dtype META, acotar por cabecera |
| instances matrix | (17818,12 o 4x3) | < 2 MiB |
| 201 pilot NPZ | por `models.json` faces | < 20 MiB en total |

Con cap 512 MiB y proceso modelo a modelo, el margen es amplio. Lo que el contrato debe exigir es una comprobación de cabeceras integrada en el productor: lista de miembros exacta contra el manifest, sin pickle, suma de tamaños descomprimidos antes de `np.load`, y rechazo si la shape leída no coincide con la derivada. No hace falta mmap sobre NPZ y no debe prometerse. El disco de 32 MiB basta porque la salida es índice de referencias, no geometría.

**Observaciones sin bloqueo.**

- **Bucle documental.** Hay tres capas antes de código: este plan, el contrato externo con fixtures, y la revisión del contrato. Es aceptable, pero el contrato no debe reabrir este documento ni pedir otra revisión del plan. Una revisión del contrato es suficiente.
- **Cobertura Visual de lecho.** Sólo los 201 modelos piloto tienen caras `bed` del Visual guardadas; el inventario sólo conserva Roadway completo y agua Visual. La fila terminal para los otros modelos debe decir `visual_bed=NOT_SAVED`, no `absent`, como ya exige el plan. Esto limita Q03C a lecho Roadway para la escena general, y el contrato debe declararlo como alcance, no como hallazgo.
- **Marco de proxy.** Las 65 caras condicionales ya incluyen `center` del hijo vía `proxy_transform`, mientras las caras padre son locales raw. El índice debe etiquetar ese marco mixto por fila y mantener la dependencia Q04 como el plan dice.
- **Equivalencia no orientada.** La distinción de kit118_0000 se preserva correctamente; el contrato no debe añadir comparación orientada.

Con los cuatro fixes incorporados, el contrato puede fijarse con fuentes, schema, oráculos y presupuesto cerrados. Nada de esto autoriza abrir arrays ni ejecutar todavía.
