# EV91 preflight: guard del collar

**PASS_PREFLIGHT_GUARD_AND_FOCUS_BOX_WITNESS**. Auditoría estática solamente: no se modificaron EV90, EV91 author, alturas, candidato ni geometría.

- Reconstrucción anclada a B `f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`, preflight EV90 y lista exacta de 85 variables. La lista EV91 coincide con `eligible_after_face_freeze_nodes`; las 85 cotas float32 interiores coinciden nodo a nodo con el preflight EV90.
- El guard congela `43/85` variables: `43` participan en alguna de las `107` stencils de collar y `43` en las bisagras medidas; ambos conjuntos coinciden. Quedan `42` variables libres, todas dentro del núcleo9 centrado (filas836–844, columnas368–374): `42/42` elegibles.
- Se conservó la población completa: `350` stencils y collar de `{'diag': 112, 'vertical': 108, 'horizontal': 108}` bisagras; los conteos concuerdan con el reporte EV90 y la máscara `incident_any` del helper EV87. Una perturbación sintética de todos los grados libres deja idénticos la energía de stencils y todos los ángulos collar, componente por componente; esto verifica la suficiencia estructural del guard.
- Foco `(840, 370)`: libre `True`, B `3.736105204 m`, intervalo tras guard `(1.8115131855010986, 4.236104965209961)`. El testigo EV91 es `(841, 369)` a `0.656751215 m`. Con los demás nodos en B hay testigo float32 `3.278029680 m` que cumple los objetivos cardinales de reducción ≥25% en ambos ejes y mantiene la desigualdad foco≥testigo. Resultado: **True** para esta prueba de caja local, sin solver.

## Conservadurismo y alcance

El guard replica la población efectiva EV90: `incident_any` incluye una bisagra si cualquiera de los cuatro vértices de sus dos triángulos toca el collar, y se congelan las variables entre esos cuatro nodos. La intersección por extremos del edge compartido sería menor (112/84/84 hinges diag/vertical/horizontal; 24 dependencias mutables), pero las 19 dependencias adicionales ya pertenecen al guard de stencils. Por eso la unión final sigue siendo 43; la definición amplia de normales no reduce más el núcleo que la energía de collar ya exige. Se compararon las 328 normales de collar, no solo sus máximos.

Para una prueba local, se deja todo en B salvo el foco en `3.278029680 m`. Ese testigo satisface todas las filas de descenso EV91 (incluido el testigo del foco), las cinco puertas del shape contract sobre WINDOW y reduce la bisagra incidente máxima `5.476322°` (puerta 2°: `True`). Es evidencia de que la libertad central existe y de que el objetivo del foco no queda bloqueado por cotas/testigos; no es solución del objetivo energético EV91 ni chequeo completo de sectores, p99 o cobertura.

El detalle reproducible está en `collar-guard-preflight.json`; script `collar_guard_preflight.py`.
