# Discriminador aislado Luga 4/5 — 02/03-10-2026

Run `0428d12b-e1b2-4be3-aca2-3d6c535ce6b2`, mismo mundo916948ec,
aguae9b52b8c, controladorc5414ffe, rutas y criterios congelados df205b7a.
Sin builds, mosaicos ni Computer Use propios durante el movimiento.
Memoria libre observada al inicio ~7,75GiB; no aislamiento de toda la carga del host.

- Caso4 PASS: 553 muestras, hueco máximo0,702s, salud600 constante.
- Caso5 FAIL solo `monotone_continuous_clock`: 529 muestras, hueco máximo0,929s
  frente a0,8s. Todos los criterios físicos pasan: llegada/parada, salud, suelo,
  trayectoria, waypoints, mando y movimiento. Paso máximo1,024872m.
- Ambos END/ARRIVED_AND_STOPPED, registro final ALL_CASES_COMPLETE.
- Error máximo de suelo0,000143352m. Log SHA562b12dcdaa5789d9876e62006d530a407ceb91dfce822358e2fd82dd32a8783.

Veredicto del consumidor íntegro: **FAIL_OR_INCOMPLETE**. El único intento adicional
del subplan ya se consumió. No se modifican umbrales ni se reclasifica el run original
d0f7811a (6/8). El caso4 aislado aporta nueva evidencia; caso5 sigue abierto.
La reducción de las pausas no demuestra su causa ni rendimiento multijugador.
No hay evidencia aquí de encallamiento, daño o ruptura física del cauce.

Cierre orderly_close en2,588s, run retirado, lease liberado; self none,
pending_commands0 y banco vacío al cierre. Logs completos verificados en
`E:/DayZ-Baltic-Build/v30-luga-validation/runtime-0428d12b`; manifiesto logs-archive.json.
La recuperación del editor puede continuar independientemente; cualquier nuevo
ensayo temporal necesita un diagnóstico y un subplan diferente antes de ejecutarse.

Análisis posterior sin nueva ejecución: `clock-gap-analysis.json` localiza un
único intervalo superior a0,8s entre las líneas717–718 del log, caso5,
78,410→79,339s. La lancha recorre0,915420m, conserva salud600 y registra29
callbacks de entrada; el objetivo de ruta no cambia. La mediana de intervalos
es0,502s en ambos casos. La profundidad registrada en esas columnas se mide
desde la hélice y NO es el calado del canal. El registro no tiene ancla absoluta
de inicio ni traza del planificador del host: causa temporal INCONCLUSA y
veredicto original intacto. Mecanismo de registro leído en la misión desplegada:
`init.c:69,93,135–149` (CallLater100ms, una fila cada cinco callbacks de misión).
