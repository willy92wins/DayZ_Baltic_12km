**Veredicto: SOUND-with-fixes** (revisión solo lectura del empaquetador; no se aprueba sonda ni RAM, no escritos).

**Fuentes verificadas**: los archivos leídos coinciden con las rutas de source-hashes.json. La herramienta `tools/navigation/package_nav8_onload_config_ev112.py` y los 14 tests de `tests/test_nav8_onload_config_ev112.py` corresponden al plan.

**Aislamiento del flag y material WRP/NM: asegurado.**
- Identidad de baseline por hash de PBO, WRP y NM antes de tocar nada (`package_nav8_onload_config_ev112.py:84`). Prefijo y cabecera raP comprobados (`:86`).
- Control nulo decode/compile/decode exige bytes idénticos al config.bin original y tokens idénticos (`:107`). Falla cerrado si CfgConvert interfiere.
- Oráculo real: diff posicional de tokens entre el decodificado original y el roundtrip del candidato, exactamente un token, "true" a 1, en la declaración con scope CfgWorlds/BalticTrial/Navmesh fuera de GenParams (`:64-71`, `:50-53`). Se repite sobre el config releído del PBO empaquetado (`:139`).
- Paridad del contenedor: `after != expected` compara todas las entradas byte a byte con config.bin sustituido, y `after_props != props` (`:133`). Entradas comprimidas o duplicadas fallan en read_pbo (`attach_navmesh.py:46,54`). Una entrada extra, faltante o un byte distinto en NM/WRP hace fallar el dict. Correcto.
- Scope independiente del parser: `class CAWorld;` se limpia con `;` (`:44`), herencia `: CAWorld` no altera la pila, llaves de arrays apilan None y se filtran (`:48`). Verifiqué contra el fixture real `original.cpp:17-69`.

**Tests**: el fixture literal con SHA constante construye el esperado por reemplazo de texto, no por el propio tokenizador (`test_nav8_onload_config_ev112.py:22-25`). No es autorreferencial. Negativos de GenParams, ancho, mundo, clase, duplicado, desplazado, sin cambio, declaración extra y desbalanceo cubren los riesgos del parser.

**Fixes (ninguno exige reescribir el parser):**

1. **Tipo entero no demostrado por el tool.** CfgConvert imprime float 1.0 como `1` (ver `crouchHeight=1` junto a `standHeight=1.5` en el fixture). El diff de tokens no distingue int 1 de float 1.0, y `test_float_one_is_not_integer` solo prueba el verificador, no el pipeline. verification.json afirma `onload_after=1` sin evidencia de tipo. Fix barato: comprobar en el config.bin compilado la secuencia raP del entry entero, byte de tipo 2 seguido del nombre y `01 00 00 00`, y fallar si aparece el tipo float. Esto también blinda la sonda posterior, cuyos getters int/float no separan ambos tipos.

2. **Control nulo no cubre la ruta de escritura Python.** El noop compila el archivo decodificado directamente (`:104`), pero el candidato pasa por read_text utf-8-sig y write_text sin BOM con newline nativo (`:102,110`). Diferencias semánticas las atraparía el diff de tokens; diferencias binarias silenciosas no. Fix: compilar también el texto reescrito por Python sin cambio, o escribir el candidato con el mismo BOM y newline que el original.

3. **Negativos de contenedor no testeados.** La comparación de `:133` es trivialmente correcta, pero el plan los exige como controles. Extraer esa comparación a una función pura de pocas líneas permitiría los tests con dicts sintéticos (entrada extra, byte NM alterado, prop distinta) antes del empaquetado, como propone el usuario. Recomendado, no bloqueante.

**Observaciones menores, sin acción obligatoria:**
- Los argumentos `--expected-sha256` y `--wrp-sha256` son redundantes con las constantes; está bien como doble declaración.
- El PBO empaquetado tendrá timestamps distintos, así que `pbo_sha256` no es comparable con el baseline. Es esperado.
- Si FileBank añade propiedades propias, el tool falla cerrado. Es el comportamiento deseado.

**Nada crítico falta** para la fase que termina en PBO nuevo en E: sin sustituir el original. El fix 1 es el único que cierra un false-pass real sobre la afirmación del tipo. Deployment, relectura, 607 y RAM quedan fuera de esta revisión.

FIN_REVISION
