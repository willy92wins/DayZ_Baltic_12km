# Recuperación del editable V30

Estado: **copia nativa abierta y guardada con nombre nuevo; importación V30 pendiente**. El mod aislado de
pruebas y el paquete canónico permanecen intactos.

- La importación de mapa WRP rechazó la cabecera `0WZD`; no importó alturas,
  materiales ni objetos. `import-result.json` y `import-unsupported.jpg`.
- Alternativa prevista: copia íntegra V29 de 9.084 archivos en
  `E:/DayZ-Baltic-Build/editor-v30-delta/native-asc`. `asc-clone.json` verifica
  origen y destino. Se añadió el ASC V30 `64d4f160`.
- El 03-10 se abrió `native-asc/road_v29.tv4p`: un mapframe y 10.161 objetos
  heredados de V29. Save As produjo `native-asc/delta_v30_native.tv4p`,
  452.752 bytes, SHA `2e5de2c837be0b2391d1bc1fba6f6fcd439a306c3861ac68946c28415e8d11c5`.
  La rejilla quedó referenciada en E: bajo el nombre nuevo. El original sigue
  SHA `5f5acd3ae79ed19775ac6fa83b9f7e956295e2a9358046e0800d13e95a41001a`.
- La raíz de salida **ya está aislada** en `P:/baltic_editor_v30_delta`, junction a
  `E:/DayZ-Baltic-Build/editor-v30-delta/world`. Guillermo aplicó el campo y OK;
  después se pulsó Save project mediante CU. La relectura del archivo confirma
  la referencia nueva: 452.726 bytes, SHA
  `fd8b3905ba16f5549ffb346fe46af7ab9dc98dfbfd14d6f884824927abafc9be`.
  El hash `2e5de2c8` anterior corresponde a Save As antes del cambio de raíz.
  `root-isolation.json` conserva recibo, referencias y hash del original intacto.
  Las referencias de importación aún nombran `road_v29.asc`: no se ha importado V30.
- La edición automática del campo había introducido un valor distinto del
  solicitado; `set_value` y varios clics agotaron el tiempo. Tras guardar la
  corrección manual, File volvió a agotar el tiempo y una observación mostró
  otra aplicación: no se envió texto ni teclado y se liberó CU. No se atribuye
  causa interna al helper; reobservar antes de actuar.
- `water-import-preparation.json`: 17.622 instancias, 13.419 modelos, poses
  canónicas y alturas absolutas. No incluye los nueve puentes. Las plantillas
  V29/V30 tienen nombres coincidentes: resolver exclusivamente contra la
  biblioteca V30 al sustituir la capa antigua en la copia.
- `surface-source-preparation.json`: satélite y máscara 12.288², 1 m/píxel,
  derivados de las 2.048 PNG actuales verificadas por hash; 1.984 comprobaciones
  de solape por imagen. Exportación PNG exacta por comparación de todos los
  píxeles con el mosaico TIFF. Satélite `95b25acd`, máscara `526bfdfe`.
- El `layers.cfg` nuevo conserva cuatro materiales vanilla y usa rojo para
  coníferas y verde para hierba, conforme al productor V30. No reutiliza la
  correspondencia invertida de `source/layers.cfg`. El archivo antiguo no cambia.

Fuentes completas en `E:/DayZ-Baltic-Build/editor-v30-delta/world/native_sources`.
El primer intento falló por mayúsculas en el manifiesto y el segundo se detuvo
durante una prueba de lancha. Ambos se conservan en carpetas separadas;
el resultado final procede de una ejecución completa posterior, sin prueba
de movimiento propia concurrente. No se atribuye causalidad de las pausas.

Pendiente: importar ASC y recursos en la raíz aislada,
Rebuild, guardar/exportar/reabrir y comparar todas las alturas/materiales/poses.
No usar un TV4P existente como prueba de esos pasos. No promover ni reutilizar
la navmesh si cambia el WRP. Procedimiento: `plans/v30-native-editor-recovery.md`.
