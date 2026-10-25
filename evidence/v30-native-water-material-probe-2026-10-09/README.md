# EV17 — material nativo comprobado, sin arreglo del residual

El módulo diagnóstico obtiene handles reales de `oceanold`, `_nice`, `_storm` y `shoreFoam`; `_samplemap` devuelve null. Los índices de las propiedades conocidas y el control negativo funcionan. El control de consumo también funciona: `NormalPower=0` elimina el detalle normal de las olas y reset lo devuelve. Esto supera el límite de los antiguos marcadores CfgMaterials, que no demostraban consumo.

`WetFloor=0` altera claramente las orillas legítimas. En el centro seco calibrado de la captura del usuario, el cambio RGB medio es 0,071 niveles, frente a 0,286 entre capturas con valores restaurados. En un control de orilla es 9,392 frente a 0,986. No hay supresión demostrada del residual seco y no se convierte este parámetro en un arreglo. El residual original tampoco se reprodujo con intensidad estable en ese centro durante la serie; no se descarta universalmente una contribución de este material.

Una ejecución, sin recompilación de reparación ni variante de colores. Fases 0→1→2→3→9→2→9, todas con readback de aplicación y capturas a cámara fija; olas sin sincronización de fase. La vista próxima confirma cambios en el sombreado de las charcas vecinas, no agua física en el centro seco. No se cambia ninguna geometría, nivel, shader ni fichero vanilla.

Limitación adicional: la fase 0 ya llama a `ResetParam` de las tres propiedades. Por tanto es una referencia con parámetros restaurados, no una prueba de identidad con el estado inicial intacto del motor. El control positivo de consumo sigue siendo válido; la serie no permite excluir globalmente el material como causa del residual original.

Run `35b8a7fe-c651-4701-81c7-80f56b0c5aff`, cierre normal cliente/servidor, parámetros restaurados, lease liberado y sesión disponible. El addon `@BalticNativeWaterProbeV1` no pertenece a la base ni a las pruebas físicas posteriores. Sus hashes y los del mapa están en `reference.json`. `pixel-measurements.json` es lectura numérica de capturas originales; no genera imágenes editadas.
