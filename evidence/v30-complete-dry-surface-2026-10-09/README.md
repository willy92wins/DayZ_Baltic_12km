# EV72 — superficie completa sobre el terreno EV71

Estado: **OFFLINE_PASS_NATIVE_PENDING**. Base 1.0 incompleta. EV61 sigue siendo la última geometría comprobada dentro del motor.

Paquete preparado: `P:\Mods\@DayZ_Baltic_BaseSurfacePreviewV1`.

- Mundo: `a08b96a1f952edca98e525221ed48790051291b8fcc9db7cc7661ea8bacc1335`.
- Agua: `3946db8bf3a70ca6ae0253e15935fd6500c5fcdfc47551b3370238f39f02ae14`.
- Terreno: `b54963eb3cf5429c6192fb6f1e8f6d10c9a3cc397fdbabdf5c2f89cbabcf8e36`.
- WRP compilado: `d3924a80d1f7ffe31372858a465345efc6bee1df71aba66daa2d4358e747947f`.

Las 1.024 teselas se regeneran desde el terreno actual y P verificado. El consumidor independiente revisa 150,847,524 píxeles y 3.968 solapes. Ningún píxel fuente mojado usa otra superficie que grava; los interiores compilados también pasan. Las 4,323 mezclas DXT de borde se inventarían explícitamente.

Frente a las texturas EV67 cambian 88 satélites y 90 máscaras. Todas las demás entradas de paquete son exactas respecto a EV71; el WRP no cambia en este paso. Se decodifican los 1424 mipmaps nuevos y se contrastan con controles del conversor nativo. La truncación del payload se rechaza. Esto comprueba archivos, no la residencia de texturas en la GPU ni el fallo de streaming 019.

La misión `BalticBaseSurfaceFullWaterV1.BalticTrial` queda instalada, con 4.194.304 vértices, 1212 puntos y 1205 planos de agua. Lint: un archivo, cero errores. **No se ha ejecutado.** `offline-gate.json` enlaza los informes exactos y verifica de nuevo paquete y misión desplegados.

Continuación: recuperar herramientas publicadas de dayz-mcp, consultar ocupación y adquirir lease según el runbook, revalidar hashes y lanzar esta misión; ejecutar `verify_native.py` sobre el log nuevo. Después comparar vistas cargadas de puente, Msta, Volkhov y distancia. No aceptar una captura gris como referencia. Cerrar el run propio ordenadamente y liberar el lease. EV68/Volkhov se prueba aparte y requiere resolver su excepción 647/651 antes de promoción.

Pendientes del objetivo completo: reflejos residuales sin mecanismo cerrado, contornos todavía poligonales, grandes lagos reservados, 45 cruces de reserva vial, streaming, Terrain Builder y después navmesh/IA. El índice de bajos secos no convierte riesgos en defectos confirmados. El ticket de foco ya existe: `fb-20261008-233507-8b1c`.

Entorno: la UI indica conectado sin errores, pero `connector-availability.json` registra cero herramientas dayz-mcp disponibles para este turno. Sin nuevo run, lease ni bypass. El estado actual del banco compartido no se puede certificar.
