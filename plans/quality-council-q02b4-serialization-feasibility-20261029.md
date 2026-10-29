Estado vigente: CONSUMIDO_SAVED_SERIALIZATION_FEASIBILITY_ONLY. Resultado y límites en evidence/shore-serialization-q02b4-20261029. No repetir medición ni CLIs. El contrato externo c814 y el texto de diseño histórico se preservan abajo.

# Q02B4 — coste de serialización guardada, sin repetir el censo

Estado: REVISADO_PARA_AUTORIA_DE_MEDICION_GUARDADA. Contrato final en tests/fixtures/q02b4/contract.json; revisión recuperada66.985s adjudicada, primer intento120.078s sin entrega. Todavía sin código ni medición. Estado histórico de descubrimiento sigue documentado abajo.

 Fable98.484s SOUND-with-fixes adjudicado; aún no código ni medición. Unidad de descubrimiento posterior a Q02B3. Trazabilidad Q02/P11: hacer viable la cobertura de todos los contornos sin cambiar geometría, clasificación ni precisión. No constituye reparación ni aceptación visual.

## Hecho y límite de causalidad

[EXACT] Q02B3 produjo una excepción controlada `REJECTED:totalbytes`, rc1, a439.281s, RSS89.27MB. El inventario posterior registra2.147.479.730bytes en2618archivos, bajo el cap2GiB; no fue timeout. shore_multiscale_coverage_ev112.py:23-26 reserva antes de escribir; :65-70 serializa cada consulta y :80 el terminal. El consumidor único terminó después de la revisión: VERIFIED_PARTIAL_NUMERIC_COVERAGE,850cadenas/466550selectores cubiertos;440130consultas y26420exclusiones degeneradas.409712DEFINED/30418INSUFFICIENT_SUPPORT,0numéricamente no verificados en el prefijo. Cola de cadena850 no aceptada. No cobertura completa538390. No aumentar el cap ni relanzar Q02B3.

La causa inmediata del aborto está leída en reserve, sin hipótesis sobre motor/mapa. [HIPÓTESIS] La repetición de claves y enteros en NDJSON permite una representación comprimida reversible con menor ocupación. No se conoce aún su ratio ni si permitirá completar los538390selectores dentro de tiempo/disco. El coste del consumidor es otra dimensión, no resuelta por esta hipótesis.

## Alcance autorizado propuesto [DESIGN]

Una medición sobre la captura guardada e inmutable y su inventario externo, sin ejecutar consultas, crear geometría ni modificar código Q02B3. Esperar a que termine el consumidor existente antes de fijar contrato: pin de inventario, reporte o ausencia/timeout documentado, completions y fuente del guard reserve. El nuevo contrato delimitará exactamente archivos y pertenencia a prefijo aceptado/cola; si el consumo rechaza o no entrega, toda medición será DIAGNOSTIC_UNVERIFIED_INPUT y nunca prefijo certificado.

Probar UN codec y UN nivel preregistrados: zlib nivel1, flujo independiente por archivo, sin diccionario externo. Descubrir primero firmas reales en el Python instalado y fijar versión/runtime antes de autoría; aquí son diseño, no llamada lista para ejecutar. No comparar niveles ni seleccionar el que dé el menor tamaño. La codificación es exploración para un futuro contrato de formato, no sustitución de los archivos existentes. No guardar los flujos comprimidos; sólo contadores/hash/resultados por archivo. No ordenar, eliminar campos, redondear, convertir racionales ni reconstruir JSON. El roundtrip debe conservar exactamente los bytes, LF y orden originales, incluso la cola incompleta.

Leer cada archivo en chunks<=64KiB, hash de bytes leídos igual al inventario; stat inicial/final observados dentro de cada API. No prometer vigilancia continua. Alimentar un flujo decodificador separado, de la misma biblioteca zlib, con las salidas que éste produzca; suma de salida decodificada nunca puede superar el tamaño original pinado, max_length por llamada acotado, manejar unconsumed_tail/unused_data/eof explícitamente. No aceptar truncados ni bytes posteriores. SHA/longitud decodificados exactos contra fuente. Decoder no regenera bytes mediante parsear/reemitir JSON. Los archivos de captura no se publican.

Agregados: bytes originales y comprimidos medidos, tiempo, picoRSS, hashes origen/comprimido/roundtrip, estados por archivo, prefijo/cola separados según consumidor. Ningún ratio de muestra se extrapola a las180cadenas que faltan; ni a todas las consultas cuando no hay manifest. El resultado es SAVED_SERIALIZATION_FEASIBILITY_ONLY, o INCONCLUSIVE_RESOURCE/REJECTED_INTEGRITY. build_ready/map_repaired/natural_calibration=false. El conteo humano9/0 y C1 sin revisar permanecen.

## Límites, negativos y revisión

Contrato externo antes de código: inventario<=2MiB, fuentes2618como máximo para esta captura, cada archivo<=16MiB, totaloriginal<=2GiB, reporte<=2MiB, memoria512MiB. Sin cargar fuente/shard entero. Reservar/contar cada bloque antes de producir o retener salida; no concatenar historial de buffers. Una medición120s y un consumidor de metadatos60s; ningún reintento interno ni extensión si satura. Autoría180s, revisión120s y suite90s antes de medir. Límites de disco del experimento: sólo reporte<=2MiB y recibos, nada equivalente a nueva captura.

Fixtures literales: vacío, bytes noUTF8, LF/CRLF, alto ratio, incomprensible, chunk que deja unconsumed_tail; corrupto/truncado/concatenado rechaza; overrun de longitudes/caps, fuente alterada/añadida, reparse/symlink y cap global bloquean. Contador de llamadas debe probar que no importa ni llama productores numéricos ni abre NPZ/WRP/PBO. Consumidor guardado independiente sólo verifica cobertura de todos los IDs del inventario, pins, sumas por dimensión y límites; no afirma haber repetido el roundtrip y no certifica la matemática Q02B3. Guardar esa diferencia de alcance.

El resultado sólo entrega ratios medidos del prefijo y cola; no decide suficiencia. Preparar NUEVO plan/contrato de formato con consumidor independiente, recursos descomprimidos y compatibilidad semántica antes de producción completa. No autoriza esa producción ahora. Si no resulta viable, cambiar estrategia a contrato de rasgos compacto revisado, nunca relajar precisión o esconder estados. Ángulos, referentes naturales/agua y Q03/Q05 siguen pendientes; este experimento no los reemplaza.

## Adjudicación de Fable98.484s y condiciones previas

Aceptar orden literal del inventario y recibo parcial por archivo terminado, escrito y fsync antes del siguiente, dentro de reporte total2MiB. Un timeout externo puede dejar sólo ese prefijo: no prometer informe final después de kill. No confundir medición parcial con inviabilidad del codec. Cola listada por archivo desde consumidor o, sin dictamen, INPUT_UNVERIFIED; no certificarla por ausencia de terminal solamente.

El consumidor del experimento verificará pins/esquema SHA256 del inventario y las fuentes de su clasificación; el hash por sí solo no acredita algoritmo histórico. El formato existente de inventario guarda path/bytes/sha256 y no se modifica. stdout/stderr originales se ligan a completion; el stderr real fue leído y su SHA confirmado. Running fija600s, completion439.281s/reasonnull y ruta explícita de excepción: el aborto observado no es timeout. No deducir si lo siguiente era línea/cache/terminal sólo de los3918bytes restantes.

El cap16MiB NO se eligió de una muestra: coincide con output_limits del contrato302216 ya aprobado y se mantiene. Incumplimiento se etiqueta INPUT_OUT_OF_CONTRACT, no fallo de codec. Salida codificada tiene techo operativo explícito2*tamañooriginal+1024bytes porarchivo, sin afirmar que sea cota matemática universal de zlib. Exceso ENCODING_RESOURCE_INCONCLUSIVE, datos intactos. Antes de autoría, descubrir/justificar cota de asignación de cada retorno de compress/flush para chunks64KiB; no reservar después de una asignación potencialmente ilimitada.

Refutar premisa de captura en OneDrive: captura e inventario están en E:/DayZ-Baltic-Build, distintos del worktree C: sincronizado. No hay evidencia de hidratación. Conservar comprobación existente de reparse/enlaces y atributos realmente observados; no atribuir causa ni inventar una guarda basada en nube.

La independencia se limita a flujo decodificador separado de la misma biblioteca; no comparación entre implementaciones. Auditoría de open/import mediante API real verificada y allowlist será una condición antes de código; probar intento prohibido, no sólo contar llamadas esperadas. Los módulos/runtime de stdlib que necesitan lectura se descubren explícitamente, sin allowlist comodín de todo el disco. No modificar la política del proceso padre globalmente.

Descubrimiento de firmas/retornos y versión es la próxima acción, sin correr el codec sobre captura. Contrato externo/oráculos y su revisión propios antes de autoría. Ninguna medición Q02B4 todavía; productor/consumidor Q02B3 consumidos al terminar y no se repiten.

Resultado recibido sin repetir consumidor:549.657s/156037120RSS,rc2/reasonnull. SHA de consumer.json 90323e42630a3c1a14f8ae69f9180087068cbe7712a547d9e3713bbce6b99a74. El nuevo contrato deberá pinar ese archivo y completion, inventario y archivo por archivo; fuenteactual no se modifica. Presupuestos y alcance del plan no cambian.

## Contrato final29-10 tras descubrimiento

Runtime3.12.14/zlib1.3.2 builtin observado; probe audit propio0.203s y tres rechazos previstos, sin codec ni corpus. CotaB(cap16777216)=16782349, distinta deB(maxobservado16777106)=16782237.128MiB reserva derivada condicional, no garantía deRSS ni procedencia upstream. Progreso decoder incluye input consumido/salida producida/transiciónEOF; encodedSHA concatenación ordenada. Hash original y encoder reciben el mismo chunk una sola vez. No fullread a memoria. CapturaE:; ninguna causaOneDrive. Todos2618fsync dentro del techo120s, no tiempo garantizado. Clasificación externa2612prefix/5tail/1header y evidencia previa pinados. Siguiente autor180/review120/suite90; no duplicar sondeos ni Q02B3.
