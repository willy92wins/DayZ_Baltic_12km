## Veredicto: **SOUND-with-fixes**

El núcleo es correcto y cerrable sin nuevas fases: las correcciones se pliegan en el anclaje/oráculo previo al código, ya autorizado. No procede escena real ni otra ronda documental.

**Lo que la evidencia adjunta sí sostiene**

- Identidad por nombre: en la fuente, `slots` son pares `(model_index del padre, ordinal)` y el salto se resuelve siguiendo `p['model']` literal; `META.model` acaba en la raíz y `META.source_model` conserva el dueño de la cara (líneas 173-198, 20-22). Resolver cada `p['model']` por nombre canónico en `sections` y exigir que coincida con el siguiente padre o con `source_model` final cierra exactamente la regresión histórica: en el repro, el hijo literal `test/unrelated.p3d` mapea al índice 3 ≠ `source_model=2`, con números internamente coherentes; el algoritmo propuesto lo rechaza. El oráculo debe conservar ese caso tal cual.
- Ruta: primer par con `root_model`, ordinal dentro de `proxies` del padre actual, `visited` anti-ciclos dentro de la ruta, sin dedup ni reordenar rutas (el campo `proxy` es posición en la lista; deduplicar rompería la referencia). `proxy` en kind0/1 debe ser −1 y `source_model=model`; en kind2, raíz/`source_model` iguales a los de la ruta indicada.
- No se reaplican `matrix`/`center`; `kind2` queda condicional, sin certificar marco motor, época ni cierre global. Salida `FIXTURE_FACE_ROUTE_IDENTITY_ONLY` es honesta.

**Fixes obligados antes del executor (mismo corte)**

1. **Sección: bajar la afirmación a lo comprobable.** La fuente guarda por sección sólo `index/material/texture/faces=count` (líneas 126-127, 147); el mapa cara→sección de `sections(lod)` no se persiste. Por tanto el validador sólo puede exigir `section` en rango dentro de ese LOD, no pertenencia real de la cara. El contrato debe decirlo explícito y el negativo «sección fuera de rango» no debe venderse como detección de sección errónea en rango. Ídem LOD: `face < lod.faces` sí es comprobable; el índice se busca por campo `index`, no por posición.
2. **Kind semántico fuera o dentro, sin término medio.** kind0/1/2 se usan como discriminadores de enlace proxy; la función no recibe resolución/material por cara, así que no certifica que kind0 sea Roadway ni kind1 agua. Declararlo `NOT_EVALUATED` en la salida, o el fixture pasa caras con kind mal etiquetado. El plan ya prevé esta salida; hay que fijarla como la opción por defecto del corte.
3. **Normalización asimétrica real.** `extract` añade `.p3d` si falta en nombres proxy (línea 166), pero los nombres de `sections` vienen de bindings/catálogo, no de esa línea. El anclaje debe demostrar con la muestra guardada que ambos lados comparten convención de sufijo; si no, la resolución por nombre rechaza hijos válidos (falso FAIL). Nada de añadir `.p3d` en el validador para taparlo.
4. **`expected` como multiconjunto literal completo** (identidades + rutas), no cuentas: si no, omitir una fila y duplicar otra compensa. El oráculo de multiplicidad 2 lo exige. Comparación independiente, nunca derivada de la función.
5. **Límite 1 MiB pre-parseo fuera de la función pura:** `validate_face_routes` recibe objetos ya parseados; ese control pertenece al cargador del fixture y debe testearse ahí, no declararse propiedad de la API.
6. **Hash del contrato con digest completo**, no prefijo `e967`, en el manifiesto del oráculo.
7. Tipos exactos (`type(x) is int`, rechazo de bool) y claves estrictas en todos los niveles anidados, no sólo arriba; ruta con `slots` vacío rechazada; rutas no referenciadas por ninguna cara también validadas.

**Presupuesto:** suficiente y sin inflación. Función pura con ≤64 modelos/64 rutas/512 caras no justifica más de 120 s/256 MiB de suite; 600 s de executor y 180 s de reviewer externo van sobrados. La única corrección de 180 s tras repro concreto y la recuperación de dictamen de 180 s sobre mismos bytes son proporcionadas; cualquier segundo fallo vuelve a revisión humana, no a otra corrección automática.

**Riesgos residuales declarados:** falsos PASS acotados a pertenencia cara→sección y semántica de kind (ambos `NOT_EVALUATED`); falso FAIL posible sólo si el anclaje del fix 3 revela nombres de sección sin `.p3d`, en cuyo caso se corrige el diseño antes de codificar, como el propio plan manda.
