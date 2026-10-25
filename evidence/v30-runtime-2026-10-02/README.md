# V30: navegación verificada y revisión visual parcial

Actualización 02-10-2026, 12:58 UTC. Paquetes originales conservados: mundo `69140d41`, agua `e9b52b8c`, WRP `471dc77b`, NM `24baf069`.

| Prueba | Resultado y límite |
|---|---|
| Caminos nativos, e6c65771 | 9 positivos y NONE negativo PASS; 7 corrupciones del lector rechazadas. No locomoción física |
| Visita 46086176 | END;8, 24 muestras; ocho observadores secos, alturas coinciden con la fuente hasta 0,000468 m. Cierre orderly_close |
| Imágenes de esa visita | Siete sin menú: delta, Narva sur, arroyo, costa, terraplén, colinas y puente. Laguna descartada por obstrucción ajena |
| Cima d7f63f11 | Imagen válida en visual-followup/hills-peak.jpg; END;2 y cierre orderly_close |
| Repetición d66cfcaf | END;2 copiado; sin captura de laguna por Escape. Sin lease; run posteriormente retirado por el gestor, sin prueba de cierre ordenado |

En las vistas útiles no aparecen los grandes cuadros azules anteriores, pero no se acredita toda la superficie ni el LOD lejano. Narva sur conserva una orilla escalonada. Las colinas se ven desde la cima; no sustituye recorrer la reserva o todos los biomas. La toma pendiente de laguna no justifica reconstruir navmesh.

El run 46086176 conserva advertencias de CloudsEffect y recursos de diagnóstico/partículas en RPT; no se declara un log libre de avisos. Los logs crudos privados se archivan en E:/DayZ-Baltic-Build/navmesh-v30/{acceptance-runtime,visual-tour-resume-runtime,visual-followup-runtime}. Los hashes y cierres están junto a cada identidad.

Continuación sin Computer Use: [diagnóstico y copia corregida del Luga](../v30-offline-followup-2026-10-02/README.md). Esa copia no cambia los paquetes de estas capturas. Carga 80–100 pospuesta; pruebas físicas V29/V10 no se transfieren a V30.

La skill local dayz-terrain-workflow incorpora el límite de las capturas y el evaluador de canal. quick_validate no arranca por falta de PyYAML en los intérpretes comprobados; sin instalar dependencias. Validación manual de frontmatter y referencias, sin afirmar PASS del validador.

## Histórico de la primera interrupción

### Carga y navegación; interrupción inicial

02-10-2026, cierre 11:31:53 UTC. Mundo `69140d41`, agua `e9b52b8c`, WRP compilado `471dc77b`, navmesh `24baf069`; paquetes conservados.

- Run `e6c65771-1d46-4b2c-a9d9-c63c92b99a76`: carga cliente/servidor y jugador confirmados. `native-paths-result.json`: nueve rutas completas PASS (puente en ambos sentidos) y filtro NONE negativo PASS; `native-paths.log` termina en END;10. Son consultas del grafo, no locomoción física ni capacidad multijugador.
- `path-log-controls/result.json`: el registro original pasa y siete corrupciones se rechazan (truncado, mundo incorrecto, caso ausente, duplicado, extremo parcial, NaN y control negativo que tiene éxito). Controles offline del parser, no siete nuevas pruebas en el motor.
- `spb-player-view.jpg`: captura real desde jugador. `runtime-receipt.json`: cierre orderly_close. Logs crudos fuera de Git en `E:/DayZ-Baltic-Build/navmesh-v30/acceptance-runtime`.
- Visita `9dcd12b1-67fd-4f59-a238-2ba4911a4bf7`: misión temporal de ocho posiciones congeladas en `visual-tour-reference.json`; script-validator PASS, 1 archivo, 0 errores/avisos. Despliegue de init.c/sites.csv idéntico por SHA. No cambia el mod.
- La visita llegó a las mediciones de costa (etapa 4). El usuario detuvo Computer Use con Escape físico antes de su captura. `visual-tour/partial-tour.log` NO contiene END;8 y no es una aceptación completa.
- Hay tres imágenes reales con menú de pausa: Narva sur, arroyo y laguna. El menú no respondió al clic y a Escape automático; no se repitieron entradas tras esos dos intentos. La vista inicial de otra aplicación no se guardó. Los polígonos blancos de la primera carga del delta ya no aparecían en la siguiente vista; no se ha aislado su causa ni declarado un fallo persistente.
- Muestras: el mar informa min 0,5 / max 1 m. Cota pond Narva 2,625 m; laguna 7,425 m. Los cinco puntos de observación medidos están secos. No equivale a probar todas las orillas con marea máxima. Las muestras en bordes de celdas pueden leer la pieza vecina; no comparar una única celda como si fuese un plano continuo. GetWaterSurfaceHeightNoFakeWave también puede devolver objetos.
- En las partes visibles de las tres imágenes no reaparecen los grandes cuadros azules antiguos. Siguen pendientes vistas sin menú, costa/terraplén/colinas/puente y juicio visual global; BALTIC-007/009/010/011 permanecen abiertos.

## Cierre y siguiente paso

La visita se cerró con `orderly_close`, ambas terminaciones confirmadas, run retirado y lease liberado. Computer Use fue detenido por el usuario; no hubo más llamadas de control tras el Escape. Logs crudos en `E:/DayZ-Baltic-Build/navmesh-v30/visual-tour-runtime-interrupted`. Recibo: `visual-tour/interruption-receipt.json`.

Retomar la inspección visual cuando Guillermo indique continuar. No regenerar navmesh ni reconstruir el terreno por esta interrupción de UI. Conservar las pruebas físicas V29/V10 como históricas; no promoverlas a V30. La prueba 80–100 jugadores sigue pospuesta a un sector mapeado. No commit en este cierre: interrupción explícita del usuario; los cambios de la continuación quedan en el árbol, delimitados por esta carpeta, la misión visual y el plan/estado.
