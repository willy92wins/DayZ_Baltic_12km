**Veredicto: SOUND-with-fixes.** El diseño bloquea los cierres falsos principales. Quedan cinco huecos por omisión en contrato y consumidor que conviene fijar antes de implementar.

**Lo que cuadra con fuente**

- Universo de 9: feedback.json:28-47 (3), kit118-feedback.json:12-26 (2), continuous65-feedback.json:11-19 (1), road49-feedback.json:16-26 (1), additional-crossing-feedback.json:4 (1), relief-east-feedback.json:5 (1). Coincide con tour-ended-20261028.json:9 y con el extracto de observations. Plan:75 "3Narva+2kit+4otros" suma 9.
- No duplicar: relief-east:106 y kit118:11 impiden un décimo caso. Plan:77 ya prueba el mutante de consolidación.
- Avatar no es defecto: feedback.json:15, road49:23, relief-east:46-47. Plan:39 lo conserva.

**Fix 1. Literales de estado heterogéneos (riesgo de cierre por normalización)**

Los veredictos no comparten literal: `OPEN` (feedback.json:33, kit118:17, continuous65:17), `VISUAL_REJECTED_BY_USER` (road49:21, relief-east:14), `USER_REJECTED_ROAD_INTERRUPTED_BY_RIVER` (additional-crossing:6). Plan:62 pide "veredictos literales" pero no fija un allowlist. Contraejemplo: si el consumidor sólo compara ledger==fuente, una fuente regenerada con `status: "FIXED"` y hash re-pinado pasa. Fix: el contrato enumera por ID el literal esperado y el pointer exacto; el consumidor rechaza cualquier literal fuera del conjunto de rechazo. Además registrar dos pointers por caso cuando existen: estado de archivo (`/status`, feedback.json:2) y estado del finding (`/findings/1/status`), ambos obligatorios. Si sólo se verifica el nivel archivo, un finding editado a `RESOLVED` no se detecta.

**Fix 2. Controles de alcance sin fuente primaria pinada**

Plan:9-24 no lista forest-feedback.json ni causeway-c0-feedback.json; el control bosque/c0 se apoya sólo en tour-ended:10-13, que es resumen. Fix: pinar forest-feedback.json:11,13 (`global_forest_acceptance:false`) y causeway-c0-feedback.json:11,14,15. Para carretera49 hay dos literales distintos del mismo veredicto local: road49:9 `LOCAL_VISUAL_OK_WITH_PAVING_PENDING` y tour-ended:14 `..._NO_DRIVING_TEST`. Un consumidor que compare uno contra otro falla o, peor, normaliza. Fix: pinar ambos pointers con su literal propio, más road49:13-14 (`global_road_acceptance:false`, `bug_005_closed:false`).

**Fix 3. Evidencia nativa negativa que puede degradarse a NOT_DETECTED**

additional-crossing:28-31: 80 de 108 entidades devueltas, `bridge_detected_in_returned_subset:false`, `absence_proven:false`. Un productor literal podría mapear ese `false` a `NOT_DETECTED`, que plan:45-47 reserva para cobertura completa. Lo mismo con relief-east:56 `matched_to_user_feature:false`. Fix: añadir a los negativos de plan:76-80 el mutante "promover false-en-subconjunto a NOT_DETECTED" y exigir que el estado sea `CONTEXT_ONLY_UNCONFIRMED` con pointer y límite (`returned_entities<count_total`). Añadir también el mutante "rellenar `river_source_id`" para road49:22, que debe seguir `null` aunque contexts.json tenga un río cercano.

**Fix 4. Omisión sin esquema cerrado**

Plan:64 rechaza "omisión" sin decir de qué. Contraejemplo: un ledger sin `resolved_count` que el consumidor interpreta como 0 cumple plan:53-54 por defecto. Fix: esquema con claves obligatorias explícitas para caso y agregado, sin valores por defecto; `resolved_count:0`, `c1_verdict`, `visual_acceptance` deben estar presentes y comparados con constantes del contrato (tour-ended:7-9), no con totales que el consumidor derive del propio ledger.

**Fix 5. Capturas y pins externos**

feedback.json:17-27 y relief-east:89-98 llevan sha256 de PNG locales; feedback.json:49 declara una imagen no archivada. Si el contrato pina esas capturas y plan:64 rechaza "ficheros ausentes", un ledger correcto falla por un PNG no publicado. No es cierre falso, pero es un bloqueo evitable. Fix: clase de referencia `REFERENCE_ONLY` para capturas, verificada sólo si el fichero existe, y prohibido pinar la imagen de feedback.json:49. Pinar en cambio feedback.json:5-8 (`mod`, `world/pilot/water_sha256`) como identidad de versión para plan:57-58 y el mutante de plan:78.

**Límites de esta revisión**

No he visto observations.json completo, contexts.json ni summary.json; sólo el extracto de 9 observaciones. Plan:18-24 describe su uso correctamente, pero los pointers de esos tres archivos quedan sin verificar y deben fijarse desde lectura real, como ya exige plan:26-27. La correspondencia dominio→estado (`unknown`, `native_candidate`, `*_not_evaluated`) debe ir en el contrato como tabla literal, no inferida.

Con los cinco fixes el consumidor no puede cerrar por omisión, normalización ni promoción de un `false` parcial.