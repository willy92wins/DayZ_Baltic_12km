# Factibilidad local acoplada de orilla: FEASIBLE

LP offline sobre dos parches 7×7; anillo externo fijo a B. No se guardó un terreno candidato.

| Foco (x,z) | Altura B | Interior elegible | Cota delta |
|---|---:|---:|---:|
| (1146,1002) | 6.325840 m | 21/25 | [-2.000000, 0.000000] m |
| (2196,1572) | 6.156673 m | 18/25 | [-1.723764, 0.000000] m |

Nodos variables: 39; aristas 8-vecinas tocadas: 220; restricciones de cruce P/F: 222.

## Resultado LP

- Minimizar foco [1880, 191]: factible, delta foco -1.715434 m; ambos deltas {'(1880, 191)': -1.7154335975646973, '(1785, 366)': -0.1}; violación máx 0.00e+00 m.
  Nodos con delta no nulo (28): (1134,1014) -0.0830m, (1140,1014) -0.0160m, (1146,1014) -0.1941m, (1152,1014) -0.4434m, (1158,1014) -0.2491m, (1134,1008) -0.1611m, (1140,1008) -0.4545m, (1146,1008) -0.4219m, (1152,1008) -0.3386m, (1134,1002) -0.4103m, (1140,1002) -0.7464m, (1146,1002) -1.7154m, (1152,1002) -0.8036m, (1134,996) -0.7245m, (1140,996) -1.5151m, (1146,996) -1.2623m, (1134,990) -0.0363m, (1140,990) -0.5568m, (2184,1584) -0.0175m, (2190,1584) -0.1513m, (2196,1584) -0.5356m, (2202,1584) -0.4609m, (2208,1584) -0.2876m, (2184,1578) -0.2142m, (2190,1578) -0.5222m, (2196,1578) -0.0650m, (2208,1578) -1.0989m, (2196,1572) -0.1000m
- Minimizar foco [1785, 366]: factible, delta foco -1.560572 m; ambos deltas {'(1880, 191)': -0.1, '(1785, 366)': -1.5605716705322266}; violación máx 0.00e+00 m.
  Nodos con delta no nulo (26): (1134,1014) -0.0830m, (1140,1014) -0.0160m, (1146,1014) -0.1941m, (1152,1014) -0.4434m, (1158,1014) -0.2491m, (1134,1008) -0.1611m, (1140,1008) -0.4545m, (1152,1008) -0.3386m, (1134,1002) -0.4103m, (1146,1002) -0.1000m, (1152,1002) -0.8036m, (1134,996) -0.7245m, (1134,990) -0.0363m, (2184,1584) -0.0175m, (2190,1584) -0.1513m, (2196,1584) -0.5356m, (2202,1584) -0.4609m, (2208,1584) -0.2876m, (2184,1578) -0.2142m, (2190,1578) -0.5222m, (2196,1578) -1.5255m, (2208,1578) -1.0989m, (2184,1572) -0.6844m, (2190,1572) -1.0635m, (2196,1572) -1.5606m, (2202,1572) -1.2330m

## Alcance y límites

- Las restricciones de orden comparan la nueva altura de cada arista 8-vecina tocada con su orden en B; igualdad exacta en B permanece como igualdad.
- Fixtures: se enumeran los ocho vecinos del nodo variable, incluido el fijo lexicográficamente anterior; se valida la fila real de orden con ese vecino fijo. El delta cero se comprueba directamente contra bounds, `A_ub/b_ub` y `A_eq/b_eq` antes de imponer los descensos objetivo. El solver solo debe devolver una solución factible/óptima; no se exige que una solución de objetivo cero sea el vector cero.
- Se usó el contrato original EV79 +/-2 m + suelo físico (EV82 `original_budget_interval`, autor.py:372-379), intersectado con no-raise respecto a B y la banda escalar de cruce <=1 m. No se usaron `constraints.lower/cap` como bounds: esos arrays codifican el veto histórico de `wet_support` y congelarían ambos focos. El anillo de cada parche permanece fijo.
- `wet_support` no veta nodos por sí solo; los demás filtros semánticos sí se aplican por separado.
- El resultado es solo una respuesta a factibilidad de este LP local. No prueba gates angulares, cuantización float32, cobertura del consumidor ni mejora visual.

Fuentes principales: EV83 `author_pilot.py:38-86` (intervalos de cruce); EV79 `author.py:14-46` (máscaras y lower/upper); fuente EV79 `constraints.npz`; B/EV79 y P/F hashes registrados en `feasibility.json`.
