**Veredicto: SOUND-with-fixes.** La unidad nueva es fail-closed en los caminos revisados; no encuentro un falsePASS directo. Hay dos ajustes que recomiendo antes de la preparación y varios menores.

**Verificado correcto**

- `FileInfo` coincide con BY_HANDLE_FILE_INFORMATION; share mode 7 y GENERIC_READ sin escritor. `snapshot` compara FileID antes/después, exige lectura completa y marca crecimiento sin inventar continuidad.
- `stable_pair`, `metadata` y `health` ligan sha/bytes/size/created a FileID y encadenan tiempos host<=created<=write<=checked. El consumidor reclasifica bytes exactos y exige igualdad con el diagnóstico guardado.
- `classify` cumple la adjudicación: cero o un bloque, timestamp igual, contigüidad estricta, cualquier SCRIPT(E) fuera del bloque bloquea, avisos listados. `load_golden` deriva de 99df8cd5 líneas 20-29 y liga cuatro fuentes a pins.
- Recibos con `xb` y fsync; `native.log` como marca de consumo; prefijo del script conservado; PIDbirth comprobado vivo.

**Fixes recomendados (ninguno abre falsePASS; dos evitan falseFAIL en el run real)**

1. **shared_log_b3g2_ev112.py:98 y observe_contact_b3g2_ev112.py:23**. `ntpath.normcase` no quita barra final ni normaliza `.`/`..`. Si el servidor fue lanzado con `-profiles=...\` o ruta no normalizada, `script_location`/`native_location` fallan siempre. Fix: aplicar `ntpath.normpath` a ambos lados antes de `normcase`. Lo mismo en capture_contact_b3g2_identity.ps1:53, donde `profiles` se guarda tal cual la opción.

2. **shared_log_b3g2_ev112.py:100**. El encabezado `started at .*\((YYYY-MM-DD HH:MM:SS) UTC\)` sólo está probado contra la fixture del test (línea 103 del test), no contra la primera línea del raw archivado. Si el formato real difiere, el run vivo falla con `script_header` en cada poll. Fix: en `load_golden` o en un test, parsear la línea 1 de `golden['archive']` con ese mismo regex y exigir match. Es barato y cierra el riesgo.

3. **shared_log_b3g2_ev112.py:86**. La detección usa `m[2]==expected[0]` sin normalizar la ruta de misión, mientras la línea 89 sí normaliza. Funciona sólo porque el frame 0 no contiene `$MISSION`. Fix: `m[2].replace(str(mission),'$MISSION')==expected[0]` para coherencia. Si fallara, el resultado sería `unknown_script_error`, no un pase.

4. **shared_log_b3g2_ev112.py:92 (ventana residual)**. Una última línea parcialmente escrita, por ejemplo `SCRIPT    (E` truncada antes del paréntesis, no casa con `ERROR` y el snapshot at-capture se clasifica limpio. Fix mínimo: en `health` para el snapshot post, exigir `raw.endswith(b'\n')` o tratar la cola sin salto como pendiente. La ventana es de microsegundos pero el stable_pair sólo se aplica al nativo, no al script.

5. **observe_contact_b3g2_ev112.py:39**. `st_ctime` como creación en Windows está deprecado en Python 3.12+ y cambiará de semántica. Fix: `getattr(st,'st_birthtime',st.st_ctime)`. Sólo selecciona candidatos, pero conviene.

6. **contact_b3g2_native_ev112.py:30**. El consumidor no verifica ausencia de `script-failure.json`. Un poll con fallo transitorio (WinError) seguido de captura exitosa deja ese archivo sin registrarlo como confusor. Fix: `require(not (root/'script-failure.json').exists(),'script_failure_present')` o incluirlo en `limitations`/inputs.

7. **contact_b3g2_native_ev112.py:17-19**. Falta `script_log_checked_utc <= capture_started_utc <= first chec