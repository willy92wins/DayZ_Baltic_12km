# Puente al relieve de toda la superficie

Estado: recomendación de cobertura [DESIGN], sin autoría ni cambio de terreno. El censo ordena dónde mirar; no declara qué forma está mal.

## Cobertura medida en B

B (`f9fb23de…61f0`) tiene 2048² vértices a 6 m. El censo nativo EV93 v2, anclado a `verify_ev87.py` (`964206…fee27`), cuenta una vez cada bisagra diag/vertical/horizontal: 12.566.533 en 1.024 sectores de 64² nodos (384 m). En las tres familias conserva ángulo y las cuatro incidencias exactas; entre bisagras con ANY elegible, p99/max son diag 12,69°/63,46°, vertical 13,37°/83,05° y horizontal 12,98°/81,13°. El v2 corrige el `all_eligible` erróneo del v1. El dominio `eligible` suma 2.988.565 vértices, particionados en banco 581.794, interior 2.340.816 y `eligible ∩ wet_support` 65.955. Los diagnósticos separados registran 1.205.739 `protected`, 1.179.270 `fixed` y 999.352 `waterline_blocked`; las máscaras se solapan y no deben sumarse. La elegibilidad exacta sigue siendo la fórmula EV87 P/F/clase/fijos, no una etiqueta geométrica.

El censo multiescala mide prominencia cardinal positiva `max(0,H[r,c]-max(H[r±d,c]))`, análoga en EW, solo donde hay contexto completo: d=1/2/4 son 6/12/24 m. Entre elegibles, d12 tiene 359.477 nodos positivos en algún eje y 48.339 en ambos; d24 tiene 592.635 en algún eje y 103.003 en ambos. La cola congelada EV87 selecciona 5.450 semillas con el AND `eligible ∧ ángulo incidente >30,0001° ∧ prominencia d1 >0,1 m`; el informe multiescala cuenta 31.497 elegibles omitidos con d1>0,1 m. EV93 mantiene por ahora esas 5.450 semillas, su primera capa 17×17 disjunta y 4.747 solapamientos pendientes (HANDOFF, línea 23). Son universos de señal/selección, no recuentos de defectos ni de altura corregida.

## Siguiente unidad concreta

Extender **solo el inventario/preflight** a una cobertura exhaustiva de ventana, antes de decidir otra autoría. Partir los 2048² vértices en núcleos no solapados de hasta 13×13; por geometría serían 158×158 = 24.964 núcleos, cifra calculada, no ejecutada. Expandir cada núcleo dos nodos por lado para formar WINDOW17; los bordes del mapa requieren soporte recortado y validación propia. Asignar cada núcleo una sola vez a un sector 64×64 por su ancla, y conservar las cuatro incidencias completas de bisagras que crucen sectores.

Ordenar dentro de cada sector y de las tres poblaciones elegibles (`bank`, `interior`, `wet_support`) por rondas de cuatro canales independientes: máximo ángulo nativo incidente y prominencia d6, d12 y d24. Para cada pareja núcleo/población, el valor del canal es el máximo sobre sus vértices elegibles; ordenar descendente y desempatar por ancla fila/columna. Intercalar los canales y las poblaciones, deduplicar al emitir el núcleo y anexar por coordenada los núcleos todavía ausentes, incluidos los que no tienen elegibles. Ningún umbral elimina candidatos y cada núcleo aparece exactamente una vez; se conservan todos sus tags. Estas métricas solo priorizan revisión: los ángulos son no firmados; las prominencias cardinales solo registran máximos sobre su eje, por lo que no describen valles, rampas monotónicas ni intención. El fallback cubre también los bordes sin contexto d4 y zonas con señal cero. No usar relief3x como verdad ni como etiqueta.

El preflight por WINDOW17 debe reconstruir allí los vértices EV87 elegibles desde B y P/F/SEA, los fijos/protegidos, estencils, vecindades D8, bisagras completas y caras del índice EV93 que intersecten la ventana; derivar guard y máscaras de esa geometría. EV91/92 da un contrato de ventana local (17×17, núcleo13, collar2), pero sus 85 variables, 43 guardadas, 42 libres y alpha pertenecen al foco 840,370: no se copian. Los núcleos no se solapan, pero sí sus márgenes; cualquier secuencia futura debe rebasar cada preflight sobre el B actualizado y volver a ejecutar los gates del consumidor. El plan EV93 aprobado solo autoriza preparar índice/cola y generalizar preflight, no resolver estas 24.964 ventanas ni afirmar aceptación global.

## Riesgos que siguen abiertos

1. Las señales no son defectos: bisagras unsigned no expresan convexidad deseada; d1/2/4 dejan sin contexto 8.188/16.368/32.704 vértices respectivamente. El orden exhaustivo evita omisiones, no prueba materialidad visual.
2. Elegibilidad y guard varían con P/F, agua, máscaras y caras físicas/visibles; copiar los conteos del piloto puede modificar soporte fijo o ignorar una incidencia de collar. La actualización secuencial puede cambiar el orden y las señales vecinas.
3. P12 pide relieve selectivo en zonas jugables; P14 pide contorno general suave y orillas sin agua indeseada. Cubrir el dominio elegible no decide esa prioridad ni habilita modificar fijos/protecciones, y un PASS geométrico offline no prueba navegación, agua dinámica, render o aceptación de juego.

## Anclas

- `P:\DayZ_Baltic_12km_dev\CLAUDE.md:3-8`; `product-spec.md:18-20` (P12/P14).
- `E:\DayZ-Baltic-Build\v30-global-bank-extension-20261010\plan.md:5-9,27` (EV93 aprobado, límites de alcance). SHA256 `CCC018A9E1CC8A51B075A91905B1CBE7D3CDAF72040E51992F2AC55DB8AD7E82`.
- `...\ev93-face-index\surface-census\v2\summary.json` (`scope.population_vertex_counts`, `families.*.global`, `formulas`), SHA256 `E555A736C37054FD4AA4CCC3AA699B53E297F017C498527EEC68B85A2CD307A3`; NPZ `sector-native-curvature-census.npz`, SHA256 `EF3DB76BB2FA8CB468CC60614EEB36A981E75E7886E6D0181AFD2B20E1194935`.
- `E:\DayZ-Baltic-Build\v30-bank-multiscale-census-20261010\summary.json` (`formula`, `d1`, `d2`, `d4`, `crosscheck_against_ev87_preflight`), SHA256 `12CD2F71A6F719D019DB6DBF71D843D52D3D6233B96E0C8B68BEEF0774A49EDA`; arrays NPZ SHA256 `6BDD42B298E538B4ECCE3063A8A53E3AAFB65B0F15373D78254EA8BC57E0C213`.
- `...\v30-global-strict-bank-relief-20261010\review-independent\verify_ev87.py:261-271,836-871` (ángulos/incidencias, elegibilidad y selector); `...\v30-wide-bank-fairing-pilot-20261010\ev91-descent\plan.md:7-23` y `...\ev92-damped\plan.md:13-38` (geometría/guard locales y prohibición de copiar sus dimensiones).


