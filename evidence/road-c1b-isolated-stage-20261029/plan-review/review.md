## Dictamen: **SOUND-with-fixes**

El alcance es coherente como copia verificada por bytes: `build_ready=false`, `dependency_closure=NOT_EVALUATED` y `compiled_terrain_decoder=NOT_VERIFIED` evitan exigir compilación o cierre semántico. No hay imposibilidad de principio. Deben cerrarse estas ambigüedades antes de autorizar código:

1. **Reconciliación exacta de referencias del config** — Ancla: referencias históricas líneas 26, 32-33, 48 y 51-54 frente al resumen “dos texturas exteriores y cuatro RVMAT”. Son cuatro PAA referenciadas, no dos: `outside_sat_co.paa`, `cp_grass_nopx.paa`, `cp_grass_ca.paa` y `middle_sat_mco.paa`, más cuatro RVMAT. Corrección: tabla cerrada referencia→destino normalizado→fuente, indicando a qué conjunto pertenece cada una —8 PAA, 2048 PNG o entrada separada— sin contar dos veces ni usar basename.

2. **Destino literal del WRP y del config nuevo** — Ancla: `worldName` línea 37 y “WRP0/3 bajo el mismo nombre”. Corrección: fijar destino `dayz_baltic_12km_dev/tb/narva_trial/baltic_trial.wrp` en ambas raíces y fijar también la ruta normalizada exacta del nuevo `config.cpp` propio, distinta de `bin/config.cpp`. Sin esto, “sólo difieren en `baltic_trial.wrp`” no es comprobable.

3. **Pins completos y fuentes C0 identificadas** — Ancla: hashes elididos `f00c3f57...` y `candidato2fb3686b.../17307968B`. Corrección: el manifiesto sellado contiene SHA-256 completos, tamaños y rutas fuente explícitas de control y candidato. Las elipsis valen en el plan, nunca en el contrato ejecutable.

4. **Literal de laboratorio cerrado por inclusión/exclusión** — Ancla: líneas 213-222 `Names/Sounds/Ambient` y omisión de Navmesh líneas 56-212. Corrección: enumerar expresamente qué bloques históricos se conservan, cuáles se omiten y el texto exacto resultante antes del código, con diff y SHA externos. Debe quedar explícito si las clases vacías finales se conservan u omiten; ambas ramas usan el mismo literal byte a byte.

5. **Fusión de duplicados y re-apertura por el consumidor** — Ancla: “duplicados sólo se fusionan si SHA/bytes y fuente física observada coinciden”. Corrección: si dos rutas físicas distintas alimentan un mismo destino, el manifiesto conserva todas como alias-fuente; el consumidor reabre y verifica cada alias. Fusionar borrando una fuente haría el contrato no re-verificable independientemente.

6. **Cotas como condición de aborto, no como expectativa** — Ancla: totales PNG/PAA/RVMAT/core conocidos, pero no máximos individuales ni tamaño B4A3 en la cápsula. Corrección: en la preparación, antes de codificar, comprobar cada archivo ≤32MiB, entradas ≤8192, payload común ≤384MiB y total ≤1GiB. Si alguna fuente supera la cota o falta, resultado `REJECTED` sin elevar topes ni buscar rutas sustitutas fuera de la lista cerrada.

7. **Alcance de raíces y reparse en tiempo de uso** — Ancla: raíces amplias `E:`, `P:/DZ` y posibles junctions en `P:`. Corrección: fuera de la enumeración única de `P:/core`, autor y consumidor abren sólo rutas individuales del manifiesto, sin enumerar `P:/DZ` ni `E:`; revalidan identidad `dev/ino/mtime/size` y ausencia de reparse en ancestros al abrir, no sólo al preparar. Cualquier junction produce rechazo, sin tocar `P:`.

8. **Veredictos separados del consumidor** — Ancla: consumidor que “reabre todas las fuentes” y comprueba los stages. Corrección: reportar por separado `STAGE_BYTES` y `SOURCE_PIN_MATCH`. `FULL` exige ambos, pero una deriva posterior de la fuente no debe presentarse como corrupción del stage ya materializado.

**Límites del dictamen:** revisión exclusivamente sobre la cápsula aportada, sin lectura de archivos ni binarios. No valida existencia actual de fuentes, hashes completos, formato PNG/PAA/RVMAT/WRP, herencia `CAWorld`, precedencia nativa ni compilabilidad. Con las ocho correcciones incorporadas al manifiesto y al literal previos al código, el plan es ejecutable dentro de su declaración limitada de stage de laboratorio.