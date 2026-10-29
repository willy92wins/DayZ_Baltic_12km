**Dictamen: SOUND-with-fixes.** La lógica de verificación y recuperación es correcta en lo esencial (hash antes de parsear, 23 pins, 1 sola llamada al runner, marker fuera de output, consumidor independiente recalcula todo). Hay un test roto y dos puntos de pérdida de evidencia que conviene corregir antes de dar por cerrado.

**Bugs concretos**

1. **Test siempre falla** en `tests/test_road_material_recovery_ev112.py:97`. La aserción comprueba que la cadena `marker_inside_output` esté dentro de `str(V.SnapshotError)`, que es la representación de la clase, no del error capturado. La excepción sí se lanza en la línea 82 del verificador, pero la aserción posterior es falsa de forma determinista. Debe capturar la excepción con `as e` y comprobar `str(e)`. Hasta arreglarlo, la suite está en rojo y no sirve como evidencia.

2. **Pérdida de evidencia por sobrescritura** en `tools/quality/recover_road_material_samples_ev112.py:83`. Si el informe final ya se escribió en la línea 77 y el consumidor independiente de la línea 78 lo rechaza, el bloque de excepción reescribe el mismo fichero con `INCONCLUSIVE_RECOVERY`. Se pierde el informe que el consumidor rechazó, que es justo lo que hay que inspeccionar. Mejor escribir el fallo en un fichero aparte, o incluir el informe rechazado dentro del de error.

3. **Comprobación tautológica del ejecutable del parent** en `tools/quality/verify_road_material_snapshot_ev112.py:215`. Se pasa `prun.get('executable')` como valor esperado del propio `prun`, así que ese campo nunca se contrasta con nada. Es aceptable como fracaso antiguo, pero conviene documentarlo o pinnar el valor en el contrato. Mismo patrón en el test golden, línea 68 del fichero de tests, donde input_sha y executable se comparan consigo mismos.

**Observaciones menores (no bloqueantes)**

- El receipt del parent admite 120 s de ventana mientras el contrato fija 90 s de unidad. Coherente si es histórico, pero el motivo no está escrito.
- La comprobación de mtime en la línea 266 del verificador depende de que el reloj del runner y el del sistema de ficheros coincidan. Con CfgConvert real y NTFS debería funcionar, pero el fake sólo valida la ruta feliz.
- El fixture golden real no está en el scope adjunto. No puedo confirmar que su `running.seconds` sea menor o igual a 30, que es lo que exige la llamada con valores por defecto.

**Verificado y correcto**

- Marker se crea con `xb` antes de tocar output. Si output ya existe, `mkdir` con `exist_ok=False` falla sin escribir informe. El test del sentinel lo cubre.
- Estado de tools y snapshot se hashea antes y después del runner. Cambios durante la ejecución se detectan.
- El valor devuelto por `run` se normaliza vía JSON y se compara con `completion.json` más `id`. Claves enteras en `identities` quedan cubiertas por la normalización.
- Límites del contrato se comparan por valor y por tipo, así que `90.0` se rechaza.
- Conversión 1 nunca se relanza. Sólo se verifica su receipt pinneado con rc 0.
- Flags `build_ready` false y `dependency_closure` NOT_EVALUATED se exigen en contrato, informe histórico e informe nuevo.

**Siguiente paso**: corregir la aserción del test y el destino del informe de fallo. Después reejecutar la suite con el fixture real presente y adjuntar la salida.
