# EV87-S — suavizado incremental, agua dinámica pendiente

**Base 1.0 no aceptada.** EV87-S pasa la no regresión geométrica estática, la superficie y la lectura nativa completa. La prueba temporal adicional encuentra margen reducido frente a fake-wave en orillas secas; no se promueve como solución del agua sobre tierra. EV82-B queda disponible como referencia operativa. El nuevo preview aislado es `P:/Mods/@DayZ_Baltic_StrictBankPreviewV1`.

## Qué cambió y qué se descartó

La primera pasada EV87 produjo 718 parches y 10718 cambios. Su geometría pasó, pero la cobertura absoluta no: aparecieron déficits nuevos de soporte nominal y mayor exposición de caras heredadas. El candidato original `a7146c27...` y todos sus FAIL siguen conservados, sin construir.

El inventario completo recorrió 41008 celdas de modificación/frontera y marcó 1110 discrepancias. EV87-S conserva a B los cuatro vértices de todas esas celdas: excluye 384 parches enteros y retiene 334, con 4987 alturas modificadas. No se volvió a resolver el optimizador. Consumidor independiente `cc2b94b1a1b86e8e139edd532be9d77f95edc3526a5af1706c5dc29f2bfc41a0`: `PASS_INCREMENTAL_NONREGRESSION`, 249.735 s. El contrato absoluto global continúa `FAIL_WITH_INHERITED_OPEN`; no se convirtió el FAIL anterior en PASS.

Las protecciones, caras mojadas P/F/mar y signos de vecinos permanecen. No hay nuevos quiebros >30° ni extremos débiles, ni máximos de sector peores. Desplazamiento máximo de cruce 0.468685 m. La media cuadrática angular del banco seco baja 1.422570→1.409295 y del interior 0.757290→0.756497; p99 de banco prácticamente igual. Los perfiles incluyen un pico piramidal sin modificar: no es suavizado uniforme ni cierre de BALTIC-007.

## Paquete y motor

- NPZ `8e239f8e2815b61a920421af1dfbb1b64f353ab4978d633eb39fe74f04946d1b`.
- 352 teselas regeneradas, 1904 solapes exactos; 615 PAA y WRP cambiados, 6211/6827 entradas conservadas. 4920 mips nuevos verificados con negativos y decodificaciones nativas de control.
- Mundo `727fadeaf1a26fb4ae8362cc894e80e83194c64d5062ac7c2512b79879721420`; agua idéntica `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`. OPRW `dcdd41ebe2839d1a19ee08c71126dca2f23e9a81b4d8f6ba81f5fb536a195541`. 18033 objetos/materiales exactos en 0WZD fuente.
- Run servidor `20c41dc7-ac5b-411b-9f9c-04fe28af199d`: 4194304 vértices, 1212 puntos calibrados y 1205 planos; 25.871 s, máximo error de vértice 1.52588e−5 m. Snapshot `f69470851e82ce01f144a5530f1e28edf6541a3ef82cdf270bb20778103281c8`.

El preparador calculó los puntos nuevos y su CSV correctamente, pero olvidó guardar `points` en `reference.update`: el JSON conservaba alturas B. V1 falló en diez puntos. Se preservan referencia V1 `8cb6f96d...`, verificador `230d6540...` y FAIL `dd97462b...`. V2 reconstruye las referencias por una solución independiente del plano triangular y las contrasta con el CSV enviado, sin cambiar terreno, misión, snapshot ni tolerancia nativa de1mm. Referencia V2 `f748ec16...`, verificador `be9a531e...`: PASS y negativo nuevo que rechaza referencias obsoletas. Máximo error calibrado 0.000480 m. Para futuras misiones, no heredar el preparador sin añadir `points` al JSON.

La lectura completa encuentra cero flags de agua sobre clase seca en la fase observada; 23 puntos de clase agua sin presencia y327 consultas escalares positivas sin flags. Ocho consultas Q nuevas caen en alturas rebajadas. La ausencia de flags NO equivale a ausencia de agua dibujada.

## Hallazgo temporal nuevo: no confundir plano estático con oleaje

Run servidor `a1f95dd7-d460-43f0-82e8-8410f5e7c37d`, misma build: 241 muestras/60.002s, viento20m/s, todos los162 vértices modificados con margen nominal<25cm y16 controles vecinos. No cambió geometría ni se lanzó cliente.

- Ninguno de los162 tiene flags Sea/Pond durante la serie.
- 22 dan GetWaterDepth>2cm a la altura nueva; 12 lo hacen al consultar simultáneamente en la altura B. Son dos alturas de consulta en el mismo mundo H, **no** un segundo run B.
- Profundidad coincide con `GetWaterSurfaceHeightWithFakeWave − ground − .01` con error máximo0.0000604m. El cambio por altura de consulta coincide con B−H con error máximo0.0000116m.
- Fake-wave alcanza0.19325m sobre la consulta nominal en esta muestra. Esto NO prueba un límite universal de20cm ni la causa de los rectángulos grises.

Snapshot temporal `27575a64c5e448c44fe14f86fb7b80dc976fbcaa7402b5a427f68f9be070a526`. `archive/build/scalar-probe/series-review.json` conserva todos los puntos y rangos. Hace falta una regla defendible de margen dinámico antes de aceptar rebajes cercanos al agua; no elevar tolerancias ni repetir variantes a ciegas.

Ambos runs terminaron orderly, lease liberado, owner null/self none y banco libre. RPT conserva errores de recursos, avisos pond y fuga MCPPollCallback al cerrar; no se declara limpio. No hay prueba gráfica nueva, ni lancha, Terrain Builder final o navmesh.

## Continuación

EV88-Q estudia un perfil local ancho en X2220/Z7242 desde B, permitiendo bajar cresta y subir hombros. No se apila sobre S sin una integración revisada. El antiguo target quintico se descartó antes del solver por crear mesetas; el primer stencil mixto de Q fue corregido antes de ejecutar. Autor y consumidor independientes, una solución, sin barridos.

Los pendientes de agua aparente, rectángulos grises, contornos/finales, reservas y grandes lagos continúan abiertos. Evidencia externa completa: `E:/DayZ-Baltic-Build/v30-global-strict-bank-relief-20261010`; `manifest.json` fija hashes y los archivos grandes no incluidos en Git.

La revisión independiente V2 confirma el defecto del oráculo y conserva sus límites
en `archive/build/native-reference-v2-independent-review.md`. La nueva comprobación
`archive/historical-fixes-recheck.json` identifica once archivos de correcciones
históricas exactos, sin deriva; no renueva la aceptación física sobre otro terreno.
