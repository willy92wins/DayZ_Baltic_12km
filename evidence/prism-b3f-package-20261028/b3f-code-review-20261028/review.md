**Veredicto: SOUND-with-fixes.** La composición y el consumidor cierran los puntos de la adjudicación del plan; hay tres huecos acotados que conviene fijar antes de ejecutar y un par de fixtures observables que faltan.

**Lo que está bien verificado**

- Guard de cabecera (`prism_b3f_package_ev112.py:27-48`) es ordenado, independiente, detecta duplicados de propiedad antes del dict, duplicados casefold, nombres inseguros, entrada comprimida, posición del bloque Vers y cuerpos truncados. La reconciliación con read_pbo (línea 53) compara raw, props, orden y tamaños, así que una divergencia del lector compartido sale como Inconclusive, no como PASS.
- package_identity se consume como función pura (línea 58) y el test contrafactual (test 54) altera CANDIDATE_SHA/ANCHORS del módulo legado y verifica que no intervienen. Correcto.
- context() (líneas 69-85) liga proof, resumen, ambos census y output por hash y por campos cruzados, revalida pins transitivos de gate.context, y la autocomparación de la línea 84 garantiza que el candidato difiere del control antes de escribir nada.
- Mutación entre fases: pins_check tras preflight, antes y después de pack, manifest rehash (línea 125), source_check post-pack, inventario PboUtils en tres momentos y de nuevo en el consumidor. Salida restringida a un único archivo regular (líneas 65-67).
- Preflight B3F: primitiva official.run sin CLI consumido, FileBank fijado por hash, disco mínimo, deadline sobre la propia medición, y la identidad pid del reporte queda ligada al running.json (línea 115).
- Aprobación: postimages del suite deben coincidir con los pins de código aprobado, así que no se puede re-pinear código no testeado. Cubierto por test 118.
- Consumidor CLI: salida preexistente no se pisa y falta de manifiesto da rc 2 con reporte preservado.

**Fixes requeridos antes de ejecutar**

1. `prism_b3f_package_ev112.py:47`: la condición `offset+sum(sizes)<=len(data)` admite bytes arbitrarios tras los cuerpos. Un PBO con el trailer de firma corrupto o con datos anexados pasaría identidad de entradas. Fix: calcular `rest=len(data)-(offset+sum(sizes))`, exigir `rest in (0,21)` y, si es 21, `data[-21]==0 and hashlib.sha1(data[:-21]).digest()==data[-20:]`, con razón `trailer`. Es una línea, no un segundo parser.
2. `prism_b3f_package_ev112.py:127`: el consumidor no queda ligado a su proceso observado, a diferencia del preflight en la línea 115. Fix: leer `output/'consumer.running.json'` y exigir `result['measurement']['pid']==identity['pid']`, razón `consumer_identity`.
3. `prism_b3f_package_ev112.py:126` frente a `:114`: el preflight se lanza con `runtime.reads.interpreter_image()` y el consumidor con `sys.executable`. Usar la misma imagen en ambos (sin `-S` en el consumidor, porque runtime necesita psutil) para que el recibo del consumidor nombre el mismo intérprete fijado.

**Fixes menores, no bloqueantes**

- `prism_b3f_package_ev112.py:32,34`: `data.index` y `unpack_from` sobre una cabecera truncada lanzan ValueError o struct.error, que el consumidor clasifica como INCONCLUSIVE_PACKAGE en vez de REJECTED_PACKAGE. Envolver ambos en `require(False,'truncated_header')` da la clasificación fiel. La seguridad no cambia.
- El runner externo `run_b3f_execution_20261028.py` no está pineado por la aprobación. Es un envoltorio de 300s y no toca el producto, pero conviene registrar su hash en completion o en la aprobación.

**Pruebas específicas que faltan (observables, no espejo de texto)**

- Fixture con entrada `mime!=0` que debe producir `compressed_entry` en read_package.
- Fixture con bloque Vers tras la primera entrada, sin bloque Vers, y con dos bloques Vers: deben producir `property_header_position` o `truncated_or_missing_header`.
- Fixture con terminador cuyos campos no son cero: debe producir `terminator`.
- Fixture con bytes anexados tras los cuerpos y con trailer de SHA1 incorrecto: hoy pasa; tras el fix 1 debe producir `trailer`.
- Fixture de read_package donde el `original` del header difiera de `size`: hoy el guard sólo usa `size`; documentar si read_pbo lo rechaza o no, porque el bind de la línea 53 no compara ese campo.

**Límites aceptados tal como se declaran**: read_pbo compartido para cuerpos, inventario instalado y no DLL cargadas, ninguna certificación de hijos no observados, sin DayZ ni despliegue, 47 FAIL y 21 inciertos siguen abiertos. Los args de FileBank (líneas 122-124) sólo se verifican en la composición única mediante pack.log y el recibo, lo cual es coherente con el presupuesto sin reintentos.

FIN_REVISION