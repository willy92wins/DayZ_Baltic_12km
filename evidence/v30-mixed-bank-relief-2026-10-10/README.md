# Suavizado global de taludes EV80 — 10-10-2026

EV80 está desplegado en `P:/Mods/@DayZ_Baltic_MixedBankPreviewV1` y la lectura de alturas de todo el mapa pasa. Es una mejora geométrica comprobada, no la aceptación de la base 1.0 ni del render del agua.

- Fuente: EV79; candidato `0a18c5623885eed274cfe7d296e02aba290ed491b835d317213fc7876b2fc45b`. Dos agentes Luna: autoría y consumidor independiente. Se corrigieron fallos de implementación antes del único cálculo completo; los intentos inválidos están registrados y nunca produjeron un terreno utilizable.
- Alcance: vértices de tierra libres a 96 m o menos de ríos/arroyos, participantes en quiebros >30°. 4329 evaluados, 2591 editados; delta −0,2194 a +2 m. Metadatos, soporte mojado, P/F, reservas, plataformas y sus protecciones exactos.
- Consumidor independiente: energía angular de las bisagras modificadas −21,22%; p99 seco de ribera 5,00489→4,98207°. Cero quiebros nuevos >30°, cero máximos peores en 330 sectores modificados. Quiebros mixtos >30°: 4693→3384. El informe residual distingue grados de libertad y protecciones; no equivale a haber eliminado todos los taludes poligonales.
- Modelos compilados: 10429 caras físicas y 14978 visibles intersectadas en 1335 celdas; 0 m² de agua ganada o perdida. Los 18033 objetos y materiales del WRP son idénticos a EV79.
- Superficie: 459 teselas regeneradas con su margen, 565 intactas por identidad de entradas, 2308 solapes sin diferencias. Cambian 720 píxeles de máscara y 3401 de satélite. Compresión: 2410 píxeles húmedos de borde no-grava inventariados; ninguno en el interior a >=4 píxeles del borde. No afirmar cero sobre toda la huella.
- Paquete: 132 PAA y el WRP cambian; 6694/6827 entradas exactas. 1056 mipmaps nuevos verificados, con controles negativos. Revisión independiente del PBO fuente/desplegado en PASS.
- Motor: run `fea3ba4e-88a5-48ae-92f3-c10732f9e192`, solo servidor y sin file patching. 4194304 vértices, 1212 puntos y 1205 planos; error máximo 1,52588e−5 m. Siete negativos detectados. Los puntos de control y sus planos no cambian respecto a EV79.
- Inventario nativo: 25 flags ausentes de agua de diseño, 317 escalares sin flag y 3 lecturas dinámicas en playa. Las tres playas conservan altura 0,8000–0,8032 m, bajo el mar en la fase muestreada; ninguno de los 5 flags A o 88 escalares Q añadidos cae en un vértice editado. No es un cierre del shader ni una comparación de fases iguales.
- RPT conserva mensajes de entorno/animación y stack PluginItemDiagnostic; no se declara limpio. Censo completo y cierre orderly confirmados, lease liberado y banco libre.

Diagnóstico posterior: de los 3384 quiebros residuales, 3167 tocan el selector original y 217 quedan íntegramente fijados por protecciones en sus esquinas de ribera. El replay único de 89,844 s reproduce exactamente las alturas EV80. Los 1275 rechazos p99 pasan los invariantes locales con un ULP hacia la altura previa; no se aplicaron al replay ni se guardó el margen angular original por coordenada. No equivalen a imposibilidad geométrica. La aplicación conjunta requiere un candidato y consumidor separados: plan EV81 en `E:/DayZ-Baltic-Build/v30-mixed-bank-float32-20261010/plan.md`. EV80 sigue vigente hasta que pase ese proceso.

Identidades de distribución: mundo `ec3785d1eab89eb18503e358a9f7d786dca35f9eef829301bae45a1ec28d7038`; agua `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`; OPRW `3ae8f82cfc7279cec5c58dd8f253b9da79bfbfe52004695ebe02cb5587383680`.

Pendientes: rectángulos grises y agua aparente sobre tierra (sin causa local aislada), contornos mojados/giros/finales, niveles protegidos y excepciones EV68, decisión sobre grandes lagos, Terrain Builder y después navmesh. No reabrir pruebas visuales inválidas como si hubieran concluido. El ticket de foco ya existe; esta sesión no lo duplicó. EV79 anterior se conserva para rollback; EV68 sigue sin promoción.

Los NPZ/PBO completos permanecen en E:/P: identificados por hash. Aquí se conserva el delta reversible, scripts, resultados y referencias. La figura es geometría offline. Sin push.
