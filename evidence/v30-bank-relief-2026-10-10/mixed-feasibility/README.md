# EV79 — factibilidad local de tres bisagras mixtas

**Resultado:** las tres perturbaciones de un solo vértice tienen intervalo factible y reducen la suma local de ángulos²; cumplen el límite de pendiente nativa, no crean caras mojadas, no introducen diedros nuevos >30° y no empeoran el máximo local. Es un diagnóstico numérico de tres focos, no un candidato ni una autorización de edición.

Se usó exclusivamente el terreno EV79 `dbc59ec5…`, sus máscaras exactas de soporte mojado/halo de ingeniería, `P`, `F` y los tres anchors de la selección. En cada caso se varió solo el vértice central dentro de `h±2 m`, con piso `max(min(h,1.8), max(P,F,mar)+1e-4)`. Se limitaron las seis caras nativas incidentes a `max(35°, pendiente EV79 original)` y se minimizó la suma de ángulos² en las 40 bisagras del parche de 5×5 vértices. Se verificaron además todas las caras mojadas locales antes/después.

| Anchor (x,z) | h EV79 → h óptimo | Reducción suma ángulos² | Bisagras objetivo antes → después | Nuevos >30° | Máximo local |
|---|---:|---:|---|---:|---:|
| (2196,1578) | 5.9544 → 5.9603 m | 0.00034% | 31.824→31.769°, 31.598→31.542° | 0 | 45.230°→45.230° |
| (5538,3918) | 5.8628 → 6.1254 m | 0.8269% | 31.415→28.918°, 33.871→31.416° | 0 | 44.195°→44.195° |
| (1140,1002) | 4.9054 → 6.0391 m | 13.1122% | 43.499→32.945°, 43.675→33.015° | 0 | 46.841°→46.841° |

En los tres, soporte mojado y halo de ingeniería son falsos en el vértice cambiado, y el número de caras mojadas del parche permanece en cero. **Límite importante:** los tres anchors están fuera de `allowed` EV79 porque esa selección solo cubre Narva. Por tanto el resultado mide factibilidad geométrica local bajo las restricciones indicadas; no autoriza alterar estos vértices en EV79. El foco 1 mejora de forma numéricamente despreciable; los focos 2 y 3 sí reducen las bisagras señaladas, aunque el máximo del parche no cambia porque lo domina otra bisagra.

El optimizador fue acotado 1D con extremos comprobados; no es una prueba formal de óptimo global de un problema multi-vértice. No se generó NPZ, paquete ni resultado de motor. Datos y cálculo reproducible: `single-node-feasibility.json` y `analyze_single_node.py` en esta carpeta.