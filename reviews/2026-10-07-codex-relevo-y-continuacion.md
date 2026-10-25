# Revisión del relevo de Claude y continuación de Baltic — 07-10-2026

**Veredicto: SOUND-with-fixes para retomar el trabajo; base 1.0 no aceptada.** Los artefactos de V12 corresponden al relevo. Hay que acotar las conclusiones de renderizado y ampliar el plan para el suavizado pedido hoy. No se ha editado el mapa ni iniciado un run de juego en esta revisión.

Consumidor: Guillermo y la siguiente ejecución sobre la rama `claude/codex-handoff-review-74f290`. Revisión de `4382029394f27f7e256fe410eee71285134b449b`, sin subagentes.

Petición viva: revisar el relevo y continuar con smoothing y renderizado a media/larga distancia. Guillermo precisó **orillas, cauces y relieve general**. Esa ampliación está incorporada a la propuesta de abajo; no equivale a aceptar V11/V12 ni a cambiar niveles, Narva o requisitos de navegación.

## Árbol y base correctos

Raíz de todas las referencias de código de este informe:
`C:/Users/guill/OneDrive/Documentos/DayZ Projects/DayZ_Baltic_12km_dev/.claude/worktrees/codex-handoff-review-74f290`.

El directorio inicial `P:/DayZ_Baltic_12km_dev` está en `v29-base`, commit `994d9d4`, y su HANDOFF es del 04-10. La ruta física de C: contiene el mismo documento antiguo: no es una divergencia de OneDrive. `git worktree list --porcelain` localizó el árbol actual de Claude, cuyo HANDOFF es del 07-10. No hacer merge ni reconstruir desde el árbol antiguo por su puntero automático.

La aceptación de V10b está escrita por decisión, no inferida de mtime: `evidence/v30-v10-candidate-2026-10-06/decisions/aceptacion-v10b.json:4`. V11 y V12 siguen sin aceptar (`HANDOFF.md:33`). V12 es candidata sobre V11, no otra base ya validada.

## Comprobación ejecutada

Intérprete: `C:/Users/guill/Documents/Codex/2026-09-29/vamos/work/gis-env/Scripts/python.exe`, `PYTHONUTF8=1`, `PYTHONDONTWRITEBYTECODE=1`.

[Script reproducible](../evidence/v30-handoff-review-2026-10-07/recheck.py) y [resultado](../evidence/v30-handoff-review-2026-10-07/recheck.json). Salida 0, `PASS_DELTA_AND_DEPLOY_ONLY`.

- NPZ V11 `6e452bd3`, V12 `8b3a8c55`; alturas finitas; **21.777 vértices**, todos navegables y todos elevados. Máximo +7,012607 m. Ningún otro array cambia, incluidas clases, niveles y máscaras.
- Calado nominal en los vértices modificados: **1,000–2,175 m**. No prueba ancho útil entre vértices, margen con oleaje ni circulación de una embarcación.
- Despliegue releído: mundo `f0813174748ef648ccfcfdee82c375a2becf7e1691b6a310c6ef07dcf720cccf`; agua `07c5295f112746d621e96324467b1d54fccc415a785c227feb245f59adff503f`. Hashes y tamaños coinciden con el recibo. `chain.log` acaba en `done v12`.
- Los informes guardados conservan `FAIL` del verificador general: un fallo de calado y 21 de esquinas de piezas; `channel-reaches.json` los acota a las zonas sustituidas por cauces y conserva un vértice mojado sin pieza. No son nuevos fallos demostrados por esta revisión. Carreteras registradas: PASS en 77.381 muestras; no se repitió el consumidor físico.
- Las caras de orilla >35° bajan de 2.322 a 1.273 en los informes V11/V12. No es una aceptación visual ni demuestra por sí solo que ninguna cara empeore.
- Revisadas las imágenes `evidence/baltic-019-teselas-oscuras-2026-10-07/figures/panels.jpg` y `evidence/v30-v11-candidate-2026-10-06/figures/river-ends-engine.png`: detalle cercano con banda media oscura, control Chernarus defectuoso y finales cuadrados visibles.

## Hallazgos del relevo

### P2 — La atribución de BALTIC-019 excede el experimento

`HANDOFF.md:38` declara que las teselas no son del mapa y `HANDOFF.md:17` atribuye la carga al cliente sin foco. El control con Chernarus demuestra que el síntoma **no es exclusivo de Baltic**. No aísla el foco como causa ni excluye otro defecto simultáneo de LOD/materiales del mapa.

Evidencia: `evidence/baltic-019-teselas-oscuras-2026-10-07/README.md:7`, `:73` y `:115`: el propio registro conserva la prueba de foco como inconclusa y no probó el cliente retail. Los dos intervalos breves de foco se mezclan con el tiempo transcurrido desde el teletransporte.

Corrección propuesta: escribir «síntoma reproducido en Chernarus con el mismo método; sospecha de carga del cliente, foco sin aislar; aceptación de distancia de Baltic pendiente». No aumentar smoothing ni cambiar capas para intentar corregir este síntoma antes de separar las causas.

### P2 — El índice global <0,2 no basta para declarar válida una vista

`HANDOFF.md:69` conserva solo el umbral en su receta. `tools/playtest/dark_tiles_v30.py:21-35` promedia bloques planos/oscuros en el 55 % inferior, sin identificar tierra ni banda de distancia. Puede ocultar una franja pequeña defectuosa y puntuar agua legítima como oscuridad.

Contraejemplo real: END_GRIB_40 tiene 0,1541 y 0,1441 en `evidence/baltic-019-teselas-oscuras-2026-10-07/reports/dark-tiles-v11.jsonl:23-24`, y la franja oscura sigue visible en la figura de finales. El README del ensayo sí añade inspección visual en `:81`; esa condición no debe perderse al ejecutar el handoff.

Corrección propuesta: mantener el índice como alarma auxiliar. Aceptar por zonas de tierra fijadas antes del ensayo, inspección de cada banda cercana/media/lejana y ausencia de bordes anómalos. Agua separada. Una imagen puede ser útil para forma de orilla y no para color/LOD; registrar ambos juicios.

### P2 — El mínimo de 1 m está demostrado en lo elevado, no en toda la red

La frase «cada vértice navegable ... siempre ... 1,0 m» de `evidence/v30-v12-candidate-2026-10-07/README.md:15` y el comentario de `scripts/chain_v12.sh:4` es demasiado amplia. `tools/terrain/profile_inland_v30.py:312-319` excluye Narva, borde, piezas de cauce y componentes no perfiladas, y solo eleva fondos inferiores al objetivo; no ahonda someros existentes.

Repro: `recheck.py`. Sobre el corte normalizado a float32 de 0,80 m hay 31.953 vértices navegables interiores; **4.030 conservan menos de 1 m nominal y ninguno fue modificado por V12**. Incluyen orillas y zonas excluidas: esto no demuestra un canal bloqueado. Sí impide certificar toda la red con el mínimo calculado en los vértices cambiados.

Corrección propuesta: acotar la afirmación al conjunto cambiado, medir caras y secciones del corredor útil real con agua mínima y probar la lancha en ambos sentidos. El contrato P9 mantiene margen para barcos medianos (`product-spec.md:15`); una prueba de lancha no acepta automáticamente ese margen.

## Cambio necesario del plan: smoothing en tres ámbitos

El generador actual no cubre toda la petición nueva. `tools/water/smooth_water_outlines_v30.py:199-220` solo cambia ríos/estanques y lagos de contorno; conserva navegables, delta, arroyos y bandas de río de contorno. V11 lo llama con sigma 12 m y desplazamiento nominal 4 m (`evidence/v30-v11-candidate-2026-10-06/scripts/chain_v11.sh:40`). Aumentar ese sigma no arreglará por sí solo los dientes del Luga ni el relieve seco.

El relieve procede de `tests/relief_v30/relief_v30_mix.npz` (`tools/terrain/build_v30.py:366-368`), mezcla de zonas altas y llanos (`tools/terrain/design_relief_v30_mix.py:1-7`). El límite de pendiente de 35° es distinto de suavidad: no controla todos los cambios bruscos de normales entre caras.

Atención a las máscaras: `terrain_inland.npz::reserve` viene de reservas **viales** (`tools/terrain/build_v30.py:408-413`). No debe confundirse con la reserva natural. Para proteger naturaleza se debe reanclar su máscara específica; `tools/terrain/finish_shores_v30.py:137` lee `reference.npz::reserve` de `tests/regional_outline_v1`.

## Propuesta [DESIGN] de continuación

Se modifica el orden del relevo para resolver la observación antes de aceptar visualmente más geometría. No se cambian las decisiones de niveles ni la aceptación histórica de V10b. Esta propuesta no es una implementación ni una aprobación de una base nueva.

1. **Render a media/larga distancia, sobre paquete fijo.** V12 por hash ya comprobada. Comparar aparición directa en un sector y llegada por teletransporte, con pose/clima/FOV/distancia de visión fijos y foco registrado. Incluir control Chernarus del mismo procedimiento. Para comprobar foco, capturar antes/durante/después y usar zonas nuevas equivalentes o invertir el orden para evitar confundir carga acumulada con efecto del foco. No forzar foco por script: el handoff lo prohíbe en `:111`. Una prueba con ventana activa requiere que Guillermo la mantenga delante. Si sigue inconcluso, registrarlo y pasar al discriminador retail/configuración; no declarar cerrado BALTIC-019 por esperar seis minutos.
2. **V12 como candidato de agua.** Revisar aparición, navegable grande, transición baja y Narva. Separar textura terrestre de espuma/oleaje/color del mar bajo el río (BALTIC-018). Adaptar y comprobar el consumidor de lancha citado en `HANDOFF.md:73-82`; no heredar el PASS del piloto de otra geometría. El calado de todas las secciones obligatorias y el recorrido real deben pasar; no aceptar solo la cota de vértices modificados.
3. **Piloto de smoothing en tres superficies, sin reconstruir todo el mapa en cada intento.** Congelar V12 y el diseño firmado como referencias. Seleccionar orillas del conjunto RIVER_80, Luga navegable y un sector de relieve seco con carreteras/cimas. Para los contornos ya compatibles, comparar sigma 18 y 24 m frente a 12 m conservando el presupuesto nominal de desplazamiento de 4 m; verificar el desplazamiento real final después de restaurar áreas. Son parámetros de ensayo, no valores elegidos para producción. Para navegables hace falta una máscara/perfil explícito que conserve el corredor útil. Para relieve seco, suavizar irregularidad local conservando silueta y alturas regionales, con transición suave a carreteras, orillas y zonas protegidas. No aplicar un blur uniforme a todo el heightmap.
4. **Aceptar con consumidores independientes.** Medir línea de agua extraída de los triángulos contra el diseño original congelado, por sector y clase; no medir únicamente contra el contorno producido por la misma variante. El auditor actual también tiene exclusiones (`tools/water/audit_waterline_v30.py:47-49`), que deben ampliarse o complementarse para Luga. Comparar curvatura/cambio de normales y perfiles del relieve, identidad fuera de las máscaras autorizadas, todas las clases/niveles, carreteras con estaciones congeladas, islas, reserva natural y calado con agua mínima. Repetir imágenes cerca/media/lejos bajo el método validado. Una mejora agregada no compensa un sector obligatorio peor.
5. **Integración y pendientes.** Elegir la intensidad visual con las comparativas; construir solo el candidato elegido. Finales de río (Volkhov/Grib/Msta): el redondeo de una celda no basta, ensayar transición longitudinal de varias celdas manteniendo conectividad y regla del borde. Mantener pendientes explícitos los tramos bajos/Narva, RIVER_80 somero, lagos 269/170 y BALTIC-012/013 con el contrato vigente. Después de congelar geometría: Terrain Builder, paquete final, navmesh, grafo e IA; BALTIC-014 no se cierra con la NM anterior. Población, ferrocarril y 80–100 jugadores siguen fuera de este bloque.

Presupuesto propuesto: baseline y dos intensidades en el piloto offline, selección de una y como máximo una corrección acotada antes de reconsiderar el mecanismo. Fijar sectores, métricas y negativos antes de generar; PASS solo si todas las puertas obligatorias pasan, FAIL ante regresión reproducible, INCONCLUSO ante vista no válida/consumidor no ejecutado. Es propuesta para la siguiente unidad, sin bucle ni generación iniciados aquí. Fuente de parada: `C:/Users/guill/.claude/skills/gates-ledger/SKILL.md:409-430`.

## Estado al cierre de esta revisión

Solo se añaden este informe, el script/JSON de evidencia y el relevo de sesión. Sin cambios en generadores, terreno, PBO, HANDOFF/bugs compartidos o rama `v29-base`. Sin commit ni push: son artefactos de revisión, no una integración del trabajo de Claude. No hay lease ni run propio; `session_status` confirmó banco libre durante la revisión. El código de escena de las futuras pruebas no se ha implementado ni ejecutado.
