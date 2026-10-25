# EV112 — corregir restricciones innecesarias en grupos pendientes

Continuación de la corrección autorizada. GuardedD queda preservado: publicado,
compilado y probado con4292 controles. No mover alturas protegidas ni cambiar
umbrales, radio24m o delta0,75m. Segundo cálculo de navegación se hará sobre la
última versión validada; todavía no está lanzado.

Descubrimiento: de8 fallos SLSQP,5 conjuntos de testigos lineales son incompatibles
y3 factibles. Esto solo describe los testigos suficientes elegidos, no la
infactibilidad de la prominencia real. Inicializar los3 factibles desde una
solución LP no resolvió ninguno. Experimento separado: conservar los testigos
originales cuando la forma ya cumple y usar cotas alcanzables solo cuando
incumple resuelve4 clústeres (10,11,38,39),6grupos,113alturas. Todos los controles
del autor pasan, pero el resultado sigue EXPERIMENTAL_NOT_ACCEPTED.

[DESIGN] Opción explícita `preserve_satisfied_witnesses` en `fair_native_patch`,
solo con `bound_witnesses`. Predeterminados sin cambio. Para cada desigualdad,
si min(originalP)-max(originalR)≤cap, conservar ese par; si no, elegirlo por
límites alcanzables como D. La desigualdad del par sigue siendo suficiente
para min(P)-max(R), independientemente de que luego cambie el extremo real.
No añadir un umbral nuevo ni tolerancia a la decisión.

[DESIGN] El autor acepta un candidato anterior fijado por hashes y una opción
híbrida. Conserva exactamente las alturas ya cambiadas por D y sus grupos
aceptados. Solo reintenta los clústeres SOLVER_FAILED, contra las mismas cotas
y base original. El clúster rechazado por energía queda pendiente. Guardar
identidad del candidato heredado y método por clúster. La composición completa
debe pasar todas las puertas globales; no sumar dos PASS locales.

Antes de integrar: fixture real del clúster10 con prueba negativa del modo
anterior y verificación independiente de prominencia/aristas/fijos en el modo
nuevo; suite completa. Revisión Fable del plan, código y evidencia. Después
huella de agua exacta/bury0, P11 y bordes nativos, nuevo censo completo, auditoría
de todos los extremos protegidos, bosque y fuente/compilación/sonda ampliada.
El delta D debe permanecer exacto. Fallo de cualquier puerta impide desplegar E.

Un candidato compuesto inicial y una reparación motivada como máximo; si no
mejora, conservar D y registrar el discriminador. No repetir warm-start ni
reducir protecciones. Vista, carreteras físicas, navegación y rendimiento siguen
siendo puertas independientes.

Revisión Fable 5.1: SOUND-with-fixes. Se fijan por separado hashes de terreno
y dominios retenidos, se comprueban las máscaras y su procedencia y se conserva
la unión de la capa de retoque. Si el contexto acolchado de un clúster pendiente
contiene alturas cambiadas por D, no se reintenta contra la base antigua. Esto
deja el clúster39 pendiente: su contexto contiene6 alturas de D. Los6 grupos
del experimento aislado no se presentan como6 mejoras integradas. El candidato
formal y sus consumidores globales determinarán cuántos se pueden aceptar.
Los hashes del experimento instrumentado no sustituyen los del autor y solver
reales usados para producir el candidato formal.
