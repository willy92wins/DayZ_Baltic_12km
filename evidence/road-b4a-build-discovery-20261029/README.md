# RoadB4A — referencias viales identificadas; build pendiente

Resultado **INCONCLUSIVE_DISCOVERY**, una ejecución 1.203s/47,005,696bytesRSS. El PBO instalado34c1cabe (318,217,469bytes,501entradas) mantuvo hash y prefijo. Sus tres modelos y cuatro recursos internos concordaron con el catálogo guardado. Todos los LOD de las tres piezas aportan cinco referencias únicas; asphalt_ext.paa del RoadwayLOD3 está fuera de este PBO y permanece UNRESOLVED_EXTERNAL.

Las siete rutas del build devolvieron SOURCE_UNSTABLE. Los metadatos causantes no quedaron en el retorno temprano del extractor: **no se ha probado cambio de contenido ni su causa**. sources_stable=true se refiere exclusivamente a las fuentes primarias fijadas y al PBO; no certifica estas siete rutas. El agregado inconcluso y build_ready=false se conservan.

Un discriminador posterior de una sola pieza observa SHA7eb9f894 y firmaODOL54, distintos del instaladoODOL56 d72224ed. Los dev/ino/size/mtime coinciden entre ruta y handle; ctime difiere entre APIs, estable dentro de cada API. No demuestra la causa de los siete estados ni modifica R0. Plan separado B4A1 revisado para capturar todas las observaciones, sin repetir la CLI ni eliminar guardas.

Se fijó por QueryDosDeviceW el SUBST P: y se observaron los cinco junctions históricos. No se cambiaron enlaces, vanilla, geometría, WRP ni configuración. El metadato PowerShell previo y el de Python se conservan sin explicación causal inventada. QueryDosDeviceW está documentado en [Microsoft](https://learn.microsoft.com/es-es/windows/win32/api/fileapi/nf-fileapi-querydosdevicew); sólo la primera cadena representa el mapping actual.

Suite final:39coleccionados,38PASS y1SKIP por privilegio de symlink. Hay además negativo reparse simulado sin privilegios. R0 conservó17tests/1FAIL/1SKIP; R1 31/30PASS/1SKIP. Fable129.688s y correcciones Muse adjudicadas. El fallo inicial de preparación fue una ruta de report inexistente antes de lanzar un modelo; la continuación usó el report público RoadB3 fijado, sin repetir B3.

Integridad del manifest no equivale a validación geométrica. Los JSON publicados sustituyen prefijos de rutas por variables; publication-source.json enlaza cada hash original y publicado. private-manifest.json sigue refiriéndose al informe ORIGINAL privado, no al JSON sanitizado. No se publican binarios ni caras vanilla.

Pivote, ancho útil, accesos, pavimentado, conducción y aceptación del mapa siguen abiertos. Siguiente: plans/ev112-road-b4a1-source-stability-20261029.md. Sin build, paquete ni DayZ en esta unidad.
