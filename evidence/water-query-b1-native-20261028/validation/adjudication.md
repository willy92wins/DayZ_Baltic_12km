Fable5.1 SOUND-with-fixes460.266s. Inputs íntegros durante revisión, sin permisos denegados.
Hallazgo1 aceptado: timestamp host100ns frente a psutil microsegundos, banda1ms únicamente para vincular serialización de identidad de proceso. PID/run/creación nativa de MCP siguen exactos; PS comprueba2ms. Sin cambiar ninguna tolerancia física.
Fixture propuesto necesitó mtime1s posterior a creación para no producir legítimamente stale_log.
Hallazgo2 aceptado: close=null ahora falla ValueError lifecycle_not_closed.
Contraejemplo propio: binder aceptaba file_patching=True. Añadido helper host exclusivo con detección filePatching y servermod; cualquier modo externo rechaza, y el binder exige ambos campos explícitos en before/after. Helper histórico intacto.
21tests binding+8mocks lifecycle PASS; timestamp1s y2.001ms rechazan, redondeo submicrosegundo acepta; filePatching verdadero/ausente y servermods extra rechazan; fallbackstop propio acepta y ajeno rechaza.
API130 reanclada: C:/temp/DayZ_MCP_130/tools/dayz_mcp/server.py:5391preflight y5777close. dayz_test_tool.py/request.py hashes idénticos al dev examinado. Política proyectoDayZ_MCP usa C:/temp/DayZ_MCP_130_dev/mpmissions y P:/Mods. No tocar MCP.
Reserva de adopción errónea: dejar incidente explícito y resolver oficialmente sólo propio; nunca tomar run ajeno.
Revisión independiente sobre fuentes previas archivadas; correcciones puntuales adjudicadas por Codex y tests, no fingir nueva revisión externa.
