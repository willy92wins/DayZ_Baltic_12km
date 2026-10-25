# Experimento acotado: arrancar el generador sin .nm propio previo

El servidor con -startNavmeshDataServer se inició mediante MCP, run
a23141ac-c7ac-4ff2-9f4e-718464ecb7e7. El argv real contiene el literal nuevo.
NavMeshGenerator mostró Data Server Connected y Receiving world params; el
motor mostró Unable to load navmesh for BalticTrial. Tras aceptar el aviso,
el generador perdió la conexión y desaparecieron las ventanas del motor.
Stop oficial: succeeded, forced_kill, exit_metrics_valid=false. No Mission.

Fuente primaria que explica el comportamiento esperado desde 1.18:
https://forums.dayz.com/topic/252788-experimental-update-118-change-log/
El juego se cierra si no encuentra la navegación configurada. La guía de
generación sigue diciendo que puede prescindirse de .nm, sin explicar este
bootstrap. No concluir que el servidor de datos evita la carga previa.

Referencia de autor en foro oficial para el arranque temporal:
https://forums.dayz.com/topic/243693-how-to-load-custom-map-into-server-for-testing/
Ruta vanilla verificada: P:/DZ/worlds/chernarusplus/world/config.cpp:47.

[DESIGN] Discriminador de una variable: addon temporal separado, dependiente
de BalticTrialWorld, cambia solo BalticTrial.Navmesh.navmeshName a la ruta
vanilla existente. PBO del terreno, WRP, alturas, materiales y parámetros de
generación quedan idénticos. No actores IA ni aceptación de rutas sobre esa
navegación prestada. Es una excepción técnica de bootstrap al plan inicial
de no reutilización; la salida final debe ser un .nm nuevo del Baltic.

PASS bootstrap: mundo y misión propios cargan, generador recibe sus parámetros
y comienza una generación nueva. FAIL: reaparece error o no se reciben
parámetros. Un fallo requiere diagnóstico antes de repetir. Al acabar, retirar
el addon temporal, empaquetar el .nm propio y probar el mapa sin este addon.
Conservar hash exacto del WRP usado para generarlo; no rebinarizar después.

## Resultado verificado

Bootstrap y generación completados; navegación propia cargada sin bootstrap.
Fuente actual: `evidence/navmesh/checkpoint.json`. El primer bootstrap fue
ignorado por el empaquetado con config.cpp vacío; sonda efectiva y contraste
con config.bin idéntico aislaron el cambio. No repetir esa forma de paquete.
