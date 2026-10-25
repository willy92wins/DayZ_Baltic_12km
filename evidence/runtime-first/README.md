# Revisión del acceso y primera prueba en DayZ

29-09-2026. **El bloqueo de permisos está resuelto.** La sesión tiene acceso completo; `session_status` responde. `server_reload` actualizó el worker y `bridge_status` confirmó módulos frescos, sin petición de reconexión.

Se desplegaron el PBO y 16 archivos de misión en carpetas nuevas, comprobando sus hashes. PBO: `6d6b1c163412e92a221d8b7580e6943eec9818f7e08e894359e84b03fca582f0`. Se utilizó el proyecto de pruebas ya registrado `DayZ_MCP` con `@DayZ_Baltic_12km` como mod adicional, misión propia y file patching desactivado. No se modificaron políticas, registros ni código compartido de MCP.

## Resultado de consumidor

El preflight pasó. El lanzamiento real de servidor y cliente devolvió run `25d45413-a1d7-465a-98f1-86cf5ce7b14b`; se adoptó correctamente. Los procesos arrancaron, pero el puente nunca quedó listo y no se recibió la sonda de misión.

Un diálogo nativo de DayZ mostró **Unable to load navmesh for 'BalticTrial'.** El servidor generó un ErrorMessage minidump. Sus logs confirman módulos GameLib/Game/World, sin confirmación de Mission. No se ha inspeccionado la pila del minidump ni aislado la causa interna; no atribuir todo el fallo a una sola ausencia por el texto del diálogo.

La documentación oficial dice que el juego puede tolerar la ausencia de navmesh, aunque la IA no navegue. También requiere una clase Navmesh para configurar generación/carga. Nuestro config de ensayo aún no la incluye ni declara un .nm propio: ambos son pendientes concretos que hay que resolver/contrastar. [Guía oficial](https://community.bistudio.com/wiki?mobileaction=toggle_view_mobile&title=DayZ%3AGenerating_navigation_mesh&useskin=darkvector). El tracker oficial recoge el mismo mensaje y sugiere comprobar ruta y empaquetado; es una pista, no prueba de causa en este caso. [BI T190908](https://feedback.bistudio.com/T190908).

## Cierre y siguiente paso

Lease liberado y run exacto detenido por `dayz_test_stop`; resultado succeeded, stop forzado, sin métricas válidas de salida normal. Comprobación final: sesión sin lease, sin procesos de run, caja libre, cero comandos pendientes y cleanup sin degradación.

Siguiente paso: completar y contrastar la configuración Navmesh con el ejemplo oficial; preparar generación de un .nm correspondiente a este WRP mediante NavMeshGenerator (instalado). La receta oficial necesita `-startNavmeshDataServer`; la interfaz pública de `dayz_test_run` de esta sesión no expone ese argumento. Resolver esa integración mediante el flujo registrado, sin eludir el guard de procesos. No usar un .nm ajeno ni declarar IA validada por conseguir cargar el terreno.

[Recibo y logs](first-run.json) · [Despliegue verificado](deployment.json). La 1.0 sigue pendiente de carga, agua/cruces, contenido regional, CE/IA y rendimiento.
