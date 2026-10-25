# Curvas R1 rechazadas; alternativa plana en prueba

**Ninguna variante de curvas se desplegó.** Se ejecutaron las dos variantes y la única corrección previstas por el paso 5 de `plans/v30-rumbo-agua-1.0.md`. Después, Guillermo autorizó incluir la orilla local de Narva en la alternativa plana. La preview nueva es `@DayZ_Baltic_FlatWaterPreview`; la anterior Floor095Preview se conserva. Ninguna se promueve a base 1.0 por una prueba offline.

| Caso | Piezas / curvas | Doble lámina entre piezas | Huecos en caras mojadas | Resultado |
|---|---:|---:|---:|---|
| Control desplegado | 8 / 0 | 56,53 % | 0 | Control funcional; solape visual pendiente |
| A, escala 4 | 4 / 3 | 0,000109 % | 45 caras; 0,0483 m² | FAIL |
| B, escala variable | 6 / 6 | 0 % | 124 caras; 109,60 m² | FAIL |
| A1, única corrección | 4 / 3 | 0,01193 % | 0 | FAIL por cambios de orilla |

Las huellas se leen de caras roadway de los modelos vanilla, no de sus cajas. Los 14 modelos coinciden con la biblioteca por SHA256. El dominio R1 incluye 582 caras completamente mojadas y un corredor local de 24 m; no equivale a todo el mapa. `footprints.png` compara la disposición; las líneas negras escalonadas son el dominio de comprobación de celdas, no una nueva línea de agua diseñada.

A1 alinea los extremos ya inclinados, añade 1 cm de solape en cada junta y redondea las matrices a float32, como WRP. La corrección desplaza tres piezas como máximo 2,9 cm. Cierra todos los huecos medidos y pasa 510 muestras de profundidad. Sin embargo, seis muestras de una malla de 3 m pasan de secas a mojadas; una está rodeada por cuatro vértices de clase seca. Además, la huella coincide con 5.148,67 m² de planos vecinos, cuya integración aún tendría que tratarse. El solape entre piezas no demuestra ausencia de doble agua con los planos. `correction.json` conserva coordenadas y límites.

Los primeros controles de `result.json` eran diagnósticos sobre candidatos ya fallidos, sin positivo suficiente. La aceptación usa los controles posteriores de `correction.json`: A1 positivo para cobertura/profundidad, retirada de piezas, duplicación, hash realmente rechazado por el lector y profundidad seca. Pasan esas comprobaciones; el candidato completo sigue fallando por las orillas. No se abre una tercera variante de curvas.

## Vuelta a planos

El siguiente paso autorizado por el plan es representar R1/R2/R3 con planos. Se evaluó primero la regla actual `cell_planes` sobre las celdas de las piezas que se retirarían. Esta tabla corresponde al diagnóstico previo al perfil y al paquete nuevos.

| Tramo | Muestras | Nuevos puntos mojados | Puntos que pierden agua | Falta de cobertura |
|---|---:|---:|---:|---:|
| R1 | 1.579 | 3 | 1 | 0 |
| R2 | 830 | 14 | 1 | 0 |
| R3 | 765 | 1 | 1 | 0 |

Esto exige reperfilar orillas y comprobar su resultado; sustituir las piezas y declarar PASS conservaría fallos. Es una comparación nominal de 3.174 puntos, no prueba continua ni envolvente de oleaje. Los cuatro cambios de R1 están en el ámbito protegido de Narva.

La exploración mínima, restringida a los 35 vértices que soportan los 21 puntos discrepantes y con margen local de 0,201 m, resulta inviable incluso permitiendo Narva. No demuestra imposibilidad de un perfil con transición: prueba que ese parche mínimo no basta. `flat-shore-proposal.json` conserva ambos FAIL; ese intento no generó terreno.

Guillermo respondió «Sí, ajustar también ese tramo de Narva» (`narva-decision.json`). La decisión de fondo 1 m / calado 0,95 m sigue vigente. Puentes, reserva vial y plataformas están protegidos.

## Perfil y paquete plano

El perfil local reutiliza `profile_inland_v30` con sigma/banda de 18 m y una transición hasta 24 m del dominio. Cambia 456 vértices, 229 en Narva. El intento de conservar toda altura de la reserva deja 13 esquinas someras en R3; la corrección de solo lecho empeora taludes y se rechaza. Se revisó la implementación para resolver conjuntamente lecho y orilla dentro del encargo de cauces y smoothing: 60 vértices de agua y 33 de tierra en R3, bajadas máximas 26,8/19,4 cm. P13 conserva el perímetro y los biomas, que no cambian. Esta excepción local y sus motivos se anunciaron antes de incorporarla; no es una nueva aceptación visual del usuario.

Resultado: **549 vértices** frente a Floor095Preview; clases, niveles, perímetro de reserva, carreteras, plataformas y las demás zonas protegidas exactos. `flat-verification-r2.json`: 698 caras completamente mojadas sin huecos; cobertura de celdas restauradas completa; redundancia de agua **0,08061 %**, incluidos planos vecinos. Ninguna esquina seca bajo el agua ni esquina mojada por encima de su plano mínimo. Taludes dentro de la tolerancia previa de 0,0001 grados; una diferencia float32 de 0,0000086 grados se informa expresamente, junto al resultado estricto anterior.

Los 19 corredores y 36.494 caras mantienen mínimo **0,955609 m**; la corrección adicional de R3 está a más de 1.126 m de ellos, por lo que sus soportes no cambian. Carreteras: 77.381 estaciones PASS. Negativos de hueco, duplicación y obstáculo real de calado 0,94 m rechazados. La prueba nominal no acredita el máximo oleaje ni la estética.

Se regeneran 46 grupos de teselas: se retiran 148 poses y entran 538 modelos/poses planos; 16.451 registros WRP y los nueve puentes quedan exactos. Los modelos compilados se comparan por geometría y altura con sus MLOD, con error <0,01 mm. Se preservan las 9.606 entradas anteriores del PBO de agua y las 6.826 entradas del mundo distintas del WRP.

`flat-deploy-receipt.json`: mundo **48cc4d94**, agua **62a14dee**, terreno **e0d35db0**, fuente WRP **1706f559**. Productos fuera de Git en `E:/DayZ-Baltic-Build/v30-curved-channel-pilot-20261008`. Las fuentes/scripts y recibos se guardan aquí. No se sobrescribe la preview anterior.

## Pruebas realizadas y pendientes

Motor: 28 puntos x 62 muestras en calma/tormenta, controles secos y hueco antiguo: PASS, run 93339a52. Lancha R1: ambos sentidos, 177,9 m cada uno, 662 muestras y salud conservada, run fe128ccc. Ver flat-runtime-verification.json y flat-boat-verification.json.

**Visual FAIL del usuario:** reflejos sobre tierra, juntas en cuadrícula en R2 y cauces/taludes demasiado angulares. Estos resultados físicos no acreditan estética. Continúa en ../v30-water-visual-fix-2026-10-08/README.md; la preview plana no se acepta como base 1.0.

Finales 020, lagos grandes, vistas completas y aceptación de geometría siguen abiertos. Terrain Builder precede a navmesh. Sin nueva variante de curvas nativas ni revisión externa de este piloto.
