# Sensibilidad offline del terreno remuestreado — EV95

Estado: cálculo estático y muestreado. **No mide el LOD que el motor selecciona, no ejecuta DayZ y no establece causalidad.** B y EV95 se reportan separadamente; ninguna captura EV73 se transfiere a estos mundos.

## Método

- ROI: envolvente XZ de los bbox visuales locales transformados por las posiciones WRP de los objetos `16812770`, `16812771`, `16812805` y `16812815`, leídos de `v30-water-object-boundaries-20261010/exact-pairs.json`. El bbox es una aproximación conservadora del objeto, no su footprint de caras. En esta envolvente hay 2.112 centros de muestra a 1,5 m; la unión real de las cuatro máscaras bbox contiene 1.408. Los recuentos por objeto pueden solaparse.
- H nativa: malla de 6 m y diagonal NW-SE. Para cada paso 2/4/8/16/32 m, se muestrean valores en una retícula anclada a `x=0,z=12282` desde la superficie triangular nativa; luego se triangula NW-SE en ese paso. `2 m` es un refinamiento de control, no un LOD grueso.
- P es el valor por celda. F se interpola entre NW/NE/SW/SE dentro de cada celda, con diagonal NW-SE; no se mezclan celdas vecinas. Los centros de muestra se desplazan 0,75 m para evitar costuras nativas.
- Se cuentan los centros donde H nativa queda bajo P o F y, dentro de ese conjunto, aquellos donde H remuestreada queda por encima de la superficie. Las magnitudes son `H_remuestreada − P/F` en metros.

## Resultado sobre el ROI

B y EV95 tienen iguales las 2.112 alturas nativas muestreadas. En ambos, 1.333 centros están bajo F finito y 1.334 bajo P. El paso 8 m tiene el mayor número de cruces muestreados: 9/1.333 sobre F (máximo +0,18 m; p95 del uplift positivo +0,16 m) y 9/1.334 sobre P (máximo +0,18 m; p95 +0,16 m). A 4 m se observan 3 cruces (máximo +0,08 m); a 16 m, 7 (F máximo +0,14 m, P +0,15 m). A 2 m y 32 m no hay cruces muestreados sobre P/F donde H nativa estaba debajo.

Los máximos por bbox con H nativa bajo F fueron: objeto `16812770`, +0,14 m a 16 m (7 puntos); `16812771`, +0,03 m a 4 m (1); `16812805`, +0,18 m a 8 m (4); `16812815`, +0,13 m a 8 m (1). Son estadísticas de cajas visuales muestreadas, no conteos de cara exacta. Aunque H nativa coincide en los centros de parche, las superficies remuestreadas B/EV95 difieren allí en 65 puntos a 16 m (máximo 0,0173 m) y 647 a 32 m (máximo 0,0637 m); esos nodos coarse pueden caer fuera de los centros de parche.

## Límites y artefactos

Esto cuantifica que un remuestreo triangular de escalas gruesas puede subir unos puntos de terreno sobre P/F en este ROI; no predice oclusión/render, vista de cámara, selección de LOD, orden Z, wave state ni shader. Los bbox incluyen zonas vacías y los puntos no son un raycast/union de caras ODOL. La afirmación de mecanismo requiere después una comparación in-game válida; este diagnóstico solo hace medible una posibilidad.

- Fuente/cálculo: `analyze_coarse_terrain.py`; incluye fixtures de plano afín exacto, no-promedio entre celdas F y rechazo fuera del grid.
- Resultados y readset: `report.json`.
- Muestras reproducibles: `samples.npz`.
- Corrida de prueba anterior retenida por un rótulo ambiguo del conteo de la envolvente: `attempt-01-preserved-envelope-count-label/`.
- Entorno: GIS Python `C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe`; 0,43 s y pico de working set 81.9 MB, debajo de 180 s/512 MiB.