# Vista de Guillermo de EV111 V2 (= EV110 + piloto de bosque), 2026-10-17

Cliente: `@DayZ_Baltic_EV111_ForestPilotV2`, misión BalticBasic, run ae304ba6-78af-4167-b657-a7208e21cf0f. Antes de la vista, el lanzador de
DayZ MCP estaba caducado porque Steam actualizó `DayZDiag_x64.exe` y `binarize.exe` (15-10). Con su permiso, se renovó con
`replace-dayz-test-v1` (buzón del pipeline fb-20261016-144210-11b4 y fb-20261016-155416-c9aa).

| Sitio | Lo que dijo | Diagnóstico | Arreglo en EV112 |
|---|---|---|---|
| Aparición en Narva (2392, 6948) | «agua de dos colores y a dos alturas» | Río en charca a 1,95–2,35 m contra hoya de mar del motor (fondo −2 m), dentro de la máscara `narva`, que EV102 no tocó | Presa vanilla en el escalón (decisión: «Presa vanilla»), más censo de los encuentros charca/mar restantes |
| kit-118 | «las piedras bien colocadas pero los montículos de tierra están descentrados y en el aire … todos en general» | 56 grupos de piedras: q p50 3,8–5,3 m frente a 2,27 m en Chernarus; base flotando p50 0,17–0,30 m, p90 0,84 m, máx. 1,18 m (Chernarus p50 −0,08, p90 0,42) | Kit v9: piedras a la q de Chernarus y base enterrada |
| Islote (6900, 10500) | «se ve bien pero queda suavizar esos caminos que hay hacia la isla por ambos lados» | Dientes residuales de 7–11 cm donde la plataforma llega al agua; el tramo 313 se rechazó | Terraplén de ancho constante en las 8 calzadas, con orillas paralelas al eje |
| 015-13 | «subiste un poco la esquina bajada, pero hay que nivelarlo un poco mejor» | Aire bajo el extremo del tablero, en todo el ancho | Puentes v6: nivelado bajo los extremos y taludes 1:1,5 |
| 015-13 | «la parte del río a ambos lados del puente cerca le falta smoothing» | Canal recto del corte con quiebros contra el río natural; la pasada de orillas excluía el corte | Puentes v6: entradas y salidas en curva, y orillas suavizadas en las zonas de corte |
| 015-16 | «aquí lo dejamos así de momento, el río al lado es totalmente poligonal» | Cauce fino de charca en zigzag (rumbo NE) | Kit en malla en los cauces finos poligonales de todo el mapa (decisión: «Kit en malla») |
| Ríos y laderas, en general | «montículos poligonales piramidales que suavizar (y lo mismo con montículos y ríos por todo el mapa)» | Vértices sueltos más altos que sus 6 vecinos, dejados por pasadas posteriores al suavizado de EV97 | Censo de pirámides, arreglo en su origen y pasada final de despike |
| Bosque A y B | «muy bien, queda alguna zona de suelo más oscuro donde debería haber árboles, pero casi perfecto» | Suelo de bosque sin árboles: bordes de los cuadrados del piloto y claros sobre textura de bosque | Bosque en todo el mapa y concordancia textura/árboles como puerta |

Sin comentario: la turbera (pino disperso) y el sector B se vieron sin quejas concretas.
Sigue abierto: las rampas de madera («tablero enrasado») y 015-25.
