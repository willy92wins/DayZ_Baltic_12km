# Q02B4 — coste de serialización guardada, sin repetir el censo

Estado: BORRADOR_PENDIENTE_DE_REVISION. Unidad de descubrimiento posterior a Q02B3. Trazabilidad Q02/P11: hacer viable la cobertura de todos los contornos sin cambiar geometría, clasificación ni precisión. No constituye reparación ni aceptación visual.

## Hecho y límite de causalidad

[EXACT] Q02B3 produjo una excepción controlada `REJECTED:totalbytes`, rc1, a439.281s, RSS89.27MB. El inventario posterior registra2.147.479.730bytes en2618archivos, bajo el cap2GiB; no fue timeout. shore_multiscale_coverage_ev112.py:23-26 reserva antes de escribir; :65-70 serializa cada consulta y :80 el terminal. Hay850terminales y una cola de cadena850 según metadatos, todavía pendientes del consumidor único en curso al redactar. No afirmar que todas las cifras/racionales sean válidos hasta ese consumo. No aumentar el cap ni relanzar Q02B3.

La causa inmediata del aborto está leída en reserve, sin hipótesis sobre motor/mapa. [HIPÓTESIS] La repetición de claves y enteros en NDJSON permite una representación comprimida reversible con menor ocupación. No se conoce aún su ratio ni si permitirá completar los538390selectores dentro de tiempo/disco. El coste del consumidor es otra dimensión, no resuelta por esta hipótesis.

## Alcance autorizado propuesto [DESIGN]

Una medición sobre la captura guardada e inmutable y su inventario externo, sin ejecutar consultas, crear geometría ni modificar código Q02B3. Esperar a que termine el consumidor existente antes de fijar contrato: pin de inventario, reporte o ausencia/timeout documentado, completions y fuente del guard reserve. El nuevo contrato delimitará exactamente archivos y pertenencia a prefijo aceptado/cola; si el consumo rechaza o no entrega, toda medición será DIAGNOSTIC_UNVERIFIED_INPUT y nunca prefijo certificado.

Probar UN codec y UN nivel preregistrados: zlib nivel1, flujo independiente por archivo, sin diccionario externo. Descubrir primero firmas reales en el Python instalado y fijar versión/runtime antes de autoría; aquí son diseño, no llamada lista para ejecutar. No comparar niveles ni seleccionar el que dé el menor tamaño. La codificación es exploración para un futuro contrato de formato, no sustitución de los archivos existentes. No guardar los flujos comprimidos; sólo contadores/hash/resultados por archivo. No ordenar, eliminar campos, redondear, convertir racionales ni reconstruir JSON. El roundtrip debe conservar exactamente los bytes, LF y orden originales, incluso la cola incompleta.

Leer cada archivo en chunks<=64KiB, hash de bytes leídos igual al inventario; stat inicial/final observados dentro de cada API. No prometer vigilancia continua. Alimentar el decoder independiente del encoder con las salidas que éste produzca; suma de salida decodificada nunca puede superar el tamaño original pinado, max_length por llamada acotado, manejar unconsumed_tail/unused_data/eof explícitamente. No aceptar truncados ni bytes posteriores. SHA/longitud decodificados exactos contra fuente. Decoder no regenera bytes mediante parsear/reemitir JSON. Los archivos de captura no se publican.

Agregados: bytes originales y comprimidos medidos, tiempo, picoRSS, hashes origen/comprimido/roundtrip, estados por archivo, prefijo/cola separados según consumidor. Ningún ratio de muestra se extrapola a las180cadenas que faltan; ni a todas las consultas cuando no hay manifest. El resultado es SAVED_SERIALIZATION_FEASIBILITY_ONLY, o INCONCLUSIVE_RESOURCE/REJECTED_INTEGRITY. build_ready/map_repaired/natural_calibration=false. El conteo humano9/0 y C1 sin revisar permanecen.

## Límites, negativos y revisión

Contrato externo antes de código: inventario<=2MiB, fuentes2618como máximo para esta captura, cada archivo<=16MiB, totaloriginal<=2GiB, reporte<=2MiB, memoria512MiB. Sin cargar fuente/shard entero. Reservar/contar cada bloque antes de producir o retener salida; no concatenar historial de buffers. Una medición120s y un consumidor de metadatos60s; ningún reintento interno ni extensión si satura. Autoría180s, revisión120s y suite90s antes de medir. Límites de disco del experimento: sólo reporte<=2MiB y recibos, nada equivalente a nueva captura.

Fixtures literales: vacío, bytes noUTF8, LF/CRLF, alto ratio, incomprensible, chunk que deja unconsumed_tail; corrupto/truncado/concatenado rechaza; overrun de longitudes/caps, fuente alterada/añadida, reparse/symlink y cap global bloquean. Contador de llamadas debe probar que no importa ni llama productores numéricos ni abre NPZ/WRP/PBO. Consumidor guardado independiente sólo verifica cobertura de todos los IDs del inventario, pins, sumas por dimensión y límites; no afirma haber repetido el roundtrip y no certifica la matemática Q02B3. Guardar esa diferencia de alcance.

Si el resultado sugiere ahorro suficiente, preparar NUEVO plan/contrato de formato con consumidor independiente, recursos descomprimidos y compatibilidad semántica antes de producción completa. No autoriza esa producción ahora. Si no resulta viable, cambiar estrategia a contrato de rasgos compacto revisado, nunca relajar precisión o esconder estados. Ángulos, referentes naturales/agua y Q03/Q05 siguen pendientes; este experimento no los reemplaza.
