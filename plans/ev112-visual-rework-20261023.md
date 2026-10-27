# EV112: corrección tras la vista del 23-10

Estado: trabajo abierto. La vista de Guillermo rechaza el aspecto del candidato RuntimeMarginsV2. La sonda anterior conserva su valor técnico, pero no acepta este resultado visual. Esta petición viva amplía el seguimiento visual de `ev112-plan-astra.md`; no rebaja sus umbrales ni convierte pendientes en PASS.

## Petición y decisiones vivas

- «En general, el rio es muy poligonal (muchas esquina y tramos rectos si lo ves a media y alta altura)»; después precisa «casi todos los rios son angulos rectos practicamente a partir de media altura». El alcance es el trazado de los ríos del mapa, incluido el agua conservada como charca, no solo kit-118.
- «El ultimo extremo de un rio junto a ese kit» no se ve. Localización de trabajo: los extremos de kit-118 y el cauce contiguo; falta enlazar una captura señalada con el extremo concreto. La comparación de geometría ya detecta pérdidas en ambos extremos del piloto.
- Junto a la presa hay terreno con picos y caras poligonales; pide un repaso general.
- Confirmación posterior: «y en el terreno igual! hay mucha \"piramide\"». El repaso cubre todo el relieve, no solo Narva ni los máximos aislados.
- Picker aprobado: **piloto de cauce continuo con geometría propia y materiales vanilla**. Se ejecuta primero en kit-118 y un tramo NE/SW; la extensión requiere comprobar agua, lecho y colisión.
- Picker 23-10: **mar hasta el pie de la presa, con tierra solo en los apoyos laterales**. Sustituye el acabado visual anterior de conservar las 33 celdas del antiguo lecho seco. No autoriza descalzar la presa, invadir reserva/plataformas ni cambiar otros encuentros mar/charca.
- Se mantienen secos los 12 islotes; la excepción de c2 sigue limitada a sus 11 vértices. 015-45 conserva el disco de 60 m pendiente. No se confunde este nuevo trabajo visual con los 271 labios/juntas de hormigón ya declarados pendientes.

## Hechos comprobados

Base: terreno `07054c46ebf2861bc905fe2d68fb3b734d7b8e9ad1d538c73a7ee745edd56d62`, huella `49ee2a69db85f047425f8e1d31a964f92771ceb19b203c42570b04c3c6207de5`; mundo desplegado `751823ac65cd56c9093de9705ee30b08a448a69606690c1363ecf944a15ac838`, agua `97edcafe1fc86d9abb4c3aa591d5081a6dd940b87020069fd45c04f8d0deae43`.

1. `tools/water/streambed_kit_v31.py:178` restringe el eje a N/E/S/W/NW/SE. `:424` solo admite curvas de 45 grados o ciertos codos de 90; `:435` busca sobre la rejilla. Su cabecera explica que NE/SW se convierte en escalera de codos. Los 49 sitios construidos suman 2.897 giros de trazado, 2.321 de ellos codos. Son direcciones del eje; las piezas físicas redondean algunos encuentros.
2. Kit-118: eje de 298,37 m, siete giros, dos codos y recta máxima de 102 m. Los extremos geométricos son S=(8268,8934) y N=(8220,9204). El tramo mojado del informe solo cubre estaciones 11,655–278,435 m; hay dos piezas recortadas.
3. La geometría final pierde agua que existía en EV107: muestreo de 1 m en X=[8130,8352], Z=[9189,9222] da 246 m² antes y cero ahora; Z=[8928,8943] da 120 m² antes y cero ahora. Solo hay piezas de kit-118 en la ventana ampliada. Esto demuestra la pérdida local de representación; no demuestra aún qué extremo señalaba Guillermo ni la continuidad jugable de una solución.
4. G3 (`evidence/v31-pond-layer-2026-10-13/ev112/ot1/gates/gate_g3_continuity.py:90`) mide solo `wet_span`. G11 (`.../gate_g11_junctions.py:187`) omite las uniones de sitios cuyo modo no es `reach`. Kit-118 y kit-7 son `component`. Un PASS de esas comprobaciones no acredita los finales originales de los pilotos.
5. El censo global actualizado encuentra 111 vértices de pico y cinco de depresión en tierra con prominencia >0,5 m. No son 116 bugs independientes. Su dominio libre antiguo no incluye todas las guardas de orilla posteriores: no sirve como permiso de edición. El rótulo interno «Baltic EV110 land» es legado; este pase usa el hash EV112 indicado arriba.
6. En un cuadro de 600×600 m junto a Narva, excluyendo celdas con un vértice bajo la charca o bajo 0,8 m, 37 celdas tienen un cambio de normal >20 grados entre sus dos triángulos; máximo 46,72 grados. Es un inventario descriptivo, no un umbral de aceptación. El censo de picos aislados no detecta todas esas aristas. Hay además un pico de prominencia 2,67 m en (2130,6672), protegido por `narva`.
7. Las 33 celdas retiradas de la capa de agua delante de la presa tienen las cuatro esquinas finales sobre el mar de referencia a 0,75 m. El lecho queda expuesto. Se conservan exactamente los 21 cambios del contrato anterior. Naturalizarlo exige una nueva capa explícita, no alterar el contrato anterior para hacer pasar su gate.

## Ejecución de la corrección

1. **Piloto de trazado continuo — aprobado por picker el 23-10.** Implementación [DESIGN]: geometría propia de cauce, agua y lecho continuo con materiales vanilla, siguiendo el cauce anterior y el censo; conservar anchos/clases, extremos y receptores. Comparar kit-118 y un tramo NE/SW representativo a escala peatonal y media altura. No basta con penalizar codos: podría producir rectas todavía mayores. El prototipo deberá demostrar soporte del lecho, colisión y continuidad antes de extenderlo al mapa; esta aprobación de diseño no afirma que esas propiedades estén ya resueltas.
2. **Extremos.** Inventariar ambos extremos de todos los sitios, incluidos los pilotos `component`, y los tramos que siguen como charca. Comparar con la referencia previa al recorte, clasificar receptor o cabecera natural y corregir la pérdida de agua. Extender la prueba de uniones al receptor externo; control negativo con cola eliminada que mantenga íntegro el cuerpo del kit. No extender agua hacia un receptor elegido solo por cercanía.
3. **Narva.** Preparar una capa de batimetría separada para llevar el mar al frente de la presa. Enumerar vértices, delta y banda de costa antes/después. Conservar los apoyos laterales, el terreno que entierra la cara aguas arriba y la estructura. Verificar que no aparece mar bajo charca, ni un paso por debajo del muro, ni pérdidas de apoyo. La nueva decisión visual está aprobada; Narva B ya se integra en Q y sus25 controles delanteros pasan servidor. Falta la vista personal.
4. **Relieve.** Auditar picos, depresiones, pliegues y transiciones junto a cauces en todo el mapa. Medir por dominios (libre, orilla, kit, puente, Narva, reserva/plataforma) y conservar agua/islas/conexiones. Corregir con una transición amplia donde corresponda; no perseguir solo el contador de máximos locales ni aplicar un suavizado global que deshaga las orillas.
5. **Integrar y comprobar.** Volver a generar `bury` y usar su última huella; agua exacta, soporte de objetos/bosque y consumidores afectados; builds aislados y hashes desplegados. Sonda de extremos y controles obligatorios, vistas comparables desde suelo y media altura. No se entrega ni se acepta visualmente por cantidad de pruebas.

## Criterios de cierre y límites

- Ningún final objetivo desaparece por un recorte sin representar su receptor o su terminación natural. Las exclusiones se listan por sitio; cero medidas no es PASS.
- El trazado del piloto debe dejar de mostrar la escalera cardinal reportada; no se inventa una métrica estética universal. Medidas de curvatura/rectas y vistas a la misma escala, además del visto bueno visual de Guillermo.
- Mar delante de Narva hasta la cara de la presa en el rango de agua que se valide; tierra solo donde deba apoyar la estructura. Delta y soporte verificables.
- Ninguna regresión de los contratos de agua, protecciones vigentes, 12 islotes, c2 y disco 015-45. Cambios de diseño adicionales se proponen antes de integrar.
- No hay corrección visual de producción aceptada. Q está integrado con bosque, compilado y desplegado de forma aislada; servidor786/786 PASS. La vista personal queda preparada. El run propio se cerró ordenadamente, lease liberado y banco libre; ningún cierre ajeno.

Evidencia: `evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/README.md` y originales en `E:/DayZ-Baltic-Build/v31-pond-layer-20261013/ev112-build-20261018/view-20261023/`.

Seguimiento 24-10: candidato P, relieve general C y Narva B combinados sin solape; véase `../evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/continuation-20261024-a/README.md`. Todo runtime, aceptación visual y expansión siguen pendientes.

Seguimiento posterior24-10: sonda compilada y desplegada aislada con786 puntos; preflight correcto y banco ocupado. Bosque B pasa soporte después de93 exclusiones, quedan gates de contexto/densidad y compilación. Inventario de102 extremos,66 candidatos de pérdida todavía abiertos. Estado y reanudación en `../evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/continuation-20261024-b/README.md`.

Seguimiento final24-10: Q corrige las dos juntas numéricas de colisión, conserva las superficies visuales y pasa786/786 en servidor con2.560.922 elementos de bosque. Gates afectados revalidados; mundo compilado y leído. Vista conjunta preparada y global todavía abierto. Carreteras iniciadas según P11:11 fallos heredados y cuatro candidatos descartados por nuevos pliegues. Estado completo en ../evidence/v31-pond-layer-2026-10-13/ev112/visual-review-20261023/continuation-20261024-c/README.md.

## Comparación de optimización solicitada24-10

P7 amplía el cierre con comparación reproducible frente a Chernarus. Véase
`ev112-performance-chernarus-20261024.md`: inventario de Q y vanilla instalado
completado; rendimiento INCONCLUSO hasta las mediciones cliente/servidor.
No aplazar esta puerta hasta después de extender el piloto por todo el mapa.

## Revisión presencial 27-10: rechazo y alcance procedimental

Guillermo rechaza el saliente en L delante de la presa, la alineación del puente y las orillas con rectas/arcos demasiado regulares. Exige detección y reparación procedimental de todos los casos, no una reparación local. Incorporar NARVA-VIS-01/02/03 como regresiones de validación y del generador: [evidencia](../evidence/visual-tour-20261027/README.md). Causa exacta y plan ejecutable aún pendientes; no dar por aprobado un algoritmo ni inventar umbrales. Se conserva toda protección y tolerancia anterior.

Segunda parada: **KIT118-VIS-01/02** añade lechos demasiado salientes y un extremo solapado con carretera, señalados por Guillermo como errores de revisión. Incorporar controles de envolvente completa del lecho contra terreno/agua independientes, y de ambos extremos contra corredor viario y accesos del mundo compilado. Aplicar a todos los cauces; separar cruces intencionados, no ocultarlos con una exclusión general. [Reporte deduplicado](../evidence/visual-tour-20261027/kit118-feedback.json). Causa, geolocalización exacta y diseño de reparación pendientes; tolerancias/protecciones sin cambios.

Tercera parada: **CONT65-VIS-01** vuelve a rechazar un lecho demasiado saliente en un segundo cauce. Mantenerlo junto a KIT118-VIS-01 como dos regresiones reales del mismo patrón; no afirmar causa común sin aislarla. Censar y reparar procedimentalmente la integración de lechos, transiciones y siluetas en todos los sitios. [Reporte](../evidence/visual-tour-20261027/continuous65-feedback.json). Revaluar el plan MLOD pendiente contra estos casos antes de implementar; la factibilidad offline del piloto seco no acredita naturalidad ni integración visual.

Cuarta parada: carretera49 bien visualmente en el tramo visto, con pavimentado pendiente y sin prueba de conducción. **ROAD49-RIVER-VIS-01:** río adyacente a la derecha rechazado por zigzags. Guillermo exige detección y corrección procedimental de todos estos casos hacia curvas continuas y naturales; conservar cauces, anchuras, extremos, receptores, cruces, topología y protecciones. Sigue vigente el rechazo de arcos excesivamente regulares; no basta con redondear codos aislados. Identificar el río y contrastarlo con el censo previo antes de atribuir la carencia a un algoritmo concreto. [Evidencia](../evidence/visual-tour-20261027/road49-feedback.json).

Cruce adicional **CROSSING-VIS-01**: posible puente ausente, personaje en X4789.515/Z5516.522 mirandoSW, ubicación leída por MCP y confirmada por el usuario. Confirmar cruce real y ausencia/carga/pose en WRP; inventarios históricos y consulta truncada no prueban ausencia. Añadir censo independiente de TODAS las intersecciones carretera/agua y contrastarlo con puentes y continuidad desplegados; validar sólo los puentes generados deja fuera los omitidos. [Evidencia](../evidence/visual-tour-20261027/additional-crossing-feedback.json).

Aclaración de CROSSING-VIS-01: Guillermo confirma una **carretera partida por un río**, fallo de revisión geométrica. Tratar el defecto como rechazo visual real y mantener sólo su mecanismo como pendiente. Revisar continuidad de TODOS los cruces a partir de geometría independiente de la lista generada; ampliar la revisión geométrica también a orillas de ríos Y mar. No restringir a los ejemplos visitados.
