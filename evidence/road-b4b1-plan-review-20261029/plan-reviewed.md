# RoadB4B1 — equivalencia de contenido guardado, sin identidad física inventada

Estado: BORRADOR_PENDIENTE_DE_REVISION. Trazabilidad Q04/P10/P11. Unidad distinta de B4B0 consumido; no modificarlo ni repetir su censo. Objetivo: evitar que aliases de escritura generen conflictos de contenido ficticios, conservando la incertidumbre de precedencia física/nativa.

## Mecanismo leído y alcance

[EXACT] road_scene_reference_index_ev112.py:244-245 devuelve provider con package crudo, SHA PBO, prefix, entry crudo y SHA modelo; :305 indexa por JSON canónico del objeto completo y :353-358 une proveedores y declara conflicto si hay más de uno. verify_road_scene_reference_index_ev112.py:241,293,340-345 usa la misma definición de identidad. La representación de filesystem y el contenido virtual son dimensiones distintas.

Los cuatro registros de saved-provider-comparison.json conservan SHA PBO/modelo iguales y diferencias sólo package slash y entry case. Son 28 instancias existentes, no los tres objetos nuevos. Ese archivo es una pista guardada; la nueva herramienta debe verificar sus fundamentos directamente en las fuentes de metadatos fijadas, no aceptar su booleano content_pin_dimensions_equal como oráculo.

Entradas externas nuevas por hash/bytes antes de código: contrato B4B0, su report88589882, consumidor53bd9540 y recibo de recuperación que los vincula; índices B2A models/report/config y road_models/road_entries/B4A3 contract/summary ya fijados por B4B0. No abrir ninguna ruta WRP/PBO/modelo/material referenciada por esos JSON. Lectura de metadatos guardados únicamente; no funciones scan_source/build_report/CLIs consumidos ni modificar helpers sellados. No duplicar censo de instancias. Originales intactos.

## Contrato de contenido [DESIGN]

Para cada uno de los5512nombres virtuales del reporte, conservar conteos, aliases, estado y proveedor original, y derivar grupos de contenido desde los índices guardados. El nuevo resultado nunca sustituye el reporte antiguo. Key=(package_sha256, normalized_prefix, normalized_entry, model_sha256). Normalización virtual ASCII exacta de slash/case/strip exterior ya autorizada; rechazar traversal, drive, controles, componentes interiores vacíos y colisión de contenidos bajo la misma key virtual. No basename fallback. El join prefix+entry debe dar exactamente el nombre esperado.

Cada grupo conserva todas las procedencias crudas: source_file_sha, JSON pointer/line, package_locator, prefix_raw y entry_raw. Package locator NO entra en igualdad de contenido; sí se conserva como observación. No resolverlo, ni usar normpath/realpath para afirmar identidad física. Dos paquetes con SHA distinto permanecen distintos aunque el modelo coincida. Dos entradas normalizadas iguales con SHA modelo distinto bloquean. Clave igual con locators distintos significa SAME_PINNED_CONTENT, no SAME_PHYSICAL_PROVIDER. Claims provider_precedence_current,physical_file_identity,build_ready y native_resolution permanecen NOT_EVALUATED/false.

Recibos de B2A package/config, B4A3 sources, tabla entries y READ_STRICT deben validarse conforme al esquema real leído, sin inventar keys. Reutilizar primitivas de JSON/hash sólo; derivaciones de grupos productor y consumidor separadas. Productor construye grupos mediante diccionario; consumidor recorre filas fuente, verifica pertenencia y cobertura de cada referencia, detecta grupo omitido/inventado/duplicado contra fuentes. Compartir una normalización no convierte todo el consumo en independiente: usar implementaciones distintas y fixtures literales para ella. Fuente y report ligados a recibos; SHA autodeclarado no basta.

Resultado SAVED_CONTENT_IDENTITY_VERIFIED_ONLY si toda referencia tiene exactamente una identidad de contenido fijado y todo pin/recibo se cumple. Si permanece conflicto o hueco, INCONCLUSIVE_SAVED_CONTENT_IDENTITY. Aunque las cuatro filas resultaran equivalentes, B4B0 sigue VERIFIED_MISMATCH_DIAGNOSTIC histórico. No cambiar build_ready ni decir reparación del mapa. Esta unidad sólo permite planificar después roots/precedencia reales del build.

## Pruebas, límites y revisión

Fixtures literales: slash y case con SHA iguales forman un grupo; diferentes SHA PBO forman dos aun si SHA modelo igual; SHA modelo distinto bajo mismo nombre rechaza; alias malicioso/traversal/ASCII inválido rechaza; omitir procedencia, falsificar pointer, duplicar referencia, cambiar cuenta y co-mutación productor+reporte contra fuentes rechazan. Nuevo consumidor no llama productor y no reabre WRP/PBO (test con apertura centinela que falla para esas extensiones). CLI completa sobre fixture y consumidor guardado, no sólo positivos de funciones.

Presupuesto antes de ronda1: contrato/plan revisión120s; autoría240s, código review180s, suite120s. Una derivación30s/256MiB, un consumidor30s/256MiB, JSON total de entrada32MiB (metadatos B4B0+sus fuentes guardadas), archivos individuales16MiB, referencias10000, grupos porreferencia16 y procedencias64, reporte16MiB. Comprobar caps antes de materializar; rawstat/hash doble lectura en cada archivo guardado, sin prometer vigilancia continua. No reintentos internos. Saturación o fuente cambiada queda inconcluso y evidencia conservada; no ampliar caps para PASS.

No P:, copia de vanilla, build, DayZ ni colocación. Geometría Q02B3, cruces Q03/Q05 y referentes naturales siguen activos y no se sustituyen por esta auditoría de nombres.
