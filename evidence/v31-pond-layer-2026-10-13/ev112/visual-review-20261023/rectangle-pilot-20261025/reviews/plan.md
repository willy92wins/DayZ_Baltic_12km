**Veredicto: SOUND-with-fixes.** El mecanismo encaja y las puertas son coherentes con E, pero la evidencia de factibilidad del LP no cubre el contrato que el plan va a resolver. Hay una puerta omitida y una fix.

**Mecanismo verificado**

- El detector mide exactamente la segunda diferencia centrada por eje que el plan acota, con umbral .30 y etiquetado 8-conexo (`tools/quality/shape_patterns_ev112.py:133`, umbral en `:17`). La caja [906,484,911,490] del hallazgo coincide con filas 906..910 y columnas 484..489 (`shape-screen.json:20124`). El cap .2999 deja margen 1e-4, muy por encima del error float32 a alturas < 3 m.
- La restricción es lineal en alturas y el solver ya admite un bloque `LinearConstraint` junto a pendiente y pliegue (`tools/terrain/repair_free_shapes_ev112.py:79-80`). Añadir un bloque opcional es compatible sin tocar prominencia, pendiente ni pliegue.
- `crown_bounds` solo estrecha lo/hi con extremos protegidos del recorte (`tools/terrain/repair_guarded_shapes_ev112.py:21-34`, aplicado en `:107-110`). Reutilizable tal cual.
- El diagnóstico leyó el E merged publicado y la máscara libre de E, y no escribió terreno (`diagnose_rectangle_bounds.py:8-9`, hash coincidente con `HANDOFF.md:9`).

**Puerta omitida: el LP no certifica el contrato del plan**

- Dominio distinto. El LP liberó todo vértice libre en la ventana caja±4 en Chebyshev (`diagnose_rectangle_bounds.py:14-15`). El plan dice "dentro de 24 m del componente", que con la convención del autor guardado es euclídeo desde los vértices del componente (`repair_guarded_shapes_ev112.py:63`). Es un subconjunto, y un subconjunto puede ser infactible.
- Restricciones ausentes. El LP solo acotó stencils dentro de la caja (`diagnose_rectangle_bounds.py:21-23`) y usó límites ±.75 y suelo sin corona (`:16`). El plan añade "fuera de la caja no empeorar ni introducir" y la corona de extremos protegidos. Ninguna estaba en el LP.
- Formulación ambigua fuera de la caja. "No empeorar" debe incluir stencils cuyo centro es fijo pero cuyo vecino es libre, y conviene la forma unilateral: si d0 > .3, imponer -.2999 ≤ d ≤ d0, no |d| ≤ |d0|, para no permitir cambios de signo.

**Fix única propuesta**: antes de tocar el solver, repetir el LP de solo lectura con el contrato exacto (dominio euclídeo 24 m, lo/hi con `crown_bounds`, filas unilaterales fuera de la caja para todo stencil que toque un vértice libre) y condicionar la unidad al resultado. Si es infactible ahí, el piloto termina sin candidato, como ya prevé el presupuesto.

**Notas no bloqueantes**

- El plan no nombra el autor. El guardado exige grupos pico/pozo (`repair_guarded_shapes_ev112.py:57-62`), así que hace falta un autor nuevo con `bound_witnesses=True` y caps `max(pk0,.2999)` como en `:113-117`.
- Cambiar `fair_native_patch` altera el hash del solver fijado por el replay de E (`evidence/.../hybrid-relief-20261025/replay/proof.json:9`). Aceptable si el kwarg nuevo tiene default None sin cambio de ruta, los 159 tests pasan intactos y el piloto registra ambos hashes.
- El diagnóstico escribió dos JSON dentro del directorio candidato E (`diagnose_rectangle_bounds.py:42`). Con navE en curso, toda salida del piloto debe ir a un directorio nuevo.
- Ninguna invariante es demasiado floja; "toda la caja" es más fuerte que lo que exige el detector, pero es la lectura honesta y debe mantenerse.

**Primera unidad**: LP con contrato exacto en directorio nuevo. Si pasa, `extra_linear=None` en el solver, autor del piloto con fixture que falla el stencil y lo corrige sin mover fijos, negativo de infactibilidad, y control float32 independiente con `rectangle_components` sobre la rejilla completa más las comprobaciones existentes de E.