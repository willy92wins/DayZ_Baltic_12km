**Veredicto: SOUND-with-fixes** (plan y código). Alcance, mecanismo y ausencia de afirmaciones causales correctos; dos correcciones mecánicas y tres menores antes de ejecutar.

## Plan (`plans/ev112-prism-b3-quantization-discovery-20261028.md`)

- Alcance y marco correctos: sólo lectura, B3B sigue REJECTED_BINARY (líneas 3-7), hipótesis sin causa atribuida (10-16), mundo ODOL declarado cálculo del instrumento (104). Enumeración en Y local MLOD (109) coincide con el código.
- Condiciones de factibilidad (68-85) son las ya aprobadas: plano/base 1e-6, grosor EXACTO en MLOD, igualdad mundial exacta, bbox intacto, overlay ±.02/.01, presupuesto 100k/1M → INCONCLUSIVE. Sin tolerancias nuevas.
- Observación: el plan exige grosor exacto sólo en MLOD (`prism_contact_b3_ev112.py:36`); el código añade grosor exacto en marcos local y mundial (ver hallazgo 1). El plan no lo autoriza ni lo prohíbe; hay que alinear uno u otro.

## Código `tools/quality/prism_b3_quantization_ev112.py`

Verificado sin ejecutar:

- Asociación por coordenada local predicha exacta y única (`:111-118`): lookup por tupla float64, unicidad e inyectividad; no hay nearest-neighbour. Igualdad de valor y de bits separadas (`:128-133`), cero con signo cubierto porque la tupla asocia por valor y los bits se reportan aparte.
- Cobertura: denominador 1520 (`:224`), vértices/caras completos (`:89,:139`), noncomparables conservados en el conteo y status CENSUS_INCONCLUSIVE (`:142`).
- Marcos: `y_frames` (`:63-65`) reproduce exactamente `prism_b3_binary_ev112.py:86-87,97`; restas float64 de dos float32 cercanos son exactas, y el oracle `round_fraction32` (`:39-52`) es racional independiente. Fixtures manuales en el test (ties par/impar, negativos, 4/8, subnormales, 2^100-1) verificadas a mano; el caso `test_manual_double_rounding_case` (test `:70-74`) produce 0x3f800001 vs 0x3f800002 correctamente: es un no-conmutación real, no tautología.
- Enumeración float32 ordenada con signo (`:28-30,:54-61`): monotónica incluyendo -0.0 < +0.0, bordes redondeados hacia dentro, tope de tamaño antes de materializar la lista → DomainBudget, nunca UNSAT (`:60,:179`).
- Dominio real: Y MLOD ≈ -0.42…+0.04, ULP 2^-25…2^-28 → 67…540 valores por par, 36 pares; muy por debajo del presupuesto. Correcto que no se adopte la estimación mundial.
- Testigo: sólo Y autorizado y X/Z bit-exactos (`:186`), bbox Geometry/modelo/compilado (`:187,:189,:192`), plano+grosor (`:197-198`), cierre/winding/convexidad (`:199-201`), overlay con primitivas v31 (`:203-205`), sólo JSON (`:231`). Signo de volumen y convexidad coherentes con el winding MLOD invertido de ODOL (`binary:109,149`).
- Pins y backend fijado (`:212-217`); contrato R1 5df50091 y ODOL 0fcc/b2c8 pineados en el contrato.

## Hallazgos

**1. Sobre-restricción no autorizada que puede producir falso NO_WITNESS** — `prism_b3_quantization_ev112.py:155`. Exige `lt-lb==T` y `st-sb==T` en los marcos local y mundial float32. Ninguna puerta citada lo requiere (dilate sólo en MLOD; B3B compara caras, no grosores). Con ULP mundial 4.77e-7 y T=45/128, RN32(top+7)−RN32(base+7) puede diferir de T en un ULP aunque ambas esquinas sean bit-iguales entre marcos; el filtro descarta testigos válidos bajo las condiciones del plan y el par se reporta como conflicto. Repro: test unitario que compare `eligible` de `solve_pair` con y sin la línea 155 en un dominio con o=7.0, c=0.396484375, T=7.396484375 y expected_plane=-0.42; o aplicar el filtro a un valor cuyos marcos sean iguales y comprobar que `st-sb` puede valer T±2^-21. Corrección: calcular y reportar esas diferencias por par, sin filtrar; o pedir al plan que autorice la condición explícitamente.

**2. Cobertura de tests: ruta de factibilidad con testigo no trivial no probada** — `test_prism_b3_quantization_ev112.py:125-129`. `test_complete_witness_is_analysis_only` usa centro 0, origen 0, traslación identidad: todos los marcos coinciden trivialmente y `changed_vertices==0`; no ejerce la lógica de movimiento, bbox, cierre ni overlay tras un cambio real. Añadir fixture 12 prismas con centro/origen/traslación del caso manual (`0x337fffff`, `0x3f800001`, `0x3fc00001`) tal que el censo tenga mismatches mundiales sólo-Y y la factibilidad devuelva FEASIBILITY_ONLY con `changed_vertices>0`, overlay y oracle verdaderos. Repro: fixture actual con `od.model_info.bounding_center.y=.5` y `matrix[10]=t` → debe salir del camino trivial.

**3. Oracle sólo sobre el testigo elegido** — `:160`. Si numpy y el oracle divergieran en un valor no elegido, un testigo se perdería en silencio (sesgo hacia conflicto). Dominios ≤~600 valores: aplicar `oracle_frames` a todos los `indices` elegibles (o a todo el dominio) es barato y elimina el sesgo.

**4. Pins autorreferentes** — `:214-216`. Script, test y plan se hashean y se exigen iguales a sí mismos: es registro, no comprobación. Etiquetarlos como `recorded` o separar del bucle `require` para no sugerir verificación.

**5. Censo del control no consumido por factibilidad** — `:163-169,:191`. Si el control tuviera diferencias de bits mundiales en componentes no seleccionados, el fallo aparecería como ValueError genérico `witness_world_frame_mismatch` → INCONCLUSIVE_DISCOVERY sin diagnóstico. Añadir puerta explícita: `control['summary']['world_bit_differences']==0`, si no INCONCLUSIVE_CONTROL_FRAME.

Menores: `plane_at` con tres techos colineales lanzaría LinAlgError → INCONCLUSIVE_DISCOVERY (aceptable); `in_r1_local_checked_prefix` depende del orden de `named_selections`, igual al que recorrió R1 (`binary:89-92`), correcto.

## Sin tautologías ni falsa precisión detectadas

Las condiciones de plano son redundantes con el dominio enumerado (`:148`), inocuo. Los ULP reportados (`:133`) son los del marco fuente, bien etiquetados. El resultado FEASIBILITY_ONLY no certifica compilación (`:208`), y Water control 700/723 no se toca.

**Identidad:** revisión realizada por Claude Fable 5.1 (claude-fable-5-1), modelo nativo, sólo Read/Glob/Grep, sin ejecución ni escritura.

FIN_REVISION