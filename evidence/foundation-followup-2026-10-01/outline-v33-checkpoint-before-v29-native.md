# Base Baltic: continuación 2026-10-01T18:14:21.550962+00:00

V33 sigue siendo el candidato importado y probado; V10 permanece intacto.
La corrección conjunta de carreteras y orillas V29 está calculándose. Ninguna
variante vial V24-V28 fue importada. Estado de procesos: state.json.

## Hitos conservados

- Mundo V33 38ebe847, WRP2ccb8dc4, navmesh425b8488/446230080bytes;
  966289 teselas y paridad de6826 entradas restantes.
- Consumidor regional V6:81212 puntos/314 muestras nav/15 rutas PASS.
- Agua local:664 épocas/15936 muestras, margen seco mínimo0.28706m;
  positivo y18 negativos. No prueba todas las orillas ni máximo global de oleaje.
- Sur y reserva capturados; Neva repetido tras autorización de continuar,
  run333442bf EXITED_ORDERLY, cámara/restauración PASS, outline-v33-visual-neva-repeat/neva.png.
  Textura provisional y aspecto global pendientes;19FPS descritos con trabajo
  concurrente no son aceptación de rendimiento.
- Exportación editable V33:670 residuos de agua<=0.954micra, persistentes;
  derivados explícitos restauran solo esas Y para empaquetar. No export literal.

## Carreteras y orillas

V24 resolvió su matriz, pero FAIL independiente67ancho/4rasante/1cuerda y18caras
acuáticas cambiadas. El consumidor continuo detectó25extremos de margen local
insuficiente, máximo1.28494m, aunque81212puntos y las otras12puertas pasaban.

V25-V28 conservan certificados de inviabilidad: bandas omitidas por clasificar
solo extremos, soporte incompleto y congelación excesiva de caras compartidas.
V28:346filas imposibles; la cara382/1434/0 tiene tierra a3m de una huella de agua.
La banda river_contour_0019 está a0.475m y el suelo a6.8-8.2m: la intersección
vectorial no implica agua visible. La clasificación vial permanece intacta.

V29 añade condiciones continuas de orilla a las bandas completas, preservando
cauces/fairways, agua en vértices, Narva480m, reserva/islas, límites y muestras.
Matriz247942variables/10447089filas;83caras de orilla afectadas;1501condiciones
locales,1523suelo marino y33puntos congelados adicionales. Solver600/650s,
1hilo, sesión53494; no interpretar una ronda óptima como matriz completa PASS.
Plan: plans/road-network-v25-continuous-coverage.md, revisión explícita del collar.

Antes de importar: consumidor vial sin cambios, consumidor continuo V33 completo
con metadatos fijados, hidrología conjunta, reserva/Narva y negativos reales.
La igualdad de caras ya no se hereda: hay que demostrar de nuevo sus condiciones.
Después: importación aislada, poses y persistencia nativas, build exacto,
navmesh nueva, consumidor y pruebas físicas. No reutilizar navmesh con alturas nuevas.

Sin Computer Use ni DayZ abiertos; lease libre. Solo cálculo V29 propio.
Skill local dayz-terrain-workflow actualizada; evidencia road-continuous-coverage-skill-update.json.
Cuota18:10UTC:76% usado/24% disponible; ningún reset nuevo. No automatización nocturna nueva.
Sin commit: HEAD4ff154b7 y cambios compartidos anteriores conservados. No versión1.0.
Detalle del checkpoint anterior preservado en outline-v33-checkpoint-before-joint-roads.md.

Actualización 2026-10-01T18:22:21.119088+00:00: V29 completo527.687s/19rondas. ASC ed6cdaa5,25668vértices/cambio máximo5.079304m. Consumidor239126secciones PASS con0fallos;7negativos PASS; reserva/accesos/controles PASS. Continuo de orilla e hidrología conjunta pendientes. Solo sesión98671 activa; no solver vivo.

### V29 offline aceptado

ASC ed6cdaa5: consumidor vial independiente239126secciones,0fallos; geometria continua13/13,621260extremos secos y631284marinos sin violaciones,81212puntos congelados. Reserva/Narva y7negativos viales PASS. Hidrologia conjunta PASS mas4negativos reales, incluido el FAIL continuo V24.19caras acuaticas modificadas se aceptan por prueba continua nueva, no por igualdad. Falta importacion/persistencia, navmesh y consumo real de V29.
