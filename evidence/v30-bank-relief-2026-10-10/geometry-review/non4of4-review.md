# Bisagras >30° que tocan banco seco: revisión de las 4.768 no 4/4 secas

Fuente: EV71 `terrain.npz` SHA-256 `b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36`; `plane.npy` `768e8e58525887b9db15006ba5fc4a8bbf3cde3fca9c90facc25ebbe939551e0`; `visible-field.npy` `f446a2164648e481d1216864bc879c4f6ddaa245db54d689d9ad99a82d7f095c`; constraints `18a3639907a68a8ceda37fe2a402884c2c4bc111fe8c7775d0a7d07dac02d370`. Recalculé P/F por cara con el contrato de EV71 y exigí igualdad exacta con `constraints.npz:water_support`.

## Qué significan las 4.768

El selector es el censo previo: bisagras nativas >30° con ≥1 de sus cuatro vértices en la banda de terreno seco elegible de 96 m y excluyendo las que tienen 4/4 vértices elegibles secos. No es un censo de agua profunda ni de todas las orillas.

| Estado de las dos caras que comparten la bisagra | Bisagras | Interpretación |
|---|---:|---|
| borde geométrico mojado-seco real según P/F | 3,317 | orilla en esta bisagra |
| ambas caras secas; soporte de vértices viene de otras caras incidentes | 1,451 | no confundir soporte de vértices con transición de orilla aquí |
| dos caras mojadas (ninguna en este subconjunto) | 0 | sin evidencia de caras profundas dentro del subconjunto |

De las 3.317 bisagras `wet-dry`, las caras mojadas marcan 9.951 incidencias de vértice como soporte; 6.634 incidencias son vértices `cls=0` secos pero bloqueados por ese soporte. En las 1.451 `dry-dry`, hay 3.874 incidencias de vértices secos con soporte: dado que las dos caras de la bisagra están secas, el soporte proviene de otras caras P/F que comparten esos vértices. Es conteo de incidencias, no de vértices únicos.

Las clases agrupadas son componentes raster 8-conexos combinando `cls ∈ {3,5,6}`; sirven para agrupar por sector, no son nombres de ríos ni una conectividad hidrológica demostrada. Los mayores grupos son:

| Componente espacial | Bisagras | wet-dry | dry-dry | Caja X/Z (m) | Códigos |
|---:|---:|---:|---:|---|---|
| 41 | 915 | 686 | 229 | 2337,1731–10617,8382 | 3,5,6 |
| 114 | 600 | 413 | 187 | 1785,51–6879,4251 | 5,6 |
| 136 | 230 | 186 | 44 | 1833,1383–3609,1824 | 6 |
| 143 | 187 | 103 | 84 | 813,789–1611,1419 | 6 |
| 51 | 167 | 116 | 51 | 7665,7119–9039,7593 | 6 |
| 19 | 141 | 104 | 37 | 11277,8655–12093,9987 | 5,6 |
| 59 | 137 | 125 | 12 | 5301,5976–5727,7044 | 6 |
| 58 | 126 | 88 | 38 | 8874,3918–9453,7113 | 5,6 |
| 131 | 120 | 94 | 26 | 3345,3093–4515,3573 | 6 |
| 146 | 106 | 59 | 47 | 1242,75–3243,606 | 5 |
| 106 | 105 | 82 | 23 | 4875,3825–5961,4671 | 6 |
| 95 | 104 | 71 | 33 | 7479,4320–8055,5373 | 6 |

## Tres focos de relieve local

Se agruparon las bisagras por vértice seco elegible y se eligieron puntos donde convergen al menos dos bisagras >30° de transición mojado-seco. El punto objetivo es un vértice `cls=0` seco, no parte del soporte P/F y no bloqueado por EV71; los demás vértices de esas caras incluyen 3 puntos de soporte y deben quedar intactos para conservar el contorno P/F. Esto discrimina un nudo local de cambio de pendiente de una larga faceta inclinada, aunque no demuestra que el render lo perciba como una pirámide.

| Foco (X,Z) m | Componente | h local | h−mediana 5×5 | Diedros convergentes | Condición del vértice objetivo |
|---|---:|---:|---:|---|---|
| (2196, 1578) | 136 | 5.954 m | +1.981 m | vertical 31.8°, horizontal 31.6° | cls0, no soporte, no fixed, sin reserve/platform/water/beach |
| (5538, 3918) | 106 | 5.863 m | +1.124 m | vertical 31.4°, horizontal 33.9° | cls0, no soporte, no fixed, sin reserve/platform/water/beach |
| (1140, 1002) | 143 | 4.905 m | +0.700 m | vertical 43.5°, horizontal 43.7° | cls0, no soporte, no fixed, sin reserve/platform/water/beach |

Control de carretera sobre la referencia de centerlines `tests/regional_foundation_roads_v6/reference.npz` enlazada por `road-grade-chains-v6.json`: las distancias mínimas desde los tres vértices elegidos son 1.917 km, 619 m y 2.267 km. Esto descarta proximidad de centerline para estos puntos en esa referencia; no comprueba anchura de camino ni fuentes posteriores.

Una intervención futura acotada sería ajustar únicamente el vértice seco objetivo y su vecindad elegible dentro del mismo sector, dejando inmóviles todos los vértices del soporte P/F, reservas, plataformas y carretera. Este diagnóstico no calcula ni valida tal ajuste; el hecho de que cada objetivo esté editable no prueba que una modificación de un solo vértice suavice el terraplén sin efectos laterales.

## Reproducibilidad y límites

El cálculo usa `classify_non4of4_folds.py`, que reproduce 4.768 y los estados de las dos caras con la topología de triángulos de `audit_native_surface.py`. `select_bank_focuses.py` agrupa por vértice y genera los tres anclajes. `non4of4-folds.csv` y `non4of4-fold-classification.json` contienen los registros completos. No se modificó terreno, P/F, constraints ni DayZ.

Las 1.451 bisagras `dry-dry` son soporte seco geométricamente cercano a agua, no una falsa clasificación de profundas. Para censar bajo agua profunda haría falta otro dominio que incluyera vértices sin banda seca; eso quedó fuera de esta petición. Las cifras no prueban una “pirámide visual” ni la factibilidad del solver.
