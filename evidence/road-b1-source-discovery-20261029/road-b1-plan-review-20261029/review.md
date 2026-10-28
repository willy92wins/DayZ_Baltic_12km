**Veredicto: SOUND-with-fixes.** El plan acota bien el pivote y evita censos repetidos, pero el paso 1 busca en el sitio equivocado y el paso 3 puede cerrar sin poder discriminar hipótesis.

**Hallazgo 1, fuente editable ya resuelta (repro).** `tools/terrain/wrp0wzd.py:1-10` documenta el 0WZD con cuatro secciones: cabecera, alturas, materiales y objetos; `wrp0wzd.py:49` exige `o == len(b)`, sin bytes sobrantes. Toda fuente editable del pipeline que pasa por ese lector no contiene ninguna sección RoadNetwork. Por tanto "definición RoadNetwork si existe en la fuente WRP editable" ya tiene respuesta negativa para 0WZD. Modificación: el descubrimiento de 120s debe mirar la capa de formas de carretera y la biblioteca de plantillas del proyecto Terrain Builder bajo W/tb y los recibos package-kit7, no el 0WZD. Si no hay capa de formas, el único consumidor observable es WRP_OBJECT por TXT/0WZD; si la hay, la vía RoadNet se declara INCONCLUSIVE porque el pipeline no la decodifica.

**Hallazgo 2, tabla compilada no puede negar RoadNet (repro).** `package_visual_forest_ev112.py:67-71` detiene el barrido en la primera fila inválida y `:30-43` sólo acepta la tabla de modelos que contiene el marcador baltic_water_v30. Cualquier sección posterior nunca se inspecciona. El plan lo reconoce, pero debe prohibir explícitamente extender ese lector a RoadNet dentro de esta unidad.

**Hallazgo 3, convención de pivote ya existente, no citada.** `package_visual_forest_ev112.py:117` calcula raíz = posición menos R traspuesta por centro de bounding del ODOL, verificada a 5mm contra terreno para bosque (`:118-119`). Es la única transformación local->mundo demostrada en este repositorio para objetos 0WZD. Modificación: nombrarla hipótesis H1, su variante sin trasponer H2 y la de recentrado doble H3; no redescubrirlas.

**Hallazgo 4, contraejemplo a las tres poses.** Identidad, giro90 y curva sólo discriminan H1/H2/H3 si el centro de bounding de la pieza tiene componente horizontal no nula. Para una pieza asf1_25 con centro cercano a su origen (bc horizontal ≈ 0), las tres hipótesis producen la misma superficie mundial y la unidad cerraría "consumidor demostrado" sin haber separado nada. Modificación: leer bc de cada pieza B0 por hash antes de fijar poses; exigir al menos una pieza con |bc horizontal| > tolerancia de contacto, y registrar NO_DISCRIMINA si ninguna la cumple. "Curva" debe definirse como pieza curva en pose identidad, no como trayectoria curva.

**Hallazgo 5, oráculo de la pose.** Para WRP_OBJECT, la única lectura de pose es la matriz 0WZD en `wrp0wzd.py:38-47`. El contraste con superficie "mundial completa" requiere la tabla compilada; ese paso ya exige Binarize y es plan posterior, como dice la línea 37. Debe quedar explícito que la primera unidad sólo contrasta pose fuente contra geometría local, no contra compilado.

**Puntos correctos sin cambio.** 28 instancias de puente ≠ 28 cruces, config no prueba consumidor, prohibición de bbox como ancho útil, P9 fondo1/calado0.95/corredor24, P11 cross0.03/grade0.065/chord0.03 con exclusiones no evaluadas, P10 terreno antes de mapeado, sin DayZ/WRP nuevo.

**Próximos pasos concretos.**
1. Reescribir paso 1 con las anclas de Hallazgos 1 y 2; salida única con estado WRP_OBJECT_ONLY, SHAPES_PRESENT_UNDECODED o INCONCLUSIVE_CONSUMER.
2. Añadir a paso 3 la comprobación de bc y el estado NO_DISCRIMINA.
3. Añadir H1/H2/H3 y la pose fuente como único oráculo de esta unidad.
4. Mantener presupuesto 120s/2GiB; ninguna autoría hasta cerrar 1.

FIN_REVISION