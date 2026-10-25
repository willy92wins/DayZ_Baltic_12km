# Revisión del bloque de orillas: 3 fallos concretos, 2 riesgos menores

Revisión hecha solo leyendo código y recibos. No he cargado los `.npz` ni ejecutado nada, así que no tengo recuentos medidos.

## Hallazgos

**1. Falso PASS en 30 puntos «wet» de estanques bajos** — `tools/playtest/verify_shorefinish_v30.py:41-46`
- **Mecanismo:** para un punto con `pond_plane_m` se acepta una superficie entre `max(sea_min, plane)` y `max(sea_max, plane)`. Si el plano está entre 0,825 y 1,0 m, el mar (0,5–1,0 m) cae dentro de esa ventana aunque falte la pieza de estanque. La fila `Q` no registra el nivel del mar en ese momento, solo los límites. El indicador `SurfaceIsPond` (`f[4]`) se lee y se valida como booleano, pero no se usa.
- **Alcance:** en `reference.json` hay 30 puntos «wet» con `pond_plane_m` ≤ 1,0x de un total de 252 puntos de estanque.
- **Controles:** ninguno de los nueve controles toca la rama del plano de estanque. El único punto «wet» tiene `pond_plane_m=None`.
- **Consecuencia:** si faltan piezas en estanques casi al nivel del mar, el verificador puede dar PASS igualmente.
- **Acción:** para puntos con plano, exigir `f[4]=='true'`, o registrar `SurfaceGetSeaLevel()` en `Q` y exigir que el mar esté por debajo de `plane - tol`. Añadir un control negativo de «pieza ausente».

**2. Holgura frente a las piezas más estrecha que el contrato original, y sin comprobar** — `finish_shores_v30.py:25,118,131` frente a `build_v30.py:41,461-465`
- **Mecanismo:** el contrato original pone el fondo mojado a `pmin − 0,05` (`piece_depth_m`) y la tierra seca a `pmax + 0,03` (`piece_freeboard_m`). El nuevo constructor usa 0,025 en ambos sentidos.
- **Dónde aplica:** en estanques llanos manda `level − 0,101`, así que este límite solo aplica en cauces con pendiente (celdas vecinas con planos distintos). Ahí un fondo elevado puede quedar a 2,5 cm bajo el plano, la mitad de lo acordado.
- **Por qué no se detecta:** `review_shores_v30.py` no repite la regla 5b de consistencia con las piezas. La misión clasifica ±0,05 alrededor del plano como «transition», donde solo comprueba la altura. Ningún paso actual lo vería.
- **Acción:** usar 0,05 / 0,03, o contar cuántos vértices quedan en ese límite y justificarlo. Añadir a `checks` la invariante `h ≤ pmin − 0,05` (mojado) y `h ≥ pmax + 0,03` (seco).

**3. La pendiente de orilla es un dato agregado, no una comprobación** — `review_shores_v30.py:100-103`
- **Mecanismo:** `after_over35` (4043) frente a `before_over35` (4149) es un recuento global y no forma parte de `checks`. Puede haber caras nuevas de más de 35° tapadas por las que se eliminan.
- **Hueco en el constructor:** `recover_dry_gradients` (`finish_shores_v30.py:61-69`) solo limita aristas de ejes entre pares seco-seco. No cubre la diagonal NW-SE, ni las aristas seco-mojado, ni la subida de fondo.
- **Acción:** comparar cara a cara: `after>35 & after>before+ε` igual a cero dentro de `checks`.

**4. (Menor) El dominio de exposición a marea baja depende de una suposición sin comprobar** — `review_shores_v30.py:78-80`, `finish_shores_v30.py:135`
- **Mecanismo:** «tidal» se define como `level ≤ 0,8`. Lo que de verdad importa es «agua que no cubre ninguna pieza de estanque» (`pmin` NaN). Las dos cosas coinciden solo si ningún vértice mojado fuera de `POND_CLASSES` (clases 1 y 4) tiene nivel por encima de 0,8, y nadie lo comprueba.
- **Acción:** si existe un vértice así, no se vigila su exposición a 0,5 m. Basta con añadir esa comprobación en `review`.

**5. (Menor) Falso FAIL en vértices situados en bordes de celda** — `prepare_shorefinish_runtime.py:62-64`
- **Mecanismo:** un tercio de las consultas son vértices exactos. Se clasifican solo con el plano de la celda SE, pero el motor puede resolver ese punto con la pieza de una celda vecina, cuyo plano puede diferir más de los 0,04 de tolerancia. Un mojado de borde con la celda SE sin plano saldría como «dry» y fallaría.
- **Consecuencia:** puede dar fallos espurios, no PASS falsos.
- **Acción:** usar `pmin`/`pmax` de las cuatro celdas, o clasificar esos vértices como «transition».

**6. (Menor) Colisiones de hash solo dentro de la biblioteca nueva** — `prepare_water_templates_v30.py:98-99`
- No se cruzan con los 6.187 hashes nativos. Si la biblioteca antigua sigue cargada en el proyecto TB, una colisión no se vería. Es una intersección barata de añadir.

## Riesgos que solo resuelve el consumidor (no son fallos)

- **Origen frente a centro en la importación de TB:** el contrato anterior (`derive_world_v30.py:4-5,45-48`) dice que la traslación del WRP es el origen más el centro de la caja que incluye el origen. La TML es coherente con esto: añade el punto (0,0,0) y fija `BoundingCenter` en ese centro. El CSV exporta esa traslación ya desplazada. Si el importador de TB toma la posición como origen y vuelve a sumar `BoundingCenter`, habría un doble desplazamiento de hasta unos 12 m (`edge_00000`: centro 12,005, 0, 12,005). Solo lo decide una prueba aislada: importar una pieza asimétrica, exportar el WRP y comparar.
- **Elevación absoluta y campos copiados de `templates[0]`:** lo mismo, solo se confirma con la importación nativa.
- **Navmesh, apariencia visual y rendimiento:** sin evidencia de motor, como ya se indica.

## Sin defectos encontrados en

- **`render_view_v30.py:78-79`:** equivale a la regla de agua de `build_surface_v30.py:103`.
- **Exposición por vértices:** es completa porque las caras son lineales y lo mojado nunca baja.
- **Recuperación seca:** nunca supera la altura original.
- **`float32`/ASC y corredores:** los corredores coinciden exactamente en sus vértices.
- **Hashes del paquete:** `stage-receipt` → `f27aacd3`, y los PBO coinciden con `reference.json`.
- **Terminación de la misión:** `QBEGIN`/`QEND` con 961, `END;7` por temporizador, reutilización segura de los arrays temporales y `queries.csv` con 961 filas.

## Límites de la revisión

- No he medido cuántos vértices quedan en el límite de 0,025 (hallazgo 2) ni si hay clases 1/4 con nivel por encima de 0,8 (hallazgo 4).
- No he leído los LOD reales con `py3d`.
- No he comparado `init.c` con su misión de origen más allá de las sustituciones que hace el script.
- Nada de esto prueba el comportamiento del motor.
