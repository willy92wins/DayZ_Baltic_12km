**Identidad:** Claude Fable 5.1 (`claude-fable-5-1`), familia Claude 5. Revisión de sólo lectura sobre la evidencia adjunta; no he ejecutado nada ni consultado el repositorio.

**Veredicto: SOUND-with-fixes.** El núcleo del diseño es correcto: un codec preregistrado, roundtrip byte-exacto, nada de extrapolación, y contrato pospuesto hasta que termine el consumidor de Q02B3. Los fallos siguientes no invalidan el alcance, pero sin corregirlos el experimento puede fallar por causas propias y confundir un límite de recursos con una conclusión sobre el codec.

## Hechos verificados contra la evidencia

- El completion adjunto confirma rc 1, 439.281 s, pico RSS 89.27 MB, `reason: null`, stdout vacío. El texto literal `REJECTED:totalbytes` no está adjunto, sólo el SHA de stderr. El plan debe pinar el contenido de stderr contra ese hash en el consumidor, no darlo por leído.
- El código es consistente con la lectura causal: `reserve` suma antes de escribir y lanza `Bad('totalbytes')` si supera el cap. El inventario queda 3.918 bytes por debajo de 2 GiB, luego la línea rechazada medía más que eso y nunca se escribió. El `finally` cierra el shard en curso sin pasar por `close_shard`, así que la cola puede ser un shard sin entrada en terminal. Eso es exactamente la "cola incompleta" que el plan quiere conservar.
- El pico de memoria descarta que el motivo fuera RAM. No hay evidencia de timeout en el completion, pero tampoco del límite de tiempo configurado; "no fue timeout" debe quedar como inferencia de rc y stderr, no como hecho independiente.
- Las cifras 850 terminales, cola 850, 538.390 selectores y 180 cadenas faltantes no son derivables del código ni del completion. El plan ya las marca pendientes del consumidor. Deben escribirse como marcadores CONSUMER_PENDING, no como números que el nuevo contrato pueda citar antes del consumo.

## Fallos concretos y corrección

1. **Cap por archivo de 16 MiB elegido a ciegas.** El `shard_bytes` y `cache_bytes` del contrato Q02B3 no están en la evidencia. Si algún shard real supera 16 MiB, el experimento rechazará la fuente por un límite inventado, y eso no sería ni resultado numérico ni resultado de codec. Corrección: derivar el cap por archivo del máximo del inventario pinado o del `output_limits` del contrato Q02B3, y clasificar cualquier exceso como INPUT_OUT_OF_CONTRACT, estado separado de INCONCLUSIVE_RESOURCE.

2. **Presupuesto de 120 s sin prueba de rendimiento.** La medición implica leer unos 2 GiB, comprimirlos, descomprimirlos y calcular tres SHA-256 completos. Sin reintento ni extensión, un corte por tiempo quedaría indistinguible de inviabilidad del codec. Corrección: fijar orden determinista de archivos igual al inventario, emitir resultado por archivo según se completa, y preregistrar que un corte produce INCONCLUSIVE_RESOURCE con el prefijo medido etiquetado como tal. No pido subir el presupuesto. Pido que el plan declare qué se obtiene si no alcanza.

3. **Riesgo de hidratación OneDrive.** El árbol de trabajo vive bajo una carpeta sincronizada de OneDrive. Si los archivos de captura son marcadores "a demanda", `stat` devolverá el tamaño correcto pero la lectura descargará datos y consumirá el presupuesto. Corrección: en el pin de inventario comprobar atributos de archivo offline o de recuperación bajo demanda, y rechazar la medición como INCONCLUSIVE_INPUT_NOT_LOCAL si aparecen. Esto se verifica en el descubrimiento de firmas, no se asume.

4. **"Decoder independiente del encoder" sobredimensionado.** Con zlib ambos lados usan la misma biblioteca. Lo independiente es el objeto de flujo, no la implementación. Corrección: redactar "flujo decodificador separado, misma biblioteca" y no reclamar verificación cruzada de implementaciones.

5. **Falta cota de tamaño comprimido.** La regla de reservar cada bloque antes de producir salida exige un límite para la salida comprimida, que puede superar el original en datos incomprimibles. Corrección: cap comprimido por archivo igual al original más un margen fijo preregistrado. Superarlo es un resultado válido del codec para ese archivo, no un error del experimento.

6. **"Ahorro suficiente" sin regla.** Decidir suficiencia obliga a proyectar sobre las cadenas faltantes, cosa que el propio plan prohíbe. Corrección: esta unidad entrega sólo ratio medido sobre prefijo y cola, por separado. La decisión de suficiencia y cualquier proyección pasan al plan de formato siguiente, con sus supuestos escritos. Así se mantiene la separación entre resultado numérico y codec.

7. **Contador de llamadas no prueba un negativo.** Contar llamadas no demuestra que nada importó productores numéricos ni abrió NPZ, WRP o PBO. Corrección: usar un gancho de auditoría de importaciones y aperturas, verificado en el descubrimiento de firmas del Python instalado, y comprobar que el conjunto observado está contenido en una lista blanca. Cualquier evento fuera de lista rechaza la medición.

8. **Hash del inventario sin algoritmo pinado.** El plan dice que el hash de bytes leídos debe igualar el inventario, pero el inventario y su algoritmo no están en la evidencia. Corrección: el consumidor pina formato, algoritmo y SHA del inventario antes de que exista código de medición.

9. **Cola incompleta mal definida hasta el consumo.** La existencia o no de `terminal.json` para la cadena 850 depende de en qué reserva saltó el cap, y eso no está en la evidencia. Corrección: el contrato debe listar la cola por archivo según el consumidor, nunca por cadena.

## Lo que sí está bien y debe conservarse

- Un codec y un nivel, sin comparación ni elección del menor tamaño.
- Roundtrip exacto sin parsear JSON, sin ordenar, sin tocar racionales, preservando LF y la cola.
- Flujos comprimidos no guardados, sólo contadores y hashes.
- Lectura en bloques acotados con `max_length`, manejo explícito de `unconsumed_tail`, `unused_data` y `eof`, rechazo de truncados y concatenados.
- Resultado restringido a SAVED_SERIALIZATION_FEASIBILITY_ONLY, con build_ready, map_repaired y natural_calibration en falso y el conteo humano 9/0 y C1 sin tocar.
- Fixtures literales cubriendo vacío, no UTF-8, CRLF, alto ratio, incomprensible y overrun.

## Límites de esta revisión

- No he visto el inventario, el contrato Q02B3, `shore_coverage_io_ev112`, ni el piloto. Las afirmaciones sobre el consumidor son pendientes.
- No he verificado firmas de zlib ni de atributos de archivo en el Python instalado. El plan hace bien en exigir ese descubrimiento antes de la autoría.
- No he estimado rendimiento con mediciones; el fallo 2 es un riesgo, no un resultado.
- Ninguna de las correcciones pide ampliar tolerancias ni caps de Q02B3, ni autoriza relanzarlo. El nuevo contrato sigue bloqueado hasta que el consumidor en curso entregue o documente su ausencia.
