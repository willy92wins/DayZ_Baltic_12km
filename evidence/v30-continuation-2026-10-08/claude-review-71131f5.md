# Revisión adversarial del commit 71131f5: reparación de orillas, comprobadores y propuesta de calado

## Veredicto: **SOUND-with-fixes**

- **Reparación local de orillas (765/1176).** Es coherente entre productor, consumidor offline y la repetición en motor. No he encontrado ningún falso PASS demostrable.
- **Propuesta de calado (BALTIC-012).** Su cálculo es consistente. Sin embargo, la decisión pendiente está incompleta: no solo hay que decidir sobre el fondo de 1 m.
- **Comprobador de cauces.** Contiene mecanismos que podrían ocultar fallos. No tengo repro y los marco como HIPÓTESIS.

Ningún hallazgo demostrado bloquea el paquete `b363b79d` dentro del alcance declarado.

## Comprobado sin hallazgo

- **Pesos baricéntricos.** Los de `repair_wave_banks_v30.py:47-48` coinciden con `tri_sample` (`v30_common.py:27-29`) y con `sample` (`waterway_common.py:43-45`), con la misma diagonal y el mismo desempate `fc>=fr`.
- **Pendiente de las medias caras.** La fórmula de `check_wave_banks.py:67-69` y `check_fairway_candidate.py:42-44` es geométricamente correcta en ambas orientaciones.
- **Clasificación de puntos.** Se congela antes del lanzamiento y se afirma explícitamente (`prepare_wave_fixed.py:30-34`).
- **Guarda de terreno.** La de ±0,02 m (`read_water_temporal_v30.py:35`) distingue el WRP reparado en 765 y 1176, que cambian 0,108 y 0,071 m.
- **Controles negativos sobre la serie real.** Mutan la fila y el campo correctos (`verify_wave_fix.py:33-42`). El de tormenta muta el id 13, que es el primer punto que lee `phase_gate` (`read_water_temporal_v30.py:69`).
- **Certificado de inviabilidad.** Es consistente con la propuesta. El máximo de 0,079369 m sale exactamente de 0,045391 / 0,5719, el testigo de `floor-feasibility.json:71-80`. Esto confirma que 3026173 es mutable y que su capacidad nula se debe al suelo, no a que esté excluido del ámbito.

## P2

**P2-1. La propuesta de calado modifica la reserva; esa decisión no está en la lista pendiente ni la comprueba ningún check.**
- **Dónde:** `repair_current_fairways_v30.py:34-36`. `mutable` no excluye `t['reserve']`.
- **Choque con el plan:** el plan exige no cambiar la reserva (`plan.md:7`; `plan.md:15`: «Reserva… permanecen fijos»).
- **El precedente citado no cubre este caso:** el paso de fondos del 07-10 solo **eleva** («never lowers anything», `profile_inland_v30.py:308`; `h2[bed]=need[bed]` con `h2<need`, `:318-319`). Además excluye `reach_vertices` y `border` (`:312-313`), que la propuesta no excluye.
- **Falta el check:** `check_fairway_candidate.py:21-26` no tiene equivalente a `reserves_fixed` (`check_wave_banks.py:27`).
- **Consecuencia:** si se aprueba «la excepción al fondo de 1 m» (`README.md:8,31`), se introduciría también un rebaje de lechos dentro de la reserva que nadie ha aprobado.
- **Repro verificable:** `np.count_nonzero(changed & t['reserve'])` sobre `fairway-proposal-r2/terrain_fairways.npz` frente a `a292b6c3`. No tengo el resultado.
- **Límite:** las fuentes no definen si el invariante de «reserva» incluye los lechos sumergidos.

**P2-2. El control positivo de agua alta (693) está seco y el gate lo da por bueno sin reclasificarlo ni informarlo.**
- **Dónde:** `wave-fixed-verification.json:612-625`. Rol `high_deep_pond`, `pond_true 0`, `depth_bed` entre −0,683 y −0,541. El suelo está a 5,354 m y el plano a 4,675 m. Ya era así en `a292b6c3` (`wave-bank-verification.json:87-92`).
- **Por qué pasa:** `unchanged_presence_controls` y `unchanged_dry_stays_dry` (`verify_wave_fix.py:23-24`) solo comparan con el baseline V1, que ya tenía la pérdida. `phase_gate` solo examina `frozen_shallow_failure` (`read_water_temporal_v30.py:75`).
- **Qué dicen los informes:** el README (`:11`) y los límites (`prepare_wave_fixed.py:61`) solo mencionan seis someros convertidos en tierra.
- **Consecuencia:** los 17 puntos no contienen ningún control positivo de estanque alto. Una pérdida de agua alta pasa sin alarma.
- **Es hecho verificado en las fuentes:** el punto está seco. **Es límite:** si se trata de un defecto del mapa o de un cambio de contorno autorizado (016) depende de una definición de rol que no está aquí.

**P2-3 (HIPÓTESIS). El comprobador de cauces confía en `removed_cells` sin verificar que esos planos falten realmente en el agua construida.**
- **Mecanismo:**
  - En `verify_channel_reaches_v30.py:68-72,78`, las celdas que declara el propio productor (`axes.json`) pasan a `NaN`.
  - Con eso salen de `wbad`/`lbad` (`:100-102`).
  - Sus vértices secos solo se comparan con piezas vanilla (`:108`). Los planos conservados no se usan para la regla de tierra (`:114-121` solo mira vértices mojados).
- **Consecuencia:** si una celda se declara eliminada pero su plano sigue emitido en `pieces.json`, un vértice seco bajo ese plano desaparece del recuento. Ese es precisamente el mecanismo que se invoca para descartar los 21 fallos (`README.md:9`).
- **Repro propuesto:** para cada celda de `removed_cells`, llamar a `retained_pond_surface(fit, manifest, centro_x, centro_z)` y exigir `None`.

**P2-4 (HIPÓTESIS). Mezcla de geometrías en BALTIC-012: el calado se mide contra planos que el comprobador de cauces declara inexistentes.**
- **Dónde:** `repair_current_fairways_v30.py:30,37` y `check_fairway_candidate.py:27,30` usan `cell_planes` sin anular las celdas `removed_cells`. En cambio, `verify_channel_reaches_v30.py:78` sí las anula.
- **Indicio de solape:** el paso de fondos excluía `corridor` y `reach_vertices` (`profile_inland_v30.py:312-313`), lo que sugiere que pueden coincidir.
- **Consecuencia:** algunas de las 236 + 122 caras «fallidas», o las aprobadas, podrían medirse contra una superficie que el motor no tiene.
- **Repro:** intersectar `rec['face']` (celda de cada cara) de Luga_0 y Neva_0 con `axes.json` `removed_cells`. Si el resultado es vacío, se descarta.

**P2-5 (HIPÓTESIS). La cobertura de cauces solo se comprueba en vértices; «cero huecos nominales» no cubre las costuras.**
- **Dónde:** `verify_channel_reaches_v30.py:84-92` y `:114-121` muestrean únicamente en los vértices de la malla de 6 m.
- **Consecuencia:** un hueco entre una pieza inclinada y una cara roadway conservada que no contenga ningún vértice pasa el control (`README.md:9`).
- **Posición de las caras:** `:35-41,56` usan solo `origin`, sin rotación. Si alguna pose conservada lleva orientación, la cara se sitúa mal. Esto es un **límite**: el esquema de `pieces.json` no está entre las fuentes.
- **Hash:** la comprobación (`:44`) cruza el archivo con el manifiesto del mismo `fit`, no con el PBO de agua `07c5295f`.

## P3

**P3-1. La tormenta verifica el ajuste del viento, no un oleaje mayor.**
- **Datos:** en la serie reparada, el mínimo en calma (0,0639703) es inferior al de tormenta (0,064074) (`wave-fixed-verification.json:1156,1171`). En el baseline V1 hubo exposiciones en ambas fases (116 y 47 en total frente a 58 y 24 en tormenta).
- **Por qué:** `weather_reached` lee `GetWindSpeed()`, es decir, el valor fijado (`init.c:107`; `read_water_temporal_v30.py:71-74`).
- **Consecuencia:** la evidencia no muestra que la tormenta sea el peor caso. El margen observado es de unos 0,064 m frente a una depresión de onda de unos 0,12-0,13 m. Es correcto como PASS, pero «calma y tormenta» no equivale a «envolvente máxima».

**P3-2. Tres problemas de informe en la propuesta de calado.**
- **Recuento de los 88 vértices:** `high_water_vertices_below_1m` (`repair_current_fairways_v30.py:72`) no distingue los vértices que ya estaban por debajo de 1 m de los que se empujan bajo el suelo. El testigo de Neva (0,975 exacto, una banda) sugiere vértices en h = 1,0 con nivel de vértice ≥ 2 y plano de celda promediado de 1,975 (`v30_common.py:95-104`; `profile_inland_v30.py:315-317`).
  - **Límite:** no hay una definición fijada de «agua alta», si por nivel de vértice (`:54`; `check_floor_feasibility.py:35`) o por plano de celda. De esa definición depende la propia excepción.
- **Rebajes de 1 ulp:** con x ≈ 0, el redondeo (`:66-67`) puede rebajar 1 ulp y contar como cambio. Conviene publicar la distribución de los 6.305 vértices.
- **Motivo de la capacidad nula:** el certificado (`check_floor_feasibility.py:41-46`) no registra si cada testigo tiene capacidad nula por el suelo o por estar fuera del ámbito. Lo he deducido por contraste con la propuesta, pero el certificado debería decirlo explícitamente.

**P3-3. Independencia parcial del comprobador de calado.**
- **Qué comparte:** `check_fairway_candidate.py:11,27,30` reutiliza `records` y `cell_planes` del productor; solo cambia el muestreo.
- **Consecuencia:** un error en la enumeración de caras del corredor quedaría oculto en ambos.
- **Tolerancia:** su umbral `<0,99` (`:35`) es la tolerancia histórica, no el objetivo de 1,001 m.

**P3-4. La composición pendiente debe exigir disjunción por caras, no por vértices.**
- **Por qué:** por clase (`cls==3` frente a `cls==0`), los vértices modificados son trivialmente disjuntos (`README.md:57`). Pero una cara mixta puede contener un vértice de cada corrección.
- **Qué hay que repetir sobre el compuesto:** pendiente, contorno, los 17 observadores, el comprobador de cauces y las rutas de lancha.

## Límites de esta revisión

- No he ejecutado nada.
- No he leído `audit_fairway_triangles_v30`, `engine_water_model`, `axes.json`, `pieces.json` ni los logs en bruto.
- `diagnostic-controls.json` solo contiene booleanos, así que sus controles no son verificables desde aquí.
- La aceptación global del mapa queda fuera de alcance.