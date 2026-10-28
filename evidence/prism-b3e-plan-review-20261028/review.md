Revisión del plan B3E, sólo lectura de la cápsula.

**Veredicto: SOUND-with-fixes.** El plan es coherente con B3D publicado, respeta REJECTED_BINARY/FEASIBILITY_ONLY previos y no amplía alcance a 201 modelos, despliegue ni DayZ. Los hallazgos son de instrumentación, reproducibles con fixtures, y deben resolverse en el código antes de la pareja. Ninguno exige bajar tolerancias ni tocar controles.

**Hallazgos**

1. **Censo parcial en source_faces (prism_b3_binary_ev112.py:100-111).** Cada `need` dentro del bucle aborta en el primer componente discrepante. Contradice gate 4 (plan:99-103) y la regla de plan:115. Consecuencia: un rechazo listaría sólo un componente y las puertas 5 quedarían sin dictamen declarado. Fix: acumular por componente (local_match, error bidireccional, contador de caras) y lanzar un único ValueError con las 12 entradas al terminar; `component_coverage` (:114) debe evaluarse siempre. Contraejemplo: fixture con dos componentes mutados un ULP (p. ej. Component1368 y Component1410); el informe debe nombrar ambos, el código actual nombra uno.

2. **face_counter no distingue bits (:50-53, :104-111).** `key` compara tuplas de float64; `-0.0 == 0.0` en Python, y la igualdad numérica no es igualdad de bits. El plan (:57-58) ya lo reconoce, pero debe fijar el método: comparar los arrays float32 vía `.view('<u4')` por vértice orientado, antes de pasar a float64. Contraejemplo: fixture signed-zero donde una coordenada mundial del ODOL es `-0.0` y la prevista `0.0`; face_counter actual PASS, B3E debe rechazar. Añadir identificador de cara testigo al resultado de contactos (:79) para poder exigir "witness_component" igual al proof B3D.

3. **Puerta de control no es ejecutable aislada (verify_pair:123-135).** `control_identity` y `control_surface` sólo se alcanzan tras exigir baseline+control+candidato (:124-125) y tras leer `centre` del candidato (:129). El plan (:75-77, gatecontrol 180s) requiere control antes de consumir la compilación candidata. Fix: entrada `gate_control(baseline,control,control_mlod,...)` que tome `centre` de `control.model_info.bounding_center` (igual al histórico por `control_identity`:47) y produzca su propio artefacto sellado. Contraejemplo: control con winding sin invertir debe detener la secuencia sin que exista `candidate/saved-odol.p3d`.

4. **Inversión de winding tautológica (:109, :117-121).** El `[::-1]` se aplica igual a control y candidato, así que el control "justifica" la inversión sólo si ambos usan el mismo código. Aceptable, pero el informe debe declarar explícitamente que la justificación es "control compilado d130 reproduce caras 3514 con inversión", no una propiedad del compilador verificada independientemente. Sin fix de código; fix de redacción en `frames`.

5. **bind_context no reutilizable tal cual (:55-61) y riesgo de error interno.** Tiene el hash 447d literal y exige `proof['selected_components']`. El proof B3D mostrado no contiene `selected_components` ni `targets`: un acceso directo lanza KeyError, no Inconclusive, violando plan:113-114. Fix: parametrizar hashes (b445/ae5e/f2b7), tomar componentes y targets del contrato b445, y envolver el consumidor en un manejador superior que mapee cualquier excepción no clasificada a INCONCLUSIVE_BINARY con traza. Contraejemplo: proof con clave eliminada debe producir INCONCLUSIVE, no traceback. El esquema del contrato b445 (campos `source`, `pins`, `targets`, `origin`, `original_result`) no está anclado en la cápsula; el código debe validarlo, no asumirlo.

6. **Etiqueta de estado y texto de marcos heredados (:151, :156).** `COMPILED_B3_CONDITIONAL` y la frase de `frames` corresponden a B3B; reutilizar verify_pair sin cambiar la etiqueta produciría un estado distinto al que el plan define (:112). Fix: estado `COMPILED_B3E_CONDITIONAL` y `limits` que mencione que ODOL guardado no acredita ni motor ni 201.

7. **Sellado de herramientas no cubierto por el empaquetador (pack_continuous_stream_pilot_v31.ps1:8,23).** El script sólo comprueba existencia de AddonBuilder y escribe log; no registra hashes de AddonBuilder/Binarize/CfgConvert ni compara config.bin. El plan (:68-69, :89-90) lo exige, así que corresponde al preparador nuevo. Límite a declarar: hashear ficheros del directorio Bin prueba qué binarios existían, no cuáles ejecutó AddonBuilder internamente. Las junctions creadas en :16-20 no se eliminan; con dos raíces pilot independientes no hay conflicto, pero el preparador debe excluirlas al hashear "salidas antes/después".

**Compatibilidad con B3D**

- Gate 4 "localraw bit-idéntico a float32(MLOD−centro)" es la predicción de recentrado por vértice (:97-101), no grosor exacto entre pares; es coherente con la instrucción de no exigir grosor local exacto y con `world_frames_bit_exact: true` del proof.
- Centro [-4.0107421875, .396484375, -5.59375] y pose: `pose_check`:67 redondea origen+centro a float32 y exige igualdad con la fila de traslación; el valor de plan:37 es exactamente representable, sin riesgo de falso Inconclusive. Si el compilador nuevo cambiase `bounding_center`, `unchanged`:128 da Inconclusive (model_info_changed), no REJECTED; correcto, es cambio de entorno no error geométrico.
- `nonselected_compiled_data_changed` (:142-144) sobre 72 vértices seleccionados es coherente con 17 Y y 50 normales incidentes, dado que cada componente es un prisma cerrado de 6 vértices sin compartir índices.
- Márgenes 700/723: la igualdad exacta con 0.000640991… y 0.000522692… sólo es exigible si B3E usa el mismo algoritmo shapely en el marco mundial float32; el plan lo supone (:109) y las caras bit-exactas lo garantizan. Documentarlo como dependencia del método, no del motor.

**Afirmaciones sin ancla en la cápsula**

- Hash 5fb69872 de la copia de preflight y su diff contra la skill original (plan:63).
- Compatibilidad de `read_backend` (compiled_dry_road_gate_ev112.py:42-49) con `strict=True` y cuatro LOD: citado pero no mostrado.
- Esquema interno del contrato b445 (ver hallazgo 5).
No se inventan; deben verificarse en code review.

**Cobertura y límites de esta revisión**

Revisado: binding transitorio, alcance, orden de puertas, campos nuevos, marcos, relación con B3D, presupuesto. No revisado: código B3E inexistente, read_backend, overlay (review_compact_collision_v31.py), sonda nativa. Esta revisión no acredita ODOL, motor, RAM ni los 47 FAIL / 21 inciertos originales, y no autoriza construir antes de code review (300 s) y suite con los fixtures de plan:121-127 más los contraejemplos 1, 2, 3 y 5 de arriba.

**Identidad:** Fable 5.1 revisor, lectura única, sin herramientas ni ejecución; Codex ejecutor/integrador; ruta nativa CLI 2.1.310 sondeada 28-10-2026; presupuesto cerrado.

FIN_REVISION