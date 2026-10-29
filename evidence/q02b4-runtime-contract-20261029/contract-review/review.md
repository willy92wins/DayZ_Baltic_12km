Veredicto: **SOUND-with-fixes**. El contrato es coherente y conservador en lo esencial. Hay cuatro correcciones concretas antes de autorizar la autoría, ninguna de ellas de diseño.

**Lo que está bien fundamentado**

- **Cota B(N).** La rama por defecto de deflateBound aplica porque wbits=15 y memLevel=8 fijan exactamente la condición de esa rama, y la cota cubre cualquier estrategia. La nota de zlib.h sobre flushes extra se respeta porque sólo hay NO_FLUSH más un único Z_FINISH. Concluir "cada retorno ≤ B del fichero completo" es correcto. Inventar una cota de 64 KiB sería erróneo. No lo hagas.
- **Pico de memoria.** La suma de bloques de salida más el bytes final unido es la forma correcta de contar el pico de CPython. Reservar 128 MiB antes de la llamada y liberar historial entre ficheros es suficiente para N máximo ≈ 16,8 MB dentro de 512 MiB.
- **Decodificador.** max_length nunca 0, drenaje con progreso, rechazo de unused_data, de no-EOF y de salida mayor que N, y SHA más longitud exactos. Eso es un oráculo de ida y vuelta completo.
- **Integridad de salida.** Apertura exclusiva, registros sólo tras ida y vuelta completa, fsync por fichero, última línea truncada rechazada sin recorte. Prefijo parcial nunca equivale a FULL. Correcto.
- **Alcance epistémico.** Hash de exe/dll como observación y no procedencia, hook de auditoría declarado como no-sandbox, 180 cadenas ausentes no extrapoladas, banderas de reclamación en falso y C1 NOT_REVIEWED. Honesto y consistente.

**Correcciones requeridas**

1. **Recalcular y mostrar la aritmética de B(16777106).** Con la fórmula citada, mi cálculo mental da 16777106 + 4095 + 1023 + 0 + 13 = 16782237, no 16782349. La diferencia es pequeña y la cifra del contrato es más holgada, así que no invalida nada. Pero una derivación citada por línea debe cuadrar al byte. El informe debe imprimir los cuatro sumandos.
2. **Definir "progreso" en el drenaje del decodificador.** Cuando decoded == N, max_length vale 1 y la llamada que consume el trailer adler32 produce cero bytes de salida. Si el progreso se mide sólo en bytes decodificados, el bucle rechazaría ficheros válidos. Progreso debe ser: reducción de unconsumed_tail, o transición de eof a verdadero. Cero avance en ambos es el único caso de rechazo.
3. **Fijar encoded_sha256 y encoded_bytes sobre la concatenación ordenada** del retorno de compress más el retorno de flush. El contrato lo implica pero el esquema no lo dice. Mismo criterio para la comprobación del cap 2N+1024: por pieza y acumulado, declarado como cap operativo y no como cota derivada.
4. **Declarar el riesgo de ruta OneDrive.** El árbol vive bajo OneDrive. El stat mismo-handle antes y después no detecta hidratación de marcadores en la nube ni latencia de lectura. Hay que afirmar que el snapshot está hidratado localmente antes de los 120 s, o aceptar que una ejecución parcial por tiempo es un resultado legítimo y no un fallo del contrato.

**Observaciones sin bloqueo**

- 2618 fsync en Windows pueden sumar varios segundos. Cabe en 120 s, pero debe figurar en el presupuesto, no descubrirse en la ejecución.
- Hash del original "realmente leído" exige leer el fichero una sola vez a memoria y alimentar hash y codec desde ese mismo buffer. Dos lecturas invalidan la garantía.
- El selftest no puede abrir NPZ/PBO reales. Eso ya está declarado. El consumidor de metadatos no debe inferir nada de los preloads a partir del audit.

**Condición de suficiencia**

Con las cuatro correcciones, el contrato permite afirmar exactamente: "sobre los 2612 ficheros numéricamente aceptados más 5 de cola, zlib nivel 1 con estos parámetros produce E bytes, verificados por ida y vuelta byte a byte, en el runtime observado". No permite afirmar provenance de la librería ni generalizar a las cadenas ausentes. Esa es la frontera correcta.

Siguiente paso: aplicar las cuatro correcciones al texto del contrato y pasar a la ventana de autoría de 180 s.