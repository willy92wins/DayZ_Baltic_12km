# EV13: contorno nativo, cobertura y regresión completa

R1/R2 mejoran con 261 vértices modificados y dos microjuntas nuevas. Preview aislada `P:/Mods/@DayZ_Baltic_NativeContourV1`, probada en motor; no es aceptación de la base ni cierre de todos los giros.

| Artefacto | SHA256 |
|---|---|
| Terreno | cff6d175da46a0080bd761c327babf9c0ef4c53434744ceec9241bc9cc28c82c |
| narva_trial.pbo | 40cffa8c6fc055a40be67d22893c25ad3530ddde5488da2e202ea061aeaadac5 |
| baltic_water_v30.pbo | 4d9359a4f1844038be9f640d1b7047ba59be26b6d8f553bf994d991000a1ea2e |
| Agua visible, conservada | 7a5d0900533670a1e533965b36a6dcf28be2715f96f94ccbfbe6a846bdf98e37 |

El consumidor reconstruye los triángulos del NPZ final: p90 R1 25,32→16,93 grados; R2 25,37→19,66. Conserva 830 masas significativas, contactos, islas, controles, ingeniería y calado protegido. Desplazamiento máximo de contorno 2,60/4,00 m. El primer candidato incumplió pendiente y distancia; una proyección a las restricciones originales lo corrige, sin otro solver ni cambiar umbrales. Fuente y reparación quedan conservadas.

El censo compilado abarca 404.484 celdas. Dos rendijas submilimétricas nuevas se cierran con las mismas juntas exactas EV12; 0 hueco físico y residuo visible 3,8464e-12 m². 17.928 instancias de agua y nueve puentes; 13.032 modelos referenciados. Paridad de los demás contenidos del paquete comprobada.

La ejecución nativa lee 4.194.304 vértices: error máximo de suelo 0,0000152588 m; cero anomalías de inundación en los puntos clasificados secos. Las consultas con flags ausentes no se descartan: 19 faltas de presencia y 222 profundidades positivas sin flags se inventarían. La serie ampliada mide 439 puntos en 62 instantes, en calma y viento de 20 m/s, con controles y antiguos gaps en PASS. Hay 285 contactos intermitentes entre los diagnósticos, incluidas las faltas de presencia, un nuevo escalar siempre positivo y discrepancias de presencia, documentados en `native-diagnostic-classification.json`; no se declaran todos secos.

El residual gráfico del puente sigue abierto. Punto 6113: suelo 1,52045 m, profundidad máxima medida -0,646111 m. La vista calmada carga texturas y conserva una mancha pequeña cerca del puente. La vista previa en tormenta fue demasiado gris para aceptación. `visual-reference.json` separa observación gráfica y consulta física. No se repite una elevación del terreno sin mecanismo probado.

El bloqueo UDP 2316 se resuelve cerrando normalmente el Crash Reporter identificado como hijo del cliente muerto; no se matan procesos ajenos ni se evita el guard. Los dos runs de censo y temporal cierran ordenadamente. La vista calmada posterior también cierra con terminación cliente/servidor; lease liberado, banco vacío. El ticket de foco ya existe (`fb-20261008-233507-8b1c`).

El censo de forma completo inventaría 1.001 cadenas y 427 km de orillas. Continúa en EV14 por bloques con validación global. No se reabren los presupuestos de A/B/C ni finales Msta A/R2. TB, navmesh, navegación final, lagos 269/170 y los fallos visuales siguen su orden y sus puertas.

Fuentes grandes en `E:/DayZ-Baltic-Build/v30-native-turn-optimizer-20261009`; scripts, informes, delta de terreno y fuentes de las dos juntas en este directorio. `preservation.json` verifica las copias. Sin push ni subagentes; revisión externa no realizada.
