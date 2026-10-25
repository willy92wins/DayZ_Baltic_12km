# Comparación de relieve a 6/12/24 m — diagnóstico, no selector

**Estado:** censo comparativo readonly terminado. No es una receta de edición, no define umbrales ni clasifica automáticamente rasgos como naturales o artefactos. La propuesta anterior quedó archivada en `surface-wide-relief-proposal-v1-superseded.md` (SHA-256 `145e7f40ed2da64636bc399bd3229a4630966687802213d4b6b768e420dfdaa4`). No se aprueba arquitectura EV87 de ventanas 7×7/9×9; el trabajo EV91 usa otro ámbito (`WINDOW17/core13/guard9`) y aquí no se seleccionan parches.

## Método y alcance

Se comparó B (`f9fb23decc6dbcfa2837b5bedcb02aea3eec44d2bbdc7b4c07d5d3f5fee061f0`) con `source/baltic_relief3x_2048_6m.asc` (`ecb2bd99a1751362bfcab0c150f10d18649bf3a50b24ea49a3eb0ffdb48bdf1f`) en índices idénticos 2048×2048. ASC declara `ncols/nrows=2048`, `xllcorner=200000`, `yllcorner=0`, `cellsize=6`, `NODATA_value=-9999`; hay 0 celdas NODATA y todos los valores son finitos. El valor −12 es dato, no sentinel. `row 0` es norte; centro de celda `(r,c)` en `X=200000+(c+0.5)*6`, `Y=12288-(r+0.5)*6`, coherente con `tools/geo_common.py` y el contrato TB documentado allí. Cinco muestras se verificaron además con lectura independiente de tokens ASCII y conversión float32.

Para ambos arrays se aplicó, sin tolerancia, `prom_d=max(0,Hc−max(H−d,H+d))` por separado en EW y NS, para `d=1,2,4` nodos (6, 12, 24 m). El informe da cuantiles del delta de prominencia B−relief3x, conteos de soporte positivo común/B-only/relief3x-only y cobertura de antiguas semillas EV87 por población. Poblaciones elegibles: bank 581.794; interior 2.340.816; wet_support 65.955; total 2.988.565. Además se conservan `all` y explícitamente protegidos.

## Lectura de resultados

En la población elegible, el delta de altura almacenada B−relief3x tiene p50 −3,368 m, p01 −12,476 m y p99 +35,572 m. Esto es una diferencia entre representaciones: `relief3x` es la variante de relieve vertical ×3 identificada por `tools/navigation/compare_relief_options.py`, mientras B es otra base. No equivale a error de terreno ni a altura física común; el delta se publica para describir la disparidad, no para decidir cota.

El soporte de prominencia tampoco coincide de forma simple. A 6 m en los elegibles bank, EW tiene 7.387 positivos comunes, 24.757 B-only y 122.774 relief3x-only; en interior: 15.762 comunes, 50.710 B-only y 505.350 relief3x-only. El signo positivo es invariante a una multiplicación vertical positiva, pero la discrepancia espacial significa que la referencia no funciona como veto ni como “verdad” independiente. A 24 m el mismo informe muestra las cifras completas por eje y población; no se impone una cuota ni un nuevo umbral.

Las 5.450 semillas pre-spacing EV87 son 722 bank, 27 interior y 4.701 eligible∩wet_support. Entre las 4.701 semillas wet_support, el soporte positivo de fuente en la misma ubicación/eje aparece en 815 EW y 833 NS a 6 m; en 1.043/1.083 a 12 m y 852/887 a 24 m. Esto es coincidencia de descriptor, no prueba de identidad de rasgo ni clasificación visual.

Cinco muestras fila/columna (valor ASC recargado por tokens y cotejado float32 con `numpy.loadtxt`): (0,0) −12/−1,25 m; (100,100) −12/−12 m; (840,370) 2,0685/3,7361 m; (1024,1024) 14,4134/6,5279 m; (1800,1500) 10,1204/4,7145 m (relief3x/B). Los cinco centros XY y las lecturas independientes están en el JSON.

## Artefactos y límites

- `compare_relief3x.py` — comparación reproducible; SHA-256 `cefa6eca00116f9877ff4e7698bb4de2c88e2edc280c3657a692f68534fbb5f5`.
- `summary.json` — SHA-256 `3998dde16249438facf3b0be5ae408f094e75b38b9d1ec67c71b653666ec9c8f`; cuantiles, poblaciones, soporte por eje/escala, hashes, fórmula, nodata y muestras.
- `relief3x-prominence-comparison.npz` — delta de altura, prominencias relief3x, mapa de poblaciones, bits de contexto completo y mapas de soporte común/B-only/relief3x-only. SHA-256 `b8b5ecea9ae472575045c49958d6157b279c5ceb62212ea305a5339245b9c39c`.
- `README.md` — alcance de los arrays y claves.

La comparación no determina qué relieve quiere el diseño, no detecta artefactos de render, no verifica pendientes/agua/objetos y no autoriza cambios. Para decidir una intervención futura, las fuentes pueden informar perfiles y carácter local; no se ha fijado selector, ventana, cuota, objetivo ni proceso de edición.
