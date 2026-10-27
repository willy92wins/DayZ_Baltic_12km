**Veredicto: SOUND-with-fixes.** El plan es coherente con la evidencia y con las herramientas citadas. Pide correcciones acotadas antes de aceptar; ninguna abre bucles ni council.

**Evidencia contrastada con fuentes**

- Sonda: 9 observaciones, controles PASS, ambos flags Baltic `native_type 2` con int/float 0; Chernarus `native_type 0` con 1 (result.json:7-46). Cierre ordenado y paquetes Nav8 con worldSHA ac088cc… (identity-verification.json:3-28). Cuatro avisos de zonas fuera de marcadores (script-config-observations.json:16-37). Coincide con plan:9-20.
- Histórico RAM: FAIL con ratios 1,266/1,241 y dispersión <0,3% (comparison.json:25-33,48-56). El plan no lo usa como aceptación ni causalidad (plan:73-78). Correcto.
- No verificable en mis fuentes: "118 paquetes vanilla verificados" (plan:14). Marcar como referencia externa o enlazar su artefacto.

**Aislamiento config y paridad**

1. El patrón citado compara `tokens(after)` con `tokens(rewrite(before))` (package_nav8_config_ev112.py:34-36). Es la transformación contra sí misma; el plan lo reconoce (plan:51-52) pero debe concretar el oráculo independiente: diff posicional de listas de tokens entre `original.cpp` y `roundtrip.cpp` con exactamente una posición distinta, valor antes `"true"` y después `1`, resto idéntico.
2. Alcance de clase. `filterIsolatedIslandsOnLoad` y `filterIsolatedIslands` comparten prefijo; un regex por nombre no garantiza clase. Exigir que la única declaración esté dentro de `class Navmesh` de `class BalticTrial` y fuera de `class GenParams`, y que `GenParams.filterIsolatedIslands="true"` siga presente una vez. Control negativo adicional: fixture con el flag duplicado en GenParams debe fallar.
3. Control nulo de roundtrip. `config.bin` saliente es reemitido íntegro por CfgConvert, no parcheado. Añadir pasada decode→compile→decode sin cambio y registrar si el bin nulo iguala bytes al original de Nav8. Como Nav8 ya salió de CfgConvert (package_nav8_config_ev112.py:63-78), se espera igualdad; si no, documentarlo como límite, no como bloqueo.
4. Tipo esperado tras compilar: fijar `native_type 0`, texto "1", int 1, float 1.0, replicando Chernarus (result.json:29-36). "int/float1" (plan:60) es ambiguo; `1.0` daría tipo 1.
5. Paridad de entradas: reutilizar el contrato `after != expected` y propiedades (package_nav8_config_ev112.py:91-93; attach_navmesh.py:111-113). Añadir relectura del PBO final desde la ruta `P:\Mods\@…\Addons` que consumirá el servidor, no solo desde la carpeta de salida.

**Positivos y negativos**

Lista de plan:46-50 es adecuada. Faltan dos positivos: fixture literal con el texto exacto decodificado de Nav8 (hash registrado) y verificación de que el bin candidato difiere del original en bytes. Falta un negativo: entrada `config.bin` que no empiece por `\0raP` tras compilar.

**Adecuación del bloque RAM**

- El comparador exige seis identidades nuevas, orden ABBAAB, paquetes constantes por mundo y config/ejecutable/misión comunes (compare_server_baseline_ev112.py:17-23,81-88). El mod nuevo cumple si las tres pasadas Baltic usan el mismo PBO y el server config incluye el mod en las seis. Esto replica el histórico: el mod también se carga en pasadas Chernarus. Aceptable y debe quedar escrito.
- Sensibilidad: con dispersión histórica <0,3% y umbral 1,10, el bloque distingue sin ambigüedad una reducción de ~16 puntos. Es adecuado para rechazar o conceder candidato local.
- Caso no cubierto: `INCONCLUSIVE_DISPERSION` o `INCONCLUSIVE_PAIRED_EXCESS` con seis pasadas válidas (compare_server_baseline_ev112.py:37,40). El plan solo trata pasada inválida (plan:93). Fijar: inconcluso = no aceptado, sin repetir bloque, cerrar y replantear.
- Presupuestos 30s+120s (plan:67) dependen de `read_server_baseline_ev112.py`, no incluido en fuentes. Congelar su hash en el manifiesto antes de la primera pasada.

**Riesgos fuera de 607 y promoción**

Plan:80-85 limita correctamente a candidato local. Añadir resultado predefinido: 607 PASS y RAM igual a Nav8 (FAIL contra Chernarus) significa variante sin efecto observable; rechazar sin probar otros valores. Esto evita interpretar "sin cambio" como "inconcluso". El oráculo local 607 no cubre islas filtradas; para alcance experimental es aceptable porque no hay promoción distribuida. Riesgo inaceptable solo aparecería si alguien sustituyera Nav8 por el candidato; el plan lo prohíbe (plan:81-82).

**Anclas desplazadas (corregir)**

- plan:41 "19-37": tokens 22-24, rewrite 27-31, verify 34-36.
- plan:42 "68-84": decode/compile/decode es 63-74.
- plan:42 "85-105": FileBank y comparación es 79-93.
- plan:71 "conditions_identity:51-74": es 49-69; compare es 17-46.

**Presupuesto**

Una variante, un run config+607, un bloque de seis pasadas. Sin repeticiones favorables ni inconclusas. Dos rondas de corrección de instrumentación máximo (plan:58). Sin cambio de tolerancias. Código de empaquetado y sonda no existen aún; esta revisión no los aprueba.

FIN_REVISION
