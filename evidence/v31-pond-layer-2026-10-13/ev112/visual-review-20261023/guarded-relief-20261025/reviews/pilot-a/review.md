**Veredicto: SOUND-with-fixes.** La matemática del testigo es correcta y las puertas fallan cerradas; faltan un control anti-corona y dos pruebas antes de extender.

**Correcto**
- Suficiencia: para cualquier a∈P, b∈R vale min(P)−max(R) ≤ H(a)−H(b). Elegir a por cota inferior y b por superior solo afecta factibilidad, nunca la validez. `tools/terrain/repair_free_shapes_ev112.py:28-35`.
- Signos: fila +1 en a, −1 en b, rhs = cap − constante. Correcto en `:41-45`. Pits intercambian P/R con `pit_cap` en `:35`.
- Cap por forma = mínimo sobre los puntos P, conservador respecto a cómo `prominence` asigna por p. `:34`.
- Fijos: par fijo-fijo que viola cap lanza error en `:38-39`. Par libre-fijo infactible no se detecta ahí, pero SLSQP falla y `:74` lanza. Fallo cerrado en ambos casos.
- Modo anterior por defecto; `main` no activa `bound_witnesses` en `:110`.
- Verificadores del piloto son independientes del solver y de grid completo: picos/pozos/pendiente/aristas/agua. `pilot_guarded_relief.py:35-46`. Ápice, orilla, carreteras y exterior 24 m exactos tras float32.

**Fallos concretos y correcciones**
1. **Sin gate anti-corona.** El piloto mueve un vértice 0,516 m para apagar un pico de 0,337 m. Nada impide que un vecino libre acabe por encima del ápice fijo, convirtiendo el pico en meseta. Añadir: para picos, max(after[use]) ≤ h0[ápice]; para pozos, min(after[use]) ≥ h0[ápice]. Registrar deltas con signo y conteo subidas/bajadas. `pilot_guarded_relief.py:35-43`.
2. **Prior sesgado.** `prior = gaussian_filter(h0, 2)` incluye el propio pico, así que `energy_decreased` premia parcialmente acercarse a una loma suavizada. Añadir el valor thin-plate puro (sin prior) al report. `pilot_guarded_relief.py:25-26`.
3. **Pruebas insuficientes.** No hay prueba de pozo con `bound_witnesses=True`, ni del caso testigo libre con cotas infactibles que debe terminar en ValueError de `:74`. `tests/test_shape_repair_constraints_ev112.py:55-74`.
4. **Margen float32.** Cap 0,29999 deja 1e-5 frente al umbral; con alturas >64 m la diferencia de dos float32 puede alcanzar 1,5e-5. El verificador fallaría, no daría falso verde, pero para la extensión conviene cap 0,2999 o documentarlo. `:108-109`, `pilot_guarded_relief.py:23-24`.

**Riesgo corona:** mitigado por rings() multiescala, pendiente ≤max(35°,orig), aristas y energía, pero no cerrado sin el fix 1. La sección/malla de `patch.npz` basta para revisión visual futura.

**Extensión:** sí, como candidato offline por grupo, un report por grupo conservando cada fallo (SOLVER_INFEASIBLE, verificador rojo) sin agregarlos ni declarar los 66+15 corregidos. Exponer `--bound-witnesses` en `main` explícitamente, mantener 0,30, protecciones inmóviles, y no desplegar mientras corre la navmesh U2.
