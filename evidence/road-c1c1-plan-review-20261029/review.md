## Veredicto: **SOUND-with-fixes**

El plan [RoadC1C1](<C:\Users\guill\OneDrive\Documentos\DayZ Projects\DayZ_Baltic_12km_dev\.claude\worktrees\handoff-astra-map-review-6d301c\plans\ev112-road-c1c1-canonical-preflight-probe-20261029.md>) conserva correctamente el intento C1C: bloqueo `REPARSE` antes de preflight/help/build, brazos `NOT_LAUNCHED`, sin fallo de Binarize demostrado. No reabre C1C ni exige decoder antes de observar bytes. La dirección canónica, el resultado máximo `COMPILE_PROBE_OBSERVED_ONLY` y no ampliar presupuestos son correctos.

### Fixes obligatorios antes del contrato

1. **Canónica: cerrar TOCTOU.** Anclar ancestros no basta si la comprobación ocurre antes de la lectura. El contrato debe fijar literalmente target, tag `2684354563`, SHA `9f8786a5…`, 10743 B y `dev/ino` de `preflight.py`, y revalidar cada ancestro canónico inmediatamente antes de abrirlo. Debe rechazar si entre ancla y lectura aparece reparse, cambia el target o cambia cualquier identidad anclada. Las observaciones del discriminador no son identidad continua, como el propio plan reconoce.

2. **Fuente instalada divergente.** Si la fuente instalada actual difiere de la original fijada, debe bloquearse. No debe rederivarse silenciosamente la copia raw-fix `812e68aa`, el diff ni `SyntaxError213` desde una fuente nueva.

3. **Logger por fase: definir la transición.** Falta precisar en qué fase cambia el logger desde el original `1d24d7d4…` hasta la receta de ejecución y qué inventario exacto se espera en cada fase, incluidas rotaciones numéricas. Debe existir recibo `STARTED` con `fsync` **antes** del lanzamiento y recibo de cierre después. Así, “arrancada sin recibo” es detectable y la ausencia de recibo no puede reinterpretarse como `NOT_LAUNCHED` si hubo inicio.

4. **Helper OS: el pin está incompleto.** Fijar solo ruta y firma válida de `C:\Windows\System32\conhost.exe` no es un pin suficiente. El contrato debe incluir SHA-256, tamaño, identidad de archivo y cadena/firmante Authenticode observados hoy. Además debe exigir padre/PID/birth coherentes con la raíz autorizada y un patrón de argv de conhost; que sea hijo observado de Python no autoriza su presencia bajo AddonBuilder ni bajo cualquier raíz. Su presencia nunca debe satisfacer Binarize y su ausencia no debe bloquear. Si no se acepta este pin completo, se mantiene el bloqueo del helper desconocido, sin permisos genéricos para hijos Microsoft ni analogías con `cmd`/PowerShell/Steam.

5. **Presupuesto: explicitar la suma interna.** Copy+prechecks 180 s + preflight 60 s + help 30 s + dos brazos de 300 s suman 870 s; con drenajes debe demostrarse que todo cabe en los 930 s del writer, reservando 120 s al observador dentro de los 1050 s totales. El coste C1C de 148 s no prueba que copy+postcheck quepa: si excede, corresponde `BUDGET`/parcial, sin repetir ni ampliar, tal como propone el plan.

Con esos cinco cierres incorporados al contrato previo al código, el plan es ejecutable sin reabrir C1C ni ampliar alcance.