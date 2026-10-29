# Revisión del integrador antes de ejecutar RoadB4A

No se ha ejecutado el extractor real. La suite R0 conserva 17 pruebas, 1 fallo y 1 omitida.

- `road_build_discovery_ev112.py:314`: FORMAT_DIFFERS entra en drift y produce INPUTS_DIFFER; contradice el plan. Sólo DIFFER comparable debe tener esa precedencia.
- `observe_file` lee los bytes para parsear después de los dos hashes y del fstat final. Esa tercera lectura no queda ligada al hash. El contrato se hashea y después se lee por separado sin volver a hashear los bytes parseados. Usar la misma captura para hash y parseo.
- Catálogos no fijados o con hash discrepante pueden parsearse; los pins iniciales no impiden su uso. Verificar antes de parsear y volver a comprobar al final. La prueba de fuente mutada antes de ejecución no debe aceptar ningún informe exitoso.
- `entry_norm` contiene `or True`, y `find_catalog` admite sufijos. El contrato exige nombres exactos normalizados y prefijo exacto. Eliminar las vías permisivas.
- Campos obligatorios de catálogo/LOD y contrato usan defaults. Un catálogo sin `lods` podría borrar referencias y reducir cobertura. Validar presencia y tipos antes de observar modelos.
- `pbo_info.size_status` no llega al agregado. Validar longitud y hash antes de tabla/rangos; un PBO no fijado no es referente válido.
- `inspect_build` no compara lstat inicial/final con el handle y no revalida ancestros al cerrar. Conservar identidad de ruta y fichero y rechazar cambio.
- Falta control positivo INPUTS_MATCH sin referencias externas. La prueba de formato debe exigir agregado INCONCLUSIVE; añadir negativos de ausencia de campos, repinado local/contrato cambiado, referencia no Visual y reparse simulado sin depender de privilegios.

Corrección del propio briefing: la firma RAP documentada aquí como `rap\0` era errónea. Fuente real `tools/playtest/attach_navmesh.py:77` exige `b'\0raP'`; primer16bytes de installed-config.bin de B0: `0072615000000000080000009f790000`. Corregir fixture y detector. No atribuir el error al ejecutor.

No se ha probado causa del contraste metadata PowerShell/Python ni aceptado resolución nativa, pivote o ancho.
