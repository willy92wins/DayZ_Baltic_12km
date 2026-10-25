# EV91 author — revisión independiente pre-solve

**Dictamen: READY_FOR_ONE_SOLVE**, solo para la única llamada prevista. No es un PASS de candidato ni de producto. La revisión no ejecutó SLSQP ni escribió terreno.

## Identidad y reanclaje

- `author_ev91.py`: SHA-256 `d17e358e9e9e92952e51e008148b534c2fde4a3ae7fe1e4197fdab4215adc9f1`.
- `plan.md`: SHA-256 `f06e72d568823c5475c301d9baed851619cf0e0b0b4ee5b42eeb0c7cd5ec953f`.
- `prepared.json`: SHA-256 `127b906c1d2a5d2aa09172ed47dac16cd489aae6a2955428a96166a325605877`.
- Guard independiente: SHA-256 `1f1e68cf1b2358c2bb5d21d9268cfd2f030b46b6d7247227bc55be0efe2fc0df`. EV90 preflight: `8c8ec80cbb7029f510c832adf90a8871e385fbd8ec52ee5043d5ea24e1099d63`.
- B: SHA-256 `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`. Se revalidaron los 112 source pins: 0 cambiados y 0 ausentes.

## Guard y cotas

La reconstrucción produjo exactamente 85 variables y 350 stencils, con las poblaciones originales intactas: 107 stencils de collar y 328 bisagras medidas (112 diagonal, 108 vertical, 108 horizontal). El guard fijó a B 43 variables; quedan 42 libres. Se incluyeron los cuatro vértices de cada bisagra cuya máscara EV90 marca como incidente al collar, conforme a `verify_ev90.py:685-693` y el `incident_any` de EV87. El conjunto coincide exactamente con el preflight independiente.

Las cotas físicas float32 inward reconstituidas desde EV90 coinciden exactamente con `prepared.json`. Las cotas del solver difieren solo en el guard, donde ambas cotas se fijan al B correspondiente. B queda dentro de todas las cotas y cumple las 90 filas de descenso preparadas. Los controles negativos confirman que omitir un miembro cambia la identidad del guard y que una perturbación de 1 ULP float32 rompe el pin exacto post-cuantización.

## SLSQP y límites

En GIS Python/SciPy 1.18.1, el gradiente analítico del objetivo coincide con diferencia central con error absoluto máximo `1.5833e-8` en B y tres puntos interiores deterministas. El adaptador real de `LinearConstraint` entrega Jacobiano exactamente igual a la matriz C. SciPy convierte constraints lineales a `fun(x)=A@x` y `jac(x)=A` (`scipy/optimize/_constraints.py:526-538`). Como tanto el gradiente del objetivo como los Jacobianos de constraints son callables, la condición `fd_needed` de `_minimize.py:725-733` es falsa: SciPy no elimina las 43 variables fijas para aproximar derivadas. El solver recibe 85 variables, con 43 bounds iguales y 42 libres.

El worker impone timeout de 120 s y solo permite una llamada. Antes de escribir candidato, el autor exige cotas float32, guard exacto y todas las desigualdades de testigos tras cuantizar (`author_ev91.py:155-177`). El candidato y `authoring.json` siguen ausentes; `prepared-d8-only/` permanece preservado.

El full EV90 más reciente terminó con `FAIL_EV90_OFFLINE_CONSUMER` (attempt-02: forma y dos puertas del collar fallidas). El plan exige que ese full haya terminado, no que sea PASS; el fallo queda explícito y es precisamente el antecedente que motiva el guard. Las puertas del consumidor para EV91 siguen pendientes.

Fuentes de implementación: `author_ev91.py:45-67,101-139,70-98,142-181`; consumidor EV90 `verify_ev90.py:685-693,722-727`; SciPy `_constraints.py:526-538` y `_minimize.py:725-733`. El detalle reproducible y los hashes completos están en `final-author-review.json`.
