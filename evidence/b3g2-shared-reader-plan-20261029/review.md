**Veredicto: SOUND-with-fixes.** El plan no relaja el criterio físico ni oculta errores. El riesgo de falsepass es bajo tal como está escrito, pero dos puntos del discriminador son ambiguos y uno del lector usa una identidad inestable. Corregidos offline antes de autoría, no veo motivo para bloquear.

**Lo que es correcto**

- Retiro de B3G1 bien justificado. ReadAllBytes abre con FileShare.Read y eso deniega la escritura que el motor ya tiene abierta. El error 32 es esperable y no dice nada del candidato.
- Abrir con FileShare.ReadWrite es el remedio estándar. Sin handles privados ni cierre del escritor es la decisión correcta.
- Clasificar sólo un bloque exacto, con fuentes fijadas por SHA, y seguir reportándolo como confusor residual es conservador. La pareja queda en DIAGNOSTIC, no en cierre de calidad.
- Doble snapshot para END270 con misma longitud y hash cubre el caso de copia a mitad de escritura.
- Prohibir reintentos internos y no tocar DayZ_MCP ni skills mantiene el perímetro.

**Fixes exigidos antes de autoría**

1. **Timestamp.** El plan exige "un mismo timestamp" para el bloque. El script_*.log de Enforce no lleva marca de tiempo por línea; la lleva el RPT. Si el lector busca timestamps en ese archivo, el bloque nunca coincide y cada run queda bloqueado o, peor, alguien afloja el criterio en caliente. Sustituir por contigüidad estricta: el mensaje y todos los frames en líneas consecutivas, sin línea ajena intercalada, y sin frame antes ni después.

2. **Discriminador concreto.** Definir un golden offline derivado de los bytes archivados de B3G1 (sha 99df8cd5...), no escrito a mano. Tupla normalizada: literal exacto del mensaje de GetPlugin tal como aparece en PluginManager.c, lista ordenada de frames con archivo y número de línea, y nada más. Los números de línea se validan contra los tres entries por SHA del report.json. Un frame con línea distinta, un archivo distinto, un frame extra, un traceback truncado o cualquier texto adicional dentro del bloque devuelve BLOCKING. Test positivo con el golden y test negativo por cada mutación que el plan ya enumera.

3. **Cardinalidad.** Decidir y documentar cuántas apariciones se esperan. Por fuente, OnInit de PluginItemDiagnostic se ejecuta una vez por PluginsInit. Fijar expected=1. Una segunda aparición idéntica no es "conocida", es BLOCKING, como ya implica el plan, pero hay que decirlo explícito para que nadie lo lea como repetición benigna.

4. **Avisos al cerrar.** El plan menciona avisos pero no los clasifica. Regla explícita: SCRIPT(W) se conserva y se lista en el recibo, no bloquea por sí solo; cualquier SCRIPT(E) fuera del bloque golden bloquea. Sin esa regla hay espacio para interpretación en el momento de adjudicar.

5. **Identidad del archivo.** Usar nombre, ctime y mtime como identidad es frágil. mtime cambia en cada append, que es justo el caso normal de archivo creciente. Usar creación más índice de archivo y serial de volumen (GetFileInformationByHandle) tomados en el primer open y recomprobados en el segundo snapshot. mtime se conserva como dato, no como clave.

6. **Origen del PID.** "PIDbirth propios" debe decir de dónde sale. El script_*.log no imprime PID; el RPT sí. Si el PID se toma del proceso adoptado por el wrapper, declarar que se compara con el proceso vivo y no con el contenido del log.

7. **Repro offline con modo de compartición realista.** No se conoce con qué share flags abre el motor su log. El repro debe cubrir dos escritores: uno con FILE_SHARE_READ y otro sin compartición. En el segundo caso el lector debe devolver INCONCLUSIVE limpio, nunca intentar backup semantics ni VSS. Verificar que el fallo de ReadAllBytes reproduce error 32 exactamente. Añadir FileShare.Delete para tolerar rotación sin falso cambio de identidad.

**Riesgo residual que queda declarado**

El bloque conocido demuestra que ese DumpStack no es excepción ni causa de la falta de END. No demuestra que el candidato no tenga otro problema; la evidencia de 31Q sin END sigue siendo un fallo abierto y así debe reportarse. La inocuidad se apoya en el guard if(m_ConfigDebugProfile) dentro de PluginItemDiagnostic; si en B3G2 aparece cualquier otro consumidor de ese plugin, el bloque deja de ser "el mismo" y bloquea por el fix 2. Eso es correcto.

**Condiciones de adjudicación**

Code review posterior sobre el lector y el clasificador, suite verde incluyendo el golden y sus mutaciones, y sólo entonces preparación y una pareja. No autorizar motor con esta revisión sola.

FIN_REVISION