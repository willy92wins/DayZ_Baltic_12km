**Dictamen: SOUND-with-fixes. Convergencia: CONVERGE.** Una corrección mínima en el productor más un negativo exacto; el resto del contrato, oráculos y ambos caminantes se sostienen sin cambios de alcance.

## Validación del repro del integrador

El delta propuesto es correcto y está bien acotado. Razonamiento:

- En `terrain_water_producer_q03c2r1.py:58` el invariante `0<=nofoot<=uncovered<=regarea` encadena tres comparaciones de orden entre Fractions no nulas. Python las resuelve con producto cruzado interno sin pasar por `Budget.cmp`, así que ni se contabiliza el tick ni se aplica la cota de bits que el sellado exige en `selected_water_io_q03c1.py:66`.
- Los operandos del repro (41 bits cada uno, cap 64) ilustran exactamente la divergencia: la vía sellada devuelve RESOURCE_INCONCLUSIVE, la comparación cruda devuelve un booleano. En el productor eso convierte un terminal que debería cerrarse como RESOURCE_INCONCLUSIVE en una posible ruta INTERNAL_ERROR, o en un DEFINED cuyo `stats.ops` subcuenta trabajo. No es un error aritmético; es una violación del presupuesto declarado como contrato.
- El alcance es preciso: todas las demás comparaciones crudas del código nuevo son contra cero (`terrain_water_producer_q03c2r1.py:36,45,48,53`; `terrain_water_consumer_q03c2r1.py:22,40,58,67,69,71`). Comparar una Fraction con cero inspecciona solo el numerador, sin producto cruzado, igual que hacen las primitivas selladas en `clip` y `half`. No requieren cambio. El único punto que compara dos racionales no nulos sin `q.cmp` es la línea 58. El consumidor ya usa `q.cmp` en su invariante equivalente (`terrain_water_consumer_q03c2r1.py:74`), así que el fix también restaura la simetría de política entre caminantes.

## Fixes mínimos con anclas

1. **Productor, línea 58.** Sustituir la cadena por comparaciones contabilizadas:

```python
I.need(q.cmp(nofoot,F(0))>=0 and q.cmp(uncovered,nofoot)>=0 and q.cmp(regarea,uncovered)>=0,'INTERNAL_ERROR','water remainders')
```

Un RESOURCE_INCONCLUSIVE lanzado aquí ya cae dentro del `try` y se captura en la línea 65, produciendo el terminal correcto.

2. **Suite, negativo exacto.** Añadir un test cerrado que fije el comportamiento del presupuesto con los operandos del repro y que detecte la regresión del productor sin tautología geométrica:

```python
def test_budget_comparison_is_counted(self):
 q=S.Budget({'bits':64});a=S.F(1099511627775,1099511627777);b=S.F(1099511627773,1099511627779)
 self.assertFalse(a>b)  # comparación cruda no acotada
 self.reject(lambda:q.cmp(a,b),'RESOURCE_INCONCLUSIVE')
 code=(D/'terrain_water_producer_q03c2r1.py').read_text()
 self.assertNotIn('0<=nofoot<=uncovered<=regarea',code);self.assertIn("q.cmp(regarea,uncovered)>=0,'INTERNAL_ERROR'",code)
```

El `assertNotIn` es el negativo contra la preimagen; el `assertIn` ancla la postimagen. Cuenta 16 métodos tras la corrección.

Ambos cambios son adjudicables por el integrador en una sola pasada; no tocan contrato ni oráculos, por lo que los SHA congelados de `contract.json` y `oracle.json` se mantienen. Solo cambia el SHA del productor y del test.

## Otros problemas revisados y descartados

- **Rango de celdas.** El productor usa `floor(xmin/step)-1` (`terrain_water_producer_q03c2r1.py:26`) y el consumidor `ceil(xmin/step)-1` (`terrain_water_consumer_q03c2r1.py:27`). El productor puede visitar una columna extra en el lado bajo. Es trabajo redundante con intersección vacía, nunca un contacto espurio. Solo afecta a la cota de 1024 celdas de forma asimétrica; el consumidor trata esa divergencia como "unverified", no como REPORT. Aceptable, no bloquea.
- **Convención de ranuras.** Productor: `delta=bp-hp`, clip positivo a ranura 0; agua `wd=wp-bp`, clip positivo es cobertura. Consumidor: mismo `delta`, `difference>0` a ranura 0; `cover` si `wd>=0`. Las nueve áreas coinciden en definición y los oráculos planos lo confirman (bed 1 sobre terreno 0 con agua a 1 cae en la ranura 0).
- **Diagonal y filas.** Tríángulos `(0,1,3),(0,2,3)` en el productor y `[nw,ne,se],[nw,sw,se]` en el consumidor describen la misma diagonal NW-SE. La fila 0 es el norte (`top-rr*step`) en ambos. El oráculo `noncoplanar_diagonal` (9/2 frente a 9/4) y el mutante de diagonal del test 67-71 discriminan realmente.
- **Ceros con signo y épsilon.** `float(grid.h[...])` seguido de `q.val` con `as_integer_ratio` convierte -0.0 a 0 exacto. `near_zero_not_contact` y `negative_zero_contact` cubren ambos lados sin tolerancia.
- **Contactos frontera.** Ambos caminantes registran contacto solo cuando la intersección es no vacía con área cero, con el mismo deduplicado de vértices consecutivos y de cierre. El test 47-50 exige igualdad semántica incluida esa lista.
- **Subclase Budget.** `hold` fija el estado retenido y `reserve` lo suma; las primitivas selladas llaman a `q.reserve` sobre la instancia, así que el retenido se propaga a sus reservas internas sin modificar el código sellado.
- **Reservas de retención.** La constante de `terrain_water_io_q03c2r1.py:57` reproduce exactamente `height_load_peak_charge` del contrato y queda bajo los 64 MiB declarados.
- **Guardia de vista.** `view_input` compara la ruta canónica antes de cualquier apertura ZIP, y el test 83-88 verifica con parche que `zipfile.ZipFile` no se invoca en la ruta rechazada. El SHA del original 815ef8 solo aparece como `source_sha256` en los pins del informe, nunca como ruta abrible.

## Riesgos que no cierra esta revisión

- **Marginal Q03C1.** `check_marginal` exige igualdad exacta entre `water_marginal` y `metrics.faces[i].areas`. Se asume que Q03C1 serializa sus tres áreas en el orden cubierta, pie sin cobertura, fuera. Si el orden difiere, el gate real falla con REPORT. Es un fallo seguro, no silencioso, pero el primer gate real debe esperarlo.
- **Sin geometría real todavía.** Los 15 (16 tras el fix) métodos corren solo sobre literales. Los resultados de los 1520 lechos contra 4760 aguas y la vista 16873c siguen siendo claims no evaluados, como declara `CLAIMS`.
- **Comparaciones crudas en primitivas selladas.** `clip` y `half` comparan contra cero, lo cual es barato; pero `subtract` y `area` encadenan operaciones que sí pasan por `q`. No hay otra comparación de orden entre no nulos fuera de la línea 58 del productor en el código auditado.

## Recapitulación

El repro cerrado del integrador identifica un defecto real de fidelidad de presupuesto, no de aritmética, localizado en la única comparación de orden no contabilizada del código nuevo. El fix en `terrain_water_producer_q03c2r1.py:58` y el test negativo propuesto bastan; contrato y oráculos no cambian. Tras la postimagen, el siguiente paso es el gate real con pines, marcador exclusivo y runner de 120 s y 512 MiB por proceso, con atención al orden del marginal Q03C1.
