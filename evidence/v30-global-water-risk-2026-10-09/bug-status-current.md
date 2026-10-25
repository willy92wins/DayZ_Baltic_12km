# Revisión de los veinte fallos: vigente hasta EV72

NativeContourV1 (EV13): mundo `40cffa8c`, agua `4d9359a4`, terreno `cff6d175`; censo completo y 439×62 PASS en sus controles. GlobalContourV1 (EV14): mundo `d72ebb45`, agua `3946db8b`, terreno `223029de`; fuente/cobertura completas y censo nativo pasan, temporal ampliado 674×62 PASS en sus controles. Las pruebas heredadas conservan su ámbito y fecha. No hay aceptación global visual ni revisión externa de estas unidades.

| ID | Estado actual y evidencia | Pendiente real |
|---|---|---|
| 001 | Abierto. La referencia gráfica reciente funcionó; un marcador diagnóstico distinto provocó una terminación nativa. | No atribuir ese crash al fallo histórico de cámara lejana ni declarar reparado el motor. |
| 002 | Cinco fuentes de persecución exactas, cotejo fresco. Apoyos de puente conservados. | IA y accesos sobre la navmesh final. |
| 003 | Dos fuentes de parada/ruta exactas. Viajes de lancha anteriores conservan alcance local. | No prueba de flotilla global. |
| 004 | Dos fuentes del observador exactas. | Repetir consumidor final; el PASS histórico no cubre todos los cauces. |
| 005 | Geometría vial EV18 PASS. Seis viajes frescos sobre EV16/23, 4.337 muestras, sin daños, contactos y suelo comprobados. | No equivale a toda la red, conductor humano ni rendimiento. |
| 006 | Seis viajes frescos completan llegada y parada; 18 negativos reales rechazan corrupciones. | IA y consumidores sobre navmesh final siguen pendientes. |
| 007 | EV70/71:27996 vértices secos ajustados respecto deEV61; fuente y compiladoPASS. Última pasada p99banco16.70260->16.69000, pliegues incidentes>30:89->50. | EV72sinmotor. Regresiones localesEV70/71 inventariadas. Contornos mojados, grandes lagos y aceptación artística abiertos. |
| 008 | Pospuesto explícitamente. | Capacidad 80–100 jugadores fuera de base 1.0. |
| 009 | EV71 cobertura compilada completa404484celdas:0hueco físico, residuo visible3.8464e-12m2.500objetos afectados sin cambio de exposición. | Lectura nativaEV72pendiente. EV64atribuyó cinco flags ausentes a objetos de puente; controles fluviales exactos. No cierre de oleaje/render por geometría. |
| 010 | EV72:1024teselas sobreEV71,150847524px y3968solapesPASS;88satélites+90máscaras cambiados y1424mips nuevosPASS. | Vistas sobreEV72, aceptación final yTerrainBuilder pendientes.4323mezclasDXT de borde inventariadas. |
| 011 | EV31 demuestra bruma ligada a distancia1600, desaparece a5000 y vuelve a1600 con camara/hora iguales. | Candidato exacto. Falta aceptacion de todo el contorno; no cierre019. |
| 012 | EV18: consumidor exacto de 19 corredores/36.494 caras, mínimo0,955609m. Seis viajes de lancha sobre candidato actual PASS y 11 negativos. | Viajes seleccionados, no cada cauce ni barcos medianos. |
| 013 | EV18: cuatro corredores delta/1.237caras, mínimo3,05m y cobertura de área exacta. | No aceptación para embarcaciones mayores. |
| 014 | Abierto. | Terrain Builder y Generate Layers sobre geometría aceptada, después navmesh e IA. |
| 015 | Cobertura compilada EV12/14 completa. EV44 reproduce diez matrices v11:687vértices cortados por regla vial.32 interrupciones plenamente atribuidas y13 parcialmente(4547/4592estaciones). | No aceptación ni reparación automática de cruces. Preservar P9/P11; distancia/coste gráfico pendientes. |
| 016 | EV54mejora local puente. EV70/71 completan bajos editables:2615/2760puntos a1.8m,145protegidos y0editables pendientes. Censo completo408zonas/726892m2. | MotorEV72pendiente; índice geométrico no equivale a408fallos. Shader sin identificar. No elevar automáticamente145protegidos. |
| 017 | EV39 insuficiente. EV40 mejora curvatura del talud35.5%/32.9% pero empeora contorno: RECHAZADO completo. Niveles y lechos exactos. | Decisión de niveles de grandes lagos reservada al usuario; ningún ensayo promovido. |
| 018 | EV54 corrige41de70masas bajas, lectura1205planosPASS. EV68 Volkhov: fondo1.01042m y profundidades/huellas conservadas; fuente y compiladoPASS,109objetos trasladados42.5cm. | EV68 pendiente lectura nativa/vistas y excepción647/651; no promovido. Msta comparte gran lago reservado. Bajos/Narva no cerrados globalmente. |
| 019 | EV30 audita todos16384mips por paqueteEV25/28; EV67yEV72 verifican cambios posteriores. EV72decodifica1424mips nuevos con controles nativos y negativo de truncación. | Streaming sin mecanismo cerrado. Ticket de foco existente fb-20261008-233507-8b1c. La UI MCP conectada sin tools es un bloqueo de entorno distinto. |
| 020 | EV55Msta yEV57Volkhov fuente/compilado/nativo PASS; incluyen controlcorrectodeanillos. | Peor esquinaMsta66.28igual; vistasdeaguabaja aun poligonales. Noaceptacionartistica ni cierre. |

Referencia vigente: `../v30-strict-dry-composition-2026-10-09/README.md`. CandidatoEV61 `StrictDryFloorV1`, mundo1423f25d, agua3946db8b, terreno7bcfae76. EV28/54/57preservados. EV56/60FAIL; seleccionEV61explicita. Noaceptacion global de20IDs ni base1.0. EV64 cerró orderly; ocupación actual desconocida con MCP no disponible.

EV62–66: `../v30-bridge-water-flag-probe-2026-10-09/README.md`. EV67 completa superficie offline; EV68 geometría/compilado PASS y listo para motor. Ver `../v30-volkhov-float-consistent-2026-10-09/README.md`. La UI MCP dice conectado pero el catálogo del chat no publica tools; no se ha lanzado el runtime nuevo.

EV70: `../v30-exact-dry-support-2026-10-09/README.md`. Preparado ExactDrySupportV1 mundo1853ff49; mantieneP/F/objetosEV61. Prioridad: lectura nativa y vistas con catalogo MCP restablecido. Ningun nuevo run propio.

EV71/72: `../v30-complete-dry-surface-2026-10-09/README.md`. Primera prueba pendiente: BaseSurfacePreviewV1, mundoa08b96a1. SustituyeEV70como siguiente candidato de prueba; EV61conserva la última validación nativa. Ningún nuevo run ni cierre global de20IDs.
