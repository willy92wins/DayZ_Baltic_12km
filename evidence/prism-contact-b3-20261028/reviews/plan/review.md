**Veredicto: SOUND-with-fixes.** El diseño es matemáticamente válido y las puertas son falsables, pero hay un hallazgo material sobre el margen de interior frente al ULP mundial que el plan debe convertir en umbral, no sólo en dato reportado.

**Validez matemática del operador**

La homotecia XZ en torno al centroide con λ=1+δ/r es correcta en aritmética exacta:

- El triángulo original queda contenido en el ampliado, y cada esquina original es punto interior estricto del nuevo, porque c+(V−c)/λ está en el segmento abierto entre el centroide y un vértice.
- Desplazamiento máximo de esquina exactamente δ, en la esquina de radio máximo. Las otras se mueven menos.
- Techo en el plano original, base en ese plano menos 180/512: el prisma sigue siendo recto, convexo, 6 puntos/8 caras, y conserva el emparejamiento techo/base que el verificador de la familia ya usa (verify_dry_road_mlod_ev112.py:82).
- Las normales no cambian en exacto: caras laterales paralelas a las originales, techo/base en el mismo plano. Esto simplifica el parche, ver fix 3.
- Los 12 componentes no tocan el bbox según el descubrimiento de elegibilidad, y δ es el mismo half_side que ya dio bbox exacto, así que la conservación exacta de bbox es alcanzable.
- Overlay: extensión horizontal ≤δ=0.00195 m < 0.01 m. Error vertical sobre triángulos vecinos acotado por δ por diferencia de pendientes, muy por debajo de 0.02 m.

Mapeo de índices: las filas vecinas de B2 devuelven componentes 1288/1290/1365/1366 para 700 y 1333/1334/1409/1411 para 723. Son índices base 0 del motor. Sumando 1 caen todos dentro de los 12 Component NNNN seleccionados (1289–1291, 1366–1368, 1334–1335, 1410–1412). Es coherente, pero el plan debe fijar esa convención en el verificador.

**Hallazgo material: margen interior frente al ULP mundial**

La distancia desde la esquina original al borde más cercano del triángulo ampliado es δ·h/r, donde h es la distancia del centroide a ese lado y r el radio máximo. Esa razón vale como máximo 1/2 (equilátero). Para triángulos rectángulos isósceles de una rejilla con diagonal, los valores son:

| Caso | Margen interior |
|---|---|
| Equilátero | δ/2 ≈ 0.000977 m |
| Rectángulo isósceles, hacia los catetos | δ·√2/3 ≈ 0.000921 m |
| Rectángulo isósceles, hacia la hipotenusa | δ/3 ≈ 0.000651 m |
| ULP float32 mundial en [8192,16384) | 2^-10 = 0.000977 m |

Los contactos están en X≈8256 y Z≈8941, dentro de ese intervalo. Por tanto el margen interior es **≤1 ULP mundial** en todos los casos, y 0.67 ULP en la dirección de la hipotenusa. El operador Minkowski rechazado daba exactamente 1/512 = 2 ULP. El plan cambia de operador por coste sin decir que reduce el margen a la mitad o menos.

Consecuencias:

- La puerta offline "interior estricto" se evaluará en coordenadas locales (origen 8262,7,8934, ULP ≈1e-6) y pasará con holgura de ~1e-3 m. Eso no dice nada de la hipótesis, que se refiere a la prueba de rayo en coordenadas mundiales float32.
- El plan ya pide reportar "distancia firmada y ULP mundial" pero no define pase/fallo en esa unidad. Sin umbral, un candidato con 0.67 ULP de margen sale OFFLINE_CANDIDATE_ONLY y la unidad nativa posterior no podría distinguir falsación de ruido numérico.

Fix 1 (obligatorio): definir el criterio como margen mínimo expresado en ULP mundial del contacto, con umbral fijado antes de implementar (recomiendo ≥2 ULP, que es lo que daba Minkowski). Si el diseño no lo alcanza, es REJECTED_OFFLINE sin ajustar δ, conforme a la propia regla del plan. Dado el cálculo anterior, el resultado más probable es rechazo, y el plan debería decir ya que ese rechazo es un resultado válido de la unidad, no un fallo de implementación.

Repro concreto, sin binario gigante: desde la fuente d130 leer sólo los 12 componentes con review_compact_collision_v31.load, para cada uno tomar las 3 esquinas del techo, calcular c, r, h por lado, margen = δ·h_min/r, sumar el origen, y comparar con numpy.spacing en float32 de la coordenada mundial mayor. El mutante de control que fija el hallazgo: candidato con λ aplicado y contacto desplazado 1 ULP mundial hacia el borde; con el umbral actual del plan seguiría pasando.

**Fixes menores**

2. Declarar explícitamente que verify_dry_road_mlod_ev112.py NO es consumidor válido de este candidato: rechazaría por volumen cambiado (línea 75) y por esquinas fuera de la rejilla visible (línea 79). Evita que Codex lo encadene como puerta de aceptación o lo "adapte".
3. Como las normales no cambian en exacto, la puerta debe exigir normales recomputadas desde los puntos guardados iguales a las guardadas (≤1e-6) y además bytes de normales idénticos a la fuente, o justificar por qué se reescriben. Reduce la superficie del parche XYZ.
4. La tolerancia 1e-6 de plano se sostiene porque Y local es pequeña y las pendientes del lecho son bajas, pero debe derivarse del ULP local de X y Z multiplicado por la pendiente, no fijarse como número suelto. Si la extensión local supera 16 m el ULP de X/Z ya es 1.9e-6.
5. Los 6 prismas que rodean cada contacto se solaparán entre sí tras la ampliación. Es esperado y Minkowski hacía lo mismo, pero debe quedar escrito para que convexidad no se lea como disjunción.
6. Fijar la convención índice motor = Component NNNN − 1 al "verificar los 12 identificadores".
7. Añadir al conjunto de mutantes: λ<1, homotecia sobre el centroide de la base en lugar del techo, y corner desplazado exactamente δ en una esquina no máxima. El control idéntico ya está bien planteado.

**Coste y protecciones**

Presupuesto geométrico respetado: 6/8 por componente, mismos conteos, masa por punto, bbox exacto, LOD no Geometry byte exactos. Consistente con ev112-dry-bank-mlod-materialization-20261027.md:55-62. Tiempos y memoria (60 s/2 GiB autor, 180 s/2 GiB consumidor) son holgados para un modelo. Sin compilación ni DayZ en esta unidad, correcto. Un candidato, una corrección por repro, sin ajuste de δ: coherente con falsabilidad.

**Product-spec**

P2, P9 y P14 no se tocan: ninguna escritura en agua, cauce, orillas ni terreno. P7 se respeta al no incrementar geometría. P10 queda en cabecera del plan. No se emite elección de producto ni se reaudita B1/B2/agua.

**Resumen**

El operador es correcto y conserva todo lo que el presupuesto exige. El defecto material es que el margen interior resultante es ≤1 ULP mundial, la mitad o menos del Minkowski descartado, y el plan sólo lo reporta en vez de gatearlo. Con el umbral en ULP mundial definido antes de implementar, más los seis ajustes menores, el plan es ejecutable; lo más probable es que la unidad termine en REJECTED_OFFLINE y cambio de hipótesis, lo cual es un resultado legítimo.

FIN_REVISION