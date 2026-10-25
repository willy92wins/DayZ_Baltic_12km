# Persecución: separar muestras periódicas y eventos

Discriminador adicional previsto en pursuit-heading-v3.md; no cambia mapa,
navmesh, misión ni addon V3. Conservar la validación V3 estricta y sus logs.

Mecanismo leído: OnUpdate emite SAMPLE cada>=0.2s y también Record para NOISE,
SPAWN, MOVE_BEGIN y REACHED fuera de esa cadencia. El verificador V3 calcula
tasas entre todas esas filas. En el run9dea2177,0.101m en0.008s producen
12.66m/s; las muestras periódicas del mismo caso llegan a1.786m/s. Es una
incompatibilidad entre eventos y medición de tasa; no demuestra un impulso
físico ni un defecto de navmesh. Los FAIL anteriores permanecen.

[DESIGN] Verificador V4 para una repetición nueva con la misma misión V3:
- tasas calculadas entre SAMPLE consecutivos, manteniendo límites4/12m/s;
- cadencia mínima0.199s (scheduler0.2s y precisión del log), máxima1s ya fijada;
- muestras periódicas cubren todo el recorrido, extremos a<=1s de anclas;
- todos los eventos conservan contacto, salud, corredor, terreno y orden;
- posición de cada evento a distancia de la muestra periódica más cercana
  <=velocidad_límite*(distancia_temporal+0.2s). El margen de una muestra refleja
  la resolución temporal observada, no una afirmación sobre ticks internos;
- trayectorias, objetivos, adquisición, longitud y asentamiento sin cambios.

VERDE: control y dos cruces completos;15negativos anteriores más salto de
posición periódico, salto en evento irregular y falta de muestras periódicas.
Comprobar el gate específico de movimiento/cadencia en esas contrapruebas.
La aceptación tiene resolución200ms: no prometer ausencia de microajustes de
replicación por debajo de esa resolución. No usar este contrato para vehículos.

Presupuesto: una repetición física,20min máximo. Si aparece un nuevo fallo,
preservarlo y cambiar de gate; no volver a modificar criterios en este ciclo.
Preflight sobre los mismos hashes; cierre exacto y archivo de cada run.

## Cierre de la sonda cliente, antes del nuevo arranque

V3 también conservó client_end=false: el gestor cerró el run mediante
forced_kill y el cliente no ejecutó OnMissionFinish. El servidor sí había
registrado todos los casos. No inventar ni añadir el END ausente a ese archivo.

[EXACT] BalticPursuitClient.c solo llama BalticPursuitRelease en DEADMAN o
OnMissionFinish. La fase sincronizada vuelve a0 tras acabar cada caso.
[DESIGN] Paquete/misión V4: tras observar fase3 y después fase0, liberar los
overrides y cerrar los archivos de la sonda con END;PROBE_COMPLETE. Un fallo
del servidor también puede llevar a0; por eso el verificador sigue exigiendo
los tres REACHED y END;ALL_CASES_COMPLETE del servidor. No cambia movimiento.
Cabeceras/rutas V4 nuevas y hashes congelados antes del primer run V4.
