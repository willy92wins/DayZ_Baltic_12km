Ya tengo todo lo necesario; redacto el veredicto.

**Veredicto: SOUND-with-fixes** (una corrección antes del único candidato).

**Corrección única (mecanismo exacto, sin ejecutar)**

Los pins de la spline se calculan con una protección incompleta. En `tools/quality/small_native_water_pilot_ev112.py:96` se evalúa `pin` leyendo `fixed`, cuyo último `|=` previo es el de cruces en la línea 93. La congelación de celdas de otras cadenas y sus vecinos S6 ocurre después, en las líneas 105-108. Por tanto, cualquier arista del contorno 769 cuyos dos extremos queden congelados sólo por vecindad al islote 772 o a una cadena vecina no se pinea, aunque el plan (líneas 46-47 y 112-114) exige pins para "todas las protecciones". Consecuencia: el objetivo puede exigir desplazar la orilla donde la altura no puede cambiar. El consumidor lo detectaría como codo o wiggle (FAIL legítimo, no falso PASS), pero gastaría la única generación permitida, y `pin_fraction` en context.json quedaría subestimado frente a FIXED_FRAC_MAX. Arreglo mínimo: mover el bloque de las líneas 105-108 antes de la línea 95 y calcular `pin` con el `fixed` final; luego regenerar el target_file con el mismo procedimiento determinista (la guarda `reviewed_target_changed` de la línea 103 lo exigirá) y volver a ejecutar prepare, porque `source_hashes` incluye el propio autor y cualquier edición invalida el contexto. No altera umbrales ni tolerancias.

**Correspondencia plan/código verificada**

- Dominio sólo mar: `native_sea_only` (línea 72) exige pond=false y lev=.75 en todos los segmentos de la cadena. Charcas: comprobación de celda completa frente al polígono relleno con `poly.distance(square) > 15` (121-125), y esquinas de plane y env_plane congeladas globalmente con c2v (línea 90). El verificador repite la invariancia de esquinas en `footprint_guard` (82-88) para los cuatro desplazamientos.
- Desplazamiento ≤9 m medido con muestras a 0.1 m más margen 0.05 m (78-80): correcto por Lipschitz-1 de la distancia.
- Pendiente de rampa: mediana de |H-.75|/distancia a la orilla original en 0<d≤9, acotada a .05/.35 (141-144). B0/B1 9/15 con smoothstep (169-170). Collar referido al objetivo, exclusión `otherdistance >= distance` (118). Fuera del collar H bitexacta por `allowed`, y `delta_guard` lo exige (verify 102-103).
- Lado B: `side_requirements` reproduce la regla del autor anterior en shore_ramp_v31.py:584-594 (protegidos con |D|>.1, unanimidad, conflicto libre) y la proyección SIDE_CLR=.05 (shore_ramp_v31.py:98-100, 836-838) como .80/.70. El verificador lo comprueba sobre float32 guardado (verify 105-106); el test `test_side_is_checked_on_saved_heights` cubre el caso límite .79.
- Islas: contención poligonal, no de centroide (136-140); el islote queda congelado por la dilatación S6 de sus celdas, y la biyección de componentes secos (verify 44-56) detecta hundimiento. Probé el argumento de aislamiento: toda cara que comparte arista con una cara de otra cadena tiene sus tres vértices en V0∪S6(V0), luego ningún segmento nuevo puede compartir clave de arista con otra cadena; `untouched()` (161-169) además exige p/key/pond/lev idénticos para los 107641 menos los de 769.
- Componente húmedo/seco: biyección por solapamiento con supervivencia, no por contadores; los tests de unión+creación y división+borrado con igual recuento fallan por la causa correcta.
- Regeneración independiente: `extract_segments` heredado sobre el candidato y `native.segments` con `expected_faces` sobre el universo completo (verify 151-154); número libre de segmentos, como pide el plan.
- Cierre/rectas: `closed_screen` recorre todas las rotaciones del anillo, simplifica a .25 m y calcula giros cíclicos (verify 66-77); el test de esquina de cierre en todos los arranques lo demuestra. Igualdad exacta `p[0]==p[-1]` es segura: las aristas compartidas se evalúan con los mismos operandos y orientación en ambos triángulos (shore_ramp_v31.py:192-203), así que los extremos son bit-idénticos.
- Pendiente 35°/.01: `slopes` coincide con `tri_slopes` de ambos módulos heredados. Prominencia: regla "nuevo >.30 o aumento donde ya >.30" aplicada por separado a picos y pozos con `despike_v31.prominence`.
- Wiggle: WIG_W=12, WIG_STEP=.5, límite max(.08, .5·p90 antes), NaN rechazados por `wiggle_coverage`.
- Metadata: `array_keys` exige exactamente las claves previas más la máscara nueva; todo array no-heights bitexacto por `tobytes`; `change_mask` impide ocultar deltas.

**FAIL legítimo frente a falso PASS**

Las vías de rechazo que un candidato real puede activar son legítimas: `pilot_contour_identity` (fusión o fragmentación), `abrupt_turns`, `wiggle_not_reduced`, `side_*`, `component_bijection_*`, `slope_regression`, `prominence_regression` y `degenerate_contour` (un vértice que caiga exactamente en .75 produce segmentos de longitud cero, que el plan rechaza). No encontré una vía de falso PASS: el contorno final se extrae de las alturas guardadas, no de la spline; las protecciones y el dominio van ligados por hash antes de autoría.

**Notas sin cambio obligatorio**

- Los límites 120 s/1 GiB y 300 s/2 GiB se registran en segundos pero no se imponen ni se mide memoria; el ejecutor debe declarar INCONCLUSO manualmente si se superan. La distancia a `otherline` (MultiLineString de ~107 k líneas) por punto de ROI es fuerza bruta; aceptable para una charca pequeña.
- `closed_screen` repite .25/45/60 en lugar de leer `shape_patterns_ev112.POLICY`; los valores coinciden y no se cambian.
- El plan (línea 83) pide registrar cambios por anillo; el informe sólo da el delta máximo.
- No hay fixture para `untouched()` ni `contour()`; dependen del universo real y quedan cubiertas sólo por la ejecución del candidato.

**Siguiente paso**: aplicar la corrección de orden de pins, regenerar target_file, re-preparar y generar el único candidato con sigma 12.

FIN_REVISION
