Reviso el plan RoadB2 en modo sólo lectura y entrego juicio único.

**Veredicto: SOUND-with-fixes.** El plan acota bien: reutiliza B0/B1 por hash, declara el centro como hipótesis doble, separa la sonda nativa con plan propio, no deriva ancho útil de bbox y preserva P9/P10/P11. Los fixes siguientes son necesarios antes de implementar la unidad offline; ninguno exige motor ni council.

**Lo que está bien**
- Hipótesis explícitas sin selección por mejor ajuste (línea 35). Correcto frente a falsos PASS.
- Reutilización por hash de B0/B1 sin repetir extracción (línea 11). Cumple la petición.
- Sonda nativa diferida con exigencia de firmas en scripts.pbo fijado y salida INCONCLUSIVE si no hay identidad (líneas 26 y 47).
- Negativos útiles: inversión de matriz, eje intercambiado, curva con bbox mayor que huella (líneas 62 a 64).

**Fixes requeridos, medibles**

1. **Oráculo independiente del generador.** La línea 40 prueba "poses y huellas" pero no dice quién calcula lo esperado. Si el test reutiliza la transformación del generador, el PASS es circular. Fix: las predicciones de cada instancia bajo H_origen y H_centro se escriben como fixtures numéricos literales antes de ejecutar el generador, derivadas por una ruta distinta (segunda implementación o cálculo documentado a mano desde las caras B0). El test compara salida contra fixture; nunca recalcula.

2. **Definir "centro".** La línea 31 cita centros locales de B1 sin decir si son centro de bbox, centroide de vértices Visual o boundingCenter de configuración. Las tres dan números distintos en la curva. Fix: nombrar la definición, su hash de origen y marcar las otras dos como no observadas.

3. **Convención de matriz como tercera incógnita.** Con giro 90 grados, la huella predicha depende de fila/columna y mano. La línea 63 lo trata como negativo, pero en realidad es hipótesis no fijada: hay 2x2 predicciones, no 2. Fix: o bien se ancla la convención [EXACT] con las 28 instancias de puente ya selladas comprobando una pose rotada conocida, o bien la receta publica cuatro predicciones etiquetadas. No mezclar ambas cosas.

4. **Distinguibilidad cuantificada.** La línea 42 exige que las hipótesis sigan distinguibles tras serialización, sin umbral. Fix: separación mínima entre huellas predichas de H_origen y H_centro superior a diez veces el paso de cuantización observado en prism-b3-quantization, y superior a cross 0.03m. Añadir control negativo: un test que falle si ambas predicciones coinciden.

5. **Alcance de la primera unidad.** Los pasos 2 y 3 (mundo nuevo, lectura de binario) aparecen en la misma lista que la receta. Fix: etiquetar pasos 1 como UNIDAD1 autorizada y pasos 2 a 5 como pendientes de plan propio. La revisión del lector OPRW (línea 19) entra en UNIDAD1 sólo como lectura de código, con conteo de tamaño del WRP original, no como censo de 2.578.398 objetos; ese censo probablemente excede 120s/2GiB en Python y debe presupuestarse aparte.

6. **Estados desconocidos.** La línea 67 sólo permite RECIPE_HYPOTHESES_READY e INCONCLUSIVE_DISCOVERY. Fix: añadir RESOURCE_FAIL (presupuesto agotado) y READER_INCOMPATIBLE (lector OPRW no apto para el tamaño real). Cada fixture debe llevar campos verificado/asumido/no observado, no sólo la salida nativa futura.

7. **Elevación sobre suelo.** La línea 36 eleva los objetos. Correcto para aislamiento, pero deja el contacto Roadway con terreno como no observado. Declararlo así en la receta para que nadie lo lea como validación de pavimento.

8. **IDs sin colisión.** La línea 39 resuelve IDs por censo pero no da regla. Fix: regla determinista (máximo existente más uno, con hash de la tabla de origen) y test de unicidad.

**Lo que no debe cambiar**
No exigir motor en UNIDAD1. No tocar roads.tv4s ni RoadNetwork. No colocar tramo49, cruce49/301, Narva71 ni kit118 dentro del ensayo. Mantener banda8m fuera como cobertura.

**Condición de cierre de UNIDAD1:** receta con tres instancias, fixtures de predicción por hipótesis y convención, tests que fallan ante igualdad de hipótesis y ante fixture autogenerado, medición de tiempo y memoria bajo 120s/2GiB. Sin build, sin DayZ, sin pavimento.

FIN_REVISION