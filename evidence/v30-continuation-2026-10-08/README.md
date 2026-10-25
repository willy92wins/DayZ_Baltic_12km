# Continuación: controles de agua y unión R1

**Reparación local probada en motor; base 1.0 todavía no aceptada.** Continúa el smoothing del commit 71131f5 y la revisión de los veinte fallos. El terreno b363b79d queda exacto; esta unidad corrige comprobadores y una pieza de agua, sin aplicar la propuesta de calado pendiente.

## Paquete actual

`P:/Mods/@DayZ_Baltic_JunctionPreviewR2`:

- Mundo `b1bcb99da99b57075466529aaad7a66c2a1d729b76dc7650af071d98daafac91`.
- Agua `992000c42964ff45017488bbb62bab5ae5b146999712c9108b9ccc722e464702`.
- Fuente/build: `E:/DayZ-Baltic-Build/v30-continuation-20261008/junction-fix-r2`.
- Terreno `E:/DayZ-Baltic-Build/v30-bug-recheck-20261008/wave-banks-r1/terrain_wave_banks.npz`, SHA256 b363b79dc8b4374a626644da78f110666139d382ee09a38dc7aade46b2e659dc.

Solo cambia `pilot_00001.p3d` entre 9.606 entradas del PBO de agua. En las 6.827 entradas del mundo cambia únicamente el WRP: compensa el nuevo centro del ODOL en un objeto; alturas, materiales y otros 16.598 registros editables exactos. El origen físico sigue en (2184,1,45,7080). No basta con cambiar el PBO de agua: hay que cargar ambos. Recibos: package-stage-r2.json, world-package-diff-r2.json, world-package-verified-r2.json y deploy-receipt-r2.json. Los paquetes anteriores se conservan.

## Resultados

**BALTIC-015, hueco de unión.** El gate anterior examinaba vértices separados 6 m. La nueva diferencia de áreas sobre 698 caras enteramente mojadas encuentra un hueco de 1,813 m² junto a (2207,65;7080,70). Baseline: los dos observadores del hueco dan pond=0/62; el control vecino, 62/62. Primera variante: corrige el interior, pero la diagonal queda fuera de la geometría. Se conserva ese FAIL y el mecanismo en native-boundary-repro.json: recorte sin solape y cuantización de MLOD/WRP; el desplazamiento de Z del WRP es 0,128 mm.

R2 amplía el parche con solape de 1 cm: añade 1,878 m² al mismo nivel de 1,45 m. Conserva terreno y niveles. La comprobación de caras devuelve 0 área descubierta en ese ámbito. Los 31 ODOL retenidos que tocan celdas retiradas coinciden con la geometría fuente tras corregir su centro, error máximo 0,000000954 m. Un hueco subcelda sintético, una orientación desconocida y un pond real reinsertado donde se declaraba retirado son rechazados.

**Repetición en motor: PASS_LOCAL_JUNCTION_WATER.** Mismas tres coordenadas y misma misión en baseline, R1 y R2; 186 observaciones por run. En R2, ambos puntos mantienen pond y profundidad positiva 62/62 veces, mínimos 0,116759 y 0,053550 m; control vecino 0,600084 m. Calma 0,1 m/s y tormenta 20 m/s comprobadas. El verificador rechaza ambos ensayos fallidos y las mutaciones de pérdida de pond/fondo expuesto. Run final e331cded-fe15-4831-a91c-f4f0d84bc4f4; gap-verification-r2.json. No cierra todos los solapes visuales ni certifica caras mixtas completas o oleaje máximo.

**BALTIC-009, control de agua alta.** Claude detectó que el 693 ya era seco y seguía etiquetado como positivo. El nuevo gate por rol rechaza aquella serie; no cambia retroactivamente sus resultados. V3 conserva los 17 puntos originales, registra el 693 como seco explícito y añade 2001 sobre un pond alto confirmado antes del lanzamiento. Las 5.436 observaciones pasan: siete someros, dos positivos pond, mar y ocho secos. Mínimos de las orillas reparadas: 0,068747 y 0,063938 m; nuevo control alto: 0,696124 m. Cuatro negativos rechazados. Run 56b6725d-4fe2-43cb-8685-c2610c2773e7; controls-verification.json. Los 18 puntos están fuera de la única pieza modificada después, y el terreno permanece exacto. Las doce rutas anteriores de coche/lancha quedan a más de 1.729 m de ella: conservan su alcance local, sin repetirlas por rutina.

**BALTIC-012 sigue abierto.** La propuesta anterior rebaja 6.305 vértices; 483 son de reserva vial, 0 de reserva natural. Los 88 fondos altos bajo 1 m son todos nuevos. No hay cambios de una ULP: delta mínimo 0,000101 m, máximo 0,079369 m. El generador y el gate ahora conservan la reserva vial. Con esa protección, el solve es INFEASIBLE; la propuesta anterior queda rechazada y no desplegada. Resolver solo los 88 fondos altos no bastaba. Se ha planteado al usuario priorizar el calado de 1 m con esas excepciones locales, o mantener el fondo de 1 m y aceptar 0,95 m de calado mínimo. Ninguna opción se ha aplicado en esta unidad.

**BALTIC-019 y vistas pendientes.** El run visual 0aef8252 reproduce terreno sin textura, edificios degradados y cielo magenta. La reserva sigue igual tras una repetición 53 s después. Ocho muestras de foco posteriores registran ventana en segundo plano; no aíslan la causa ni describen todo el run. RPT, imágenes y superficies capturadas conservadas. No se tocó el shader ni se cerró el fallo por la heurística. La aceptación visual de reserva/SPB, cauces, costa y bajos continúa INCONCLUSA.

## Revisión y continuidad

Claude Opus 5.5 revisó el commit 71131f5: SOUND-with-fixes, solo lectura, 21 fuentes autorizadas, sin herramientas. [Contraste por hallazgo](review-response.md). La revisión no abarca automáticamente estas reparaciones posteriores. Sin merge, push ni promoción a base aceptada.

Los estados restantes del [audit de los veinte fallos](../v30-bug-recheck-2026-10-08/README.md) mantienen su ámbito. 005/006 conservan pruebas locales; 007 conserva smoothing medido; 008 pospuesto; 010/011 requieren vistas válidas; 013 conserva delta; 014 espera Terrain Builder y geometría final; 016–018 mantienen decisiones de bajos/lagos; 020 mantiene finales cuadrados. R1/arroyo no queda aceptado visualmente por tapar este hueco.

Los cinco runs propios de esta continuación terminaron con orderly_close y línea de terminación; leases liberados y banco libre. Hubo recuperaciones del lease sobre el mismo run tras análisis prolongado, sin reiniciar ni mezclar series. Evidencia: visual-lifecycle.json y runtime-lifecycle.json. Próximo paso: resolver el conflicto de calado planteado, continuar las decisiones y vistas pendientes del plan; después Terrain Builder y navmesh final.
