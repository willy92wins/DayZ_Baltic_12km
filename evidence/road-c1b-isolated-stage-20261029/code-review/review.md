## Dictamen: SOUND-with-fixes

### Hallazgos

**1. Medio — `config_refs` no se reconcilia en ningún lector.**  
En `stage_road_lab_c1b.py:31` y `verify_road_lab_c1b.py:44` solo se comprueba que la clave `config_refs` exista dentro del conjunto exacto del contrato. Ninguno valida su tipo, sus ocho entradas, ni que cada `dest` esté presente entre los archivos `common`. Ambos aceptan incluso `config_refs=[]`, como hace la fixture de `test_road_lab_c1b.py:21`. Por tanto, un contrato internamente inconsistente —referencia listada pero ausente del stage— podría llegar a `VERIFIED_LAB_STAGE_BYTES_ONLY` si el resto de hashes coincide. No es una falsa equivalencia semántica: es un hueco de consistencia del manifiesto contra F1/F3. Corrección mínima y genérica, sin parsear el config ni hardcodear rutas del laboratorio: validar lista de objetos con claves exactas, destinos `safe_rel` únicos y subconjunto de los `dest` common; añadir negativo con una referencia huérfana.

**2. Bajo — colisión ancestro/descendiente de destinos no rechazada por contrato.**  
`safe_rel`/`relative` y los conjuntos `(scope,dest)` aceptan simultáneamente, por ejemplo, `a` y `a/b`. En el autor eso termina en `OSError` al crear el segundo objetivo; en el consumidor es un stage imposible de satisfacer. No hay aceptación silenciosa, pero la colisión debería detectarse como `COLLISION` en ambos lectores antes de copiar/verificar, validando por rama efectiva que ningún destino sea ancestro de otro.

### Lo que sí cierra

- Pins CLI separados correctamente usados: el pin del contrato y el de `bindings` se exigen por separado; el co-mutante que altera el manifiesto sin tocar el pin externo de bindings cae en `BINDING`, y el que solo altere hashes cae después en `SOURCE_PIN`.
- Transferencia por chunks con límite `bytes+1`, EOF, hash del flujo, identidad antes/después y relectura de destinos; alias extra reabiertos con `transfer(s, [])` y exigencia de identidad física común.
- Consumidor sin importar el autor, con recorridos propios, rechazo de extra/faltante/reparse y separación `STAGE_BYTES`/`SOURCE_PIN_MATCH`; `FULL` exige ambos.
- Cifras exactas del contrato: 6892 common, 223031657 B; más dos WRP de 17307685 B y 17307968 B. Total de la pareja: `2×223031657 + 17307685 + 17307968 = 480678967 B`, bajo el tope de 1073741824 B. Los 57 de core son descendientes sin raíz, no una pérdida frente a los 58 con raíz.
- Cobertura estática de los negativos del oráculo: extra, faltante, hash de stage, deriva de fuente separada, binding, colisión exacta, paths, bool en `bytes`, salida existente, reparse simulado, pin de contrato erróneo y WRP cruzado. `CONFIG` queda cubierto solo como tamper de bytes, no como reconciliación de `config_refs`, que es el hueco del punto 1.

No consta en la cápsula ejecución de la suite ni materialización real; conforme a lo pedido, no lo exijo. Con la corrección 1 —y opcionalmente la 2— el diseño queda SOUND para `VERIFIED_LAB_STAGE_BYTES_ONLY`, sin extenderlo a compilabilidad ni cierre de dependencias.