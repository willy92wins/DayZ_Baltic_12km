# Propuesta: restricciones de descenso por vecino testigo

## Corrección de ancla de entorno

La revisión inicial informó SciPy 1.17.1 leyendo el Python global de usuario (`C:\Users\guill\AppData\Roaming\Python\Python314\site-packages`). Esa versión **no es el runtime GIS y la afirmación anterior fue errónea para esta implementación**. La verificación corregida usa exclusivamente `C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe`: SciPy 1.18.1 (`...\gis-env\Lib\site-packages\scipy\__init__.py`), NumPy 2.5.3. Se volvió a calcular el footprint con ese mismo ejecutable; los conteos y la factibilidad abajo se mantienen. El dato 1.17.1 se conserva aquí como linaje de la revisión anterior, no como ancla operativa.

## Dictamen y construcción congelable

El filtro elimina por construcción mínimos estrictos nuevos en todo centro cuyo stencil 3×3 toque cualquiera de las 85 variables. Conserva el funcional cuadrático y las cotas físicas actuales. En la instancia EV90, B es factible: los 85 valores están en sus intervalos inward; margen mínimo B−L = 0 m y mínimo U−B ≈ 0.2139802 m. No se ejecutó ningún solver.

Sea V el conjunto congelado de 85 nodos y Affected los centros para los que i o alguno de sus ocho vecinos pertenece a V. Usar contexto completo de evaluación, incluidos centros fijos del collar: el footprint actual contiene 135 centros. Para cada centro que no era mínimo estricto en B, elegir el testigo `j = argmin (B_j, row_j, col_j)` entre sus ocho vecinos y añadir `H_j ≤ H_i`. Se omiten las seis posiciones que ya eran mínimos estrictos en B. No añadir margen positivo.

Codificar como filas lineales `C x ≥ d`: ambos nodos variables: `+x_i − x_j ≥ 0`; solo i variable: `x_i ≥ B_j`; solo j variable: `−x_j ≥ −B_i`. Si ambos están fijos, comprobar `B_j ≤ B_i` y omitir la fila constante. En los datos actuales hay 129 testigos no estrictos: 90 filas no triviales (59 variable-variable, 21 centro variable/testigo fijo, 10 centro fijo/testigo variable) y 39 fijo-fijo redundantes. El grafo de testigos escogido no tiene ciclos no triviales en este footprint.

La condición basta: un mínimo estricto nuevo exigiría que los ocho vecinos de i fueran mayores que H_i, contradiciendo la desigualdad del testigo. B satisface todas las desigualdades por definición y las cotas en los 85 nodos, por lo que sirve como punto inicial factible. Los centros fuera de Affected conservan centro y vecinos.

Esto no obliga a levantar un terraplén: no exige elevar alturas ni una separación positiva, y B ya es factible. El óptimo sí puede subir o bajar alturas por el funcional original. Un ciclo de testigos solo puede ocurrir en una meseta B y fuerza igualdad H a lo largo del ciclo; puede prolongar una meseta si otras desigualdades también se activan. Mantener el gate independiente de ventanas 2×2 constantes y reportar mesetas nuevas. El desempate lexicográfico da determinismo, no garantiza aciclicidad para otra base; no romper ciclos con epsilon.

## API GIS verificada; ejecución pendiente

El ejecutable GIS reporta `minimize(fun, x0, ..., jac=..., bounds=..., constraints=...)` y `LinearConstraint(A, lb, ub)`; SciPy 1.18.1 acepta constraints y Jacobiano para SLSQP según su código instalado. Las rutas exactas son:

- `C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Lib\site-packages\scipy\optimize\_minimize.py:54-105,167-185,699,1134-1155`: firma/docs, normalización y conversión de `LinearConstraint` para SLSQP.
- `C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Lib\site-packages\scipy\optimize\_constraints.py:139-200,506-575`: forma `lb ≤ A·x ≤ ub` y conversión con Jacobiano lineal constante.
- `C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Lib\site-packages\scipy\optimize\_slsqp_py.py:220+`: implementación SLSQP acepta `jac`, bounds y constraints.

La energía EV88 sigue siendo `0.5 * ||A x − rhs||²`, con gradiente exacto `A.T @ (A @ x − rhs)`; mismo dominio inward (`author_ev88q.py:335-353`, `author_ev90.py:31-42`). La API estática sí permite esta formulación; su convergencia y calidad numérica no se han probado.

Después de una sola optimización, hacer el único cast float32 previsto y rechazar sin reparar si falla cualquier cota o cualquier `H_j ≤ H_i` exacta en valores cuantizados. El cast monótono preserva `≤` si la solución real la cumplió, pero el post-check sigue siendo obligatorio para cubrir tolerancias numéricas. Ejecutar el gate en todos los centros afectados sobre H float32; cualquier fallo invalida el resultado, sin relajar cotas ni repetir solver.

**Footprint recalculado en runtime GIS:** lectura de B, `prepared.json` y los resultados ya existentes; 85 nodos, 135 centros afectados, 6 mínimos estrictos B, 129 testigos; 0 valores B fuera de cotas, margen mínimo B−L 0 y U−B 0.2139801979 m. Fuente de datos: `ev90-author/prepared.json`, `ev90-author/root-shape-check.json` (registra mínimo nuevo en (844,375)); B en `E:\DayZ-Baltic-Build\v30-mixed-bank-incremental-fixed-20261010\candidate\terrain.npz`. No se llamó a `minimize`.
