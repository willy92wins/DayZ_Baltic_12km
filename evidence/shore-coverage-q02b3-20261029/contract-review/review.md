**Revisor: Fable 5.1 (claude-fable-5-1), CLI nativo, solo lectura. Unidad: contrato Q02B3 (contract-draft.json, oracles.json, output-contract). Veredicto: SOUND-with-fixes.**

**Verificado como coherente (sin ejecutar nada)**

- Conteos del selector sample reconcilian con `expected`: 107678 + 993 repeticiones de cierre = 108671 puntos (fin de chain 1029); 107678 − 37 abiertas = 107641 aristas; 107678×5 = 538390. Chain 85 (5284 puntos, 5285 con cierre, 5284 segmentos) y chain 1029 (2 puntos, 1 arista) cuadran con los offsets.
- Denominador del umbral es 2^78 exacto; floor(2^48·THR) = floor(3022314549036573/2^30) = 2814749 correcto; sqrt2 p48 lo/hi = 398065729532860/…861 correcto (2^48·√2 ≈ …860.75).
- Árbol fixture: m=5, M=8, 15 nodos útiles, 3 hojas padding; los cuatro rangos y las tres sumas dirigidas (27/29, 21/22, 12/13) son correctas, incluido el cruce de costura cerrado y el orden reverse edge=to ([0,4,3], [2,1]) conforme a la derivación.
- Esquema parcial/terminal/manifest internamente consistente: hueco único, cola no verificada no consumible, terminal inválido ≠ hueco, manifest estricto, RESOURCE nunca produce VERIFIED_FULL, crédito 4M compartido árbol+raíces.

**Fallos concretos (pueden producir falso PASS o falso FAIL) y cambio mínimo**

1. **Station literals sin convención declarada.** Usan `a_segment/c_segment/a_t/c_t` (no `from/to/edge` sellados) y en square_seam la estación reverse (0,6) aparece como segment 0, t=3/5: eso sólo es cierto con índice local al prefijo y t medido desde el centro. En índice global de arista sería edge 3 y t a lo largo de 3→0 sería 2/5. open_final_equality igual: c_segment 0 sólo vale en local (global 1). Un implementador puede ajustar la convención hasta que pase. Fix: declarar en oracles.json la convención (global edge + orientación de t de la arista, o local) y hacerla idéntica a la postimagen sellada Q02B2; añadir `direction` explícito o declarar que a=reverse, c=forward.

2. **Cadena RESOURCE_INCONCLUSIVE "sin cache": orden de publicación no fijado.** Si el crédito 4M se agota al construir árbol/raíces tras haber publicado cache.json, el directorio tendrá un archivo que el terminal declara nulo → el consumidor rechaza (archivo extra) o, peor, un consumidor laxo lo acepta. Fix: cache.json sólo se publica cuando raíces+árbol+prefijos completan dentro del crédito; en agotamiento el directorio contiene sólo terminal.json.

3. **Dominio >14000 aristas sin clasificación.** La derivación exige "registro explícito fuera de dominio", pero el terminal sólo admite NUMERIC/DEGENERATE/RESOURCE_INCONCLUSIVE. Un selector con core_count>14000 obligaría a fingir RESOURCE o a abortar. La integradora comprobó totales, no el máximo de core_count. Fix: pinear en contract-draft `max_core_count` (leído de selectors.json) y afirmar ≤14000, o añadir clasificación STRUCTURAL_INCONCLUSIVE con estado propio.

4. **Variante RESOURCE de query contradice "sin claves extra" y "ops int".** El result de recurso lleva `reason` y `ops:null`. Fix: definir dos formas cerradas exclusivas de `result` (normal: sin `reason`, ops int ≤100000; recurso: la literal con nulls); rechazar `reason` en resultado normal y nulls en resultado con estado del núcleo.

5. **Número de shards sin cota.** El productor puede emitir un shard por consulta (538390 archivos) respetando todos los caps. Fix: shard nuevo sólo cuando el siguiente registro excedería 16MiB; cota derivada por cadena: ceil(universe_chain·262144/16MiB)+1.

6. **Claim `map_repaired=false` exigido en header pero ausente del contrato.** Fix: añadirlo a contract-draft (o declarar que el header lo deriva como constante).

7. **Conjunto de imports por rol no pineado.** El texto dice que el consumidor "usa sólo primitivas del consumidor certificado" pero `helpers` lista cinco módulos sin asignación de rol. Fix: tabla productor→{shore_prefix_pilot_ev112, certified_shore_kernel_ev112}, consumidor→{certified_shore_kernel_ev112 (+verify_certified… si aporta estaciones)}; prohibición de importar los restantes verificable en el test negativo.

8. **Degeneración no pineada.** El consumidor recomputa q<THR², pero no hay expectativa externa de cuántas cadenas son DEGENERATE; un mismo error de recomputación en productor y consumidor pasaría. Fix: pinear `expected.degenerate_chains` desde q02b0_report/q02b2 si esos sources lo contienen; si no, declarar explícitamente que no hay oráculo externo de degeneración.

**Menor, no bloqueante**

- Falta oráculo de rango vacío en el extremo [5,5) y de rango que sólo toca padding; coste bajo.
- `expected` no incluye `open_chains:37`; derivable pero conviene literal.
- Las hojas del fixture tienen lo<hi; ninguna hoja lo=0 fuera de padding, coherente con el dominio.

**Dimensiones NO revisadas**

- Ningún SHA256 pineado fue verificado; los 1030 selectores completos y el máximo de core_count no se vieron.
- Contenido de las 54 postimágenes Q02B2 y los 30 oráculos previos.
- Rendimiento (900s consumo para 538390 consultas, 512MiB RSS) y naturalidad/ángulos: fuera de alcance, no se afirma nada.

**Condición de autoría:** aplicar 1–4 obligatoriamente (afectan a validez de PASS), 5–8 recomendados, antes de sellar contract-draft/oracles con el nuevo sello externo.
