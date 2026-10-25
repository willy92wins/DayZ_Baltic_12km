Revisión independiente y solo lectura de una corrección de instrumentación Enforce. No editar ni ejecutar juego.

Cambio vivo W: missions/BalticV30ContinuityNavV1.BalticTrial/init.c, bloque P de waypoints. Antes construía Vector(p[0],GetGame().SurfaceRoadY(p[0],p[2]),p[2]); ahora guarda X/Z y resultados nativos en floats y serializa strings separados. Consumidor tools/navigation/verify_continuity_nav_v30.py NO modificado; tests/test_continuity_nav_consumer.py conserva negativos XZ erróneos, suelo, rutas y semántica de negativos. 2 tests focales pasan. APIs reales P:/scripts/3_game/global/game.c:1176-1177, SurfaceY/SurfaceRoadY. Solo servidor, sin estado de cliente/red.

Prueba actual R=E:/DayZ-Baltic-Build/shape-repair-20261025:
navmesh-guarded-e-v9/generation.json e inspection.json: segunda generación terminó; TESM9/VAND12,983x983tiles12.5m,966289teselas; hash599b0ba7..., inputsE exactos. package-guarded-e-nav-v9/verification.json: solo NM sustituido; otras6826entradas exactas.
navmesh-guarded-e-v9-probe/result.json y runtime.log: todas37consultas cumplen conectividad, pero13 registros roadSample tienen X=0 y consumidorrechaza. No se ocultó ese FAIL.
navmesh-guarded-e-v9-probe-b/runtime.log, diagnostic.log,result.json,host-identity.json,mcp-identity.json: misma geometría/referencia/umbrales; en MISMA ejecución108waypoints el constructor antiguo falla13X, la forma con temporales0;37consultas+alturas PASS. diagnostic.log registra también componente legacyX antes de ToString, por lo que no es solo concatenación/representación. init.c diagnóstico en C:/temp/DayZ_MCP_130_dev/mpmissions/BalticGuardedENavV9B.BalticTrial/init.c.

Fuente final limpia preparada en C:/temp/DayZ_MCP_130_dev/mpmissions/BalticGuardedENavV9C.BalticTrial/init.c (solo el cambio W, header/log renombrados); conserva37queries exactas. Aún NO ejecutada porque F está midiendo4749puntos. Se exige su propia pasada antes de cerrar. No atribuir navE aF. No aceptar IA física/cliente/global por estas consultas.

Matiz de identidad descubierto: native_process_guard.py:70-93 de DayZ_MCP_dev calcula executable_sha256 de ruta normalizada con prefijo, NO bytes. R/navmesh-guarded-e-v9/identity-schemes.json reconcilia y fija digest real exe a500be804... Las futuras evidencias distinguen MCPidentity vsfiledigest. No modificar MCP ni credenciales.

Pide SOUND / SOUND-with-fixes / NEEDS-WORK, bugs concretos path:line, posibles falsos PASS o afirmaciones de causa excedidas. No inventes garantías; distingue aceptación local y límites. No hace falta reenviar informe a ningún chat.
