# Segunda opinión: base Baltic V30 (Opus 5.5, `claude-opus-5-5`)

Solo he leído código y planes; no he ejecutado ni validado nada.

## Orden recomendado

**Sí: termina la geometría antes de reconstruir el editable.** Las piezas de agua no dependen de la altura del fondo. En cambio, el ASC, la máscara de superficie y la navmesh (NM) sí dependen de la geometría. Así hay una sola importación ASC y una sola NM.

1. **Orillas, sin interfaz (2,5–3 h).** Usa la copia regional de `a84dfff0`; la propuesta va abajo. Mientras corre, intenta una vez recuperar Terrain Builder (TB): ver si responde y cerrar el diálogo de New Project. Solo eso, sin importar nada (`HANDOFF.md:20`).
2. **Regenerar la superficie desde la línea de agua nueva (≈1 h).** Hazlo junto con la geometría, no después. Usa la correspondencia de capas nueva y no la heredada (`plans/v30-native-editor-recovery.md:65-69`).
3. **Un único bloque en TB (≈2 h)**, en la copia `delta_v30_native`: ASC final, luego objetos de agua, luego satélite y máscara; guardar, reabrir, exportar dos veces y comparar al final (`v30-native-editor-recovery.md:15-24`). Importa el ASC antes que los objetos (riesgo 1).
4. **NM y paquete en una variante nueva**, y una sola tanda de pruebas sobre ese despliegue: carga, agua y costa, la vista A/B de orilla y un consumidor de navegación.

## Mecanismo de las caras pronunciadas

**Confirmado por lectura** (no medido):
- Dentro de un triángulo, la pendiente se calcula con sus dos catetos alineados con la rejilla (`pilot_narva_shore_v30.py:75-76`).
- El tope de pendiente limita cada cateto a 2,88 m en 6 m (`build_v30.py:12,42,485`). Si los dos catetos están en el tope, la cara llega a 34,2°.
- Por tanto, **una cara mixta de más de 35° exige un cateto por encima del tope**. Eso solo ocurre donde `settle` no puede actuar:
  - Vértices fijos contra vértices fijos: agua, plataforma de carretera o Narva (`build_v30.py:480,501`).
  - Un suelo mínimo de la tierra por encima de «lecho + 2,88 m» (`:482-484`): orilla `near_lv+0,35` (`:483`) o `shore_floor` (`:484`).
  - Saltos entre planos de agua escalonados: el agua queda bajo `pmin-0,05` y la tierra sobre `pmax+0,03` (`:460-465`).

**Hipótesis:**
- La corrección del delta/Luga se aplicó después de `build_v30` y quizá sin un nuevo `settle`. Explicaría por qué se concentran en el Luga (`evidence/v30-shore-inventory-2026-10-03/README.md:16-17`).
- La franja oscura del piloto: subió el fondo hasta 4 m dentro de los primeros 6 m (`pilot_narva_shore_v30.py:97-105`). Probablemente deja ver a través del agua somera un material de superficie que no se regeneró. Sería sobre todo un problema de textura y no solo de geometría.

## Propuesta acotada para orillas

Un script nuevo sobre una copia de `a84dfff0`, que reutilice las máscaras del piloto.

1. **Protección.** Mantener fijos los corredores navegables, `platform`, `reserve` y `narva` (`pilot_narva_shore_v30.py:88-98`), con la aserción de igualdad de `:108`. Añadir un margen de 1 vértice alrededor del canal útil de 24 m.
2. **Clasificar cada cateto por encima de 2,88 m según su causa** (las tres del apartado anterior), dentro de la misma ejecución. Es un diagnóstico interno, no un ciclo de auditoría. Las parejas fijas, como la reserva de puente con 8,088 m, quedan en una lista de excepciones y no se tocan.
3. **Corregir primero la tierra.** Rebajar la tierra cuando el suelo mínimo lo permita, ajustando solo `shore_floor` o la orilla en esos vértices, sin cambiar los parámetros globales. Solo si no basta, subir el fondo de los primeros 1–2 vértices mojados fuera de los corredores, con un límite de ~1,5 m en lugar de 4 m. Mantener la profundidad de `shore_min` y `pmin-0,05`.
4. **Volver a pasar `settle`** (`build_v30.py:508-522`) y la reparación de carreteras con el mismo conjunto fijo.
5. **Una sola tanda de comprobaciones:**
   - Calado mínimo de 3,05 m en el canal útil.
   - Las 76.536 estaciones viales.
   - Isla del Pequeño Neva separada.
   - Caras de más de 35° por causa (bajar las «corregibles», no el total).
   - Error de la línea de agua (función `metrics`).
   - Coherencia con las piezas de agua.

No tocar el piloto `bb270ecc` ni los objetos de agua.

## Riesgos concretos

1. **Altura relativa de los objetos en TB (hipótesis).** Hay una evidencia llamada `before-relative-offset-correction.tv4l` y la LIVE-STATE dice «height0 por validar relativo» (`HANDOFF.md:22`). Si TB guarda los objetos respecto al terreno, importar el agua antes del ASC final desplazaría 17.622 piezas. Por eso: ASC primero, y comprobar unas pocas cotas antes de guardar.
2. **Retroceso del canal navegable.** Subir el fondo puede romper el calado del Luga o del Neva. Mantener los corredores fijos y comprobar el calado en la misma tanda. No reabrir el caso 5 del Luga (`HANDOFF.md:21`).
3. **Geometría y superficie desincronizadas.** Cambiar la orilla sin regenerar la máscara reproduce la franja oscura. Pasan juntas a TB o no pasan.
4. **Conflictos sin solución en carreteras y puentes.** Las parejas fijas plataforma–agua y la reserva de puente no se arreglan suavizando. Hay que aceptarlas como excepción y no rebajar las plataformas.
5. **TB sin respuesta otra vez.** Limita la recuperación a 20–30 min con un intento y una recuperación distinta (`plans/overnight-2026-10-03.md:36-38`). Si falla, cierra la geometría, la superficie y el paquete offline, y deja el editable como pendiente concreto. La NM sigue siendo posible desde el WRP derivado, como en d115461b.

## Lo que no conviene hacer

- No intentar bajar las 4.149 caras.
- No repetir el importador WRP `0WZD`.
- No generar la NM antes de cerrar la geometría: cualquier cambio de altura invalida `eece8e5e`.
