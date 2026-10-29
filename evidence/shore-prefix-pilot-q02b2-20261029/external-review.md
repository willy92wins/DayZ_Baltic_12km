**Veredicto: SOUND-with-fixes** (sin brechas de falso PASS halladas; los fixes son de robustez, no bloqueantes). Revisión estática sin ejecutar, limitada a los dos archivos.

**Lo que verifiqué y cierra bien**

- **Localización equivalente productor/consumidor.** Con aristas no degeneradas (lo ≥ 2^48·1e-8 > 0) los prefijos son estrictamente crecientes, así que la condición interior S.hi<h<N.lo y la condición de vértice exacto S==h sólo pueden cumplirse en un único índice. La búsqueda binaria del productor (`_locate`, línea 181) deja ese índice exactamente en lo_i, dentro de la ventana ±2; el consumidor lo encuentra por recorrido lineal. El caso h==total exacto sólo aplica a abiertas y no puede colisionar con el bucle. Los índices de arista hacia atrás (ei=to) coinciden en `_dir_edge` y `_edge_at`.
- **Wrap cerrado en `_dir_pref`** (líneas 143-150): para k≤m con center<m las dos ramas suman exactamente el rango dirigido; k=m devuelve el perímetro completo. No hay resta intervalar cruzada.
- **Soporte bilateral.** Abiertas: cualquier lado INSUFFICIENT domina. Cerradas: 2h<P estricto en ambos. Idéntico en ambos archivos.
- **h=0.** Ambos devuelven estaciones A y C en el centro con t=0, cuerda cero, estado UNDEFINED_ZERO_CHORD. Coherente.
- **Binding.** Puntos de la cache ligados a la fuente NPZ por hash de core y por igualdad exacta de Fraction (`pointsbind`), meta ligada con contract_sha256, cache reencodeada comparada byte a byte (`cacheexact`), testigos floor/ceil verificados por desigualdad entera, prefijos y degenerados recomputados. Helpers sellados por SHA en ambos lados.
- **Presupuestos.** `_strip_ops` exige ops ≤100000 en el reporte; el consumidor usa su propio cap y descarta ops en la comparación, conforme al contrato. Bits comprobados antes de cada suma entera. Los `Res`/`Cap` se traducen a Resource, nunca a Bad ni a PASS.

**Fixes recomendados (ninguno produce falso PASS)**

1. **Perímetro recomputado por recorrido** en `verify_shore_prefix_pilot_ev112.py` (`_dir_total`, línea 132). Para la cadena cerrada de 13421 aristas cuesta ~40k ticks por consulta antes de localizar. Con 100000 ops cabe, pero el margen es ajustado si `V.CapB` tica también en cada `cmpf`. El consumidor ya validó pref_lo/pref_hi; puede usar pl[m]-pl[0] con un tick. Riesgo: INCONCLUSIVE_RESOURCE, no falso PASS.
2. **Strip del punto repetido** en `build_cache` (línea 77). El core ya viene sin repetido; si por casualidad el primer y último punto del core coincidieran, el productor quitaría un vértice legítimo y el consumidor fallaría con `pointsbind`. Falla cerrada, pero conviene eliminar ese strip o convertirlo en `Bad`.
3. **Codificación de estaciones y soporte.** El consumidor usa claves `from_point`/`to_point` en `_enc_station` y construye `sup_enc` a mano; el productor delega en `K.enc_station`/`K.enc_support`. No puedo confirmar desde estos dos archivos que las claves coincidan. Un desajuste haría fallar todo reporte válido (`querymismatch`), no aprobarlo. Conviene un fixture que compare ambos codificadores.
4. **Global `_QB`** no se restaura tras `query`. Inofensivo hoy porque sólo lo leen `_range` y `_dir_pref` dentro de `query`, pero es frágil; resetear a None en salida.
5. **Línea 85 del consumidor** (`cap.n > COPS`) es redundante con el tick del cap; no daña.

**Supuestos declarados** (no verificables aquí): `K.Budget` y `V.CapB` lanzan `Res`/`Cap` al superar 100000; `verify_witness` comprueba lo²≤q·2^96<(lo+1)² y el análogo ceil; `compute_features` y `features` son equivalentes por el sellado previo. Si alguno falla, el efecto es fallo cerrado, no aprobación indebida.

**Siguiente paso:** ejecutar el piloto y el consumidor sobre el NPZ pinneado; el primer punto de fallo esperable, si lo hay, es `querymismatch` por claves de codificación o `walkops` en la cadena cerrada grande.