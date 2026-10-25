# Inspeccion visual de la base V10

P2/P3/P9/P12/P13: repetir vistas conocidas sobre el paquete nativo definitivo,
con clima fijo, a nivel de jugador y desde alturas medias/altas. La sonda de
camara ya usada en `tests/outline-consumer-v2` se adapta a doce poses congeladas:
Narva y su puente, San Petersburgo/delta, Neva-Ladoga, reserva y dos relieves.

La sonda se carga como addon temporal solo en la prueba. No forma parte del
paquete del mapa. Guarda/restaura actividad, congelacion, pose, FOV y nearplane;
la distancia de vision temporal vuelve al valor conocido del perfil del ensayo.
Registrar la pose tres segundos despues de moverla y tambien tras restaurar.
Mantener cada vista45s para capturar por Computer Use; liberar CU entre bloques.

Vistas de jugador/medias usan el nearplane original. Las vistas aereas de
diagnostico usan10m para separar las franjas de profundidad ya aisladas antes;
no extender ese ajuste al jugador ni acreditar la vista original por ese ensayo.
Sin captura legible de cada pose, el resultado visual queda parcial.

Rechazar rectangulos de materiales, agua flotando fuera de su huella, huecos
del terreno y encuentros del puente incongruentes. Registrar por separado
limitaciones de textura provisional, distancia de dibujo y falta de mapeado.
Una captura aerea no valida flotacion, colision ni rendimiento multijugador.

APIs instaladas leidas: `P:/scripts/3_game/entities/camera.c` (SetActive,
SetNearPlane/GetNearPlane, SetFOV/GetCurrentFOV, LookAt, FreeDebugCamera) y
`P:/scripts/3_game/global/world.c:69-71` (distancia temporal frente a preferida).
La sonda precedente confirmo en motor que la lectura de camara en el mismo
frame puede seguir mostrando la pose anterior; se conserva la lectura diferida.

## Capturas del motor y coste del cliente, revision previa al ensayo

V2 conserva exactamente las doce poses y los tiempos de V1. Anade una captura
del propio motor por vista, a los25s, mediante MakeScreenshot: firma local en
scripts/1_core/proto/proto.c:134-141. Asi las imagenes pueden archivarse junto
al paquete probado. Computer Use sirve para observar/activar el cliente y se
libera cuando no se necesita. Un marcador de peticion no prueba la captura:
exigir archivo nuevo, DDS valido, dimensiones/pixeles y revision visual.

Registra cada segundo entre10 y40s los contadores nativos del cliente
GetLastFPS/GetAvgFPS/GetMinFPS/GetMaxFPS(64) y GetFPS; firmas y comentarios
leidos en global/game.c:868-906 y proto/proto.c:145-147. Se conservan como
medicion descriptiva del cliente, sin reutilizar la semantica no validada del
servidor headless. Excluir para el resumen el intervalo23-28s que contiene la
captura. Guardar ajustes/perfil y advertir camaras6-12km de diagnostico.
No variar calidad ni afirmar capacidad multijugador por estos contadores.

La restauracion registra ademas pose propia de FreeDebugCamera, nearplane,
actividad/congelacion y FOV guardados y finales. V1 se conserva sin ejecutar;
la revision V2 queda congelada y empaquetada antes de cargar el motor.
# Revision tras V2 (01-10 07:26 UTC)

V2 compiló y recorrió cámaras, pero `GetFPS()` generó excepciones «Function not
linked» y las peticiones de captura no produjeron archivos en las rutas
inspeccionadas. Se conserva el intento y se cierra ordenadamente. V3 elimina
solo ese contador global, manteniendo Last/Avg/Min/Max de DayZGame; no sustituye
el valor ausente por cero. Se adapta explícitamente el esquema a nueve columnas.
Las cámaras, tiempos, clima, restauración y criterios permanecen iguales.

La captura V3 usa el nombre simple que documenta `proto.c:134–141`, con salida
predeterminada ScreenShotes. Su eficacia sigue pendiente de archivo real. Si no
produce imágenes, observar las doce poses por Computer Use, vinculando cada
observación a la telemetría; no declarar evidencia de imagen por un marcador.

