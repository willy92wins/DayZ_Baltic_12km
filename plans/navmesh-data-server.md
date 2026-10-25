# Servidor de datos para generar navegación

Estado: PREPARADO, SIN ARRANQUE. La autorización específica del usuario para
NavMeshGenerator llegó el 29-09-2026 durante la continuación posterior a la sonda.
La aplicación abrió correctamente. Su menú ofrece Connect Data Server y mantiene
Start Generation desactivado antes de conectar. Se observó el destino local
127.0.0.1; no se inició generación ni se creó ningún .nm.

## Entrada concreta y resultado exigido

- Mundo `BalticTrial`, PBO de agua/materiales
  `e3e6b3614301950f423bf55f1819cdd4bef9743e3323f29d7669ce5a66251283`.
  No atribuirle pruebas del juego antes de desplegar y comparar el hash real.
- Misión independiente `missions/empty.BalticTrial/init.c`, sin inicializar CE,
  población ni jugador; config preparada `tests/navmesh/ServerDZNV.cfg`.
- Salida propia configurada en el addon:
  `dayz_baltic_12km_dev\tb\narva_trial\navmesh\baltic_trial.nm`.
  Guardar primero en un destino nuevo, registrar hash y WRP binarizado asociado.
- No reutilizar navegación de otro mapa ni declarar éxito por llegar al 100%:
  guardar .nm, comprobar carga del mundo y validar recorrido IA después.

## Bloqueo comprobado

[EXACT] La guía oficial de Bohemia requiere un DayZDiag con rol servidor y
`-startNavmeshDataServer`, seguido de Connect Data Server, Start generation y
Save NavMesh. URL:
https://community.bistudio.com/wiki?title=DayZ:Generating_navigation_mesh

[EXACT] El contrato actual de `P:/DayZ_MCP_dev/tools/dayz_mcp/server.py:5681-5707`
no expone esa opción. `dayz_test_request.py:14-40` usa una lista cerrada de
campos; `dayz_test_worker.py:262-283` construye los argumentos de servidor sin
la opción. No existe un argumento libre que pueda pasarse legítimamente.
No se modificó DayZ_MCP ni se insertaron argumentos dentro de rutas.

[EXACT] El runbook compartido exige el launcher registrado para lifecycle de
agente. Abrir NavMeshGenerator no inicia ese servidor. La autorización de la
herramienta no amplía por sí sola el contrato de lanzamiento de DayZ_MCP.

## Cambio aprobado por el usuario

Guillermo respondió: «Añadir y validar la opción en DayZ_MCP». La ampliación
acotada queda autorizada. Se trabaja sobre una copia Git aislada de la base
real 28f76cd, conservando el launcher compartido hasta pasar las pruebas.

[DESIGN] Añadir al launcher compartido una opción booleana tipada
`navmesh_data_server`, falsa por defecto, válida solo con modo servidor. Debe
atravesar API, validación/canonicalización, request del launcher y worker;
el worker añade únicamente el literal `-startNavmeshDataServer`.
Conservar identidades, lease, cola, ownership y cierre por run_id. Rechazar
combinaciones con cliente/offline y comprobar compatibilidad de requests
anteriores. El registro del bundle debe actualizarse por el procedimiento
autoritativo de DayZ_MCP después del rebuild; no relajar verificaciones.

Validación propuesta: casos positivos/negativos de request; argv del servidor
con y sin la opción; rechazo en otros modos; casos heredados sin nuevo campo;
integración del bundle; único arranque real con PBO y misión fijados, conexión
efectiva del generador y cierre verificado del run propio. Una prueba fallida
se diagnostica antes de otro arranque. Añadir además rechazo previo a cola y
takeover en la API pública; un request inválido no debe cerrar otro run.

Alternativa: que el usuario gestione manualmente el servidor de datos fuera
del lifecycle de agentes. No se preparó un bypass ni se ejecutó un launcher
por una shell alternativa.

## Límites actuales

El aviso anterior de navegación impedía confirmar Mission. La documentación
afirma que un terreno puede cargar sin .nm: esa discrepancia sigue sin causa
aislada. Generar el archivo es un paso necesario para IA y una prueba útil,
pero no garantiza por sí solo resolver el arranque ni completar la versión básica.
