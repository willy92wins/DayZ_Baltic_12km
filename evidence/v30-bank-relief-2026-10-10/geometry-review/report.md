# Auditoría geométrica ribereña EV71/72

**Resultado:** hallé 59 pliegues de terreno mayores de 30° en la banda seca de 96 m de los códigos 3/5/6. Los 59 tienen sus cuatro vértices protegidos; cero admiten mover un vértice bajo las máscaras actuales. Cuatro exceden 45°. Esto localiza geometría fuerte, pero no confirma qué vio el render ni que cada pliegue sea una pirámide visual.

## Dominio y método

Entrada EV71: terreno con SHA-256 `b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36`; comparación EV70: `682d5553480e779cda1874725dd6a8a5a3615c356b65c546c77342f251857244`. P y F son los ficheros del mismo paquete de candidato. Verifiqué que el soporte de caras mojadas recalculado con la semántica física/visible coincide exactamente con los 1.077.957 vértices de `constraints.npz`.

La banda se formó con distancia euclídea raster de 6 m desde `cls ∈ {3,5,6}`, límite inclusivo 96 m. Para considerar una bisagra, los cuatro vértices únicos de sus dos triángulos nativos debían quedar en clase 0, fuera del soporte P/F realmente mojado, fuera de `reserve`/`platform` y dentro de la banda. Esto deja 1.591.990 bisagras. Para la clasificación de movilidad, `movible` significa que al menos uno de esos cuatro vértices pertenece a la banda seca y no está en la máscara EV71 `fixed`; no implica que el solver encuentre una solución factible.

Las normales y el ángulo diedro se calcularon sobre la diagonal NW–SE nativa. Corrí los controles de `audit_native_surface.validate()`: plano inclinado con pliegue cero, pliegue sintético conocido de 45°, producto cruzado independiente y control de los cuatro vértices incidentes. Las alturas, P/F, máscaras y terreno no se modificaron.

## Conteos EV71 y comparación EV70

| Tipo de bisagra | En dominio | >30° (fijos / con libre) | >45° (fijos / con libre) | Máximo | p99 |
|---|---:|---:|---:|---:|---:|
| Diagonal | 538.053 | 28 / 0 | 1 / 0 | 49,971° | 5,117° |
| Vertical | 526.228 | 5 / 0 | 1 / 0 | 45,632° | 5,285° |
| Horizontal | 527.709 | 26 / 0 | 2 / 0 | 45,480° | 5,283° |
| **Total** | **1.591.990** | **59 / 0** | **4 / 0** | **49,971°** | — |

EV70 ya tenía exactamente 59 bisagras >30°, cuatro >45° y el mismo máximo. En EV71 cambiaron 12.199 ángulos de los 1.591.990 del dominio; los cinco anchors de abajo conservaron exactamente su ángulo. El p99 baja ligeramente por tipo (diagonal 5,119→5,117°, vertical 5,290→5,285°, horizontal 5,289→5,283°). Así, el último pase tocó algo de la banda, pero no liberó los pliegues mayores.

Se contaron 738.616 vértices en la banda, 596.545 de suelo seco de clase 0 fuera de agua/infraestructura y 577.643 fuera de la máscara `fixed`. El tamaño de este conjunto potencialmente movible no cambia el resultado de los pliegues grandes: ninguno de los 59 coincide con una bisagra que tenga un vértice libre.

## Anchors máximos representativos

`x,z` son coordenadas del juego (m). “Residual local” es el máximo valor absoluto de altura de las cuatro esquinas menos la mediana 3×3 en cada esquina; sirve como indicador geométrico de una esquina saliente, no como clasificación visual.

| # | Tipo; x,z | Diedro | Pendiente de caras | Rango 4 alturas | Residual local máx. | Protección de los 4 vértices |
|---|---|---:|---:|---:|---:|---|
| 1 | diagonal; 2187, 6717 | 49,971° | 24,94° / 25,05° | 2,029 m | 2,019 m | `scope.fixed` 4/4 |
| 2 | horizontal; 2577, 6864 | 34,626° | 1,08° / 0,99° | 4,223 m | 0,150 m | `scope.fixed` 4/4 |
| 3 | horizontal; 2295, 6918 | 34,479° | 34,48° / 34,48° | 4,121 m | 0,000 m | `scope.fixed` 4/4 |
| 4 | diagonal; 2679, 6399 | 32,807° | 11,32° / 21,99° | 1,906 m | 0,975 m | `scope.fixed` 4/4; un vértice estuvo en el antiguo soporte conservador “cualquier P”, pero no en el soporte P/F realmente mojado EV71 |
| 5 | diagonal; 7989, 45 | 30,074° | 21,52° / 22,46° | 2,480 m | 2,363 m | banda de borde heredada 4/4 (últimas 11 filas) |

El anchor 3 muestra por qué un ángulo diedro no demuestra una punta: sus dos facetas tienen la misma pendiente y no hay residuo local de esquina. Los anchors 1 y 5 sí tienen una esquina con residuo cercano a 2 m. El anchor 5 es una referencia geométrica válida pero cae junto al borde del mapa, así que no debe tratarse como evidencia de un defecto ribereño visible.

## Mecanismo y acción compatible

La fuente calcula normales de los dos triángulos que comparten cada arista; un cambio de alturas entre los cuatro vértices genera un diedro no nulo aunque las caras estén secas. El control sintético de 45° confirma la métrica. El suavizador existente minimiza energía de diferencias de segundo orden mediante `K`/`build_groups`, con restricciones locales de pendiente y límites de altura; no es un filtro global que pueda mover cualquier esquina. EV71 deja fijos los cuatro vértices de todos los pliegues fuertes inventariados, por lo que aplicar ese optimizador manteniendo literalmente las máscaras heredadas no puede reducir directamente esos diedros.

La intervención más acotada compatible con mantener P/F, triángulos mojados, reserva/plataforma, carreteras, suelo seco mínimo y máscaras de lagos es resolver solo los vértices secos elegibles alrededor de los pliegues menores usando el mismo optimizador, transición quintic hasta el anillo fijo y cambio acotado hasta 2 m; congelar el soporte mojado exacto P/F y las protecciones existentes. Esto no promete arreglar los 59 pliegues: para cambiar cualquiera directamente habría que revisar explícitamente la protección heredada de sus vértices, y eso queda fuera del contrato de preservarla. No sugiero relajarla de forma implícita.

## Fuentes y límites

- `audit_native_surface.py:13-27` define las normales, pares de caras y aristas compartidas; `:31-37` valida los controles geométricos.
- `verify.py:26-36` calcula el soporte de triángulos mojados usando altura física/visible; `:79-85` calcula estadísticas secas por cara y bordes.
- `discover.py:14-19` define `fixed` heredado y `editable` de dominio seco previo.
- `author.py:11-23` combina `scope.fixed`, agua/playa/clases no terrestres, lagos, soporte mojado y crea `allowed`; por eso “libre” se evalúa contra esa máscara exacta.
- `author_hinges.py:12-26` define la energía y el kernel; `:39-60` prepara protecciones; `:65-75` construye grupos de caras y radios de pendiente; `:79-95` ejecuta pasos acotados.

La métrica prueba geometría de la triangulación fuente, no selección de LOD, sombreado, colisión, visibilidad en DayZ ni que el usuario perciba un defecto en esos anchors. La clasificación de esquina es un proxy, no un render. Este informe no lanza el motor ni empaqueta nada.

## Reproducción

Usar exclusivamente `C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe`:

```powershell
& 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe' 'E:\DayZ-Baltic-Build\v30-bank-relief-review-20261010\luna-geometry\analyze_bank_creases.py'
```

La salida reproducible está en `report.json` y `representative-maxima.csv`; la implementación de medición está en `analyze_bank_creases.py`. `protection_at_anchors.py` reproduce el desglose de máscaras de los anchors.

## Desglose semántico de la máscara y alcance mojado-seco

El censo de 59 pliegues >30° es estricto: exige que las cuatro esquinas únicas de ambos triángulos estén en suelo de clase 0 dentro de 96 m de `cls 3/5/6`, fuera de soporte mojado P/F real, máscaras `water/beach`, reserva y plataforma. Por eso no representa los pliegues de transición de la orilla.

Contando toda bisagra que toca al menos un vértice de suelo seco elegible en esa banda, aunque los otros vértices no sean secos/elegibles, salen 1.987.722: 1.591.990 totalmente secos 4/4 y 395.732 mixtos/excluidos. De estos, 199.085 tocan soporte mojado P/F real. Hay 4.827 pliegues >30° que tocan la banda: 59 secos 4/4 y 4.768 no 4/4; 4.740 de esos últimos tocan soporte P/F real y 28 fallan otro criterio. Son universos distintos: los 4.740 describen geometría que participa en una transición de mojado-seco, no una confirmación de defecto visual.

| Bisagra | Toca suelo seco elegible | 4/4 seco elegible | No 4/4 | Toca P/F mojado | >30° total | >30° no 4/4 | >30° toca P/F |
|---|---:|---:|---:|---:|---:|---:|---:|
| Diagonal | 655.163 | 538.053 | 117.110 | 58.703 | 3.180 | 3.152 | 3.138 |
| Vertical | 666.991 | 526.228 | 140.763 | 70.704 | 822 | 817 | 816 |
| Horizontal | 665.568 | 527.709 | 137.859 | 69.678 | 825 | 799 | 786 |
| **Total** | **1.987.722** | **1.591.990** | **395.732** | **199.085** | **4.827** | **4.768** | **4.740** |

La reconstrucción bit a bit confirmó `candidate-a/masks.fixed`, `native-terminal.constraints.fixed` y `domain.fixed`. Entre los 59 pliegues secos >30°:

- 58/59 caen dentro del radio Narva de 620 m y con `R1dist >= 150 m`, la guarda radial histórica. 57/59 además coinciden con `t.narva` (capa raster del objeto/agua Narva).
- 56/59 tienen sus cuatro vértices fijados solo por las máscaras Narva. Dos más también intersectan un control temporal; el 59º es la franja exterior del borde del mapa.
- Ninguno de los 59 toca soporte mojado P/F real, el corredor `corridor24`, etiqueta `nature`, playa/mar, reserva/plataforma, summit o gran lago. El #4 toca un vértice de `prior.water_support` histórico (“cualquier P”), pero ese vértice no pertenece a soporte mojado P/F actual.
- `nature` se carga en `smooth_valley.py` y se usa para informar `changed_nature`; no forma parte de la unión de `fixed` de ese script. No es el veto que congela estos puntos.

Los anchors 1–4, incluidos los cuatro interiores, están en Narva radius620/guard histórica sin solape con corredor, reserva, plataforma, playa, mar, summit ni P/F mojado real. El #4 cae fuera del raster `t.narva`, así que su protección allí viene de la guarda radial antigua, no de una cara mojada. El anchor 5 pertenece solo al margen geográfico.

Los recuentos y vértices están en `mask-scope-audit.json`; `mask_scope_audit.py` reproduce el desglose semántico y la comparación de bisagras que tocan la banda.

La banda seca física literal (solo `cls==0`, dentro de 96 m y fuera del soporte mojado P/F) toca 2.021.891 bisagras; 1.642.109 tienen sus cuatro vértices secos físicos. La banda elegible estricta de arriba baja a 1.987.722 al excluir además `water/beach` y reserva/plataforma. Esta diferencia (34.169 bisagras que tocan físicamente suelo seco) evita presentar como “sin tierra” las aristas excluidas por ingeniería/mascarillas.

La fuente que explica los bloqueos es la unión heredada: `smooth_valley.py:15-30` congela corredores24, cimas, mar/playa, infra, borde y la zona Narva a más de 150 m de R1; `discover_terminals.py:14-22` recorta el borde antiguo, añade borde exterior y controles temporales, y congela el raster `t.narva`; `finish_shores_v30.py:34-51` construye `corridor24` desde las rutas certificadas. La etiqueta `nature` se carga en `smooth_valley.py:20` y solo se informa en `:64-65`; no es parte de `fixed`.

Para repetir también la descomposición semántica y los totales de bisagras mojado-seco:

```powershell
& 'C:\Users\guill\Documents\Codex\2026-09-29\vamos\work\gis-env\Scripts\python.exe' 'E:\DayZ-Baltic-Build\v30-bank-relief-review-20261010\luna-geometry\mask_scope_audit.py'
```
