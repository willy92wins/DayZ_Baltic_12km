# Fondo de 1 m y calado mínimo de 0,95 m

**Decisión aplicada y dos fondos omitidos corregidos y probados.** El usuario eligió conservar el fondo de 1 m y aceptar 0,95 m de calado mínimo. [Respuesta congelada](decision.json), aplicada a P9 y al plan de agua. El candidato antiguo que rebajaba fondos y reserva vial permanece rechazado y sin desplegar.

## Resultado y paquete

`P:/Mods/@DayZ_Baltic_Floor095Preview/Addons`, cargar ambos archivos:

- Mundo `0f1e450f13aa1401f3a73d8bc9ce32ab9887cf4f60c44b09f0e2acac33cce26d`.
- Agua `992000c42964ff45017488bbb62bab5ae5b146999712c9108b9ccc722e464702`, exacta a JunctionPreviewR2.
- Terreno `05a9d6812ba3e3391b8da0d4690e8034ea747a92aa0fdaa96425b58dd78074d3`, en `E:/DayZ-Baltic-Build/v30-navigation-contract-20261008/terrain_floor.npz`.

El WRP fuente conserva los 16.599 objetos, cabecera, materiales y terminador exactos; solo cambian dos alturas. Las 6.827 entradas del PBO se contrastan con el compilado; frente a R2 solo cambia el WRP. Despliegue verificado por hash. El agua conserva la reparación de la unión y sus posiciones. Fuentes: world-source.json, world-package-verified.json, world-package-diff.json, deploy-receipt.json.

## Hallazgo y corrección de BALTIC-018

Dos vértices de navegables altos seguían a −1,603338 y −1,04 m, pese al nivel de agua de 2,45 m: (1992,6432) y (1836,6384). Son componentes aisladas de un vértice. `profile_inland_v30.py` omitía componentes menores de cuatro vértices antes de marcar `profiled`; la elevación del fondo dependía de esa marca. Se separa esa condición para los navegables altos que admiten el fondo completo; bajos y exclusiones anteriores se conservan.

El candidato acotado eleva únicamente esos dos vértices a 1 m. No rebaja terreno ni modifica tierra seca, niveles, clases, reserva vial o plataformas. El selftest del productor incluye un navegable aislado: con la opción desactivada conserva −1 m, activada llega a 1 m. Resultado SELFTEST PASS, además de las comprobaciones heredadas. authoring.json y profile-selftest.log.

## Validación

- **19 corredores de 24 m: PASS**, 36.494 caras nativas, mínimo nominal 0,955608944 m. Umbral 0,95 sin descontar el antiguo centímetro. Enumeración por cajas y triángulos, independiente de `records`/rasterize del productor. El área cubierta se compara con cada polígono; incluye seis caras más que el enumerador anterior, sin cambiar el mínimo. Al aplicar el umbral anterior conserva las 358 caras fallidas: los datos históricos no se convierten retrospectivamente en PASS.
- **Suelo alto: PASS**, 15.095 vértices navegables con nivel ≥2 m fuera de la exclusión circular de Narva, cero bajo 1 m. Baseline rechazado por los dos fondos omitidos. Obstáculo de 0,94 m y retirada de una cara rechazan el gate.
- **Protecciones: PASS**, carreteras, tierra seca, metadatos, Narva, reserva vial y plataformas; ninguna cara mixta nueva o empeorada por encima de 35°. Los 18 observadores temporales permanecen exactos. Las doce rutas anteriores de coche/lancha quedan a más de 1.122 m de los cambios; mantienen su alcance local, sin repetir viajes por rutina. verification.json.
- **Motor: PASS_TWO_HIGH_BEDS_IN_ENGINE.** Run `976f6698-78c8-4138-a347-c7347e58b91f`, tres puntos por 62 muestras. Los dos fondos se leen exactamente a 1 m y conservan pond 62/62; profundidad mínima 1,31027 y 1,42933 m. Control vecino sin cambios, mínimo 0,600084 m. Calma y tormenta alcanzadas. Se rechazan pérdida de pond, profundidad 0,94, altura anterior y pérdida del control. runtime-verification.json, runtime.log y order.log.

Los corredores conservan sus exclusiones congeladas de extremos y Narva. Se comparte la fórmula nativa de interpolación y la regla de niveles de las piezas; la enumeración nueva no prueba por sí sola la carga de cada pieza. La serie de motor cubre estos tres puntos, no una envolvente máxima de oleaje. La lancha conserva las seis pruebas locales anteriores, no una prueba de toda la anchura ni de barcos medianos.

Cierre orderly_close con terminación del servidor; lease liberado, owner=null, banco libre. lifecycle.json. Un único candidato de dos alturas, sin corrección posterior de geometría; pruebas agrupadas al terminarlo. La revisión Claude anterior no cubre automáticamente esta unidad.

## Pendientes

BALTIC-012 satisface el mínimo geométrico elegido; no se atribuye una reparación geométrica a bajar el umbral. BALTIC-018 corrige además los dos fondos omitidos; quedan los bajos/Narva y su aceptación visual. Tiles 019, finales 020, curvas/arroyos, lagos grandes y vistas de reserva/SPB siguen abiertos con su alcance anterior. Terrain Builder precede a navmesh, una vez aceptada la geometría. No hay promoción global a base 1.0.

La prueba manual de foco está completada: [evidencia de render](render-focus/README.md). La reserva permaneció parcialmente gris en segundo plano; entre las muestras 12:51:20.552 y 12:51:21.574 pasó a texturizada al recibir foco, con matriz de cámara idéntica. El foco posterior fue intermitente, no 20 s continuos. Se acredita recuperación visible en este caso, no el mecanismo nativo ni el cierre global de 019. Cliente y servidor cerrados; banco libre. Los avisos CloudsEffect/alpha también aparecen en el run anterior texturizado y no discriminan por sí solos.
