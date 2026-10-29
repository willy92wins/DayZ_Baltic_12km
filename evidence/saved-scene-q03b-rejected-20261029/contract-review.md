**Dictamen: SOUND-with-fixes.** El contrato es consistente en lo verificable desde las cabeceras y los extractos; los fallos son de especificación incompleta, no de lógica errónea.

**Verificado al leer (sin discovery adicional)**

- Cotas de los cinco arrays cuadran exactamente con el modelo declarado. Prototipos: 539009·96 + 539009·35 + 2·16396 = 70 642 971. Instancias (ids/model_index a 8 bytes, matrix f8): 2 708 336 + 6·16396 = 2 806 712. Selected: 1 995 616 + 3·16396 = 2 044 804. Piloto cs_kit_118_0000: F=3088 caras·106 + B=1520 triángulos·168 + 12 + 35·16396 = 1 156 560. Las cotas son peor caso (i8, f8) y por tanto válidas para i4/f4.
- La prueba grid ≤3B es correcta: strip_mapping exige puntos (n·m,3) y topología completa, luego ningún punto queda huérfano.
- 35 miembros = 6 grupos·4 + 11 extras. Coincide.
- itemsize 35 es correcto para el META empaquetado.
- El oráculo de cero negativo `0000000000000080` es correcto en LE64; obliga a comparación por bytes, no `array_equal`.
- Cadena de poses: piloto → instances.npz (6c0a) por SHA propio y manifest, selected (c2be) comparado por columna exacta. Conforme a la adjudicación.

**Fallos concretos y qué debe cambiar**

1. **Límite de cabecera incoherente.** El contrato fija `npy_header_bytes` 16384 pero las APIs verificadas usan `max_header_size=10000`. Un header de 12 000 bytes pasaría la prelectura y fallaría en `np.load` con excepción genérica, violando "no broad Exception". Fijar un solo valor (recomiendo 10000 en ambos sitios) y que el caso negativo `inflated_header_size` pruebe exactamente ese umbral. Añadir también: para NPY 1.0 la longitud es u2 y para 2.0 u4; la prelectura debe leer magic(6)+versión(2)+longitud(2|4) y rechazar versión 3.0 explícitamente.

2. **Aritmética de conteos sin identidad declarada.** 5443 ≠ 5509 − 72. La lectura correcta es 5509 = 5437 no-vegetación + 72 vegetación, y 5443 = 5437 + 6 proxy-only, con 5515 filas de informe. El contrato debe escribir estas identidades y los espacios de índice: META.model ∈ [0,5443), META.source_model ∈ [0,5509), y qué valor toma source_model para las 6 filas proxy-only. Sin ello `source_face_or_section_out_of_range` no tiene rango contra el que fallar.

3. **Columna META.proxy indefinida.** No se declara sentinel (−1) ni rango (índice en los 7 proxy_paths). `lost_proxy_route` y `proxy_route_cycle` necesitan esa definición. Añadir: proxy ∈ {−1} ∪ [0,7), y kind=2 ⇔ proxy ≥ 0.

4. **Normalización del join nombre-modelo.** coverage_guard compara `norm(model)` con `catalog.name`. El contrato no define `norm` (mayúsculas, separador `/`\`\`, prefijo). Declararlo literalmente; un contraejemplo: `Baltic_Stream_Pilot\cs_kit_118_0000.p3d` debe o bien casar o bien rechazarse, no ambas cosas según implementación.

5. **Orientación: oráculo `winding_reversed` mal acotado.** Los datos reales muestran `exact_oriented_faces: false` para bed y water contra roadway. El oráculo debe aplicar solo a la copia byte-a-byte del binding (orden de vértices preservado), nunca exigir igualdad orientada visual/roadway, o rechazaría datos históricos válidos.

6. **Segundo ejemplar no verificable.** `cs_kit_7_1656.npz` carece de `pilot_specs` (F, B). La cota 980 736 implica 106F + 168B = 406 864, que no se puede despejar sin esos conteos. Incluir sus faces/source_regions o el root debe comprobar la cota con la lista completa antes de autoría.

7. **Verificación del epoch.** `HISTORICAL_PIN_CHAIN` es correcto, pero debe decirse cómo se comprueba: leyendo los hashes dentro de los inputs.json pinneados, nunca rehashando ficheros actuales. `epoch_wrong_pbo` debe mutar el contenido de inputs.json, no un fichero externo.

8. **Casos negativos faltantes** (añadir, no ampliar tolerancias): `npz_start + body_rows > source_grid.n`; `cap_before/after ∉ {0,8}`; `source_category` fuera de {CAP_START, CAP_END, BODY}; dtype de category distinto de `<U9` (la cota 36 B/triángulo asume exactamente eso); `_n` fuera de {3,4}; `pilot_count_zero` (count==0 además de >1); miembro ZIP con bit de directorio o `/`.

9. **Residencia de memoria.** `bytes retained per archive` con 262 MB totales cabe en 512 MiB sólo si no se retienen los 201 pilotos simultáneamente. Explicitar: retener únicamente el archivo en curso más los tres compartidos.

10. **Rutas OneDrive de los manifests.** Pueden ser placeholders en nube o cambiar durante sync. La política before/after lo cubre; añadir que fallo de lectura o atributo offline → INCONCLUSIVE, no excepción.

**Menor:** `review_s` 180 contradice los 120 s solicitados; alinear.

**Separación productor/consumidor:** correcta. El consumidor reabre fuentes y compara cobertura y digest por array; falta prohibir explícitamente que importe `instance_guard`, `coverage_guard` o `META` del módulo productor (solo primitivas de I/O). Añadir a `consumer_bypasses_source_open` un gemelo `consumer_imports_producer_check`.

**Claims:** los cinco falsos se mantienen; nada geométrico se publica; no se certifica marco, exposición, motor ni reparación.

**Siguiente paso:** Root aplica los diez cambios, verifica la cota del segundo ejemplar y la lista completa de 204 arrays, y pasa a autoría del productor con prelectura acotada de cabeceras dentro del mismo proceso.
