# Adjudicación RoadB4A1

Fable5.1 nativo79.766s SOUND-with-fixes; entregado y consumido.

Adoptados: cada lectura debe tener n == st_size antes/después; conservar todos los predicados R0 y añadir hash2. Rutas EXACTAS del campo build.path de R0, que son canónicas C:, no inventar alias diferentes. Rawmetadata y componente concreto que cambia. Tests validan predicado nuevo, no reproducen un fallo histórico sin metadata. Conservar artefacto parcial por fases fsync y recibo del coordinador: un kill durante llamada bloqueada no puede prometer informe completo; salida parcial + TIMEOUT implica INCONCLUSIVE, no reintento. No asumir que haya hidratación ni su causa.

Refutada exigencia de que QueryDosDeviceW devuelva una sola cadena: la documentación oficial indica primera cadena = mapping ACTUAL, siguientes = mappings anteriores no retirados. Rechazar por su mera presencia añadiría un falso FAIL. Fuente:
https://learn.microsoft.com/es-es/windows/win32/api/fileapi/nf-fileapi-querydosdevicew
Conservar opcionalmente MULTI_SZ crudo, juzgar mapping actual; comparar ambos lados mediante win_norm. El código R0 ya hace win_norm en ambos: no falta esa normalización.

No adoptada explicación causal de ctime/OneDrive: no la demuestra esta revisión; sólo campos observados. El predicado R0 ya usa ctime dentro del handle, no entre APIs. Conservamos esta limitación y el dictamen INCONCLUSIVE histórico.

Límite aceptado: cambio revertido completamente entre observaciones puede no verse. No afirmar vigilancia continua ni snapshot atómico global. Cualquier referencia externa sigue abierta. R0 no guarda firma de material PBO, así que no inventarla: para comparar formato usar sólo una firma independiente fijada si existe; de lo contrario distinguir igualdad de hash de diferencia de bytes con formato de referencia UNKNOWN. No atribuir diferencias semánticas.

