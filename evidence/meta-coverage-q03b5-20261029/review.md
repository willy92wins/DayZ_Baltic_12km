Revisaré contrato, oráculo y las tres unidades frente al plan sin ejecutar nada.

**Veredicto: SOUND-with-fixes.** No encuentro ruta de falso PASS. Encuentro una desalineación oráculo/códigos reales y dos riesgos de rechazo espurio en datos reales.

**Lo que cumple el plan**

- **Universos separados.** Productor `maps` y consumidor `verify` derivan `model` de índices no vegetación del catálogo y `source_model` de índices de secciones. No se funden.
- **Consumidor con lectura propia.** Abre su propia Session, toma `tobytes(order='C')` del META, recomputa SHA frente al payload y recorre por `struct '<iiiiiBBBid'` (35 bytes, sin padding). No importa el productor ni usa `np.unique`.
- **Comparación completa.** `I.same` compara todo el cuerpo con igualdad estructural y distingue tipos, así que `equal=0`, `rows=True`, un `unexpected` ocultado o un conteo co-mutado fallan con REPORT. Filas por grupo se reconcilian con el total real contado por el consumidor, no con checksums autodeclarados.
- **UnknownID.** ID observado fuera del universo queda como `UNEXPECTED_META_ID` con anchor `[rol,id,None,None]`; el mutante `hidden` del test lo demuestra.
- **Pins/epoch/caps.** `load` exige epoch, pins de catálogo/secciones/archivo iguales al scene e967, filas iguales a `prototype_faces`, schemas iguales al descr del scene. `emit` usa `xb` y cap 4MiB sin truncar.

**Hallazgos**

1. **Desalineación oráculo/códigos reales.** `oracle.json` `negative_codes` declara `count: SCHEMA` y `dtype: MEMBER_SCHEMA`. El test `test_dtype_count_and_output_caps` espera `NPY_SHAPE` y `NPY_DTYPE`, y ningún test lee `negative_codes`. Además esos tests mutan el dict en memoria y llaman `P.produce` saltándose `I.load`. Por el CLI real, un dtype o shape alterado en contract.json falla antes en `load` con `SCHEMA` (línea 41 de io). Resultado: `MEMBER_SCHEMA` no lo produce ninguna ruta. Lo mismo con `test_pins...`: `archive.sha256='0'*64` directo da IDENTITY, pero por CLI daría EPOCH porque el pin ya no coincide con el scene. El oráculo no describe el comportamiento del artefacto desplegado.
   - Repro cerrado: contract fixture con `schemas.meta.npy.dtype[0][1]='<u4'`, ejecutar productor por CLI. Esperado según oráculo: MEMBER_SCHEMA. Real: SCHEMA.
   - Corrección: fijar `negative_codes` a los códigos de la ruta CLI y añadir aserciones de test que carguen `oracle.json` y pasen por `I.load`.

2. **Layout del consumidor no anclado al descr.** `LAYOUT` codifica orden `model,source_model,face,section,lod,kind,vertices,flags,proxy,planarity`. Solo se comprueba `itemsize==35`. Si el descr pinned tuviera otro orden de 35 bytes, el consumidor leería columnas equivocadas. No es falso PASS porque el productor usa nombres y la comparación fallaría con REPORT, pero el diagnóstico sería ininteligible. Corrección: en `consume`, `I.need(c['schemas']['meta.npy']['dtype']==[[...lista literal...]],'SCHEMA')`.

3. **Riesgo de rechazo espurio por nombres.** `maps`/`verify` exigen IDENTITY entre nombre de catálogo y de secciones para cada índice compartido, con normalización de barras y minúsculas. Si el writer ev112 guarda rutas con prefijo distinto en ambos JSON, el productor rechaza todo con IDENTITY y no habrá testigos. El plan solo pide un mapa índice/nombre ligado por SHA, no esta igualdad. Recomendación: degradar a informar `name_mismatch` como hecho en el mapa, no como rechazo. Es cambio de contrato menor; decidirlo antes de producir.

4. **Cardinalidad de `proxy` no acotada.** Las tablas son por `(kind,lod,proxy)` incluyendo cada proxy distinto. El productor hace una máscara booleana completa por tripleta (`derive` línea 25). Con miles de proxies distintos: miles × 539009 comparaciones y un informe con conteos por modelo dentro de cada grupo. Puede exceder 60s o 4MiB. Ambos fallan cerrados (OUTPUT_CAP, timeout), no falso PASS, pero el plan dice "rechazar sin truncar" y entonces la unidad no entrega testigos. No se conoce la cardinalidad real sin abrir el NPZ histórico; dejarlo anotado como riesgo de presupuesto.

5. **`np.unique` sobre vista multi-campo.** `meta[['kind','lod','proxy']]` devuelve vista con padding e itemsize 35. Versiones antiguas de NumPy comparaban bytes de relleno. Si ocurriera, aparecerían tripletas duplicadas, la suma de filas superaría el total y `derive` falla con SCHEMA. Fail-closed; el fixture ya ejercita esta ruta con el mismo dtype.

6. **Pins declarados pero no verificados.** `oracle_sha256` y `plan_sha256` están en el contrato y no se leen en `load`. No afecta al resultado; es trazabilidad. `writer` y `failure` sí se leen y verifican por SHA.

**Memoria.** Session carga vertices (51.7MB) y META (18.9MB) simultáneamente, más copia `tobytes` (18.9MB) y dos snapshots del zip (4.7MB cada uno). Estimación bajo 256MiB, pero RSS no medido; el plan ya lo admite.

**Recibos de fallo.** `main` emite `failure.json` con `code` de `Rejected`, `ArchiveError` o `HeaderError` y relanza. Coherente con el plan.

**Qué no se aprueba por conteos.** Los siete tests verdes son fixtures de cinco filas con el mismo dtype. Cubren mutantes del informe y pins, pero no la ruta CLI para dtype/shape ni la igualdad de nombres contra los JSON reales.

**Resumen.** Código y contrato respetan el plan: roles separados, consumidor con offsets propios, UnknownID visible, igualdad no debilitada. Requiere antes de producción: alinear `negative_codes` del oráculo con los códigos reales por CLI y testearlos por `I.load`, anclar el `LAYOUT` al descr literal, y decidir si la igualdad de nombres catálogo/secciones es rechazo o hecho informado. Riesgo de presupuesto por cardinalidad de `proxy` queda anotado, sin mitigación posible sin abrir el NPZ.
