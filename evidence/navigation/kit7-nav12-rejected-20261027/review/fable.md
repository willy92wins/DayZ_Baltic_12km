**Dictamen técnico (READ ONLY, una lane, Codex integra)**

## 1. Hechos verificados (anclas)

- **Las 3 alturas nuevas son un artefacto de interpolación planar, no de muestreo erróneo en los waypoints.** `kit7-nav12-height-reconstruction-20261027/result.json` reproduce la Y nativa de los 6 waypoints con el abanico de polígonos del propio NM, residuo máximo 5.6e-7 m. `reconstruct_kit7_nav12_height.py:13` afirma que los contadores de detalle del tile son 0 (`i[9:12]==[0,0,0]`), y `:20` interpola solo con los vértices del polígono.
- **Cada tesela de 12 m tiene 1 o 2 polígonos con 3 a 5 vértices cubriendo relieve de ~1.7 m.** Vértices en (760,939): esquina compartida (9132, 2.07, 11280) frente a vecinos (9132, 2.77, 11268), (9132, 2.87, 11292), (9120, 2.57, 11280), (9144, 2.37, 11280). Vértices interiores de pie de talud a 1.17, 1.67 y 1.97 m. Las Y están cuantizadas a 0.1 m (todas de la forma k·0.1 − 0.030): coincide con cellSize2/3 = 0.1, pero la cuantización aporta ≤0.05 m, no los 0.8 m observados.
- **La esquina de tesela cae sobre el eje de 4 tiles exactamente en x=9132, z=11280**, es decir 761·12 y 940·12. Los waypoints izquierdo (x≈9128–9131) y derecho (x≈9135–9140) flanquean esa línea.
- **Las tres LOD físicas coinciden entre sí** (`kit7-nav12-layer-diagnostic-20261027/result.json`): Visual/Geometry/Roadway difieren <0.002 m en los 6 puntos; terreno bajo pieza ~1.0–1.25 m; superficie de pieza ~2.78–2.82 m. No hay discrepancia entre LODs que explique el fallo.
- **El estimador de dos diagonales no discrimina**: 12 m predice 0/14 y falla 3; 8 m predice 0/14 y falla 0; en conjunto 74 vs 3 y 10 vs 0 (`kit7-nav-after12-screen-20261027/result.json` líneas 35-38, 171-174, 193).
- **RAM Nav8**: residente 1.26591, privada 1.24133, dispersión máx. 0.2 %, seis pasadas (`kit7-nav8-ram-ab-20261027/comparison.json`). FAIL válido, no repetible favorablemente.
- **Config real** (`package-kit7-nav12-input-20261027/config.cpp:64-78`): tileWidth 12, cellSize1 0.25, cellSize2/3 0.1, agente 0.6/1.5/1/0.5/0.45/60. El plan `plans/ev112-kit7-nav12-cost-20261027.md:148-151` ya preautoriza la medición de 12.5 como discriminador diagnóstico sin aceptarlo.

## 2. Mecanismo aislado

**Hecho:** la altura NM en un punto es la interpolación planar de un polígono de pocos vértices sin malla de detalle. Donde el polígono abarca talud + plataforma + cauce, el error de altura es inevitable y depende de **dónde caen los vértices forzados**, que son casi exclusivamente las fronteras de tesela y los pies de talud.

**Hipótesis H1 (fuerte, no comprobada):** el vértice de esquina (9132, 2.07, 11280) está sobre el cauce/talud interior de la pieza cs_kit_7 (profundidad ~0.7 m respecto a la plataforma). La frontera de rejilla de 12 m atraviesa justo ahí; la de 8 m (x=9128/9136, z=11272/11280/11288) coloca sus vértices sobre plataforma. Por eso Nav8 pasa y Nav12 falla en 116, y por eso Nav12 mejora 124/133: la alineación, no la densidad, decide cada punto. El margen de Nav8 (0.712 vs 0.801) es de 0.09 m; su PASS también es alineación afortunada sobre una muestra de 607.

**Consecuencia:** cualquier serie de anchos es una lotería local. El estimador falla porque no modela ni la fusión de regiones, ni la simplificación de contorno, ni la ausencia de detalle.

## 3. Límites

- No se sabe si el generador omite malla de detalle **en todo el archivo** o solo en estas 4 teselas. Sin eso no se puede afirmar que el mecanismo sea global.
- No hay muestra física en el XZ del vértice de esquina; H1 queda como hipótesis.
- cellSize1/2/3 sin semántica documentada; el plan y la wiki prohíben tocarlos sin definición. No hay parámetro de detalle/simplificación conocido en el generador 66935ce8.
- RAM no es lineal con teselas ni con bytes de archivo; 741 MB vs 1338 MB no implica nada aún.

## 4. Opciones descartadas y motivo

- **Otro ancho (10.5/11/11.5) ahora:** el único predictor disponible está refutado por dos observaciones; sería ciego. Además 10.5 aumenta teselas (1.37 M) sin saber si existe ventana RAM.
- **Tocar cellSize1/2/3:** semántica desconocida, prohibido por plan y documentación. Cuantización 0.1 m no explica el fallo.
- **(c) corrección de representación física:** solo sería legítima si el vértice de esquina fuese *inexacto* respecto a la superficie real (p. ej. Geometry LOD con hueco). Las tres LOD coinciden en los 6 puntos; si H1 se confirma, el vértice es exacto y la corrección exigiría cambiar relieve del producto. Descartado salvo que el ancla pedida en §5 lo contradiga.
- **Parchear NM, mover consultas, relajar 0.801, geometría-trampa:** fuera de contrato.
- **Medir RAM de Nav12 como aceptación:** gate funcional fallido; solo como diagnóstico, y después de 12.5.

## 5. UN siguiente paso recomendado: opción (a)

**Medir RAM del paquete kit7 NavV9 12.5 m exacto** (966 289 teselas, base SHA `a2919a80…`, archivada en `archived-mods-nav12-space-20261027/`), seis pasadas ABBAAB nuevas, 30+120 s, mismos lectores, presupuesto 1.10 y dispersión 5 %, etiquetado DIAGNOSTIC_ONLY con sus 4 FAIL de altura preservados.

**Por qué este y no otro:** es el extremo de menor densidad de la familia y está preautorizado en el plan. Decide si el eje "ancho de tesela" tiene una ventana RAM antes de gastar otra generación.

**Criterio de parada:**

| Resultado 12.5 | Conclusión | Acción |
|---|---|---|
| Residente **y** privada ≤1.10, dispersión ≤5 % | Existe ventana RAM en la familia | Pasa al candidato de rejilla por **criterio de alineación** (§6) |
| Cualquiera >1.10 | La densidad no es la palanca del exceso; el coste está en el paquete kit7 | Cerrar la exploración de anchos. Escalar a Guillermo: hace falta decisión de producto/alcance. Nav8 funcional + FAIL_RAM sigue como registro |
| Dispersión >5 % o pasadas inválidas | INCONCLUSO | Repetir el bloque completo una vez; no seleccionar pasadas |

**Prerrequisito local, solo lectura, sin servidor (anclas que faltan):**

1. **Censo de detalle en todo el NM de Nav12 y de Nav8**: contar tiles con `ints[9:12] != 0`. Si es 0 en 1 048 576 y en 2 359 296 tiles, el mecanismo es global y queda fijado como hecho.
2. **Altura física (Roadway y Geometry, vía `diagnose_kit7_nav12_layers.py`) en los 5 vértices de rejilla** (9132,11280), (9132,11268), (9132,11292), (9120,11280), (9144,11280). Si la superficie en (9132,11280) está en 2.0–2.2 m, H1 confirmada y (c) queda descartada definitivamente. Si está en ~2.8 m, el vértice es inexacto y (c) vuelve a la mesa con la LOD como sospechosa.
3. **Mismas 4 esquinas en el NM de Nav8**: polígonos, vértices y Y para comparar alineación directa con Nav12.

## 6. Si 12.5 pasa RAM: criterio nuevo para la rejilla (no predicción)

Candidato elegido por **distancia mínima entre líneas de rejilla (múltiplos de tileWidth) y las trazas de cauce/talud de las 14 posiciones kit7 conocidas**, exigiendo que ninguna frontera caiga a <0.5 m de un cambio de nivel ≥0.45 m en esos puntos. Es un criterio geométrico comprobable sobre el NM producido, sin prometer PASS; sigue mandando la sonda de 607. Solo se autoriza una generación tras este diagnóstico.

Hoy no se concede PASS a Nav12 ni a Nav8. Destino: altura PASS y RAM ≤1.10 del mismo paquete.
